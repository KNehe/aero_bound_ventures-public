from unittest.mock import patch

from sqlmodel import Session

from backend.crud.users import create_user
from backend.utils.security import verify_password
from tests.conftest import API_V1_PREFIX


def test_me_returns_current_user_from_access_cookie(client, session: Session):
    create_user(session, "me@example.com", "oldpassword")
    login_response = client.post(
        f"{API_V1_PREFIX}/token",
        data={"username": "me@example.com", "password": "oldpassword"},
    )
    assert login_response.status_code == 200

    response = client.get(f"{API_V1_PREFIX}/me/")

    assert response.status_code == 200
    data = response.json()
    assert data["id"]
    assert data["email"] == "me@example.com"
    assert data["auth_provider"] == "email"
    assert data["groups"] == []


@patch("backend.routers.users.kafka_producer")
def test_change_password_updates_password_and_clears_cookie(
    mock_kafka,
    client,
    session: Session,
):
    user = create_user(session, "change@example.com", "oldpassword")
    login_response = client.post(
        f"{API_V1_PREFIX}/token",
        data={"username": "change@example.com", "password": "oldpassword"},
    )
    assert login_response.status_code == 200

    response = client.post(
        f"{API_V1_PREFIX}/change-password/",
        json={
            "old_password": "oldpassword",
            "new_password": "NewPassword123!",
            "confirm_password": "NewPassword123!",
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "success": True,
        "message": "Password has been changed successfully. Please log in again.",
    }
    session.refresh(user)
    assert verify_password("NewPassword123!", user.password)
    mock_kafka.send.assert_called_once()
    assert "access_token=" in response.headers["set-cookie"]
    assert "Max-Age=0" in response.headers["set-cookie"]
