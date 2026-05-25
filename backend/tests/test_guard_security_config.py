from backend.routers.oauth import google_callback
from backend.routers.payments import initiate_pesapal_payment
from backend.security.guard import build_security_config, guard, resolve_trusted_proxies


def test_resolve_trusted_proxies_prefers_explicit_env(monkeypatch):
    monkeypatch.setenv("TRUSTED_PROXIES", "10.0.0.10, 10.0.0.11")

    assert resolve_trusted_proxies() == ["10.0.0.10", "10.0.0.11"]


def test_resolve_trusted_proxies_uses_detected_gateway(monkeypatch):
    monkeypatch.delenv("TRUSTED_PROXIES", raising=False)
    monkeypatch.setattr(
        "backend.security.guard.detect_default_gateway",
        lambda: "172.17.0.1",
    )

    assert resolve_trusted_proxies() == ["172.17.0.1"]


def test_resolve_trusted_proxies_falls_back_to_localhost(monkeypatch):
    monkeypatch.delenv("TRUSTED_PROXIES", raising=False)
    monkeypatch.setattr("backend.security.guard.detect_default_gateway", lambda: None)

    assert resolve_trusted_proxies() == ["127.0.0.1", "::1"]


def test_build_security_config_uses_safe_defaults(monkeypatch):
    monkeypatch.delenv("AUTO_BAN_THRESHOLD", raising=False)
    monkeypatch.delenv("AUTO_BAN_DURATION", raising=False)
    monkeypatch.setattr(
        "backend.security.guard.resolve_trusted_proxies",
        lambda: ["172.17.0.1"],
    )

    config = build_security_config()

    assert config.trusted_proxies == ["172.17.0.1"]
    assert config.auto_ban_threshold == 10
    assert config.auto_ban_duration == 3600


def test_guard_route_exclusions_registered():
    oauth_route_id = getattr(google_callback, "_guard_route_id")
    payment_route_id = getattr(initiate_pesapal_payment, "_guard_route_id")

    oauth_route_config = guard.get_route_config(oauth_route_id)
    payment_route_config = guard.get_route_config(payment_route_id)

    assert oauth_route_config is not None
    assert oauth_route_config.excluded_detection_params == {"scope"}

    assert payment_route_config is not None
    assert payment_route_config.excluded_detection_body_fields == {"callback_url"}
