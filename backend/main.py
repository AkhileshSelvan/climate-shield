from fastapi import FastAPI
from database import Base, engine
from routers import farms, weather, policies, triggers, simulate

app = FastAPI(title="ClimateShield API")

Base.metadata.create_all(bind=engine)

app.include_router(farms.router)
app.include_router(weather.router)
app.include_router(policies.router)
app.include_router(triggers.router)
app.include_router(simulate.router)


@app.get("/health")
def health():
    return {"status": "ok", "message": "ClimateShield backend is running"}
