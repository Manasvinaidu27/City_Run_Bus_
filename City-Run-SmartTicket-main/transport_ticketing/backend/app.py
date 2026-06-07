from flask import Flask, request, jsonify, render_template, session
from flask_cors import CORS
import sqlite3
import uuid
import qrcode
import io
import base64
import json
import hashlib
import hmac
import time
from datetime import datetime, timedelta, date
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from ml_predictor import predict_crowd, recommend_routes, predict_fare

app = Flask(__name__, template_folder='../frontend/templates', static_folder='../frontend/static')
app.secret_key = 'tsrtc_hyd_2024_secret_jwt'
CORS(app)

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'transport.db')
# ─── JWT ──────────────────────────────────────────────────────────────────────

JWT_SECRET = 'tsrtc_jwt_secret_2024_hyderabad'

def _b64url(data):
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode()

def _b64url_decode(s):
    pad = 4 - len(s) % 4
    return base64.urlsafe_b64decode(s + '=' * pad)

def generate_token(user_id, role, name):
    header = _b64url(json.dumps({'alg': 'HS256', 'typ': 'JWT'}).encode())
    payload = _b64url(json.dumps({
        'sub': user_id, 'role': role, 'name': name,
        'exp': int(time.time()) + 86400
    }).encode())
    sig = _b64url(hmac.new(JWT_SECRET.encode(), f'{header}.{payload}'.encode(), 'sha256').digest())
    return f'{header}.{payload}.{sig}'

def verify_token(token):
    try:
        parts = token.split('.')
        if len(parts) != 3:
            return None
        header, payload, sig = parts
        expected = _b64url(hmac.new(JWT_SECRET.encode(), f'{header}.{payload}'.encode(), 'sha256').digest())
        if not hmac.compare_digest(sig, expected):
            return None
        data = json.loads(_b64url_decode(payload))
        if data.get('exp', 0) < int(time.time()):
            return None
        return data
    except Exception:
        return None

def hash_password(pw):
    return hashlib.sha256((pw + JWT_SECRET).encode()).hexdigest()

def get_current_user():
    auth = request.headers.get('Authorization', '')
    if auth.startswith('Bearer '):
        return verify_token(auth[7:])
    token = request.cookies.get('auth_token')
    if token:
        return verify_token(token)
    return None

def require_auth(f):
    from functools import wraps
    @wraps(f)
    def wrapper(*args, **kwargs):
        user = get_current_user()
        if not user:
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, user=user, **kwargs)
    return wrapper

def require_role(*roles):
    from functools import wraps
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            user = get_current_user()
            if not user:
                return jsonify({'error': 'Authentication required'}), 401
            if user.get('role') not in roles:
                return jsonify({'error': 'Insufficient permissions'}), 403
            return f(*args, user=user, **kwargs)
        return wrapper
    return decorator

# ─── DB ───────────────────────────────────────────────────────────────────────

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT DEFAULT 'passenger',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS routes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            route_number TEXT NOT NULL,
            route_name TEXT NOT NULL,
            stops TEXT NOT NULL,
            base_fare REAL DEFAULT 5.0,
            fare_per_km REAL DEFAULT 1.2
        );

        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            booking_id TEXT UNIQUE NOT NULL,
            user_id INTEGER,
            passenger_name TEXT NOT NULL,
            phone TEXT NOT NULL,
            route_id INTEGER NOT NULL,
            from_stop TEXT NOT NULL,
            to_stop TEXT NOT NULL,
            travel_date TEXT NOT NULL,
            travel_time TEXT NOT NULL,
            passengers INTEGER DEFAULT 1,
            fare REAL NOT NULL,
            qr_code TEXT,
            qr_expires_at TIMESTAMP,
            status TEXT DEFAULT 'active',
            boarded_at TIMESTAMP,
            scanned_by INTEGER,
            booked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(route_id) REFERENCES routes(id),
            FOREIGN KEY(scanned_by) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS travel_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            route_id INTEGER,
            from_stop TEXT,
            to_stop TEXT,
            travel_date TEXT,
            travel_time TEXT,
            passengers INTEGER,
            crowd_level INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.commit()
    _seed_routes(c, conn)
    _seed_default_users(c, conn)
    conn.close()

def _seed_default_users(c, conn):
    c.execute("SELECT COUNT(*) FROM users WHERE role='conductor'")
    if c.fetchone()[0] > 0:
        return
    c.execute("INSERT INTO users (name, email, phone, password_hash, role) VALUES (?,?,?,?,?)",
              ('TSRTC Conductor', 'conductor@tsrtc.in', '9000000000',
               hash_password('conductor123'), 'conductor'))
    c.execute("INSERT INTO users (name, email, phone, password_hash, role) VALUES (?,?,?,?,?)",
              ('Demo User', 'demo@tsrtc.in', '9876543210',
               hash_password('demo123'), 'passenger'))
    conn.commit()

def _seed_routes(c, conn):
    c.execute("SELECT COUNT(*) FROM routes")
    if c.fetchone()[0] > 0:
        return
    routes = [
        ("8A", "Secunderabad ↔ Mehdipatnam",
         json.dumps(["Secunderabad Bus Stand","Clock Tower","Paradise","Begumpet","Ameerpet",
                     "Punjagutta","Panjagutta X Roads","Khairatabad","Lakdi Ka Pul","Nampally",
                     "Abids","Koti","Sultan Bazar","Mozamjahi Market","Afzalgunj","Chaderghat",
                     "Malakpet","Dilsukhnagar","Chaitanyapuri","LB Nagar","Mehdipatnam"]),
         5.0, 1.2),
        ("1P", "MGBS ↔ Miyapur",
         json.dumps(["Mahatma Gandhi Bus Station (MGBS)","Imlibun","Nampally","Abids","Koti",
                     "Afzalgunj","Malakpet","Dilsukhnagar","Uppal","Habsiguda","Tarnaka",
                     "Mettuguda","Secunderabad","Begumpet","Ameerpet","SR Nagar","Erragadda",
                     "Bharat Nagar","Balanagar","Kukatpally","JNTU","Miyapur"]),
         5.0, 1.3),
        ("90L", "Charminar ↔ Hitec City",
         json.dumps(["Charminar","Shalibanda","Chaderghat","Afzalgunj","Nampally","Abids","Koti",
                     "Sultan Bazar","Mozamjahi Market","Ameerpet","Punjagutta","Begumpet",
                     "Somajiguda","Raj Bhavan","Khairatabad","Masab Tank","Mehdipatnam",
                     "Tolichowki","Manikonda","Gachibowli","DLF Cybercity","Hitec City"]),
         5.0, 1.5),
        ("188", "LB Nagar ↔ Gachibowli",
         json.dumps(["LB Nagar","Chaitanyapuri","Dilsukhnagar","Malakpet","Chaderghat","Afzalgunj",
                     "MGBS","Nampally","Abids","Koti","Ameerpet","Punjagutta","Begumpet",
                     "Somajiguda","Raj Bhavan","Khairatabad","Mehdipatnam","Tolichowki",
                     "Manikonda","Gachibowli"]),
         5.0, 1.4),
        ("8X", "Uppal ↔ Lingampally",
         json.dumps(["Uppal","Habsiguda","Tarnaka","Mettuguda","Secunderabad","Paradise","Begumpet",
                     "Ameerpet","SR Nagar","Erragadda","Bharat Nagar","Balanagar","Kukatpally",
                     "JNTU","Miyapur","Chandanagar","Nizampet","Bachupally","Lingampally"]),
         5.0, 1.2),
        ("224", "Secunderabad ↔ Shamshabad Airport",
         json.dumps(["Secunderabad Bus Stand","Paradise","Begumpet","Ameerpet","Khairatabad",
                     "Lakdi Ka Pul","Nampally","MGBS","Chaderghat","Malakpet","LB Nagar",
                     "Vanasthalipuram","Saroor Nagar","Kothapet","Nagole","Uppal",
                     "Hayathnagar","Pedda Amberpet","Shamshabad","RGIA Airport"]),
         8.0, 1.5),
    ]
    c.executemany("INSERT INTO routes (route_number, route_name, stops, base_fare, fare_per_km) VALUES (?,?,?,?,?)", routes)
    import random
    random.seed(42)
    stops_sample = ["Secunderabad","Ameerpet","MGBS","Charminar","LB Nagar","Hitec City","Miyapur"]
    for _ in range(200):
        hour = random.randint(0, 23)
        crowd = min(100, max(0, int(30 + 60*abs(hour-9)/9 if hour < 12 else 30+60*abs(hour-18)/6 + random.randint(-10, 10))))
        c.execute("""INSERT INTO travel_history (route_id,from_stop,to_stop,travel_date,travel_time,passengers,crowd_level)
                     VALUES (?,?,?,?,?,?,?)""",
                  (random.randint(1, 6), random.choice(stops_sample), random.choice(stops_sample),
                   "2024-01-15", f"{hour:02d}:00", random.randint(1, 4), crowd))
    conn.commit()

# ─── Initialize DB on startup (runs on Render too) ────────────────────────────
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
init_db()

# ─── AUTH ROUTES ──────────────────────────────────────────────────────────────

@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.json or {}
    name  = data.get('name', '').strip()
    email = data.get('email', '').strip().lower()
    phone = data.get('phone', '').strip()
    pw    = data.get('password', '')

    if not all([name, email, phone, pw]):
        return jsonify({'error': 'All fields are required'}), 400
    if len(pw) < 6:
        return jsonify({'error': 'Password must be at least 6 characters'}), 400
    if '@' not in email:
        return jsonify({'error': 'Invalid email address'}), 400
    if len(phone) < 10:
        return jsonify({'error': 'Invalid phone number'}), 400

    conn = get_db()
    if conn.execute("SELECT id FROM users WHERE email=?", (email,)).fetchone():
        conn.close()
        return jsonify({'error': 'Email already registered'}), 409

    conn.execute("INSERT INTO users (name, email, phone, password_hash, role) VALUES (?,?,?,?,?)",
                 (name, email, phone, hash_password(pw), 'passenger'))
    conn.commit()
    user = conn.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
    conn.close()

    token = generate_token(user['id'], user['role'], user['name'])
    return jsonify({
        'token': token,
        'user': {'id': user['id'], 'name': user['name'], 'email': user['email'], 'role': user['role']}
    }), 201

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.json or {}
    email = data.get('email', '').strip().lower()
    pw    = data.get('password', '')

    if not email or not pw:
        return jsonify({'error': 'Email and password required'}), 400

    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
    conn.close()

    if not user or user['password_hash'] != hash_password(pw):
        return jsonify({'error': 'Invalid email or password'}), 401

    token = generate_token(user['id'], user['role'], user['name'])
    return jsonify({
        'token': token,
        'user': {'id': user['id'], 'name': user['name'], 'email': user['email'], 'role': user['role']}
    })

@app.route('/api/auth/me', methods=['GET'])
@require_auth
def me(user):
    conn = get_db()
    u = conn.execute("SELECT id, name, email, phone, role, created_at FROM users WHERE id=?",
                     (user['sub'],)).fetchone()
    conn.close()
    if not u:
        return jsonify({'error': 'User not found'}), 404
    return jsonify(dict(u))

# ─── CONDUCTOR: QR SCAN ───────────────────────────────────────────────────────

@app.route('/api/conductor/scan', methods=['POST'])
@require_role('conductor', 'admin')
def conductor_scan(user):
    data = request.json or {}
    raw = data.get('booking_id', '').strip().upper()
    booking_id = raw.replace('TSRTC:', '')

    if not booking_id:
        return jsonify({'valid': False, 'message': '❌ booking_id is required', 'status': 'invalid'}), 400

    conn = get_db()
    b = conn.execute("SELECT * FROM bookings WHERE booking_id=?", (booking_id,)).fetchone()

    if not b:
        conn.close()
        return jsonify({'valid': False, 'message': '❌ Ticket not found', 'status': 'invalid'}), 404

    b = dict(b)

    if b['qr_expires_at']:
        try:
            if datetime.fromisoformat(b['qr_expires_at']) < datetime.now():
                conn.execute("UPDATE bookings SET status='expired' WHERE booking_id=?", (booking_id,))
                conn.commit()
                conn.close()
                return jsonify({'valid': False, 'message': '⛔ QR Expired', 'status': 'expired',
                                'booking': _safe_booking(b)})
        except Exception:
            pass

    if b['status'] == 'expired':
        conn.close()
        return jsonify({'valid': False, 'message': '⛔ Ticket already expired', 'status': 'expired',
                        'booking': _safe_booking(b)})

    if b['status'] == 'boarded':
        conn.close()
        return jsonify({'valid': False, 'message': '⚠️ Passenger already boarded', 'status': 'duplicate',
                        'booking': _safe_booking(b)})

    now_iso = datetime.now().isoformat()
    conn.execute("UPDATE bookings SET status='boarded', boarded_at=?, scanned_by=? WHERE booking_id=?",
                 (now_iso, user['sub'], booking_id))
    conn.commit()
    conn.close()

    b['status'] = 'boarded'
    b['boarded_at'] = now_iso
    return jsonify({
        'valid': True,
        'message': '✅ Valid Ticket — Passenger Boarded!',
        'status': 'boarded',
        'booking': _safe_booking(b)
    })

def _safe_booking(b):
    return {
        'booking_id': b['booking_id'],
        'passenger_name': b['passenger_name'],
        'phone': b['phone'],
        'from_stop': b['from_stop'],
        'to_stop': b['to_stop'],
        'travel_date': b['travel_date'],
        'travel_time': b['travel_time'],
        'passengers': b['passengers'],
        'fare': b['fare'],
        'boarded_at': b.get('boarded_at')
    }

@app.route('/api/conductor/stats', methods=['GET'])
@require_role('conductor', 'admin')
def conductor_stats(user):
    conn = get_db()
    today = date.today().isoformat()
    total   = conn.execute("SELECT COUNT(*) FROM bookings WHERE travel_date=?", (today,)).fetchone()[0]
    boarded = conn.execute("SELECT COUNT(*) FROM bookings WHERE travel_date=? AND status='boarded'", (today,)).fetchone()[0]
    active  = conn.execute("SELECT COUNT(*) FROM bookings WHERE travel_date=? AND status='active'", (today,)).fetchone()[0]
    revenue = conn.execute("SELECT SUM(fare) FROM bookings WHERE travel_date=?", (today,)).fetchone()[0] or 0
    recent  = conn.execute("""SELECT booking_id, passenger_name, from_stop, to_stop, fare, status, boarded_at
                               FROM bookings WHERE travel_date=? ORDER BY boarded_at DESC LIMIT 10""",
                           (today,)).fetchall()
    conn.close()
    return jsonify({
        'today': today,
        'total_bookings': total,
        'boarded': boarded,
        'active': active,
        'revenue': round(revenue, 2),
        'recent_scans': [dict(r) for r in recent]
    })

# ─── MAIN ROUTES ──────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/conductor')
def conductor_page():
    return render_template('conductor.html')

@app.route('/api/routes', methods=['GET'])
def get_routes():
    conn = get_db()
    routes = conn.execute("SELECT * FROM routes").fetchall()
    conn.close()
    result = [dict(r) for r in routes]
    if len(result) == 0:
        init_db()
        conn = get_db()
        routes = conn.execute("SELECT * FROM routes").fetchall()
        conn.close()
        result = [dict(r) for r in routes]
    return jsonify(result)
    
  

@app.route('/api/stops', methods=['GET'])
def get_all_stops():
    conn = get_db()
    routes = conn.execute("SELECT stops FROM routes").fetchall()
    conn.close()
    all_stops = set()
    for r in routes:
        all_stops.update(json.loads(r['stops']))
    return jsonify(sorted(list(all_stops)))

@app.route('/api/fare', methods=['POST'])
def calculate_fare():
    data = request.json
    route_id    = data.get('route_id')
    from_stop   = data.get('from_stop')
    to_stop     = data.get('to_stop')
    passengers  = data.get('passengers', 1)
    travel_time = data.get('travel_time', '10:00')

    conn = get_db()
    route = conn.execute("SELECT * FROM routes WHERE id=?", (route_id,)).fetchone()
    conn.close()
    if not route:
        return jsonify({'error': 'Route not found'}), 404

    stops = json.loads(route['stops'])
    try:
        fi = stops.index(from_stop)
        ti = stops.index(to_stop)
        distance = abs(ti - fi)
    except ValueError:
        distance = 5

    fare = predict_fare(route['base_fare'], route['fare_per_km'], distance, travel_time, passengers)
    return jsonify({'fare': round(fare, 2), 'distance_stops': distance})

@app.route('/api/book', methods=['POST'])
def book_ticket():
    try:
        data = request.json or {}
        required = ['passenger_name', 'phone', 'route_id', 'from_stop', 'to_stop',
                    'travel_date', 'travel_time', 'passengers', 'fare']
        for r in required:
            if r not in data or not data[r]:
                return jsonify({'error': f'Missing or empty field: {r}'}), 400

        try:
            travel_dt = datetime.strptime(data['travel_date'], '%Y-%m-%d').date()
        except ValueError:
            try:
                travel_dt = datetime.strptime(data['travel_date'], '%d-%m-%Y').date()
            except ValueError:
                return jsonify({'error': 'Invalid travel date format (use YYYY-MM-DD)'}), 400

        today    = date.today()
        tomorrow = today + timedelta(days=1)
        if travel_dt < today:
            return jsonify({'error': 'Cannot book for past dates. Only today/tomorrow.'}), 400
        if travel_dt > tomorrow:
            return jsonify({'error': 'Bookings only for today/tomorrow.'}), 400

        try:
            route_id   = int(data['route_id'])
            passengers = int(data['passengers'])
            fare       = float(data['fare'])
        except (ValueError, TypeError):
            return jsonify({'error': 'Invalid route_id, passengers, or fare'}), 400

        user    = get_current_user()
        user_id = user['sub'] if user else None

        booking_id = str(uuid.uuid4())[:8].upper()
        expires_at = (datetime.now() + timedelta(hours=24)).isoformat()
        qr_data = f"TSRTC:{booking_id}"
        qr = qrcode.QRCode(version=1, box_size=6, border=3)
        qr.add_data(qr_data)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        qr_b64 = base64.b64encode(img_bytes.getvalue()).decode()

        conn = get_db()
        conn.execute("""
            INSERT INTO bookings
              (booking_id, user_id, passenger_name, phone, route_id, from_stop, to_stop,
               travel_date, travel_time, passengers, fare, qr_code, qr_expires_at, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (booking_id, user_id, data['passenger_name'], data['phone'], route_id,
              data['from_stop'], data['to_stop'], data['travel_date'], data['travel_time'],
              passengers, fare, qr_b64, expires_at, 'active'))
        conn.execute("""
            INSERT INTO travel_history
              (route_id, from_stop, to_stop, travel_date, travel_time, passengers, crowd_level)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (route_id, data['from_stop'], data['to_stop'], data['travel_date'],
              data['travel_time'], passengers, 50))
        conn.commit()
        conn.close()

        return jsonify({'booking_id': booking_id, 'qr_text': qr_data, 'qr_b64': qr_b64, 'expires_at': expires_at})

    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({'error': f'Booking failed: {str(e)}'}), 500

@app.route('/api/bookings/<booking_id>', methods=['GET'])
def get_booking(booking_id):
    conn = get_db()
    b = conn.execute("SELECT * FROM bookings WHERE booking_id=?", (booking_id,)).fetchone()
    conn.close()
    if not b:
        return jsonify({'error': 'Not found'}), 404
    b = dict(b)
    if b['qr_expires_at'] and datetime.fromisoformat(b['qr_expires_at'].split('.')[0]) < datetime.now():
        conn = get_db()
        conn.execute("UPDATE bookings SET status='expired' WHERE booking_id=?", (booking_id,))
        conn.commit()
        conn.close()
        b['status'] = 'expired'
    return jsonify(b)

@app.route('/api/bookings', methods=['GET'])
def get_all_bookings():
    user = get_current_user()
    conn = get_db()
    if user:
        rows = conn.execute("SELECT * FROM bookings WHERE user_id=? ORDER BY booked_at DESC LIMIT 50",
                            (user['sub'],)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM bookings ORDER BY booked_at DESC LIMIT 50").fetchall()

    now = datetime.now()
    updated = False
    for row in rows:
        b = dict(row)
        if b['qr_expires_at']:
            try:
                if datetime.fromisoformat(b['qr_expires_at']) < now and b['status'] not in ('expired', 'boarded'):
                    conn.execute("UPDATE bookings SET status='expired' WHERE booking_id=?", (b['booking_id'],))
                    updated = True
            except Exception:
                pass
    if updated:
        conn.commit()

    if user:
        rows = conn.execute("SELECT * FROM bookings WHERE user_id=? ORDER BY booked_at DESC LIMIT 50",
                            (user['sub'],)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM bookings ORDER BY booked_at DESC LIMIT 50").fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route('/api/predict/crowd', methods=['POST'])
def crowd_prediction():
    data = request.json
    result = predict_crowd(data.get('route_id', 1), data.get('travel_time', '10:00'))
    return jsonify(result)

@app.route('/api/predict/routes', methods=['POST'])
def route_recommendation():
    data = request.json
    result = recommend_routes(data.get('from_stop', ''), data.get('to_stop', ''))
    return jsonify(result)

@app.route('/api/ml/insights', methods=['GET'])
def ml_insights():
    conn = get_db()
    history = conn.execute("SELECT travel_time, crowd_level FROM travel_history").fetchall()
    conn.close()
    hourly = {}
    for row in history:
        try:
            h = int(row['travel_time'].split(':')[0])
            if h not in hourly:
                hourly[h] = []
            hourly[h].append(row['crowd_level'])
        except Exception:
            pass
    hourly_avg = {h: round(sum(v)/len(v)) for h, v in hourly.items()}
    return jsonify({'hourly_crowd': hourly_avg})

@app.route('/api/expire_check', methods=['POST'])
def expire_check():
    data = request.json
    booking_id = data.get('booking_id')
    conn = get_db()
    conn.execute("UPDATE bookings SET status='expired' WHERE booking_id=?", (booking_id,))
    conn.commit()
    conn.close()
    return jsonify({'status': 'expired'})

if __name__ == '__main__':
    print("✅ Database initialized")
    print("🔐 Auth: POST /api/auth/login  |  POST /api/auth/register")
    print("📷 Conductor panel: http://localhost:5000/conductor")
    print("   Demo credentials: conductor@tsrtc.in / conductor123")
    print("🚌 Server: http://localhost:5000")
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)