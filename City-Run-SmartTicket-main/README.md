# 🏨 Hotel Royal Stay

> Production-grade hotel management system with AI room recommendations, Razorpay payments, and real-time analytics — built for Hyderabad's premium hospitality experience.

![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-5.1-092E20?logo=django&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/Database-PostgreSQL-4169E1?logo=postgresql&logoColor=white)
![Razorpay](https://img.shields.io/badge/Payments-Razorpay-02042B?logo=razorpay&logoColor=white)
![Render](https://img.shields.io/badge/Deployed-Render-46E3B7?logo=render&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)

---

## 📌 Overview

**Hotel Royal Stay** is a full-stack Django web application that allows guests to browse rooms, make bookings, and pay securely — while giving hotel admins a powerful dashboard to track revenue, occupancy, and guest analytics.

The system integrates an **AI-powered room recommendation engine** that scores rooms based on guest ratings and pricing to deliver personalized suggestions.

🌐 **Live Demo:** [hotel-royal-stay.onrender.com](https://hotel-royal-stay.onrender.com)

---

## 🖼️ Screenshots

> _Add screenshots or a demo GIF here._

---

## 🏗️ Architecture

```
Frontend (Bootstrap 5 + Chart.js + Font Awesome)
               ↓
Backend (Django Views + Django REST Framework)
               ↓
Database (SQLite dev / PostgreSQL prod) + Razorpay API + AI Recommendation Engine
```

---

## 🧰 Tech Stack

| Layer       | Technology                                              |
|-------------|---------------------------------------------------------|
| Frontend    | HTML5, CSS3, Bootstrap 5, Chart.js, Font Awesome        |
| Backend     | Python, Django 5.1, Django REST Framework               |
| Auth        | Django Auth + SimpleJWT                                 |
| Database    | SQLite (development) / PostgreSQL (production)          |
| Payments    | Razorpay (UPI, Cards, Net Banking)                      |
| Static Files| WhiteNoise                                              |
| Server      | Gunicorn                                                |
| Deployment  | Render                                                  |

---

## 🎯 Features

### 🛏️ Room Management
- Browse rooms with real-time availability search
- Filter by dates, guest count, and room type
- Room detail pages with amenities, capacity, and reviews
- Status tracking — Available / Occupied / Maintenance

### 📅 Smart Booking System
- Date conflict detection and validation
- Guest count enforcement per room capacity
- Special requests support
- Full booking history and management

### 💳 Razorpay Payment Integration
- UPI, Credit/Debit Cards, Net Banking support
- Secure transaction handling
- Payment status tracking
- Booking confirmation on payment success

### 📊 Admin Analytics Dashboard
- Revenue trend charts with Chart.js
- Occupancy rate tracking
- Booking analytics by date and room type
- Guest statistics overview

### 🤖 AI Room Recommendations

| Feature | Logic | Purpose |
|---------|-------|---------|
| Rating Score | Average guest rating | Prefer highly rated rooms |
| Price Score | Value-for-money index | Balance cost and quality |
| Availability Check | Real-time date filtering | Only show bookable rooms |
| Combined Ranking | Weighted scoring | Personalized suggestions |

### 👥 Role-Based Access
- Admin / Staff / Customer roles
- JWT Authentication for REST API
- Django session auth for web interface
- Secure login, logout, and profile management

---

## 🔌 REST API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/rooms/` | List all rooms |
| GET | `/api/rooms/<id>/` | Room detail |
| GET/POST | `/api/bookings/` | Bookings CRUD |
| POST | `/api/token/` | Obtain JWT token |
| POST | `/api/token/refresh/` | Refresh JWT token |

---

## 🗂️ Project Structure

```
Hotel-Royal-stay/
├── hotel/                  # Main app — models, views, forms, URLs
├── accounts/               # Auth app — login, register, profile
├── hotel_management/       # Project config — settings, URLs, wsgi
├── templates/              # HTML templates
│   ├── base.html
│   ├── hotel/
│   └── accounts/
├── static/                 # CSS, images, JS
│   ├── css/style.css
│   └── images/
├── seed_data.py            # Sample data seeder
├── manage.py
├── Procfile
├── runtime.txt
└── requirements.txt
```

---

## ▶️ Getting Started

Follow these steps to run the project locally.

---

### Step 1 — Install Python

Make sure Python 3.11 or above is installed.

- Download from: https://www.python.org/downloads/
- On Windows, **check "Add Python to PATH"** during installation
- Verify:

```bash
python --version
```

---

### Step 2 — Install Git

- Download from: https://git-scm.com/downloads
- Verify:

```bash
git --version
```

---

### Step 3 — Clone the Repository

```bash
git clone https://github.com/Harsha7215/Hotel-Royal-stay.git
```

---

### Step 4 — Open the Project Folder

```bash
cd Hotel-Royal-stay
```

---

### Step 5 — Create Virtual Environment

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# Mac / Linux
python -m venv .venv
source .venv/bin/activate
```

---

### Step 6 — Install Dependencies

```bash
pip install -r requirements.txt
```

---

### Step 7 — Run Migrations and Seed Data

```bash
python manage.py migrate
python seed_data.py
python manage.py createsuperuser
```

---

### Step 8 — Start the Server

```bash
python manage.py runserver
```

Open your browser at:

```
http://127.0.0.1:8000
```

> 🔑 Admin panel: **http://127.0.0.1:8000/admin**

---

### Common Issues

| Problem | Fix |
|---------|-----|
| `python` not recognized | Reinstall Python and check "Add to PATH" |
| `pip` not recognized | Use `pip3` instead |
| Port already in use | Stop other servers or use `runserver 8001` |
| Module not found | Run `pip install -r requirements.txt` again |

---

## 🌍 Deployment

This project is deployed on **Render** with PostgreSQL.

### Environment Variables

| Variable | Description |
|---|---|
| `DJANGO_SECRET_KEY` | Django secret key |
| `DEBUG` | `False` in production |
| `ALLOWED_HOSTS` | Your domain name |
| `CSRF_TRUSTED_ORIGINS` | `https://yourdomain.onrender.com` |
| `DATABASE_URL` | PostgreSQL connection URL |
| `RAZORPAY_KEY_ID` | Razorpay API key |
| `RAZORPAY_KEY_SECRET` | Razorpay secret key |

### Build and Start Commands

```bash
# Build
pip install -r requirements.txt

# Start
sh -c "python manage.py migrate && python manage.py collectstatic --noinput && gunicorn hotel_management.wsgi --log-file -"
```

---

## 🔐 Current Limitations

- Media uploads (room images) not persistent on free hosting
- Razorpay in test mode only
- Free tier spins down after inactivity

---

## 🚀 Planned Enhancements

### Scalability & Performance
- Migrate media storage to AWS S3 / Cloudinary
- Redis caching for room availability queries
- Celery for async email notifications

### Security
- Two-factor authentication
- OAuth login (Google, GitHub)
- API rate limiting

### Real-Time Features
- Live room availability via WebSockets
- Push notifications for booking updates
- Real-time admin alerts for new bookings

### Payments
- Stripe integration (international cards)
- Invoice PDF generation
- Automated refund processing

### ML Improvements
- Collaborative filtering for recommendations
- Dynamic pricing based on demand
- Sentiment analysis on guest reviews

### Frontend
- Progressive Web App (PWA)
- Mobile app with React Native
- Dark/light theme toggle

---

## 🌟 Key Highlights

- Full-stack development (Frontend + Backend + REST API)
- Solves a real-world hotel management problem
- End-to-end payment integration with Razorpay
- AI recommendation engine with practical use cases
- Production deployment with PostgreSQL on Render
- Clean, luxury UI with Cormorant Garamond typography

---

## 🤝 Contributing

Contributions are welcome! Please open an issue first to discuss what you'd like to change, then submit a pull request.

---

## 👨‍💻 Author

**Harsha** — [GitHub @Harsha7215](https://github.com/Harsha7215)

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
