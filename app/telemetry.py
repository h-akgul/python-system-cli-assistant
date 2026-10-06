"""System telemetry business logic (no FastAPI imports)."""
from __future__ import annotations

import importlib
import platform

from app.schemas import CPUMetrics, GPUMetrics, RAMMetrics, SystemMetricsResponse

try:
    import psutil
except ImportError:
    psutil = None

GB = 1024 ** 3


class TelemetryError(RuntimeError):
    """Raised when system metrics cannot be collected."""


def collect_cpu() -> CPUMetrics:
    processor = platform.processor() or "unknown"
    if psutil is None:
        return CPUMetrics(available=False, processor=processor)
    return CPUMetrics(
        available=True,
        usage_percent=psutil.cpu_percent(interval=None),
        core_count=psutil.cpu_count(logical=True),
        processor=processor,
    )


def collect_ram() -> RAMMetrics:
    if psutil is None:
        return RAMMetrics(available=False)
    vm = psutil.virtual_memory()
    return RAMMetrics(
        available=True,
        total_gb=round(vm.total / GB, 2),
        used_gb=round(vm.used / GB, 2),
        available_gb=round(vm.available / GB, 2),
        usage_percent=vm.percent,
    )


def collect_gpu() -> GPUMetrics:
    """GPU is optional; any failure is reported as 'not detected'."""
    try:
        gputil = importlib.import_module("GPUtil")
        gpus = gputil.getGPUs()
        if not gpus:
            return GPUMetrics(detected=False)
        gpu = gpus[0]
        return GPUMetrics(
            detected=True,
            name=gpu.name,
            memory_total_mb=gpu.memoryTotal,
            memory_used_mb=gpu.memoryUsed,
            load_percent=round(gpu.load * 100, 1),
        )
    except Exception:
        return GPUMetrics(detected=False)


def get_system_metrics() -> SystemMetricsResponse:
    try:
        return SystemMetricsResponse(
            platform=platform.platform(),
            python_version=platform.python_version(),
            cpu=collect_cpu(),
            ram=collect_ram(),
            gpu=collect_gpu(),
        )
    except Exception as exc:
        raise TelemetryError(f"Failed to collect system metrics: {exc}") from exc
