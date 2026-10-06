from __future__ import annotations

from fastapi import FastAPI, HTTPException

from app.schemas import HealthResponse, SystemMetricsResponse
from app.telemetry import TelemetryError, get_system_metrics

app = FastAPI(title="Lumina Telemetry API", version="1.0.0")


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok")


@app.get("/system/metrics", response_model=SystemMetricsResponse)
def system_metrics() -> SystemMetricsResponse:
    try:
        return get_system_metrics()
    except TelemetryError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="127.0.0.1", port=8000)
