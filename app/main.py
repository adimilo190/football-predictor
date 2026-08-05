# app/main.py
# Application entry point: create the FastAPI app and wire the routers together.
# The actual endpoints live in app/routers/ — this file stays a thin table of
# contents so it never turns back into a 500-line grab bag.

from fastapi import FastAPI

from app.routers import competitions, imports

# NOTE: tables are no longer created here. The database schema is managed
# exclusively by Alembic migrations — run: alembic upgrade head
app = FastAPI(title="Football Predictor API")

# Attach the routers: competition reads (leagues/standings/fixtures/bracket) and
# the write/import endpoints that pull data from API-Football.
app.include_router(competitions.router)
app.include_router(imports.router)


# Health check: a simple ping confirming the server and DB are reachable.
@app.get("/")
def read_root():
    return {"message": "Witaj w Football Predictor API! Serwer i baza działają."}
