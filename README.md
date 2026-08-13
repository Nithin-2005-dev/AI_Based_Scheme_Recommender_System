# 🏛️ GovScheme AI

## AI-Driven Multilingual Personalized Government Scheme Discovery & Eligibility Guidance

GovScheme AI is a production-ready web application that helps Indian citizens discover **3,400+ government schemes**, check eligibility, receive personalized recommendations, and interact with an AI-powered multilingual assistant.

The platform supports **10 Indian languages** and provides personalized scheme discovery based on a user's demographic, employment, education, location, and special-status information.

---

## ✨ Highlights

* 🏛️ **3,400+ Government Schemes**
* 🤖 **AI-powered Recommendations**
* ✅ **Eligibility Checking**
* 💬 **RAG-based Multilingual Chatbot**
* 🌐 **10 Indian Languages**
* 🔐 **JWT Authentication & Role-based Access**
* 🔔 **Notifications & Deadline Reminders**
* 📋 **Government Scheme Rule Change Detection**
* 📊 **Admin Analytics Dashboard**
* 🔍 **Advanced Scheme Search**
* 🛡️ **Encrypted Sensitive Data**

---

## 🚀 Quick Start

### Prerequisites

Make sure the following are installed:

* **Python 3.12+**
* **Node.js 20+**
* **npm 10+**

---

## ⚙️ Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
```

### Activate Virtual Environment

**Windows**

```bash
venv\Scripts\activate
```

**Linux / macOS**

```bash
source venv/bin/activate
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Import Government Schemes

Import the 3,400+ schemes from the CSV dataset:

```bash
python scripts/import_csv.py
```

### Start Backend

```bash
python main.py
```

Backend:

```text
http://localhost:8000
```

API Documentation:

```text
http://localhost:8000/api/docs
```

---

## 💻 Frontend Setup

Open a new terminal:

```bash
cd frontend
```

Install dependencies:

```bash
npm install
```

Start the development server:

```bash
npm run dev
```

Frontend:

```text
http://localhost:3000
```

---

## 🔑 Default Admin Account

For local development/demo purposes:

```text
Email:    admin@govscheme.ai
Password: Admin@123456
```

> ⚠️ Change the default credentials before deploying the application to production.

---

# 📋 Features

## 🔐 Authentication

* Email + password signup/login
* JWT authentication
* Access + refresh tokens
* Refresh token rotation
* Configurable email verification
* Token-based password reset
* Role-based access control
* Citizen and Admin roles
* Bcrypt password hashing

---

## 👤 Personalized User Profile

The platform maintains a detailed user profile containing **30+ fields**.

### Personal Information

* Name
* Age
* Gender
* Date of birth
* Mobile number

### Employment

* Occupation
* Employment status
* Income

### Education

* Education level
* Category
* Caste
* Religion

### Location

* State
* District
* Pincode

### Special Status

* Farmer
* Student
* Widow
* Senior citizen
* Person with disability
* Pregnant
* Business owner

Sensitive information is encrypted before storage.

---

## 📋 Government Scheme Management

* 3,400+ government schemes
* CSV-based scheme import
* Full-text search
* Category filtering
* State filtering
* Scheme-level filtering
* Scheme detail pages
* Scheme version history
* Rule change detection
* Category browsing
* Scheme view tracking
* Bookmark/save functionality

---

## 🎯 AI Recommendation Engine

The recommendation system combines multiple approaches:

* Rule-based matching
* Weighted scoring
* Text similarity

### Scoring Dimensions

The recommendation engine evaluates:

1. Income
2. Category
3. Occupation
4. Education
5. Location
6. Gender
7. Special status

### Explainable AI

Instead of only returning a recommendation, the system explains:

* Which conditions matched
* Which conditions failed
* Why a scheme was recommended
* Missing eligibility information
* Profile completeness
* Match probability

---

## ✅ Eligibility Checker

Users can check their eligibility for government schemes using structured profile information and free-text input.

### Supported Conditions

* Age
* Income
* Location
* Gender
* Category
* Occupation
* Education
* Special status

### Additional Capabilities

* NLP-based condition extraction
* Document requirement analysis
* Missing-criteria detection
* Eligibility suggestions
* Human-readable explanations

---

## 🔔 Notification Engine

The notification system supports:

* In-app notifications
* Priority-based notifications
* Email notifications
* SMS notifications
* Scheme rule-change alerts
* Deadline reminders
* Bulk notifications for administrators

### Deadline Reminder Schedule

Notifications can be triggered at:

```text
30 days
15 days
7 days
3 days
1 day
0 days
```

Supported integrations include configurable SMTP, Twilio, and MSG91 providers.

---

## 📝 Rule Change Detection

GovScheme AI tracks changes to government scheme rules.

Capabilities include:

* Myers diff algorithm
* Scheme version history
* Text comparison
* Change severity analysis
* Impact analysis
* Notifications to affected users

This allows users to be informed when eligibility rules or scheme information changes.

---

## 🤖 RAG Chatbot

The AI assistant helps users understand government schemes through conversational interaction.

### Capabilities

* Intent detection
* Eligibility questions
* Benefits questions
* Required document questions
* Application guidance
* Scheme retrieval
* Answer generation
* Source citations
* Chat session history
* Source chunk transparency
* Suggested questions

---

## 🌐 Multilingual Support

The platform supports **10 Indian languages**:

| Language       |
| -------------- |
| 🇬🇧 English   |
| 🇮🇳 Hindi     |
| 🇮🇳 Telugu    |
| 🇮🇳 Tamil     |
| 🇮🇳 Kannada   |
| 🇮🇳 Malayalam |
| 🇮🇳 Marathi   |
| 🇮🇳 Bengali   |
| 🇮🇳 Gujarati  |
| 🇮🇳 Punjabi   |

### Translation System

* Built-in UI translation dictionaries
* Language switcher
* Google Translate API fallback

---

## 📊 Admin Dashboard

Administrators can monitor and manage the platform through a dedicated dashboard.

### Features

* User management
* User search
* Scheme management
* Popular scheme rankings
* Category distribution
* Analytics
* Notification management
* Scheme version history
* Rule change monitoring

---

## 🔍 Advanced Search

The search engine provides:

* Full-text search
* Autocomplete
* Search suggestions
* Category filtering
* State filtering
* Scheme-level filtering
* Central scheme inclusion
* Search result ranking

---

# 🏗️ Architecture

```text
┌─────────────────────────────────────────────────────────┐
│                     FRONTEND                            │
│                                                         │
│              Next.js 15 + TypeScript                   │
│                    Tailwind CSS                         │
│                                                         │
│  Landing │ Auth │ Dashboard │ Schemes │ Profile         │
│  Recommendations │ Chatbot │ Admin │ Notifications     │
└──────────────────────────┬──────────────────────────────┘
                           │
                           │ REST API + JWT
                           ▼
┌─────────────────────────────────────────────────────────┐
│                     BACKEND                             │
│                                                         │
│              FastAPI + SQLAlchemy                       │
│                                                         │
│ ┌──────────┐ ┌──────────┐ ┌─────────────────────────┐  │
│ │   Auth   │ │ Schemes  │ │ Recommendation Engine   │  │
│ └──────────┘ └──────────┘ └─────────────────────────┘  │
│                                                         │
│ ┌──────────┐ ┌──────────┐ ┌─────────────────────────┐  │
│ │  Search  │ │   RAG    │ │ Eligibility Checker     │  │
│ │  Engine  │ │ Chatbot  │ │                         │  │
│ └──────────┘ └──────────┘ └─────────────────────────┘  │
│                                                         │
│ ┌──────────┐ ┌──────────┐ ┌─────────────────────────┐  │
│ │  Notify  │ │   Rule   │ │ Translation Service     │  │
│ │  Engine  │ │  Change  │ │                         │  │
│ └──────────┘ └──────────┘ └─────────────────────────┘  │
└──────────────────────────┬──────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│                    DATA LAYER                           │
│                                                         │
│       SQLite (Development) / PostgreSQL (Production)   │
│                         │                               │
│                       Redis                             │
│                    (Caching)                            │
└─────────────────────────────────────────────────────────┘
```

---

# 🐳 Docker Deployment

The complete application can be started using Docker Compose.

```bash
cd docker

docker-compose up --build
```

### Services

| Service    |   Port |
| ---------- | -----: |
| Frontend   | `3000` |
| Backend    | `8000` |
| Nginx      |   `80` |
| PostgreSQL | `5432` |
| Redis      | `6379` |

---

# 📡 API Endpoints

| Method | Endpoint                       | Description              |
| ------ | ------------------------------ | ------------------------ |
| `POST` | `/api/v1/auth/signup`          | Register new user        |
| `POST` | `/api/v1/auth/login`           | Login with JWT           |
| `POST` | `/api/v1/auth/refresh`         | Refresh access token     |
| `POST` | `/api/v1/auth/forgot-password` | Request password reset   |
| `POST` | `/api/v1/auth/reset-password`  | Reset password           |
| `GET`  | `/api/v1/users/me`             | Get current user profile |
| `PUT`  | `/api/v1/users/me`             | Update profile           |
| `POST` | `/api/v1/users/me/documents`   | Upload document          |
| `GET`  | `/api/v1/schemes`              | List schemes             |
| `GET`  | `/api/v1/schemes/{slug}`       | Get scheme details       |
| `GET`  | `/api/v1/schemes/categories`   | Get scheme categories    |
| `POST` | `/api/v1/schemes/save`         | Save/bookmark scheme     |
| `GET`  | `/api/v1/recommendations`      | Get AI recommendations   |
| `POST` | `/api/v1/eligibility/check`    | Check eligibility        |
| `GET`  | `/api/v1/search?q=...`         | Search schemes           |
| `GET`  | `/api/v1/notifications`        | Get notifications        |
| `POST` | `/api/v1/chatbot`              | Ask AI chatbot           |
| `GET`  | `/api/v1/translate/languages`  | List supported languages |
| `POST` | `/api/v1/translate`            | Translate text           |
| `GET`  | `/api/v1/analytics/dashboard`  | Admin analytics          |
| `GET`  | `/api/v1/admin/users`          | Admin user management    |

---

# 🔒 Security

GovScheme AI implements multiple security mechanisms:

* JWT access + refresh tokens
* Refresh token rotation
* Bcrypt password hashing
* AES-256 encryption for Aadhaar/PAN data
* Configurable CORS
* API rate limiting
* Authentication rate limiting
* Security headers
* HSTS
* X-Frame-Options
* Content Security Policy
* Pydantic input validation
* SQLAlchemy ORM
* SQL injection protection
* Role-based authorization

### Rate Limits

```text
General API: 100 requests/minute
Authentication: 20 requests/minute
```

---

# 🛠️ Technology Stack

### Frontend

* Next.js 15
* React
* TypeScript
* Tailwind CSS

### Backend

* Python 3.12
* FastAPI
* SQLAlchemy
* Pydantic
* JWT

### Database & Infrastructure

* SQLite
* PostgreSQL
* Redis
* Docker
* Nginx

### AI / NLP

* Recommendation Engine
* Weighted Scoring
* Text Similarity
* NLP-based Eligibility Extraction
* RAG Chatbot
* Explainable AI

---

# 📁 Project Structure

```text
GovScheme-AI/
│
├── backend/
│   ├── api/
│   ├── models/
│   ├── schemas/
│   ├── services/
│   ├── scripts/
│   ├── main.py
│   └── requirements.txt
│
├── frontend/
│   ├── app/
│   ├── components/
│   ├── lib/
│   ├── public/
│   └── package.json
│
├── docker/
│   └── docker-compose.yml
│
├── data/
│   └── schemes.csv
│
└── README.md
```

---

# 🔄 Application Flow

```text
Citizen
   │
   ▼
Create Profile
   │
   ▼
Profile & Requirements
   │
   ├───────────────┐
   ▼               ▼
Search          AI Recommendations
   │               │
   └───────┬───────┘
           ▼
     Scheme Details
           │
           ▼
    Eligibility Check
           │
           ▼
     Required Documents
           │
           ▼
     Application Guidance
           │
           ▼
 Notifications & Updates
```

---

# 📜 License

This project is intended for **educational and demonstration purposes**.

---

## 👨‍💻 Author

**Nithin Kumar**

GitHub: [Nithin-2005-dev](https://github.com/Nithin-2005-dev)
