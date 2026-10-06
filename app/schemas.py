from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str


class CPUMetrics(BaseModel):
    available: bool
    usage_percent: Optional[float] = None
    core_count: Optional[int] = None
    processor: str = "unknown"


class RAMMetrics(BaseModel):
    available: bool
    total_gb: Optional[float] = None
    used_gb: Optional[float] = None
    available_gb: Optional[float] = None
    usage_percent: Optional[float] = None


class GPUMetrics(BaseModel):
    detected: bool
    name: Optional[str] = None
    memory_total_mb: Optional[float] = None
    memory_used_mb: Optional[float] = None
    load_percent: Optional[float] = None


class SystemMetricsResponse(BaseModel):
    platform: str
    python_version: str
    cpu: CPUMetrics
    ram: RAMMetrics
    gpu: GPUMetrics
