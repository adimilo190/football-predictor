# app/main.py
# Application entry point: create the FastAPI app and wire the routers together.
# The actual endpoints live in app/routers/ — this file stays a thin table of
# contents so it never turns back into a 500-line grab bag.

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import competitions, imports
from app.routers import predictions, teams

# NOTE: tables are no longer created here. The database schema is managed
# exclusively by Alembic migrations — run: alembic upgrade head
app = FastAPI(title="Football Predictor API")
# CORS: a browser only lets a page read our responses if the page's origin is on
# this list. The origins come from settings (env variable), so the same code runs
# with localhost in development and with the deployed frontend domain in production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Attach the routers: competition reads (leagues/standings/fixtures/bracket) and
# the write/import endpoints that pull data from API-Football.
app.include_router(competitions.router)
app.include_router(imports.router)
app.include_router(teams.router)
app.include_router(predictions.router)


# Health check: a simple ping confirming the server and DB are reachable.
@app.get("/")
def read_root():
    return {"message": "Football Predictor API is running"}
