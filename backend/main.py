"""
Lagovia Train Tracker — Backend
================================
FastAPI service wrapping the iRail API.

Endpoint:
    GET /departures?q=<substring>
"""

from http import client
from unicodedata import name
from fastapi import FastAPI, HTTPException, Query
from DeparturesResponse import DeparturesResponse
from Departure import Departure
import httpx
import asyncio
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from typing import Optional
from fastapi.middleware.cors import CORSMiddleware
import time
# configuration constants

IRAIL_BASE_URL = "https://api.irail.be/v1"
USER_AGENT = "LagoviaTrainTracker/1.0 (syedanimrah7420@gmail.com)"
DEPARTURE_WINDOW_MINUTES = 15
MIN_QUERY_LENGTH = 3
HTTP_TIMEOUT_SECONDS = 10.0
BELGIAN_TZ = ZoneInfo("Europe/Brussels")
CORS_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]
STATION_CACHE_TTL_SECONDS = 60 * 60  # 1 hour

app = FastAPI(    
    title="Lagovia Train Tracker",
    description="Upcoming train departures for stations matching a substring.",
    version="1.0.0",
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)

async def _http_get(client : httpx.AsyncClient, url : str, params: dict) -> dict:
    response = await client.get(
        url,
        params = params,
        headers = {"User-Agent": USER_AGENT},
        timeout = HTTP_TIMEOUT_SECONDS
    )
    response.raise_for_status()
    return response.json()

_station_cache: dict = {"fetched_at": 0.0, "stations": []}
async def fetch_all_stations(client: httpx.AsyncClient) -> list[dict]:
    """Fetch (or return cached) full station list from iRail."""
    now = time.time()
    cached = _station_cache["stations"]
    age = now - _station_cache["fetched_at"]
    if cached and age < STATION_CACHE_TTL_SECONDS:
        return cached

    data = await _http_get(
        client,
        f"{IRAIL_BASE_URL}/stations/",
        {"format": "json"},
    )
    stations = data.get("station", [])
    _station_cache["stations"] = stations
    _station_cache["fetched_at"] = now
    return stations

async def fetch_liveboard(client: httpx.AsyncClient, station_name: str) -> dict:
    """Fetch upcoming departures for one station."""

    return await _http_get(
        client,
        f"{IRAIL_BASE_URL}/liveboard/",
        {"station": station_name, "format": "json", "lang": "en"},
    )


def matching_all_station(stations: list[dict], query: str) -> list[dict]:
    """Case-insensitive substring match against name and standardname."""
    q = query.casefold()
    return [
        s for s in stations
        if q in s.get("name","").casefold()
        or q in s.get("standardname","").casefold()
    ]

def transform_departure(
    raw: dict,
    departure_station_name: str,
    now_utc: datetime,
    window_end_utc: datetime,) -> Optional[Departure]:
    """
    Convert one raw iRail departure into our Departure model.

    Returns None if the departure is outside the 15-minute window or the
    record is malformed, so the caller can filter with `is not None`.
    """
    # iRail returns numeric fields as strings — cast explicitly.
    try:
        scheduled_epoch = int(raw["time"])
        delay_seconds = int(raw.get("delay", 0))
    except (KeyError, ValueError, TypeError):
        return None

    scheduled_utc = datetime.fromtimestamp(scheduled_epoch, tz=timezone.utc)

    # 15-minute window filter — filter on SCHEDULED time, not actual.
    if not (now_utc <= scheduled_utc <= window_end_utc):
        return None

    vehicle_info = raw.get("vehicleinfo") or {}
    train_number = vehicle_info.get("shortname") or raw.get("vehicle", "unknown")

    return Departure(
        train_number=train_number,
        destination=raw.get("station", "unknown"),
        station=departure_station_name,
        scheduled_time_utc=scheduled_utc.isoformat(),
        scheduled_time_local=scheduled_utc.astimezone(BELGIAN_TZ).strftime("%H:%M"),
        delay_minutes=delay_seconds // 60,
        platform=raw.get("platform") or None,
        canceled=str(raw.get("canceled", "0")) == "1",
    )

@app.get("/departures")
async def get_departures(q: str = Query(...,description = "Station name substring (>= 3 chars)"),
):
    cleaned = q.strip()
    if(len(cleaned) < MIN_QUERY_LENGTH):
        raise HTTPException(
            status_code = 400,
            detail={
                "error": "query_too_short",
                "message": f"Query must be at least {MIN_QUERY_LENGTH} characters.",
                "details": {
                    "min_length": MIN_QUERY_LENGTH,
                    "received_length": len(cleaned),
                },
            },
        )

    # Snapshot 'now' once so all departures see the same window.
    now_utc = datetime.now(timezone.utc)
    window_end_utc = now_utc + timedelta(minutes=DEPARTURE_WINDOW_MINUTES)
    async with httpx.AsyncClient() as client:
        try:
            stations = await fetch_all_stations(client)
            matched =  matching_all_station(stations,cleaned)
        
            station_names = [s["name"] for s in matched]
            liveboards = await asyncio.gather(*(fetch_liveboard(client, name) for name in station_names),
                        return_exceptions=True
            )
        except httpx.HTTPError as exc:
            raise HTTPException(
                status_code=502,
                detail={
                    "error": "upstream_error",
                    "message": "iRail is unavailable or returned an error.",
                    "details": {"reason": str(exc)},
                },
            )

    departures: list[Departure] = []
    for station_name, board in zip(station_names, liveboards):
        if isinstance(board, Exception):
            continue  # skip this station, keep the others
        for raw in (board.get("departures") or {}).get("departure", []):
            dep = transform_departure(raw, station_name, now_utc, window_end_utc)
            if dep is not None:
                departures.append(dep)

    departures.sort(key=lambda d: d.scheduled_time_utc)

    return DeparturesResponse(
        query=cleaned,
        matched_stations=station_names,
        window_minutes=DEPARTURE_WINDOW_MINUTES,
        generated_at_utc=now_utc.isoformat(),
        departures=departures,
    )

@app.get("/health")
async def health() -> dict:
    """Liveness probe — useful for ops and quick local sanity checks."""
    return {"status": "ok"}