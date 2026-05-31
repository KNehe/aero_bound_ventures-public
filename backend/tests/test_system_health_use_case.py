import pytest

from backend.application.health.check_system_health import CheckSystemHealth


class PassingProbe:
    def __init__(self, service_name: str):
        self.service_name = service_name

    def check(self) -> None:
        return None


class FailingProbe:
    def __init__(self, service_name: str, message: str):
        self.service_name = service_name
        self.message = message

    def check(self) -> None:
        raise RuntimeError(self.message)


def test_system_health_is_healthy_when_all_probes_pass():
    health = CheckSystemHealth(
        probes=(PassingProbe("database"), PassingProbe("redis")),
        clock=lambda: 123.0,
    ).execute()

    assert health.as_response() == {
        "status": "healthy",
        "timestamp": 123.0,
        "services": {
            "database": "healthy",
            "redis": "healthy",
        },
    }


def test_system_health_is_degraded_when_one_probe_fails():
    health = CheckSystemHealth(
        probes=(
            PassingProbe("database"),
            FailingProbe("redis", "connection failed"),
        ),
        clock=lambda: 123.0,
    ).execute()

    assert health.status == "degraded"
    assert health.services == {
        "database": "healthy",
        "redis": "unhealthy: connection failed",
    }


def test_system_health_is_down_when_every_probe_fails():
    health = CheckSystemHealth(
        probes=(
            FailingProbe("database", "database unavailable"),
            FailingProbe("redis", "connection failed"),
        ),
        clock=lambda: 123.0,
    ).execute()

    assert health.status == "down"
    assert health.services == {
        "database": "unhealthy: database unavailable",
        "redis": "unhealthy: connection failed",
    }


@pytest.mark.parametrize("probes", [(), []])
def test_system_health_with_no_probes_is_healthy(probes):
    health = CheckSystemHealth(probes=probes, clock=lambda: 123.0).execute()

    assert health.as_response() == {
        "status": "healthy",
        "timestamp": 123.0,
        "services": {},
    }
