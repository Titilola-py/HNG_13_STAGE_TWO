# Country Currency & Exchange API

A RESTful API that fetches country data from external APIs, computes estimated GDP based on exchange rates, and provides CRUD operations with MongoDB storage.

## Features

- Fetch and cache country data with currency exchange rates
- Calculate estimated GDP for each country
- Filter and sort countries by region, currency, or GDP
- Generate summary images with top GDP countries
- Full CRUD operations
- Async MongoDB integration
- Error handling for external API failures

## Tech Stack

- **FastAPI** - Modern Python web framework
- **MongoDB** - NoSQL database (with Motor async driver)
- **Pillow** - Image generation
- **httpx** - Async HTTP client

## Prerequisites

- Python 3.8+
- MongoDB (local or Atlas cloud)
- pip

## Installation & Setup

### 1. Clone the repository

```bash
git clone https://github.com/Titilola-py/HNG_13_STAGE_TWO
cd HNG_13_STAGE_TWO
```

### 2. Create virtual environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file in the root directory:

```bash
cp .env.example .env
```

Edit `.env` with your configuration:

```env
MONGODB_URL=mongodb://localhost:27017
# For MongoDB Atlas: mongodb+srv://username:password@cluster.mongodb.net/?retryWrites=true&w=majority
DB_NAME=countries_db
PORT=8000
```

### 5. Run MongoDB

**Option A: Local MongoDB**
```bash
# Install MongoDB Community Edition
# Start MongoDB service
mongod --dbpath /path/to/data/directory
```

**Option B: MongoDB Atlas (Cloud - Recommended for deployment)**
1. Create free account at [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
2. Create a cluster
3. Get connection string and update `MONGODB_URL` in `.env`

### 6. Run the application

```bash
python main.py
```

Or using uvicorn directly:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

## API Documentation

Once running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API Endpoints

### 1. Refresh Countries Data
```http
POST /countries/refresh
```

Fetches countries from external APIs, calculates exchange rates and GDP, then caches in database.

**Response:**
```json
{
  "message": "Countries data refreshed successfully",
  "total_countries": 250,
  "last_refreshed_at": "2025-10-26T18:00:00Z"
}
```

### 2. Get All Countries
```http
GET /countries
```

**Query Parameters:**
- `region` - Filter by region (e.g., `Africa`, `Europe`)
- `currency` - Filter by currency code (e.g., `NGN`, `USD`)
- `sort` - Sort results (`gdp_desc`, `gdp_asc`, `population_desc`, `population_asc`)

**Examples:**
```http
GET /countries?region=Africa
GET /countries?currency=NGN
GET /countries?sort=gdp_desc
GET /countries?region=Africa&sort=gdp_desc
```

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

### 3. Get Single Country
```http
GET /countries/{name}
```

**Example:**
```http
GET /countries/Nigeria
```

### 4. Delete Country
```http
DELETE /countries/{name}
```

**Example:**
```http
DELETE /countries/Nigeria
```

**Response:**
```json
{
  "message": "Country 'Nigeria' deleted successfully"
}
```

### 5. Get Status
```http
GET /status
```

**Response:**
```json
{
  "total_countries": 250,
  "last_refreshed_at": "2025-10-26T18:00:00Z"
}
```

### 6. Get Summary Image
```http
GET /countries/image
```

Returns a PNG image showing:
- Total countries cached
- Top 5 countries by estimated GDP
- Last refresh timestamp

## Testing

### Using curl

```bash
# Refresh data
curl -X POST http://localhost:8000/countries/refresh

# Get all countries
curl http://localhost:8000/countries

# Get countries in Africa
curl http://localhost:8000/countries?region=Africa

# Get a specific country
curl http://localhost:8000/countries/Nigeria

# Get status
curl http://localhost:8000/status

# Get summary image
curl http://localhost:8000/countries/image --output summary.png
```

### Using Python

```python
import requests

# Refresh data
response = requests.post("http://localhost:8000/countries/refresh")
print(response.json())

# Get countries
response = requests.get("http://localhost:8000/countries?region=Africa&sort=gdp_desc")
print(response.json())
```

### Automated Testing

Run the included test script:

```bash
python test_api.py
```

## Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `MONGODB_URL` | MongoDB connection string | `mongodb://localhost:27017` or Atlas URL |
| `DB_NAME` | Database name | `countries_db` |
| `PORT` | Server port | `8000` |

## Error Handling

The API returns consistent error responses:

**404 Not Found:**
```json
{
  "error": "Country not found"
}
```

**400 Bad Request:**
```json
{
  "error": "Validation failed",
  "details": {
    "currency_code": "is required"
  }
}
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
{
  "error": "Internal server error"
}
```

## Project Structure

```
├── main.py              # Main FastAPI application
├── requirements.txt     # Python dependencies
├── .env.example        # Example environment variables
├── .env                # Your environment variables
├── .gitignore          # Git ignore file
├── README.md           # This file
├── test_api.py         # Automated test script
├── cache/              # Generated images directory
│   └── summary.png     # Auto-generated summary image
```