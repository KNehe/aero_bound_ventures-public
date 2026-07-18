import os
from pathlib import Path

from fastapi.testclient import TestClient

from backend.infrastructure.health.redis_health_probe import RedisHealthProbe
from backend.infrastructure.health.sqlmodel_database_health_probe import (
    SqlModelDatabaseHealthProbe,
)
from backend.main import security_config
from backend.utils.kafka import kafka_producer


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _csv_env(name: str, default: str = "") -> list[str]:
    return [
        item.strip() for item in os.getenv(name, default).split(",") if item.strip()
    ]


def test_liveness_check_does_not_probe_dependencies(client: TestClient, mocker):
    database_check = mocker.patch.object(SqlModelDatabaseHealthProbe, "check")
    redis_check = mocker.patch.object(RedisHealthProbe, "check")

    response = client.get("/live")

    assert response.status_code == 200
    assert response.json() == {"status": "alive"}
    database_check.assert_not_called()
    redis_check.assert_not_called()


def test_readiness_check_success_does_not_check_kafka(client: TestClient, mocker):
    mocker.patch("redis.from_url")
    mock_producer = mocker.MagicMock()
    mocker.patch.object(kafka_producer, "producer", mock_producer)

    response = client.get("/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ready"}
    mock_producer.list_topics.assert_not_called()


def test_readiness_check_fails_when_database_is_unavailable(client: TestClient, mocker):
    mocker.patch.object(
        SqlModelDatabaseHealthProbe,
        "check",
        side_effect=RuntimeError("database unavailable"),
    )
    mocker.patch("redis.from_url")

    response = client.get("/ready")

    assert response.status_code == 503
    assert response.json() == {"status": "not_ready"}


def test_readiness_check_fails_when_redis_is_unavailable(client: TestClient, mocker):
    mocker.patch(
        "redis.from_url",
        side_effect=RuntimeError("redis unavailable"),
    )

    response = client.get("/ready")

    assert response.status_code == 503
    assert response.json() == {"status": "not_ready"}


def test_security_logs_do_not_create_separate_file(client: TestClient):
    security_log = Path("security.log")
    security_log.unlink(missing_ok=True)

    assert security_config.custom_log_file is None
    response = client.get("/live")

    assert response.status_code == 200
    assert not security_log.exists()


def test_security_config_keeps_guard_settings_and_minimal_agent_config():
    assert security_config.rate_limit == int(os.getenv("RATE_LIMIT", 100))
    assert security_config.rate_limit_window == int(os.getenv("RATE_LIMIT_WINDOW", 60))
    assert security_config.enable_redis is (
        os.getenv("ENABLE_REDIS", "true").strip().lower() == "true"
    )
    assert security_config.redis_url == os.getenv("REDIS_URL", "redis://localhost:6379")
    assert security_config.redis_prefix == os.getenv(
        "GUARD_REDIS_PREFIX", "aero_bound:guard_core:"
    )
    assert security_config.blocked_user_agents == _csv_env(
        "BLOCKED_USER_AGENTS", "curl,wget"
    )
    assert security_config.auto_ban_threshold == int(os.getenv("AUTO_BAN_THRESHOLD", 5))
    assert security_config.auto_ban_duration == int(
        os.getenv("AUTO_BAN_DURATION", 86400)
    )
    assert security_config.enable_penetration_detection is (
        os.getenv("ENABLE_PENETRATION_DETECTION", "true").strip().lower() == "true"
    )
    assert security_config.enable_rate_limiting is True
    assert security_config.fail_secure is _env_bool("GUARD_FAIL_SECURE", True)
    assert security_config.enable_cors is bool(_csv_env("CORS_ORIGINS"))
    assert security_config.cors_allow_origins == _csv_env("CORS_ORIGINS")
    assert security_config.cors_allow_methods == _csv_env(
        "CORS_METHODS", "GET,POST,PUT,PATCH,DELETE,OPTIONS"
    )
    assert security_config.cors_allow_headers == _csv_env("CORS_HEADERS", "*")
    assert security_config.custom_log_file is None
    assert security_config.passive_mode is (
        os.getenv("PASSIVE_MODE", "true").strip().lower() == "true"
    )
    assert security_config.exclude_paths == [
        "/docs",
        "/redoc",
        "/openapi.json",
        "/openapi.yaml",
        "/favicon.ico",
        "/static",
        "/live",
        "/ready",
        "/metrics",
    ]

    assert security_config.enable_agent is True
    assert security_config.agent_api_key == os.environ["GUARD_API_KEY"]
    assert security_config.agent_endpoint == "https://api.guard-core.com"
    assert security_config.agent_project_id is None


def test_diagnostic_health_endpoints_are_removed(client: TestClient):
    assert client.get("/health").status_code == 404
    assert client.get("/api/v1/health").status_code == 404
