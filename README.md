# 🚍 City-Run SmartTicket

> Intelligent Bus Ticketing System for Hyderabad TSRTC — featuring QR-based ticket validation, ML-powered predictions, and a real-time analytics dashboard.

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.1-000000?logo=flask&logoColor=white)
![SQLite](https://img.shields.io/badge/Database-SQLite-003B57?logo=sqlite&logoColor=white)
![scikit-learn](https://img.shields.io/badge/ML-scikit--learn-F7931E?logo=scikit-learn&logoColor=white)
![Render](https://img.shields.io/badge/Deployed-Render-46E3B7?logo=render&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-22c55e)

---

## 📌 Overview

**City-Run SmartTicket** is a full-stack web application built for the **Hyderabad TSRTC** bus network. Passengers can book tickets online and receive **QR-coded tickets with dynamic expiry timers**, ensuring seamless, fraud-resistant travel.

The platform integrates a **machine learning layer** for fare prediction, crowd estimation, route recommendation, and peak-hour detection — making it an end-to-end intelligent transport solution.

🌐 **Live Demo:** (https://city-run-smartticket-main.onrender.com)

---

## 🖼️ Screenshots

> _Add screenshots or a demo GIF here._

---

## 🏗️ Architecture

```
Passenger / Conductor (Browser)
            ↓
    Frontend (HTML5 + CSS3 + JS + Chart.js)
            ↓
    Backend (Flask REST APIs + JWT Auth)
            ↓
  ┌─────────────────────────────────────┐
  │  SQLite Database  │  ML Predictor   │
  │  (Routes, Users,  │  (Fare, Crowd,  │
  │   Tickets, Logs)  │   Route Rec.)   │
  └─────────────────────────────────────┘
            ↓
    QR Code Engine (qrcode + Pillow)
```

---

## 🧰 Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | HTML5, CSS3, JavaScript, Chart.js |
| Backend | Python, Flask 3.1, Flask-CORS |
| Auth | Custom JWT (HS256, cookie + Bearer token support) |
| Database | SQLite (development) — PostgreSQL-ready for production |
| QR Code | `qrcode`, `Pillow` |
| ML Models | `scikit-learn` — Linear Regression, Random Forest, Decision Tree |
| Deployment | Render (free tier) |

---

## 🎯 Features

### 🎫 Smart Ticket Booking
- Supports multiple TSRTC routes with 10–20 stops per route
- Automatic fare calculation using a trained ML model
- QR code generated per ticket with a **30-minute dynamic expiry**
- Real-time countdown timer with visual alerts on the ticket

### 🛣️ Routes & Stops
- Forward and return journey toggle
- Live stop search with instant filtering

### 🔐 Authentication & Roles
- JWT-based authentication (cookie + Authorization header)
- Role-based access control: **Passenger / Conductor / Admin**
- Secure registration, login, and session management

### 📊 Analytics Dashboard
- Booking history tracking per user
- Active vs. expired ticket status
- Interactive charts via Chart.js

### 🤖 Machine Learning Predictions

| Model | Algorithm | Purpose |
|-------|-----------|---------|
| Fare Predictor | Linear Regression | Estimate ticket fare based on distance and time |
| Crowd Estimator | Regression | Predict passenger load per route |
| Route Recommender | Random Forest | Suggest optimal routes to passengers |
| Peak Hour Detector | Decision Tree | Identify high-demand time windows |

---

## 🔌 REST API Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `POST` | `/api/register` | ❌ | Register a new user |
| `POST` | `/api/login` | ❌ | Obtain JWT token |
| `GET` | `/api/routes` | ✅ | List all available routes |
| `POST` | `/api/fare` | ✅ | Predict fare for a trip |
| `POST` | `/api/book` | ✅ | Book a ticket |
| `GET` | `/api/bookings` | ✅ | View booking history |
| `GET` | `/api/predict/crowd` | ✅ | Crowd estimation |
| `GET` | `/api/predict/route` | ✅ | Route recommendation |

---

## 🗂️ Project Structure

```
City_Run_Bus/
└── transport_ticketing/
    ├── backend/
    │   ├── app.py              # Flask app — routes, JWT, DB logic
    │   └── ml_predictor.py     # ML model serving layer
    ├── frontend/
    │   ├── templates/
    │   │   ├── index.html      # Passenger interface
    │   │   └── conductor.html  # Conductor QR scanner
    │   └── static/
    │       ├── css/style.css
    │       └── js/app.js
    ├── ml_models/
    │   └── train_models.py     # Model training scripts
    ├── database/
    │   ├── init_db.py          # Schema initializer
    │   └── transport.db        # SQLite database
    ├── requirements.txt
    ├── render.yaml             # Render deployment config
    └── run.py                  # App entry point
```

---

## ▶️ Getting Started

### Prerequisites
- Python 3.11 or above
- Git

### Installation

```bash
# Clone the repository
git clone https://github.com/Manasvinaidu27/City_Run_Bus.git
cd City_Run_Bus/transport_ticketing

# Windows
python -m venv .venv
.venv\Scripts\activate

# macOS / Linux
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start the application
python run.py
```

Open your browser at `http://localhost:5000`

---

### Common Issues

| Problem | Fix |
|---------|-----|
| `python` not recognized | Reinstall Python and check "Add to PATH" |
| `pip` not recognized | Use `pip3` instead |
| Port already in use | Set `PORT=5001` env variable and retry |
| Module not found | Run `pip install -r requirements.txt` again |

---

## 🌍 Deployment (Render)

This project is pre-configured for **Render** via `render.yaml`.

1. Push this repository to GitHub.
2. Go to [render.com](https://render.com) → **New Web Service**.
3. Connect your GitHub repo.
4. Render auto-detects the `render.yaml` and sets:
   - **Build:** `pip install -r requirements.txt`
   - **Start:** `python run.py`

### Environment Variables

| Variable | Description |
|----------|-------------|
| `PORT` | Port for the server (auto-set by Render) |
| `SECRET_KEY` | Flask/JWT secret key |

---

## 🔐 Current Limitations

- No persistent media storage on free hosting
- SQLite is suitable for development; use PostgreSQL in production
- ML models are trained on synthetic/sample data
- Free tier spins down after inactivity (~30s cold start)

---

## 🚀 Planned Enhancements

### Scalability
- Migrate to PostgreSQL / MySQL
- Redis caching for high-traffic routes
- Move to FastAPI (async) for improved throughput

### Security
- Two-factor authentication
- OAuth login (Google)
- API rate limiting & HTTPS enforcement

### Real-Time Features
- Live bus tracking with WebSockets
- ETA prediction per stop
- Push notifications for ticket expiry and arrivals

### Payments
- UPI / card payment integration
- Payment confirmation before QR generation

### ML Improvements
- LSTM for time-series crowd prediction
- Dynamic (surge) pricing model
- Automated model retraining pipeline
- Feature expansion: weather, events, holidays

### DevOps
- Dockerize backend + frontend
- GitHub Actions CI/CD (test → lint → deploy)
- Deploy backend on AWS / frontend on Vercel

---

## 🌟 Key Highlights

- Full-stack development — Frontend, Backend, REST API, ML
- Real-world problem: public transport in Hyderabad
- End-to-end ML integration (4 models in production flow)
- Secure JWT authentication with role-based access
- QR ticket system with dynamic expiry logic
- Production deployment on Render

---

## 🤝 Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Commit your changes (`git commit -m 'Add your feature'`)
4. Push to the branch (`git push origin feature/your-feature`)
5. Open a Pull Request

---

## 👨‍💻 Author

**Manasvi Naidu** — [GitHub @Manasvinaidu27](https://github.com/Manasvinaidu27)

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
