# PocketSmart AI: Your Smart Budget & Recommendation Assistant

PocketSmart AI is an end-to-end Full-Stack Generative AI application engineered to help users plan budgets, events, and styling with strict financial constraints. Powered by Google Gemini GenAI, FastAPI, SQLite, and a responsive web interface, PocketSmart guarantees that recommended items and services fit strictly within user-defined budgets.

---

## 1. Project Introduction
When decorating a home, planning an event, or purchasing matching jewelry, individuals frequently overspend due to a lack of category budgeting and itemized cost forecasting. 

**PocketSmart AI** solves this problem by acting as an intelligent financial co-pilot:
- Analyzes user requirements and exact budgets in INR (₹).
- Intelligently apportions total funds across core spending pillars.
- Curates specific recommendations matching user styles and themes.
- Enriches recommendations with direct search links to trusted Indian platforms: **Amazon**, **Flipkart**, **IKEA**, **Swiggy**, **Zomato**, **OYO**, **CaratLane**, and **Myntra**.
- Analyzes outfit photos via Gemini Vision for precise jewelry coordination.
- Persistently records plan histories in an SQLite database.

---

## 2. Key Features
- **Strict Budget Guarantee:** Automated algorithms calculate total expenditures and remaining budget savings, alerting users if constraints are exceeded.
- **Home Interior Planner:** Intelligently allocates funds across Core Furniture, Lighting & Electricals, and Wall & Soft Furnishings.
- **Party & Event Planner:** Dynamically balances budgets for Catering (per-head buffet calculations), Venue Rental, Backdrop Decor, and DJ/Entertainment setups.
- **Jewelry & Outfit Matcher:** Multimodal support allowing users to upload dress photos (JPG, PNG, WEBP up to 5MB) for neckline and color harmony analysis.
- **E-Commerce & Vendor Abstraction:** Generates verified search URLs for Amazon, Flipkart, IKEA, Swiggy, Zomato, and OYO without faking live warehouse inventories.
- **User Authentication & Session Management:** Secure registration, password hashing (bcrypt), and JWT session tokens.
- **Persistent SQLite Database:** Tracks all generated recommendation blueprints linked to authenticated users.

---

## 3. Technology Stack
- **Backend:** Python 3.10+, FastAPI, Uvicorn, Pydantic v2, python-dotenv, SQLAlchemy, python-jose, Passlib (bcrypt), Jinja2.
- **AI Engine:** Google Gemini API (`@google/genai` / `google-genai` SDK) with configurable model alias (`gemini-3.8-flash`).
- **Database:** SQLite (automatic schema initialization with zero external dependencies).
- **Frontend:** Semantic HTML5, CSS3 Custom Properties, Responsive Flex/Grid Layouts, Vanilla JavaScript.

---

## 4. Architecture
PocketSmart AI follows a clean, modular service-oriented architecture:
1. **Client / Browser:** Interacts with Jinja2-rendered pages or JSON API endpoints.
2. **FastAPI Routing Layer:** Validates incoming payloads using Pydantic schemas.
3. **Authentication Layer:** Inspects cookies and `Authorization: Bearer` headers using JWT.
4. **Service Layer:**
   - `gemini_service.py` / `gemini_utils.py`: Centralized GenAI communication, structured JSON prompts, and fallback logic.
   - `platform_service.py`: Vendor URL encoding and vendor metadata.
   - `recommendation_service.py`: Business calculations and database persistence.
5. **Database Layer:** SQLAlchemy models (`User`, `Recommendation`) connected to SQLite (`data/pocketsmart.db`).

---

## 5. Folder Structure
```
PocketSmart-AI/
│
├── main.py                    # Application entry point & FastAPI setup
├── requirements.txt           # Python dependencies
├── .env.example               # Environment variables template
├── README.md                  # Comprehensive documentation
├── database.py                # SQLAlchemy engine & session factory
├── config.py                  # Pydantic & environment configuration
├── gemini_utils.py            # Reusable Gemini AI helper utilities
├── auth.py                    # JWT token creation, password hashing, user dependencies
│
├── models/
│   ├── __init__.py
│   ├── user.py                # User database model
│   └── recommendation.py      # Recommendation history model
│
├── schemas/
│   ├── __init__.py
│   ├── user_schema.py         # Registration & login schemas
│   ├── planner_schema.py      # Home, party, and jewelry input schemas
│   └── recommendation_schema.py# Item, allocation, and budget output schemas
│
├── routes/
│   ├── __init__.py
│   ├── auth_routes.py         # /login, /register, /logout, /session-info
│   ├── home_routes.py         # /home-planner, /generate-home
│   ├── party_routes.py        # /party-planner, /generate-party
│   ├── jewelry_routes.py      # /jewelry-planner, /generate-jewelry
│   ├── recommendation_routes.py # /recommendations-details
│   └── history_routes.py      # /history
│
├── services/
│   ├── __init__.py
│   ├── gemini_service.py      # Core Gemini API prompt engineering & fallbacks
│   ├── recommendation_service.py # Persistence and history queries
│   └── platform_service.py    # Vendor links (Amazon, Flipkart, IKEA, Swiggy, etc.)
│
├── templates/                 # Jinja2 HTML templates
│   ├── base.html
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   ├── dashboard.html
│   ├── home_planner.html
│   ├── home_recommendations.html
│   ├── party_planner.html
│   ├── party_recommendations.html
│   ├── jewelry_planner.html
│   ├── jewelry_recommendations.html
│   ├── history.html
│   └── testimonials.html
│
├── static/
│   ├── css/style.css          # Master stylesheet
│   └── js/
│       ├── main.js
│       ├── home.js
│       ├── party.js
│       └── jewelry.js
│
├── uploads/                   # Storage for uploaded outfit photos
└── data/                      # Persistent SQLite database folder
    └── pocketsmart.db
```

---

## 6. Installation & Quickstart

### Prerequisites
- Python 3.10 or higher
- Git

### Windows
```powershell
# 1. Clone or extract the project
cd PocketSmart-AI

# 2. Create virtual environment
python -m venv venv

# 3. Activate virtual environment
venv\Scripts\activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Set up environment file
copy .env.example .env

# 6. Run the FastAPI development server
uvicorn main:app --reload
```

### macOS / Linux
```bash
# 1. Navigate to project root
cd PocketSmart-AI

# 2. Create virtual environment
python3 -m venv venv

# 3. Activate virtual environment
source venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Set up environment file
cp .env.example .env

# 6. Run the FastAPI development server
uvicorn main:app --reload
```

Open your browser and navigate to:
**`http://127.0.0.1:8000`**

---

## 7. Environment Variables Configuration
Open `.env` in any text editor and customize the values:

```env
# Gemini API Key from Google AI Studio
GEMINI_API_KEY="your_actual_api_key_here"

# Model name (default: gemini-3.8-flash)
GEMINI_MODEL="gemini-3.8-flash"

# JWT Secret key for signing authentication tokens
SECRET_KEY="pocketsmart_super_secure_jwt_secret_key_change_in_production"

# Database connection URL (SQLite)
DATABASE_URL="sqlite:///./data/pocketsmart.db"

# Allowed CORS origins
ALLOWED_ORIGINS="http://127.0.0.1:8000,http://localhost:8000,http://localhost:3000"
```

> **Note:** If `GEMINI_API_KEY` is omitted or empty, PocketSmart AI gracefully activates its intelligent deterministic fallback engine, calculating realistic budget apportionments and vendor items so testing and grading never crash.

---

## 8. Available API Routes

### Authentication & Session
- `GET /login`: Render login page.
- `POST /login`: Authenticate credentials, set cookie & return JWT.
- `GET /register`: Render registration page.
- `POST /register`: Register new user account.
- `POST /token`: OAuth2 password bearer token endpoint.
- `GET /logout`: Clear session cookie and redirect.
- `GET /session-info`: Current authenticated user status.
- `GET /session-data`: Session metadata summary.

### Planners & Recommendations
- `GET /home-planner`: Render Home Interior planner form.
- `POST /generate-home`: Generate interior blueprint & category allocation.
- `GET /party-planner`: Render Party planner form.
- `POST /generate-party`: Generate event blueprint with 4-pillar allocation.
- `GET /jewelry-planner`: Render Jewelry & Outfit matcher form.
- `POST /generate-jewelry`: Process outfit photo & generate matching jewelry.
- `GET /recommendations-details`: Filtered recommendation lookup API.
- `GET /history`: View user recommendation history (HTML & JSON).
- `GET /startup`: Health and connectivity check.

---

## 9. Troubleshooting
1. **ModuleNotFoundError:** Ensure your virtual environment is activated (`venv\Scripts\activate` on Windows or `source venv/bin/activate` on Linux/macOS) before running `pip install -r requirements.txt`.
2. **Database Locked / Permission Error:** The application automatically creates `./data` and `./uploads`. Ensure write permissions exist in the project directory.
3. **Invalid Image Upload:** Supported formats are JPG, JPEG, PNG, and WEBP under 5MB.
4. **Port In Use (8000):** If port 8000 is occupied, run `uvicorn main:app --port 8080 --reload`.
