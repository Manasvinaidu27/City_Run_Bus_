/* ─── app.js — TSRTC SmartTicket Frontend ─── */

const API = '';

let routesData = [];
let currentRouteIdx = 0;
let currentDirection = 'forward';
let countdownTimer = null;
let currentBookingId = null;
let qrExpiry = null;
let pendingBookingData = null;   // holds form data between payment & booking
let selectedPayMethod = 'upi';

// ─── INIT (handled in auth section below) ──────────────────

function setDefaultDate() {
  const d = document.getElementById('travel-date');
  if (d) {
    const today = new Date().toISOString().split('T')[0];
    const tomorrow = new Date(Date.now() + 86400000).toISOString().split('T')[0];
    d.min = today; d.max = tomorrow; d.value = today;
  }
  const t = document.getElementById('travel-time');
  if (t) {
    const now = new Date();
    t.value = `${String(now.getHours()).padStart(2,'0')}:${String(now.getMinutes()).padStart(2,'0')}`;
  }
}

// ─── TAB NAVIGATION ───────────────────────────────────────
function showTab(name, btn) {
  document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
  document.getElementById('tab-' + name).classList.add('active');
  if (btn) btn.classList.add('active');
  else {
    const tabs = document.querySelectorAll('.nav-tab');
    const map = { book:0, routes:1, mytickets:2, insights:3 };
    if (tabs[map[name]]) tabs[map[name]].classList.add('active');
  }
  if (name === 'routes') renderRouteTabs();
  if (name === 'mytickets') loadMyTickets();
  if (name === 'insights') loadInsights();
}

// ─── ROUTES ───────────────────────────────────────────────
async function loadRoutes() {
  try {
    const res = await fetch(`${API}/api/routes`);
    routesData = await res.json();
    const sel = document.getElementById('route-select');
    sel.innerHTML = '<option value="">-- Select Route --</option>';
    routesData.forEach(r => {
      const opt = document.createElement('option');
      opt.value = r.id;
      opt.textContent = `${r.route_number} – ${r.route_name}`;
      sel.appendChild(opt);
    });
  } catch (e) { console.error(e); }
}

function loadStops() {
  const routeId = parseInt(document.getElementById('route-select').value);
  const route = routesData.find(r => r.id === routeId);
  const fromSel = document.getElementById('from-stop');
  const toSel   = document.getElementById('to-stop');
  fromSel.innerHTML = '<option value="">-- From Stop --</option>';
  toSel.innerHTML   = '<option value="">-- To Stop --</option>';
  if (!route) return;
  const stops = JSON.parse(route.stops);
  stops.forEach(s => {
    fromSel.innerHTML += `<option value="${s}">${s}</option>`;
    toSel.innerHTML   += `<option value="${s}">${s}</option>`;
  });
  calcFare();
}

// ─── FARE CALCULATION ─────────────────────────────────────
async function calcFare() {
  const routeId = document.getElementById('route-select').value;
  const from    = document.getElementById('from-stop').value;
  const to      = document.getElementById('to-stop').value;
  const pax     = parseInt(document.getElementById('passengers').value);
  const time    = document.getElementById('travel-time').value;
  if (!routeId || !from || !to || from === to) return;

  try {
    const res  = await fetch(`${API}/api/fare`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ route_id: parseInt(routeId), from_stop: from, to_stop: to, passengers: pax, travel_time: time })
    });
    const data = await res.json();
    document.getElementById('fare-base').textContent = '₹5.00';
    document.getElementById('fare-stops').textContent = `${data.distance_stops} stops`;
    document.getElementById('fare-total').textContent = `₹${data.fare.toFixed(2)}`;
    const h = parseInt(time.split(':')[0]);
    const note = (h>=7&&h<=10)||(h>=17&&h<=20) ? '⚡ Peak hour surcharge applied'
               : pax>=4 ? '🎉 Group discount applied' : '';
    document.getElementById('fare-note').textContent = note;
    document.getElementById('fare-box').classList.remove('hidden');

    // Update pay button amount
    const btnAmt = document.getElementById('btn-book-amount');
    if (btnAmt) btnAmt.textContent = `₹${data.fare.toFixed(2)}`;

    updateCrowdInline(routeId, time);
  } catch (e) { console.error(e); }
}

async function updateCrowdInline(routeId, time) {
  try {
    const res  = await fetch(`${API}/api/predict/crowd`, {
      method: 'POST', headers: {'Content-Type':'application/json'},
      body: JSON.stringify({ route_id: parseInt(routeId), travel_time: time })
    });
    const data = await res.json();
    const icons = { 'Low': '🟢', 'Moderate': '🟡', 'High': '🟠', 'Very High': '🔴' };
    document.getElementById('crowd-icon').textContent = icons[data.level] || '🟢';
    document.getElementById('crowd-text').textContent = data.advice;
    document.getElementById('crowd-badge').textContent = `${data.level} (${data.crowd_percent}%)`;
    document.getElementById('crowd-badge').style.background = data.color;
    document.getElementById('crowd-inline').classList.remove('hidden');
  } catch (e) {}
}

// ─── PAYMENT FLOW ──────────────────────────────────────────

function initiatePayment() {
  // Validate form first
  const name   = document.getElementById('pname').value.trim();
  const phone  = document.getElementById('pphone').value.trim();
  const routeId = document.getElementById('route-select').value;
  const from   = document.getElementById('from-stop').value;
  const to     = document.getElementById('to-stop').value;
  const pax    = parseInt(document.getElementById('passengers').value);
  const date   = document.getElementById('travel-date').value;
  const time   = document.getElementById('travel-time').value;
  const fareText = document.getElementById('fare-total').textContent;
  const fare   = parseFloat(fareText.replace('₹','')) || 0;

  if (!name)    return toast('❌ Please enter passenger name');
  if (!phone || phone.length < 10) return toast('❌ Enter valid phone number');
  if (!routeId) return toast('❌ Please select a route');
  if (!from)    return toast('❌ Select boarding stop');
  if (!to)      return toast('❌ Select destination stop');
  if (from === to) return toast('❌ From and To stops cannot be same');
  if (!date)    return toast('❌ Select travel date');
  if (fare === 0) { calcFare(); return toast('ℹ️ Select stops to calculate fare first'); }

  // Date validation
  const selectedDate = new Date(date + 'T00:00:00').getTime();
  const todayTime = new Date().setHours(0,0,0,0);
  const tomorrowTime = todayTime + 86400000;
  if (selectedDate < todayTime) return toast('❌ Cannot book for past dates');
  if (selectedDate > tomorrowTime) return toast('❌ Bookings only for today & tomorrow');

  // Store pending data
  pendingBookingData = { passenger_name: name, phone, route_id: parseInt(routeId), from_stop: from, to_stop: to, travel_date: date, travel_time: time, passengers: pax, fare };

  // Fill payment modal
  const routeName = routesData.find(r => r.id === parseInt(routeId));
  document.getElementById('pay-route').textContent = routeName ? `${routeName.route_number} – ${routeName.route_name}` : '';
  document.getElementById('pay-journey').textContent = `${from} → ${to}`;
  document.getElementById('pay-datetime').textContent = `${date} at ${time}`;
  document.getElementById('pay-pax').textContent = `${pax} passenger${pax>1?'s':''}`;
  document.getElementById('pay-amount').textContent = `₹${fare.toFixed(2)}`;
  document.getElementById('btn-pay-amount').textContent = `₹${fare.toFixed(2)}`;

  document.getElementById('payment-modal').classList.remove('hidden');
}

function closePayment() {
  document.getElementById('payment-modal').classList.add('hidden');
}

function selectPayMethod(btn, method) {
  selectedPayMethod = method;
  document.querySelectorAll('.pay-opt').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  // Show/hide panels
  ['upi','card','wallet','netbanking'].forEach(m => {
    const panel = document.getElementById('panel-' + m);
    if (panel) panel.classList.toggle('hidden', m !== method);
  });
}

function selectUPI(btn, app) {
  document.querySelectorAll('.upi-app').forEach(b => b.classList.remove('selected'));
  btn.classList.add('selected');
  if (app !== 'other') {
    document.getElementById('upi-id').value = `user@${app}`;
  }
}

function formatCard(input) {
  let v = input.value.replace(/\D/g,'').substring(0,16);
  input.value = v.replace(/(.{4})/g,'$1 ').trim();
}

async function processPayment() {
  if (!pendingBookingData) return;

  // Validate UPI ID if UPI selected
  if (selectedPayMethod === 'upi') {
    const upiId = document.getElementById('upi-id').value.trim();
    if (!upiId || !upiId.includes('@')) {
      return toast('❌ Enter a valid UPI ID (e.g. name@upi)');
    }
  }

  closePayment();

  // Show processing overlay
  const processingEl = document.getElementById('pay-processing');
  processingEl.classList.remove('hidden');

  const steps = [
    'Connecting to payment gateway...',
    'Verifying payment details...',
    'Processing transaction...',
    'Confirming with bank...',
    'Payment successful!'
  ];

  for (let i = 0; i < steps.length; i++) {
    document.getElementById('processing-msg').textContent = steps[i];
    await delay(700);
  }

  processingEl.classList.add('hidden');

  // Generate fake transaction ID
  const txnId = 'TXN' + Date.now().toString(36).toUpperCase();

  // Show success overlay
  const successEl = document.getElementById('pay-success');
  document.getElementById('success-txn').textContent = `TXN ID: ${txnId}`;
  successEl.classList.remove('hidden');

  await delay(1800);
  successEl.classList.add('hidden');

  // Now actually book the ticket
  await bookTicket(txnId);
}

function delay(ms) { return new Promise(r => setTimeout(r, ms)); }

// ─── BOOK TICKET ──────────────────────────────────────────
async function bookTicket(txnId = null) {
  const data = pendingBookingData;
  if (!data) return;

  try {
    const res = await fetch(`${API}/api/book`, {
      method: 'POST', headers: {'Content-Type':'application/json'},
      body: JSON.stringify(data)
    });
    const resp = await res.json();

    if (resp.error) {
      toast(`❌ ${resp.error}`);
      return;
    }

    currentBookingId = resp.booking_id || '';
    qrExpiry = new Date(resp.expires_at);
    if (isNaN(qrExpiry.getTime())) qrExpiry = new Date(Date.now() + 30 * 60 * 1000);

    // Show QR
    document.getElementById('qr-placeholder').classList.add('hidden');
    document.getElementById('qr-result').classList.remove('hidden');
    document.getElementById('qr-img').src = `data:image/png;base64,${resp.qr_b64 || ''}`;
    document.getElementById('disp-booking-id').textContent = `#${resp.booking_id}`;
    const route = routesData.find(r => r.id === data.route_id);
    document.getElementById('disp-from').textContent  = data.from_stop;
    document.getElementById('disp-to').textContent    = data.to_stop;
    document.getElementById('disp-route').textContent = route ? `${route.route_number} – ${route.route_name}` : '';
    document.getElementById('disp-pass').textContent  = `${data.passengers} passenger${data.passengers>1?'s':''}`;
    document.getElementById('disp-date').textContent  = `${data.travel_date} at ${data.travel_time}`;
    document.getElementById('disp-fare').textContent  = `₹${data.fare.toFixed(2)} (Paid ✓)`;
    document.getElementById('qr-expires-text').textContent = `Expires: ${qrExpiry.toLocaleTimeString()}`;

    // Scroll QR into view
    document.getElementById('qr-panel').scrollIntoView({ behavior: 'smooth', block: 'nearest' });

    startCountdown(qrExpiry);
    toast(`✅ Booked! ID: ${resp.booking_id}${txnId ? ' • Payment confirmed' : ''}`);
    pendingBookingData = null;

  } catch (e) {
    console.error(e);
    toast(`❌ Booking failed: ${e.message}`);
  }
}

// ─── COUNTDOWN ────────────────────────────────────────────
function startCountdown(expiry) {
  if (countdownTimer) clearInterval(countdownTimer);
  const totalMs = 30 * 60 * 1000;
  const circumference = 326.7;

  function update() {
    const remaining = expiry - Date.now();
    if (remaining <= 0) { expireQR(); return; }
    const mins = Math.floor(remaining / 60000);
    const secs = Math.floor((remaining % 60000) / 1000);
    document.getElementById('countdown-mins').textContent =
      `${String(mins).padStart(2,'0')}:${String(secs).padStart(2,'0')}`;
    const fraction = remaining / totalMs;
    const offset = circumference * (1 - fraction);
    const ringPath = document.getElementById('ring-path');
    ringPath.style.strokeDashoffset = offset;

    const statusEl = document.getElementById('qr-status-text');
    if (remaining < 5 * 60000) {
      ringPath.style.stroke = '#dc2626';
      statusEl.textContent = '⚠️ QR Expiring Soon!';
      statusEl.className = 'status-danger';
    } else if (remaining < 10 * 60000) {
      ringPath.style.stroke = '#d97706';
      statusEl.textContent = '⏳ Less than 10 mins left';
      statusEl.className = 'status-warning';
    }
  }

  update();
  countdownTimer = setInterval(update, 1000);
}

function expireQR() {
  clearInterval(countdownTimer);
  document.getElementById('countdown-mins').textContent = '00:00';
  document.getElementById('qr-status-text').textContent = '❌ QR Expired';
  document.getElementById('qr-status-text').className = 'status-danger';
  document.getElementById('expire-btn').classList.add('hidden');
  document.getElementById('expired-banner').classList.remove('hidden');
  document.getElementById('ring-path').style.stroke = '#dc2626';
  if (currentBookingId) {
    fetch(`${API}/api/expire_check`, {
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({booking_id: currentBookingId})
    }).catch(()=>{});
  }
}

async function manualExpire() {
  if (!confirm('Mark this ticket as used and expire the QR code?')) return;
  if (countdownTimer) clearInterval(countdownTimer);
  expireQR();
  toast('✅ QR expired – Journey completed!');
}

// ─── ROUTES & STOPS TAB ───────────────────────────────────
function renderRouteTabs() {
  if (!routesData.length) return;
  const container = document.getElementById('route-tabs');
  container.innerHTML = '';
  routesData.forEach((r, i) => {
    const btn = document.createElement('button');
    btn.className = 'rtab' + (i === currentRouteIdx ? ' active' : '');
    btn.textContent = r.route_number;
    btn.onclick = () => { currentRouteIdx = i; renderRouteTabs(); renderStops(); };
    container.appendChild(btn);
  });
  renderStops();
}

function renderStops() {
  const route = routesData[currentRouteIdx];
  if (!route) return;
  const stops = JSON.parse(route.stops);
  const reversed = [...stops].reverse();
  const displayStops = currentDirection === 'forward' ? stops : reversed;
  const search = document.getElementById('stop-search').value.toLowerCase();

  document.getElementById('route-content').innerHTML = `
    <div class="card">
      <h2>${route.route_number} – ${route.route_name}</h2>
      <p class="card-sub">${stops.length} stops</p>
      <div class="dir-btns">
        <button class="dir-btn ${currentDirection==='forward'?'active':''}" onclick="setDir('forward')">➡️ Forward</button>
        <button class="dir-btn ${currentDirection==='return'?'active':''}" onclick="setDir('return')">⬅️ Return</button>
      </div>
      <div class="stops-grid" id="stops-grid">
        ${displayStops.map((s, i) => `
          <div class="stop-item ${search && !s.toLowerCase().includes(search) ? 'hidden' : ''}">
            <div class="stop-num">${i+1}</div>
            <span>${s}</span>
          </div>
        `).join('')}
      </div>
    </div>`;
}

function setDir(dir) { currentDirection = dir; renderStops(); }
function filterStops() { renderStops(); }

// ─── MY TICKETS ───────────────────────────────────────────
async function loadMyTickets() {
  try {
    const res = await fetch(`${API}/api/bookings`);
    const tickets = await res.json();
    const active = tickets.filter(t => t.status === 'active').length;
    const total  = tickets.length;
    const totalFare = tickets.reduce((a,t) => a + (t.fare||0), 0);
    document.getElementById('ticket-stats').innerHTML = `
      <div class="stat-card"><div class="stat-num">${total}</div><div class="stat-label">Total Bookings</div></div>
      <div class="stat-card"><div class="stat-num">${active}</div><div class="stat-label">Active Tickets</div></div>
      <div class="stat-card"><div class="stat-num">${total - active}</div><div class="stat-label">Used / Expired</div></div>
      <div class="stat-card"><div class="stat-num">₹${totalFare.toFixed(0)}</div><div class="stat-label">Total Paid</div></div>
    `;
    const list = document.getElementById('tickets-list');
    if (!tickets.length) {
      list.innerHTML = '<div class="card" style="text-align:center;color:#aaa;padding:60px">No tickets booked yet.</div>';
      return;
    }
    list.innerHTML = tickets.map(t => `
      <div class="ticket-card ${t.status==='expired'?'expired':''}">
        ${t.qr_code ? `<img class="ticket-qr" src="data:image/png;base64,${t.qr_code}" alt="QR"/>` : ''}
        <div class="ticket-info">
          <h4>#${t.booking_id} &nbsp;|&nbsp; ${t.from_stop} → ${t.to_stop}</h4>
          <p>
            📅 ${t.travel_date} at ${t.travel_time} &nbsp;|&nbsp;
            👥 ${t.passengers} pax &nbsp;|&nbsp;
            📞 ${t.phone}
          </p>
          <p class="ticket-pay-tag"><i class="fas fa-check-circle"></i> ₹${(t.fare||0).toFixed(2)} Paid</p>
          <p style="font-size:.75rem;color:#94a3b8;margin-top:4px">Booked: ${new Date(t.booked_at).toLocaleString()}</p>
        </div>
        <span class="ticket-status ${t.status==='active'?'status-active-badge':'status-expired-badge'}">
          ${t.status==='active' ? '✅ Active' : '⛔ Expired'}
        </span>
      </div>
    `).join('');
  } catch (e) { console.error(e); }
}

// ─── ML INSIGHTS ──────────────────────────────────────────
async function loadInsights() {
  try {
    const res = await fetch(`${API}/api/ml/insights`);
    const data = await res.json();
    renderCrowdChart(data.hourly_crowd);
    renderSamplePredictions();
  } catch (e) { console.error(e); }
}

function renderCrowdChart(hourly) {
  const canvas = document.getElementById('crowd-chart');
  if (!canvas) return;
  if (canvas._chartInst) { canvas._chartInst.destroy(); }
  const labels = Array.from({length:24},(_,i)=>`${i}:00`);
  const values = labels.map((_,i) => hourly[i] || 0);
  const colors = values.map(v =>
    v>=80 ? '#dc2626' : v>=60 ? '#ea580c' : v>=40 ? '#d97706' : '#059669'
  );
  canvas._chartInst = new Chart(canvas, {
    type: 'bar',
    data: { labels, datasets: [{ data: values, backgroundColor: colors, borderRadius: 5 }] },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: { legend: { display: false }, tooltip: { callbacks: {
        label: ctx => `Crowd: ${ctx.raw}%`
      }}},
      scales: {
        y: { beginAtZero: true, max: 100, ticks: { callback: v => v+'%' }, grid: { color: '#f1f5f9' } },
        x: { ticks: { maxTicksLimit: 12 }, grid: { display: false } }
      }
    }
  });
}

function renderSamplePredictions() {
  const samples = [
    { route:'8A', stops:8, time:'08:30', pax:1, fare:16.60 },
    { route:'90L', stops:12, time:'12:00', pax:2, fare:34.56 },
    { route:'224', stops:10, time:'18:00', pax:4, fare:68.80 },
    { route:'1P', stops:6, time:'22:00', pax:1, fare:10.80 },
  ];
  const tbody = document.getElementById('sample-pred-rows');
  if (!tbody) return;
  tbody.innerHTML = samples.map(s =>
    `<tr><td>${s.route}</td><td>${s.stops}</td><td>${s.time}</td><td>${s.pax}</td><td>₹${s.fare}</td></tr>`
  ).join('');
}

async function getRecommendations() {
  const from = document.getElementById('rec-from').value.trim();
  const to   = document.getElementById('rec-to').value.trim();
  if (!from || !to) return toast('Enter both stops');
  try {
    const res = await fetch(`${API}/api/predict/routes`, {
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({ from_stop: from, to_stop: to })
    });
    const recs = await res.json();
    const container = document.getElementById('rec-results');
    if (!recs.length || recs[0].message) {
      container.innerHTML = `<div style="padding:12px;color:#888">${recs[0]?.message||'No routes found'}</div>`;
      return;
    }
    container.innerHTML = recs.map((r,i) => `
      <div class="rec-card">
        <div>
          <strong>${r.route_number} – ${r.route_name}</strong><br/>
          <small>Every ${r.frequency_mins} mins &nbsp;${r.ac?'❄️ AC':'🌬️ Non-AC'}</small>
        </div>
        <div>
          <div class="rec-badge">${r.confidence}%</div>
          <div style="font-size:.72rem;color:#94a3b8;text-align:center;margin-top:4px">Rank #${i+1}</div>
        </div>
      </div>
    `).join('');
  } catch (e) { toast('Recommendation failed'); }
}

// ─── AUTH ─────────────────────────────────────────────────
let authToken = localStorage.getItem('tsrtc_token') || null;
let currentUser = JSON.parse(localStorage.getItem('tsrtc_user') || 'null');

document.addEventListener('DOMContentLoaded', () => {
  setDefaultDate();
  loadRoutes();
  loadInsights();
  updateAuthUI();
});

function updateAuthUI() {
  const userDisplay  = document.getElementById('nav-user-display');
  const btnLogin     = document.getElementById('btn-auth-nav');
  const btnLogout    = document.getElementById('btn-logout-nav');
  if (!userDisplay) return;
  if (currentUser) {
    userDisplay.textContent = `👤 ${currentUser.name}`;
    userDisplay.style.display = '';
    btnLogin.style.display  = 'none';
    btnLogout.style.display = '';
  } else {
    userDisplay.style.display = 'none';
    btnLogin.style.display  = '';
    btnLogout.style.display = 'none';
  }
}

function openAuth()  { document.getElementById('auth-modal').classList.remove('hidden'); document.getElementById('auth-error').textContent = ''; }
function closeAuth() { document.getElementById('auth-modal').classList.add('hidden'); }

function switchAuthTab(tab) {
  document.getElementById('auth-login-form').style.display = tab === 'login' ? '' : 'none';
  document.getElementById('auth-reg-form').style.display   = tab === 'register' ? '' : 'none';
  document.getElementById('tab-login-btn').classList.toggle('active', tab === 'login');
  document.getElementById('tab-reg-btn').classList.toggle('active', tab === 'register');
  document.getElementById('auth-error').textContent = '';
}

async function doAuthLogin() {
  const email = document.getElementById('auth-email').value.trim();
  const pw    = document.getElementById('auth-pw').value;
  document.getElementById('auth-error').textContent = '';
  if (!email || !pw) { document.getElementById('auth-error').textContent = 'Email and password required'; return; }
  try {
    const res  = await fetch(`${API}/api/auth/login`, {
      method: 'POST', headers: {'Content-Type':'application/json'},
      body: JSON.stringify({ email, password: pw })
    });
    const data = await res.json();
    if (!res.ok) { document.getElementById('auth-error').textContent = data.error || 'Login failed'; return; }
    authToken = data.token; currentUser = data.user;
    localStorage.setItem('tsrtc_token', authToken);
    localStorage.setItem('tsrtc_user', JSON.stringify(currentUser));
    closeAuth(); updateAuthUI();
    toast(`✅ Welcome back, ${data.user.name}!`);
    loadMyTickets();
  } catch (e) { document.getElementById('auth-error').textContent = 'Network error'; }
}

async function doAuthRegister() {
  const name  = document.getElementById('reg-name').value.trim();
  const email = document.getElementById('reg-email').value.trim();
  const phone = document.getElementById('reg-phone').value.trim();
  const pw    = document.getElementById('reg-pw').value;
  document.getElementById('auth-error').textContent = '';
  if (!name || !email || !phone || !pw) { document.getElementById('auth-error').textContent = 'All fields required'; return; }
  try {
    const res  = await fetch(`${API}/api/auth/register`, {
      method: 'POST', headers: {'Content-Type':'application/json'},
      body: JSON.stringify({ name, email, phone, password: pw })
    });
    const data = await res.json();
    if (!res.ok) { document.getElementById('auth-error').textContent = data.error || 'Registration failed'; return; }
    authToken = data.token; currentUser = data.user;
    localStorage.setItem('tsrtc_token', authToken);
    localStorage.setItem('tsrtc_user', JSON.stringify(currentUser));
    closeAuth(); updateAuthUI();
    toast(`🎉 Account created! Welcome, ${data.user.name}!`);
  } catch (e) { document.getElementById('auth-error').textContent = 'Network error'; }
}

function doLogout() {
  authToken = null; currentUser = null;
  localStorage.removeItem('tsrtc_token');
  localStorage.removeItem('tsrtc_user');
  updateAuthUI();
  toast('👋 Logged out successfully');
}

function authHeaders() {
  return authToken ? { 'Content-Type':'application/json', 'Authorization': `Bearer ${authToken}` }
                   : { 'Content-Type':'application/json' };
}

// Close modals on overlay click
document.addEventListener('click', (e) => {
  if (e.target.id === 'auth-modal') closeAuth();
  if (e.target.id === 'payment-modal') closePayment();
});

// ─── TOAST ────────────────────────────────────────────────
function toast(msg, duration=3000) {
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.classList.remove('hidden');
  clearTimeout(t._timer);
  t._timer = setTimeout(() => t.classList.add('hidden'), duration);
}