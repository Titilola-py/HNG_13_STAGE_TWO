# Country Currency & Exchange API

RESTful API that fetches country data, calculates GDP using exchange rates, and provides CRUD operations.

## Tech Stack
- FastAPI + MongoDB + Pillow + httpx

## Quick Start

```bash
# Clone and setup
git clone <your-repo-url>
cd country-currency-api
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Configure .env
cp .env.example .env
# Edit MONGODB_URL in .env

# Run
python main.py
# Visit http://localhost:8000/docs
```

## Environment Variables

```env
MONGODB_URL=mongodb://localhost:27017  # or MongoDB Atlas URL
DB_NAME=countries_db
PORT=8000
```

---

# API Endpoints

## POST /countries/refresh
Fetch countries and exchange rates, cache in database.

**Response:**
```json
{
  "message": "Countries data refreshed successfully",
  "total_countries": 250,
  "last_refreshed_at": "2025-10-26T18:00:00Z"
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/countries/refresh
```

---

## GET /countries
Get all countries with optional filters and sorting.

**Query Parameters:**
- `region` - Filter by region (e.g., `Africa`, `Europe`)
- `currency` - Filter by currency code (e.g., `NGN`, `USD`)
- `sort` - Sort order: `gdp_desc`, `gdp_asc`, `population_desc`, `population_asc`

**Response:**
```json
[
  {
    "id": 1,
    "name": "Nigeria",
    "capital": "Abuja",
    "region": "Africa",
    "population": 206139589,
    "currency_code": "NGN",
    "exchange_rate": 1600.23,
    "estimated_gdp": 25767448125.2,
    "flag_url": "https://flagcdn.com/ng.svg",
    "last_refreshed_at": "2025-10-26T18:00:00Z"
  }
]
```

**Examples:**
```bash
curl http://localhost:8000/countries
curl http://localhost:8000/countries?region=Africa
curl http://localhost:8000/countries?currency=NGN
curl http://localhost:8000/countries?sort=gdp_desc
curl "http://localhost:8000/countries?region=Africa&sort=gdp_desc"
```

---

## GET /countries/{name}
Get a specific country by name (case-insensitive).

**Response:**
```json
{
  "id": 1,
  "name": "Nigeria",
  "capital": "Abuja",
  "region": "Africa",
  "population": 206139589,
  "currency_code": "NGN",
  "exchange_rate": 1600.23,
  "estimated_gdp": 25767448125.2,
  "flag_url": "https://flagcdn.com/ng.svg",
  "last_refreshed_at": "2025-10-26T18:00:00Z"
}
```

**Example:**
```bash
curl http://localhost:8000/countries/Nigeria
```

---

## DELETE /countries/{name}
Delete a country record.

**Response:**
```json
{
  "message": "Country 'Nigeria' deleted successfully"
}
```

**Example:**
```bash
curl -X DELETE http://localhost:8000/countries/Nigeria
```

---

## GET /status
Get database status and last refresh timestamp.

**Response:**
```json
{
  "total_countries": 250,
  "last_refreshed_at": "2025-10-26T18:00:00Z"
}
```

**Example:**
```bash
curl http://localhost:8000/status
```

---

## GET /countries/image
Get auto-generated summary image (PNG).

Shows:
- Total countries cached
- Top 5 countries by GDP
- Last refresh timestamp

**Example:**
```bash
curl http://localhost:8000/countries/image --output summary.png
```

---

# Error Responses

**404 Not Found:**
```json
{"error": "Country not found"}
```

**503 Service Unavailable:**
```json
{
  "error": "External data source unavailable",
  "details": "Could not fetch data from restcountries.com"
}
```

**500 Internal Server Error:**
```json
{"error": "Internal server error"}
```

---

# Testing

Run automated tests:
```bash
python test_api.py
```

Or test manually:
```bash
# 1. Refresh data (takes 30-60 seconds)
curl -X POST http://localhost:8000/countries/refresh

# 2. Get all countries
curl http://localhost:8000/countries

# 3. Filter African countries by GDP
curl "http://localhost:8000/countries?region=Africa&sort=gdp_desc"

# 4. Get Nigeria
curl http://localhost:8000/countries/Nigeria

# 5. Get status
curl http://localhost:8000/status

# 6. Download image
curl http://localhost:8000/countries/image --output summary.png
```

---

# Deployment

## Railway
```bash
npm i -g @railway/cli
railway login
railway init
railway add  # Add MongoDB
railway up
```

Set environment variables in Railway dashboard:
```
MONGODB_URL=${{MongoDB.MONGO_URL}}
DB_NAME=countries_db
```

## MongoDB Atlas Setup
1. Create account at [mongodb.com/cloud/atlas](https://www.mongodb.com/cloud/atlas)
2. Create free cluster (M0)
3. Add database user
4. Whitelist IP: `0.0.0.0/0`
5. Get connection string
6. Update `MONGODB_URL` in .env

---

# Project Structure

```
├── main.py              # FastAPI application
├── requirements.txt     # Dependencies
├── .env.example         # Environment template
├── .env                 # Your config (not in git)
├── .gitignore           # Git ignore
├── README.md            # This file
├──railway.json          # Railway configuration
├──test_api.py          # Test script
└── cache/               # Auto-generated images
```

---

# Business Logic

**GDP Calculation:**
```
estimated_gdp = (population × random(1000-2000)) ÷ exchange_rate
```

**Currency Handling:**
- Multiple currencies: Uses first one
- No currencies: Sets all to `null`, GDP to `0`
- Currency not in rates: Sets rate and GDP to `null`

**Update Logic:**
- Matches by name (case-insensitive)
- Existing: Updates all fields
- New: Inserts with auto-increment ID

---

# External APIs

- **Countries**: https://restcountries.com/v2/all
- **Exchange Rates**: https://open.er-api.com/v6/latest/USD

---

# Dependencies

```txt
fastapi==0.109.0
uvicorn[standard]==0.27.0
motor==3.3.2
pydantic==2.5.3
httpx==0.26.0
Pillow==10.2.0
python-dotenv==1.0.0
pymongo==4.6.1
```