from typing import List, Dict, Any
from config import settings
import requests
from bs4 import BeautifulSoup
import requests
import datetime
import json
import re

SERPAPI_API_KEY = "YOUR_SERPAPI_KEY"


# Amadeus imports (optional if installed)
try:
    from amadeus import Client as AmadeusClient, ResponseError as AmadeusResponseError
except Exception:
    AmadeusClient = None
    AmadeusResponseError = Exception

AMADEUS_ID = settings.AMADEUS_CLIENT_ID
AMADEUS_SECRET = settings.AMADEUS_CLIENT_SECRET
USER_AGENT = settings.USER_AGENT or "TravelPlannerBot/1.0"

# -------- Amadeus flight offers -------
def _init_amadeus_client():
    if not AmadeusClient or not AMADEUS_ID or not AMADEUS_SECRET:
        return None
    try:
        client = AmadeusClient(client_id=AMADEUS_ID, client_secret=AMADEUS_SECRET)
        return client
    except Exception:
        return None

def _resolve_to_iata(amadeus_client, query: str) -> str | None:
    if not query:
        return None
    q = query.strip()
    if len(q) == 3 and q.isalpha():
        return q.upper()
    if not amadeus_client:
        return None
    try:
        resp = amadeus_client.reference_data.locations.get(keyword=q, subType='CITY')
        data = getattr(resp, "data", None) or []
        if not data:
            resp = amadeus_client.reference_data.locations.get(keyword=q)
            data = getattr(resp, "data", None) or []
        for item in data:
            if item.get("iataCode"):
                return item.get("iataCode")
    except Exception:
        return None
    return None

def amadeus_flights_search(origin: str, destination: str, depart_date: str, return_date: str | None = None, passengers: int = 1) -> List[Dict[str, Any]]:
    """
    Uses Amadeus Flight Offers API to obtain flight options (keeps function name for compatibility).
    Returns a list of normalized flight dicts.
    If Amadeus not configured, returns mock results.
    """
    # If no Amadeus credentials, return mock data
    if not AMADEUS_ID or not AMADEUS_SECRET or AmadeusClient is None:
        return [
            {"airline": "MockAir", "departure": f"{depart_date}T09:00", "arrival": f"{depart_date}T11:00",
             "price": 280.0, "currency": "USD", "stops": 0, "link": None},
            {"airline": "BudgetFly", "departure": f"{depart_date}T22:00", "arrival": f"{depart_date}T23:59",
             "price": 200.0, "currency": "USD", "stops": 1, "link": None}
        ]

    client = _init_amadeus_client()
    if not client:
        # fallback mock
        return [{"airline": "MockAir-Fallback", "departure": f"{depart_date}T09:00","arrival": f"{depart_date}T11:00","price": 300.0,"currency":"USD","stops":0,"link":None}]

    orig_iata = _resolve_to_iata(client, origin) or origin
    dest_iata = _resolve_to_iata(client, destination) or destination

    params = {
        "originLocationCode": orig_iata,
        "destinationLocationCode": dest_iata,
        "departureDate": depart_date,
        "adults": passengers,
        "currencyCode": "USD",
        "max": 10
    }
    if return_date:
        params["returnDate"] = return_date

    try:
        resp = client.shopping.flight_offers_search.get(**params)
    except AmadeusResponseError as err:
        print(err.description)
        return [{"airline": "MockAir-Error", "departure": f"{depart_date}T09:00","arrival": f"{depart_date}T11:00","price":350.0,"currency":"USD","stops":0,"link":None}]
    except Exception:
        return [{"airline": "MockAir-Exception", "departure": f"{depart_date}T09:00","arrival": f"{depart_date}T11:00","price":330.0,"currency":"USD","stops":0,"link":None}]

    offers = getattr(resp, "data", []) or []
    flights = []
    for offer in offers:
        try:
            price_info = offer.get("price", {})
            total_price = price_info.get("total") or price_info.get("grandTotal") or price_info.get("base") or 0.0
            itineraries = offer.get("itineraries", [])
            dep_time = None
            arr_time = None
            stops = 0
            airline = None
            if itineraries:
                it0 = itineraries[0]
                segments = it0.get("segments", []) or []
                if segments:
                    dep = segments[0].get("departure", {})
                    arr = segments[-1].get("arrival", {})
                    dep_time = dep.get("at") or dep.get("date") or dep.get("time")
                    arr_time = arr.get("at") or arr.get("date") or arr.get("time")
                    stops = max(0, len(segments) - 1)
                    airline = segments[0].get("carrierCode")
            airline = airline or (offer.get("validatingAirlineCodes") or [None])[0] or "Unknown"
            flights.append({
                "airline": airline,
                "departure": dep_time or f"{depart_date}T00:00",
                "arrival": arr_time or (return_date or f"{depart_date}T00:00"),
                "price": float(total_price) if total_price else 0.0,
                "currency": price_info.get("currency") or "USD",
                "stops": stops,
                "link": None
            })
        except Exception:
            continue

    if not flights:
        return [{"airline":"MockAir-EmptyParse","departure":f"{depart_date}T09:00","arrival":f"{depart_date}T11:00","price":320.0,"currency":"USD","stops":0,"link":None}]

    return sorted(flights, key=lambda f: f.get("price", float("inf")))

# -------- Agoda (hotels) - mocked placeholder -------
def agoda_search(destination: str, check_in: str, check_out: str, max_price_per_night: float | None=None, stars_preference:int | None=None) -> List[Dict[str,Any]]:
    hotels = [
        {"name": "Agoda Plaza", "stars": 4, "price_per_night": 150.0, "rating": 8.9, "currency": "USD", "link": "https://www.agoda.com/mock1"},
        {"name": "Budget Stay", "stars": 3, "price_per_night": 90.0, "rating": 7.8, "currency": "USD", "link": "https://www.agoda.com/mock2"},
        {"name": "Luxury Resort", "stars": 5, "price_per_night": 300.0, "rating": 9.4, "currency": "USD", "link": "https://www.agoda.com/mock3"}
    ]

    # extract the stars from the API calls in integer form    
    def extract_stars(value):
        if not value:
            return 0
        if isinstance(value, int):
            return value
        if isinstance(value, str):
            match = re.search(r"\d+", value)
            return int(match.group()) if match else 0
        return 0

    #extract the price of the hotel from API call into float
    def extract_price(rate_info):
        if not isinstance(rate_info, dict):
            return 0.0, "USD"

        raw_price = rate_info.get("lowest") or rate_info.get("highest")
        currency = rate_info.get("currency", "USD")

        if not raw_price:
            return 0.0, currency

        cleaned = "".join(c for c in str(raw_price) if c.isdigit() or c == ".")
        price = float(cleaned) if cleaned else 0.0

        return price, currency

    #pass in parameters
    def get_hotels_by_city(city: str):
        check_in = (datetime.date.today() + datetime.timedelta(days=30)).isoformat()
        check_out = (datetime.date.today() + datetime.timedelta(days=31)).isoformat()

        params = {
            "engine": "google_hotels",
            "q": f"Hotels in {city}",
            "check_in_date": check_in,
            "check_out_date": check_out,
            "currency": "USD",
            "hl": "en",
            "api_key": SERPAPI_API_KEY
        }

        response = requests.get("https://serpapi.com/search", params=params)
        response.raise_for_status()
        data = response.json()

        #Append json to Hotels dict
        for hotel in data.get("properties", []):
            price, currency = extract_price(hotel.get("rate_per_night"))
            stars = extract_stars(hotel.get("hotel_class"))

            rating_raw = hotel.get("overall_rating")
            rating = float(rating_raw) if rating_raw else 0.0

            hotels.append({
                "name": str(hotel.get("name", "")),
                "stars": stars,
                "price_per_night": float(price),
                "rating": rating,
                "currency": str(currency),
                "link": str(hotel.get("link", ""))
            })

    if max_price_per_night:
        hotels = [h for h in hotels if h["price_per_night"] <= max_price_per_night]
    if stars_preference:
        hotels = [h for h in hotels if h["stars"] >= stars_preference]
    hotels = sorted(hotels, key=lambda h: (-h["rating"], h["price_per_night"]))
    return hotels

# -------- TripAdvisor restaurants -------
def tripadvisor_restaurants_search(destination: str, cuisine: str | None=None, price_level: int | None=None, limit:int=10) -> List[Dict[str,Any]]:
    """
    Best-effort TripAdvisor search via HTTP parse; fallback to mock results.
    """
    query = f"{destination} {cuisine or ''} restaurants".strip()
    search_url = "https://www.tripadvisor.com/Search"
    headers = {"User-Agent": USER_AGENT}
    try:
        resp = requests.get(search_url, params={"q": query}, headers=headers, timeout=8)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        anchors = soup.find_all("a", href=True)
        results = []
        seen = set()
        for a in anchors:
            href = a["href"]
            if '/Restaurant_Review-' in href or '/Restaurants-' in href:
                name = a.get_text(strip=True) or a.get('title') or a.get('aria-label') or "TripAdvisor Restaurant"
                link = "https://www.tripadvisor.com" + href.split("#",1)[0]
                if link in seen:
                    continue
                seen.add(link)
                results.append({
                    "name": name,
                    "link": link,
                    "snippet": "",
                    "estimated_price": 15.0,
                    "cuisine": cuisine or "Various"
                })
                if len(results) >= limit:
                    break
        if results:
            return results
    except Exception:
        pass
    # Mock fallback
    mock = [
        {"name": "Local Noodle House", "link": "https://www.tripadvisor.com/mock1", "estimated_price": 8.0, "cuisine": "local"},
        {"name": "Seafood Delight", "link": "https://www.tripadvisor.com/mock2", "estimated_price": 25.0, "cuisine": "seafood"},
        {"name": "Vegetarian Corner", "link": "https://www.tripadvisor.com/mock3", "estimated_price": 12.0, "cuisine": "vegetarian"},
    ]
    return mock[:limit]
