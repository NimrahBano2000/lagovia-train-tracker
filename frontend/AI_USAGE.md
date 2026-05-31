# AI usage report

## Tools used

- **Claude (Anthropic)** — used as an interactive tutor while building
  this project. The model walked me through concepts (FastAPI async,
  React hooks, CORS, the 15-minute window logic, asyncio.gather, the
  debouncing pattern) one step at a time. I typed every line of code
  myself, after the explanation, and committed incrementally.

## How I used it

- **Concept understanding.** Before writing any code in a new area
  (FastAPI routing, React useEffect, the CORS middleware, etc.), I
  asked for an explanation.

- **Step-by-step pacing.** Rather than asking for the whole project
  upfront, I asked for one logical step at a time (e.g. "add the
  Pydantic models," "add asyncio.gather"), typed it, ran it, then
  moved on. Forces real understanding over paste-and-pray.

- **Trade-off articulation.** For non-obvious design decisions (filter
  on scheduled vs. actual time, 400 vs 422, in-process cache vs Redis,
  whether to add AbortController), I worked through the trade-offs
  explicitly so I can defend each one in the walkthrough.

- **Debugging.** Two issues came up that the model helped diagnose:
   one "the Node 18 → 20 upgrade when create-vite failed", second "missing User-Agent on iRail requests". 

## What I accepted as-is

- The overall **project structure** (`backend/main.py`, `Departure.py`, `DeparturesResponse.py`, `ErrorBody.py`,
  `requirements.txt`; `frontend/src/App.jsx` + Vite scaffold).

- The **Pydantic response model field names** (`train_number`,
  `delay_minutes`, `scheduled_time_local`, etc.) — they matched what
  I wanted to expose to the frontend and I had no reason to change
  them.



## What I wrote / rewrote myself

- **Every line of code in the repo was typed by me**, not copy-pasted
  from a Claude message. I read the suggested code, understood each
  block, then wrote it from scratch in my editor.


