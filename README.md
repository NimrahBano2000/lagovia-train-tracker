# Lagovia Train Tracker

A fullstack implementation of the [Digital Product School Engineering
Track Technical Challenge](./Lagovia_Train_Tracker.pdf): search for
Belgian train stations by substring and see every upcoming departure
within the next 15 minutes, with live delays.

- **Backend**: Python 3.11.0 FastAPI, wrapping the public
  [iRail API](https://docs.irail.be/).
- **Frontend**: React 19.2.6  Vite, debounced typeahead search.


## Prerequisites

- Python 3.10+ (developed on 3.11)
- Node.js 20+ (developed on 22)
- A working network connection — the backend calls the live iRail API.

## Run it locally

Two terminals. The backend first, then the frontend.

### Backend

```bash
cd backend
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# macOS / Linux:
# source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

The API listens on `http://localhost:8000`. The auto-generated docs
live at `http://localhost:8000/docs`.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The app opens at `http://localhost:5173`.

## API contract

### `GET /departures?q=<substring>`

Returns every upcoming departure from every station whose `name` or
`standardname` contains `<substring>` (case-insensitive, substring
match), scheduled within the next 15 minutes.

#### Success — `200 OK`

```json
{
  "query": "Bru",
  "matched_stations": ["Brussel-Centraal", "Brussel-Zuid", ...],
  "window_minutes": 15,
  "generated_at_utc": "2026-05-31T15:42:13.821432+00:00",
  "departures": [
    {
      "train_number": "IC 1234",
      "destination": "Antwerpen-Centraal",
      "station": "Brussel-Centraal",
      "scheduled_time_utc": "2026-05-31T15:48:00+00:00",
      "scheduled_time_local": "17:48",
      "delay_minutes": 0,
      "platform": "6",
      "canceled": false
    }
  ]
}
```

#### Input too short — `400 Bad Request`

Returned when `q` has fewer than 3 non-whitespace characters.

```json
{
  "detail": {
    "error": "query_too_short",
    "message": "Query must be at least 3 characters.",
    "details": { "min_length": 3, "received_length": 1 }
  }
}
```

#### iRail unavailable — `502 Bad Gateway`

Returned when the upstream iRail API is unreachable, times out, or
returns 5xx.

```json
{
  "detail": {
    "error": "upstream_error",
    "message": "iRail is unavailable or returned an error.",
    "details": { "reason": "<underlying exception>" }
  }
}
```

### `GET /health`

Liveness probe. Returns `{"status": "ok"}` with `200`.

## Decisions and trade-offs

- **Why a backend in front of an already-public API.** Three reasons:
  CORS (browsers can't always read iRail directly); shape control (we
  return a clean documented JSON, not iRail's string-typed verbose
  blob); and the 15-minute window + delay-conversion logic belongs
  server-side rather than duplicated per client.

- **FastAPI over Flask / Django.** Type-hint-driven validation,
  built-in async, auto-generated OpenAPI at `/docs`. The brief named
  it as the preferred Python option.

- **React + Vite + plain JavaScript.** Vite is the current modern
  default (CRA is deprecated). Plain JS rather than TypeScript to
  keep scope tight for the one-week budget; on a longer project I'd
  reach for TS.

- **Single-file backend (`main.py`) with three file `Departures.py` , `DeparturesResponse.py` , `ErrorBody.py`split out.**
  Routing and business logic in `main.py`, Pydantic response models
  in `Departure.py` and `DeparturesResponse.py` to keep the data contract separable. 

- **Parallel liveboard fetches via (`asyncio.gather`)with `return_exceptions=True`.** 
  Each matched station's liveboard fetch
  runs concurrently. One failed station does not poison the whole
  response; we just skip it in the aggregation loop.

- **15-minute window filter on scheduled time, not actual.** A train
  scheduled at 15:00 with a 20-minute delay still appears at 14:50,
  with the delay shown next to it — matching the brief's literal
  wording and the user's mental model. The alternative (filter on
  `scheduled + delay`, or show if either is in-window) is also
  defensible; could be flag-controlled in a future iteration.

- **Input contract: 400, not 422.** FastAPI's automatic validation
  uses 422; we reserve 400 for this specific business rule so the
  frontend can distinguish "input too short" from generic shape
  errors via the `error` code.

- **In-process 1-hour TTL cache for the station list.** The ~600
  stations rarely change. Cached in a module-level dict; restart =
  fresh fetch. For multi-instance prod I'd swap to Redis.

- **Debounce on 300 ms with `useEffect` cleanup.** Standard typeahead
  debounce. Each keystroke cancels the previous pending timer.
  Typing "Brussels" fires 1 request instead of 6.

## Known limitations

- **No request cancellation.** Debouncing prevents most race
  conditions, but a slow in-flight request followed by a fast one can
  still resolve out of order. The proper fix is `AbortController` in
  the `useEffect` cleanup — not implemented for scope.
- **No persistent cache.** The station-list cache is in-process;
  restart loses it.
- **No retries with backoff** on iRail failure — would add `tenacity`
  or similar for production.
- **Substring match is case-insensitive but not accent-folded.** `é`
  vs `e` don't match. Would normalize with `unicodedata.normalize`
  for production.
- **No automated tests.** Pure helpers (`find_matching_stations`,
  `transform_departure`) are designed for easy unit testing — would
  use pytest with `httpx.MockTransport` for the iRail client.
- **CORS hardcoded to localhost:5173.** Would move to an env var
  for production.

## Architecture in one diagram
    ┌──────────┐         ┌─────────────┐         ┌──────────────┐
    │  Browser │ ──HTTP─►│ FastAPI     │ ──HTTP─►│ iRail API    │
    │ (React)  │ ◄──JSON─│ backend     │ ◄──JSON─│(api.irail.be)│
    │  :5173   │         │  :8000      │         │              │
    └──────────┘         └─────────────┘         └──────────────┘
## AI usage

See [AI_USAGE.md](./AI_USAGE.md) for the full report.