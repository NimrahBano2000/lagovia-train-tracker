"""
Lagovia Train Tracker — Backend
================================
FastAPI service wrapping the iRail API.

Endpoint:
    GET /departures?q=<substring>
"""

from http import client
from fastapi import FastAPI, HTTPException, Query
from DeparturesResponse import DeparturesResponse
from Departure import Departure
import httpx
# configuration constants

IRAIL_BASE_URL = "https://api.irail.be/v1"
USER_AGENT = "LagoviaTrainTracker/1.0 (syedanimrah7420@gmail.com)"
DEPARTURE_WINDOW_MINUTES = 15
MIN_QUERY_LENGTH = 3
HTTP_TIMEOUT_SECONDS = 10.0


app = FastAPI(    
    title="Lagovia Train Tracker",
    description="Upcoming train departures for stations matching a substring.",
    version="1.0.0",
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


async def fetch_all_station(client: httpx.AsyncClient) -> list[dict]:
    data = await _http_get(
        client,
        f"{IRAIL_BASE_URL}/stations/",
        {"format": "json"},
    )
    return data.get("station",[])

def matching_all_Station(stations: list[dict], query: str) -> list[dict]:
    q = query.casefold()
    return [
        s for s in stations
        if q in s.get("name","").casefold()
        or q in s.get("standardname","").casefold()
    ]


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
    async with httpx.AsyncClient() as client:
        stations = await fetch_all_station(client)
        matched =  matching_all_Station(stations,cleaned)

    return {        
        "query": cleaned,
        "Matching stations": [s["name"] for s in matched],
        "match_count": len(matched),
        "departures": [],
    }