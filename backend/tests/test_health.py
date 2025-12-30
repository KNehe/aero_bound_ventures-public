from fastapi.testclient import TestClient
from backend.utils.kafka import kafka_producer


def test_health_check_success(client: TestClient, mocker):
    mocker.patch("redis.from_url")

    mock_producer = mocker.MagicMock()
    mock_metadata = mocker.MagicMock()

    mock_metadata.brokers = {1: "broker"}
    mock_producer.list_topics.return_value = mock_metadata

    # replace the produce instance with our mock
    mocker.patch.object(kafka_producer, "producer", mock_producer)

    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_health_check_degraded(client: TestClient, mocker):
    mock_redis = mocker.patch("redis.from_url")
    mock_redis.side_effect = Exception("Redis connection failed")

    mock_producer = mocker.MagicMock()
    mock_metadata = mocker.MagicMock()

    mock_metadata.brokers = {1: "broker"}
    mock_producer.list_topics.return_value = mock_metadata

    mocker.patch.object(kafka_producer, "producer", mock_producer)

    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "degraded"
