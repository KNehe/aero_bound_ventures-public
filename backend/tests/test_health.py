from pathlib import Path

from fastapi.testclient import TestClient

from backend.main import security_config
from backend.utils.kafka import kafka_producer
from tests.conftest import API_V1_PREFIX


def _mock_healthy_dependencies(mocker):
    mocker.patch("redis.from_url")

    mock_producer = mocker.MagicMock()
    mock_metadata = mocker.MagicMock()

    mock_metadata.brokers = {1: "broker"}
    mock_producer.list_topics.return_value = mock_metadata
    mocker.patch.object(kafka_producer, "producer", mock_producer)


def test_health_check_success(client: TestClient, mocker):
    _mock_healthy_dependencies(mocker)

    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_security_logs_do_not_create_separate_file(client: TestClient, mocker):
    security_log = Path("security.log")
    security_log.unlink(missing_ok=True)
    _mock_healthy_dependencies(mocker)

    assert security_config.custom_log_file is None
    response = client.get("/health")

    assert response.status_code == 200
    assert not security_log.exists()


def test_health_check_degraded(client: TestClient, mocker):
    mock_redis = mocker.patch("redis.from_url")
    mock_redis.side_effect = Exception("Redis connection failed")

    mock_producer = mocker.MagicMock()
    mock_metadata = mocker.MagicMock()

    mock_metadata.brokers = {1: "broker"}
    mock_producer.list_topics.return_value = mock_metadata

    mocker.patch.object(kafka_producer, "producer", mock_producer)

    response = client.get(f"{API_V1_PREFIX}/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "degraded"
