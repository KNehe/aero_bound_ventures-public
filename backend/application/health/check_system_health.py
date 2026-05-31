import time
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class SystemHealth:
    status: str
    timestamp: float
    services: dict[str, str]

    def as_response(self) -> dict[str, object]:
        return {
            "status": self.status,
            "timestamp": self.timestamp,
            "services": self.services,
        }


class HealthProbe(Protocol):
    service_name: str

    def check(self) -> None: ...


class CheckSystemHealth:
    def __init__(
        self,
        *, 
        probes: Iterable[HealthProbe],
        clock: Callable[[], float] = time.time,
    ):
        self.probes = tuple(probes)
        self.clock = clock

    def execute(self) -> SystemHealth:
        services: dict[str, str] = {}

        for probe in self.probes:
            try:
                probe.check()
            except Exception as exc:
                services[probe.service_name] = f"unhealthy: {str(exc)}"
            else:
                services[probe.service_name] = "healthy"

        return SystemHealth(
            status=self._overall_status(services),
            timestamp=self.clock(),
            services=services,
        )

    @staticmethod
    def _overall_status(services: dict[str, str]) -> str:
        unhealthy_statuses = [
            status for status in services.values() if status.startswith("unhealthy")
        ]

        if unhealthy_statuses and len(unhealthy_statuses) == len(services):
            return "down"

        if unhealthy_statuses:
            return "degraded"

        return "healthy"
