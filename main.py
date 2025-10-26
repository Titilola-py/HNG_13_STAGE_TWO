from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
import httpx
import random
import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import asyncio

app = FastAPI(title="Country Currency & Exchange API")

MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "countries_db")
PORT = int(os.getenv("PORT", 8000))

client = AsyncIOMotorClient(MONGODB_URL)
db = client[DB_NAME]
countries_collection = db.countries
metadata_collection = db.metadata

CACHE_DIR = Path("cache")
CACHE_DIR.mkdir(exist_ok=True)
IMAGE_PATH = CACHE_DIR / "summary.png"


class Country(BaseModel):
    id: Optional[int] = None
    name: str
    capital: Optional[str] = None
    region: Optional[str] = None
    population: int
    currency_code: Optional[str] = None
    exchange_rate: Optional[float] = None
    estimated_gdp: Optional[float] = None
    flag_url: Optional[str] = None
    last_refreshed_at: Optional[str] = None


class StatusResponse(BaseModel):
    total_countries: int
    last_refreshed_at: Optional[str] = None


class ErrorResponse(BaseModel):
    error: str
    details: Optional[dict] = None


async def get_next_id():
    """Get next auto-increment ID"""
    counter = await db.counters.find_one_and_update(
        {"_id": "country_id"}, {"$inc": {"seq": 1}}, upsert=True, return_document=True
    )
    return counter["seq"] if counter else 1


async def fetch_countries_data():
    """Fetch countries from external API"""
    url = "https://restcountries.com/v2/all?fields=name,capital,region,population,flag,currencies"
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(url)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            raise HTTPException(
                status_code=503,
                detail={
                    "error": "External data source unavailable",
                    "details": f"Could not fetch data from restcountries.com: {str(e)}",
                },
            )


async def fetch_exchange_rates():
    """Fetch exchange rates from external API"""
    url = "https://open.er-api.com/v6/latest/USD"
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()
            return data.get("rates", {})
        except httpx.HTTPError as e:
            raise HTTPException(
                status_code=503,
                detail={
                    "error": "External data source unavailable",
                    "details": f"Could not fetch data from open.er-api.com: {str(e)}",
                },
            )


def calculate_gdp(population: int, exchange_rate: Optional[float]) -> Optional[float]:
    """Calculate estimated GDP"""
    if exchange_rate is None or exchange_rate == 0:
        return None
    random_multiplier = random.uniform(1000, 2000)
    return (population * random_multiplier) / exchange_rate


async def generate_summary_image(countries: List[dict], timestamp: str):
    """Generate summary image with top 5 countries by GDP"""

    img = Image.new("RGB", (800, 600), color="white")
    draw = ImageDraw.Draw(img)

    try:
        title_font = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 32
        )
        header_font = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20
        )
        text_font = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16
        )
    except:
        title_font = ImageFont.load_default()
        header_font = ImageFont.load_default()
        text_font = ImageFont.load_default()

    draw.text((50, 30), "Country Data Summary", fill="#2C3E50", font=title_font)

    draw.text(
        (50, 90), f"Total Countries: {len(countries)}", fill="#34495E", font=header_font
    )

    draw.text((50, 120), f"Last Refreshed: {timestamp}", fill="#7F8C8D", font=text_font)

    draw.text(
        (50, 170), "Top 5 Countries by Estimated GDP:", fill="#2C3E50", font=header_font
    )

    sorted_countries = sorted(
        [c for c in countries if c.get("estimated_gdp")],
        key=lambda x: x.get("estimated_gdp", 0),
        reverse=True,
    )[:5]

    y_position = 210
    for i, country in enumerate(sorted_countries, 1):
        gdp = country.get("estimated_gdp", 0)
        gdp_str = f"${gdp:,.2f}" if gdp else "N/A"
        text = f"{i}. {country['name']}: {gdp_str}"
        draw.text((70, y_position), text, fill="#34495E", font=text_font)
        y_position += 35

    img.save(IMAGE_PATH)


# API Endpoints
@app.get("/")
async def root():
    return {"message": "Country Currency & Exchange API", "status": "running"}


@app.post("/countries/refresh")
async def refresh_countries():
    """Fetch and cache all countries with exchange rates"""
    try:
        countries_data = await fetch_countries_data()
        exchange_rates = await fetch_exchange_rates()

        timestamp = datetime.utcnow().isoformat() + "Z"
        processed_countries = []

        for country_data in countries_data:
            name = country_data.get("name")
            if not name:
                continue

            currencies = country_data.get("currencies", [])
            currency_code = None
            exchange_rate = None
            estimated_gdp = None

            if currencies and len(currencies) > 0:
                currency_code = currencies[0].get("code")

                if currency_code and currency_code in exchange_rates:
                    exchange_rate = exchange_rates[currency_code]
                    population = country_data.get("population", 0)
                    if population and exchange_rate:
                        estimated_gdp = calculate_gdp(population, exchange_rate)

            existing = await countries_collection.find_one(
                {"name": {"$regex": f"^{name}$", "$options": "i"}}
            )

            country_doc = {
                "name": name,
                "capital": country_data.get("capital"),
                "region": country_data.get("region"),
                "population": country_data.get("population", 0),
                "currency_code": currency_code,
                "exchange_rate": exchange_rate,
                "estimated_gdp": estimated_gdp if estimated_gdp else 0,
                "flag_url": country_data.get("flag"),
                "last_refreshed_at": timestamp,
            }

            if existing:
        
                await countries_collection.update_one(
                    {"_id": existing["_id"]}, {"$set": country_doc}
                )
                country_doc["id"] = existing["id"]
            else:
                country_id = await get_next_id()
                country_doc["id"] = country_id
                await countries_collection.insert_one(country_doc)

            processed_countries.append(country_doc)

        await metadata_collection.update_one(
            {"_id": "last_refresh"},
            {
                "$set": {
                    "timestamp": timestamp,
                    "total_countries": len(processed_countries),
                }
            },
            upsert=True,
        )

        await generate_summary_image(processed_countries, timestamp)

        return {
            "message": "Countries data refreshed successfully",
            "total_countries": len(processed_countries),
            "last_refreshed_at": timestamp,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": "Internal server error", "details": str(e)},
        )


@app.get("/countries", response_model=List[Country])
async def get_countries(
    region: Optional[str] = Query(None),
    currency: Optional[str] = Query(None),
    sort: Optional[str] = Query(None),
):
    """Get all countries with optional filters and sorting"""
    query = {}

    if region:
        query["region"] = {"$regex": f"^{region}$", "$options": "i"}
    if currency:
        query["currency_code"] = currency

    cursor = countries_collection.find(query, {"_id": 0})

    if sort:
        if sort == "gdp_desc":
            cursor = cursor.sort("estimated_gdp", -1)
        elif sort == "gdp_asc":
            cursor = cursor.sort("estimated_gdp", 1)
        elif sort == "population_desc":
            cursor = cursor.sort("population", -1)
        elif sort == "population_asc":
            cursor = cursor.sort("population", 1)

    countries = await cursor.to_list(length=None)
    return countries


@app.get("/countries/{name}", response_model=Country)
async def get_country(name: str):
    """Get a single country by name"""
    country = await countries_collection.find_one(
        {"name": {"$regex": f"^{name}$", "$options": "i"}}, {"_id": 0}
    )

    if not country:
        raise HTTPException(status_code=404, detail={"error": "Country not found"})

    return country


@app.delete("/countries/{name}")
async def delete_country(name: str):
    """Delete a country by name"""
    result = await countries_collection.delete_one(
        {"name": {"$regex": f"^{name}$", "$options": "i"}}
    )

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail={"error": "Country not found"})

    return {"message": f"Country '{name}' deleted successfully"}


@app.get("/status", response_model=StatusResponse)
async def get_status():
    """Get total countries and last refresh timestamp"""
    total = await countries_collection.count_documents({})
    metadata = await metadata_collection.find_one({"_id": "last_refresh"})

    return {
        "total_countries": total,
        "last_refreshed_at": metadata.get("timestamp") if metadata else None,
    }


@app.get("/countries/image")
async def get_summary_image():
    """Serve the generated summary image"""
    if not IMAGE_PATH.exists():
        raise HTTPException(
            status_code=404, detail={"error": "Summary image not found"}
        )

    return FileResponse(IMAGE_PATH, media_type="image/png")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=PORT)
