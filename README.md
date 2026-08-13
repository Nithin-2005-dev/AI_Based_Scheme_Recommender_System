# 🏛️ GovScheme AI

## AI-Driven Multilingual Personalized Government Scheme Discovery and Eligibility Guidance System

A production-ready web application that enables Indian citizens to discover 3,400+ government schemes, check eligibility, receive personalized recommendations, and get AI-powered assistance — all in 10 Indian languages.

---

## 🚀 Quick Start

### Prerequisites
- **Python 3.12+**
- **Node.js 20+**
- **npm 10+**

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Linux/Mac)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Import 3,400 schemes from CSV
python scripts/import_csv.py

# Start the backend server
python main.py
```

Backend runs at: **http://localhost:8000**
API Docs: **http://localhost:8000/api/docs**

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

Frontend runs at: **http://localhost:3000**

### Default Admin Login
- **Email:** admin@govscheme.ai
- **Password:** Admin@123456

---

## 📋 Features

### 🔐 Authentication
- Email + Password signup/login with JWT (access + refresh tokens)
- Email verification (configurable)
- Password reset with token-based email flow
- Role-based access control (Citizen / Admin)
- Bcrypt password hashing (12 rounds)
- AES-256 encryption for Aadhaar/PAN

### 👤 User Profile (30+ Fields)
- Personal: name, age, gender, DOB, mobile
- Employment: occupation, status, income
- Education: level, category, caste, religion
- Location: state (all 36), district, pincode
- Special status: farmer, student, widow, senior citizen, disabled, pregnant, business owner
- Encrypted sensitive data storage

### 📋 Scheme Management
- 3,400+ real schemes from CSV import
- Full-text search with filters (category, level, state)
- Scheme detail pages with tabbed content
- Versioning for rule change detection
- Category browsing with counts
- View count tracking

### 🎯 AI Recommendation Engine
- Hybrid: Rule-based + Weighted Scoring + Text Similarity
- 7 scoring dimensions: income, category, occupation, education, location, gender, special status
- Explainable AI (XAI): shows matched/failed conditions with reasons
- Confidence score based on profile completeness
- Match probability percentage

### ✅ Eligibility Checker
- NLP-based condition extraction from free text
- Age, income, location, gender, category, occupation checks
- Document requirement analysis
- Suggestions for missing criteria
- Detailed human-readable explanations

### 🔔 Notification Engine
- In-app notifications with priority levels
- Email notifications (SMTP configurable)
- SMS notifications (Twilio/MSG91)
- Rule change alerts with impact analysis
- Deadline reminders at 30, 15, 7, 3, 1, 0 days
- Bulk notification sending (admin)

### 📝 Rule Change Detection
- Myers diff algorithm for text comparison
- Version history for every scheme
- Impact severity analysis
- Automatic notification to affected users

### 🤖 RAG Chatbot
- Intent detection (eligibility, benefits, documents, application)
- Keyword-based scheme retrieval
- Answer generation with citations
- Chat session history
- Source chunk transparency
- Quick question suggestions

### 🌐 Multilingual Support
- 10 Indian languages: English, Hindi, Telugu, Tamil, Kannada, Malayalam, Marathi, Bengali, Gujarati, Punjabi
- Built-in UI translation dictionaries
- Google Translate API fallback
- Language switcher

### 📊 Admin Dashboard
- User management with search
- 8 key metric cards
- Popular schemes ranking
- Category distribution visualization
- Notification sender
- Scheme version history

### 🔍 Advanced Search
- Full-text search across all scheme fields
- Autocomplete suggestions
- Category and level filters
- State filtering with Central scheme inclusion
- Search result suggestions

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────┐
│                   Frontend                       │
│     Next.js 15 + TypeScript + Tailwind CSS       │
│  (Landing, Auth, Dashboard, Schemes, Chatbot,    │
│   Profile, Recommendations, Admin, Notifications) │
└──────────────────┬──────────────────────────────┘
                   │ REST API (JWT Auth)
┌──────────────────▼──────────────────────────────┐
│                   Backend                        │
│        FastAPI + SQLAlchemy (async)               │
│  ┌──────────┐ ┌──────────┐ ┌──────────────────┐ │
│  │ Auth     │ │ Schemes  │ │ Recommendation   │ │
│  │ Service  │ │ API      │ │ Engine           │ │
│  └──────────┘ └──────────┘ └──────────────────┘ │
│  ┌──────────┐ ┌──────────┐ ┌──────────────────┐ │
│  │ Search   │ │ RAG      │ │ Eligibility      │ │
│  │ Engine   │ │ Chatbot  │ │ Checker          │ │
│  └──────────┘ └──────────┘ └──────────────────┘ │
│  ┌──────────┐ ┌──────────┐ ┌──────────────────┐ │
│  │ Notif.   │ │ Rule     │ │ Translation      │ │
│  │ Engine   │ │ Change   │ │ Service          │ │
│  └──────────┘ └──────────┘ └──────────────────┘ │
└──────────────────┬──────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────┐
│      SQLite (dev) / PostgreSQL (prod)            │
│      Redis (caching)                             │
└──────────────────────────────────────────────────┘
```

---

## 🐳 Docker Deployment

```bash
cd docker
docker-compose up --build
```

Services:
- **Backend**: localhost:8000
- **Frontend**: localhost:3000
- **Nginx**: localhost:80
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/signup` | Register new user |
| POST | `/api/v1/auth/login` | Login with JWT |
| POST | `/api/v1/auth/refresh` | Refresh access token |
| POST | `/api/v1/auth/forgot-password` | Request password reset |
| POST | `/api/v1/auth/reset-password` | Reset password |
| GET | `/api/v1/users/me` | Get user profile |
| PUT | `/api/v1/users/me` | Update profile |
| POST | `/api/v1/users/me/documents` | Upload document |
| GET | `/api/v1/schemes` | List schemes (paginated) |
| GET | `/api/v1/schemes/{slug}` | Get scheme detail |
| GET | `/api/v1/schemes/categories` | Get categories |
| POST | `/api/v1/schemes/save` | Save/bookmark scheme |
| GET | `/api/v1/recommendations` | Get AI recommendations |
| POST | `/api/v1/eligibility/check` | Check eligibility |
| GET | `/api/v1/search?q=...` | Search schemes |
| GET | `/api/v1/notifications` | Get notifications |
| POST | `/api/v1/chatbot` | Ask AI chatbot |
| GET | `/api/v1/translate/languages` | List languages |
| POST | `/api/v1/translate` | Translate text |
| GET | `/api/v1/analytics/dashboard` | Admin analytics |
| GET | `/api/v1/admin/users` | Admin: list users |

---

## 🔒 Security

- **JWT** access + refresh tokens with rotation
- **Bcrypt** password hashing (12 rounds)
- **AES-256-CBC** encryption for Aadhaar/PAN
- **CORS** with configurable origins
- **Rate limiting** (100 req/min API, 20 req/min auth)
- **Security headers** (HSTS, X-Frame-Options, CSP)
- **Input validation** via Pydantic
- **SQL injection prevention** via SQLAlchemy ORM

---

## 📜 License

This project is for educational/demonstration purposes.
#   A I _ B a s e d _ S c h e m e _ R e c o m m e n d o r  
 