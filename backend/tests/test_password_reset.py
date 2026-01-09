"""
Unit tests for the password reset flow.

Tests cover:
1. CRUD operations for password reset tokens
2. API endpoints for forgot password, verify token, and reset password
3. Token expiration and invalidation
4. Security considerations (email enumeration protection)
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import patch
from sqlmodel import Session

from backend.crud.users import (
    create_user,
    create_password_reset_token,
    verify_password_reset_token,
    update_password_with_token,
)
from backend.utils.security import verify_password


# ============================================================================
# CRUD Tests for Password Reset
# ============================================================================


class TestPasswordResetCrud:
    """Tests for password reset CRUD operations."""

    def test_create_password_reset_token_for_existing_user(self, session: Session):
        """Should create a reset token for an existing user."""
        # Create a user
        user = create_user(session, "reset_test@example.com", "oldpassword123")

        # Create reset token
        token = create_password_reset_token(session, "reset_test@example.com")

        assert token is not None
        assert len(token) > 20  # Token should be reasonably long

        # Verify user has token stored (hashed)
        session.refresh(user)
        assert user.reset_token is not None
        assert user.reset_token != token  # Should be hashed, not plain
        assert user.reset_token_expires is not None
        assert user.reset_token_expires > datetime.now(timezone.utc)

    def test_create_password_reset_token_for_nonexistent_user(self, session: Session):
        """Should return None for non-existent user."""
        token = create_password_reset_token(session, "nonexistent@example.com")

        assert token is None

    def test_verify_valid_password_reset_token(self, session: Session):
        """Should verify a valid, non-expired token."""
        # Create user and token
        user = create_user(session, "verify_test@example.com", "password123")
        token = create_password_reset_token(session, "verify_test@example.com")

        # Verify token
        verified_user = verify_password_reset_token(session, token)

        assert verified_user is not None
        assert verified_user.id == user.id
        assert verified_user.email == "verify_test@example.com"

    def test_verify_invalid_password_reset_token(self, session: Session):
        """Should return None for an invalid token."""
        # Create user with token
        create_user(session, "invalid_test@example.com", "password123")
        create_password_reset_token(session, "invalid_test@example.com")

        # Try to verify with wrong token
        verified_user = verify_password_reset_token(session, "invalid_token_12345")

        assert verified_user is None

    def test_verify_expired_password_reset_token(self, session: Session):
        """Should return None for an expired token."""
        # Create user and token
        user = create_user(session, "expired_test@example.com", "password123")
        token = create_password_reset_token(session, "expired_test@example.com")

        # Manually expire the token
        user.reset_token_expires = datetime.now(timezone.utc) - timedelta(hours=1)
        session.add(user)
        session.commit()

        # Verify token should fail
        verified_user = verify_password_reset_token(session, token)

        assert verified_user is None

    def test_update_password_with_valid_token(self, session: Session):
        """Should update password with a valid token."""
        # Create user and token
        user = create_user(session, "update_pass@example.com", "oldpassword")
        token = create_password_reset_token(session, "update_pass@example.com")

        # Update password
        success = update_password_with_token(session, token, "newpassword123")

        assert success is True

        # Verify password changed
        session.refresh(user)
        assert verify_password("newpassword123", user.password)

        # Verify token is invalidated
        assert user.reset_token is None
        assert user.reset_token_expires is None

    def test_update_password_with_invalid_token(self, session: Session):
        """Should fail to update password with invalid token."""
        # Create user
        create_user(session, "invalid_update@example.com", "oldpassword")

        # Try to update with invalid token
        success = update_password_with_token(session, "invalid_token", "newpassword")

        assert success is False

    def test_token_can_only_be_used_once(self, session: Session):
        """Token should be invalidated after use."""
        # Create user and token
        create_user(session, "once_test@example.com", "oldpassword")
        token = create_password_reset_token(session, "once_test@example.com")

        # First use should succeed
        success1 = update_password_with_token(session, token, "newpassword1")
        assert success1 is True

        # Second use should fail
        success2 = update_password_with_token(session, token, "newpassword2")
        assert success2 is False


# ============================================================================
# API Endpoint Tests for Password Reset
# ============================================================================


class TestForgotPasswordEndpoint:
    """Tests for POST /forgot-password/ endpoint."""

    @patch("backend.routers.users.kafka_producer")
    def test_forgot_password_existing_user(self, mock_kafka, client, session: Session):
        """Should return success and send Kafka event for existing user."""
        # Create user directly in database (avoids Kafka call from registration)
        create_user(session, "forgot_api@example.com", "password123")

        response = client.post(
            "/forgot-password/", json={"email": "forgot_api@example.com"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "email" in data["message"].lower() or "reset" in data["message"].lower()

        # Verify Kafka event was sent for password reset
        mock_kafka.send.assert_called_once()
        call_args = mock_kafka.send.call_args
        assert call_args[0][0] == "user.events"
        assert call_args[0][1]["event_type"] == "password_reset_requested"
        assert call_args[0][1]["email"] == "forgot_api@example.com"

    @patch("backend.routers.users.kafka_producer")
    def test_forgot_password_nonexistent_user_no_enumeration(self, mock_kafka, client):
        """Should return same success response for non-existent user (prevent enumeration)."""
        response = client.post(
            "/forgot-password/", json={"email": "nonexistent@example.com"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True  # Same response as existing user

        # Kafka should NOT be called for non-existent user
        mock_kafka.send.assert_not_called()

    def test_forgot_password_invalid_email_format(self, client):
        """Should reject invalid email format."""
        response = client.post("/forgot-password/", json={"email": "not-an-email"})

        assert response.status_code == 422  # Validation error


class TestVerifyResetTokenEndpoint:
    """Tests for GET /verify-reset-token/{token} endpoint."""

    def test_verify_valid_token(self, client, session: Session):
        """Should return valid=True for a valid token."""
        # Create user and get token
        create_user(session, "verify_api@example.com", "password123")
        token = create_password_reset_token(session, "verify_api@example.com")

        response = client.get(f"/verify-reset-token/{token}")

        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True
        assert "valid" in data["message"].lower()

    def test_verify_invalid_token(self, client):
        """Should return valid=False for an invalid token."""
        response = client.get("/verify-reset-token/invalid_token_12345")

        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False
        assert (
            "invalid" in data["message"].lower() or "expired" in data["message"].lower()
        )

    def test_verify_expired_token(self, client, session: Session):
        """Should return valid=False for an expired token."""
        # Create user and token
        user = create_user(session, "expired_api@example.com", "password123")
        token = create_password_reset_token(session, "expired_api@example.com")

        # Expire the token
        user.reset_token_expires = datetime.now(timezone.utc) - timedelta(hours=1)
        session.add(user)
        session.commit()

        response = client.get(f"/verify-reset-token/{token}")

        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False


class TestResetPasswordEndpoint:
    """Tests for POST /reset-password/ endpoint."""

    def test_reset_password_with_valid_token(self, client, session: Session):
        """Should reset password with valid token."""
        # Create user and token
        user = create_user(session, "reset_api@example.com", "oldpassword")
        token = create_password_reset_token(session, "reset_api@example.com")

        response = client.post(
            "/reset-password/",
            json={
                "token": token,
                "new_password": "NewPassword123!",
                "confirm_password": "NewPassword123!",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        # Verify password was changed
        session.refresh(user)
        assert verify_password("NewPassword123!", user.password)

    def test_reset_password_with_invalid_token(self, client):
        """Should return 400 for invalid token."""
        response = client.post(
            "/reset-password/",
            json={
                "token": "invalid_token",
                "new_password": "NewPassword123!",
                "confirm_password": "NewPassword123!",
            },
        )

        assert response.status_code == 400
        assert (
            "invalid" in response.json()["detail"].lower()
            or "expired" in response.json()["detail"].lower()
        )

    def test_reset_password_mismatched_passwords(self, client, session: Session):
        """Should reject mismatched passwords."""
        # Create user and token
        create_user(session, "mismatch@example.com", "oldpassword")
        token = create_password_reset_token(session, "mismatch@example.com")

        response = client.post(
            "/reset-password/",
            json={
                "token": token,
                "new_password": "NewPassword123!",
                "confirm_password": "DifferentPass456@",
            },
        )

        assert response.status_code == 422  # Validation error

    def test_reset_password_too_short(self, client, session: Session):
        """Should reject password shorter than minimum length."""
        # Create user and token
        create_user(session, "short@example.com", "oldpassword")
        token = create_password_reset_token(session, "short@example.com")

        response = client.post(
            "/reset-password/",
            json={"token": token, "new_password": "short", "confirm_password": "short"},
        )

        assert response.status_code == 422  # Validation error

    def test_reset_password_missing_uppercase(self, client, session: Session):
        """Should reject password without uppercase letter."""
        create_user(session, "nouppercase@example.com", "oldpassword")
        token = create_password_reset_token(session, "nouppercase@example.com")

        response = client.post(
            "/reset-password/",
            json={
                "token": token,
                "new_password": "password123!",
                "confirm_password": "password123!",
            },
        )

        assert response.status_code == 422
        assert "uppercase" in response.json()["detail"][0]["msg"].lower()

    def test_reset_password_missing_lowercase(self, client, session: Session):
        """Should reject password without lowercase letter."""
        create_user(session, "nolowercase@example.com", "oldpassword")
        token = create_password_reset_token(session, "nolowercase@example.com")

        response = client.post(
            "/reset-password/",
            json={
                "token": token,
                "new_password": "PASSWORD123!",
                "confirm_password": "PASSWORD123!",
            },
        )

        assert response.status_code == 422
        assert "lowercase" in response.json()["detail"][0]["msg"].lower()

    def test_reset_password_missing_digit(self, client, session: Session):
        """Should reject password without digit."""
        create_user(session, "nodigit@example.com", "oldpassword")
        token = create_password_reset_token(session, "nodigit@example.com")

        response = client.post(
            "/reset-password/",
            json={
                "token": token,
                "new_password": "Password!!",
                "confirm_password": "Password!!",
            },
        )

        assert response.status_code == 422
        assert "digit" in response.json()["detail"][0]["msg"].lower()

    def test_reset_password_missing_special_char(self, client, session: Session):
        """Should reject password without special character."""
        create_user(session, "nospecial@example.com", "oldpassword")
        token = create_password_reset_token(session, "nospecial@example.com")

        response = client.post(
            "/reset-password/",
            json={
                "token": token,
                "new_password": "Password123",
                "confirm_password": "Password123",
            },
        )

        assert response.status_code == 422
        assert "special" in response.json()["detail"][0]["msg"].lower()

    def test_reset_password_token_invalidated_after_use(self, client, session: Session):
        """Token should be invalidated after successful password reset."""
        # Create user and token
        create_user(session, "invalidate@example.com", "oldpassword")
        token = create_password_reset_token(session, "invalidate@example.com")

        # First reset should succeed
        response1 = client.post(
            "/reset-password/",
            json={
                "token": token,
                "new_password": "NewPassword123!",
                "confirm_password": "NewPassword123!",
            },
        )
        assert response1.status_code == 200

        # Second attempt with same token should fail
        response2 = client.post(
            "/reset-password/",
            json={
                "token": token,
                "new_password": "AnotherPass456@",
                "confirm_password": "AnotherPass456@",
            },
        )
        assert response2.status_code == 400


# ============================================================================
# Integration Tests
# ============================================================================


class TestPasswordResetFlow:
    """End-to-end integration tests for password reset flow."""

    @patch("backend.routers.users.kafka_producer")
    def test_complete_password_reset_flow(self, mock_kafka, client, session: Session):
        """Test the complete flow: register -> forgot -> verify -> reset -> login."""
        # 1. Register user
        register_response = client.post(
            "/register/",
            json={"email": "flow_test@example.com", "password": "initialpassword"},
        )
        assert register_response.status_code == 200

        # 2. Request password reset
        forgot_response = client.post(
            "/forgot-password/", json={"email": "flow_test@example.com"}
        )
        assert forgot_response.status_code == 200

        # Get the token from the Kafka call
        kafka_call_args = mock_kafka.send.call_args[0][1]
        reset_token = kafka_call_args["reset_token"]

        # 3. Verify token is valid
        verify_response = client.get(f"/verify-reset-token/{reset_token}")
        assert verify_response.status_code == 200
        assert verify_response.json()["valid"] is True

        # 4. Reset password
        reset_response = client.post(
            "/reset-password/",
            json={
                "token": reset_token,
                "new_password": "NewPassword456!",
                "confirm_password": "NewPassword456!",
            },
        )
        assert reset_response.status_code == 200

        # 5. Login with new password should work
        login_response = client.post(
            "/token",
            data={"username": "flow_test@example.com", "password": "NewPassword456!"},
        )
        assert login_response.status_code == 200

        # 6. Login with old password should fail
        old_login_response = client.post(
            "/token",
            data={"username": "flow_test@example.com", "password": "initialpassword"},
        )
        assert old_login_response.status_code == 401
