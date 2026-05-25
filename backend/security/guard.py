"""Shared FastAPI Guard configuration and decorator."""

from __future__ import annotations

import os
import socket
import struct
from pathlib import Path

from dotenv import load_dotenv
from guard import SecurityConfig, SecurityDecorator

load_dotenv()

LOCAL_TRUSTED_PROXIES = ["127.0.0.1", "::1"]


def get_bool_env(name: str, default: bool) -> bool:
    return os.getenv(name, str(default)).strip().lower() == "true"


def get_csv_env(name: str) -> list[str]:
    value = os.getenv(name, "")
    return [item.strip() for item in value.split(",") if item.strip()]


def detect_default_gateway() -> str | None:
    route_file = Path("/proc/net/route")
    if not route_file.exists():
        return None

    try:
        with route_file.open(encoding="utf-8") as route_handle:
            for line in route_handle:
                fields = line.split()
                if len(fields) >= 3 and fields[1] == "00000000":
                    gateway = socket.inet_ntoa(
                        struct.pack("<L", int(fields[2], 16))
                    )
                    return gateway if gateway != "0.0.0.0" else None
    except (OSError, ValueError):
        return None

    return None


def resolve_trusted_proxies() -> list[str]:
    trusted_proxies = get_csv_env("TRUSTED_PROXIES")
    if trusted_proxies:
        return trusted_proxies

    detected_gateway = detect_default_gateway()
    if detected_gateway:
        return [detected_gateway]

    return LOCAL_TRUSTED_PROXIES.copy()


def build_security_config() -> SecurityConfig:
    api_key = os.getenv("FASTAPI_GUARD_AGENT_API_KEY", "").strip()
    project_id = os.getenv("FASTAPI_GUARD_AGENT_PROJECT_ID", "").strip()
    enable_agent = get_bool_env("FASTAPI_GUARD_ENABLE_AGENT", False)

    if enable_agent and not api_key:
        raise RuntimeError(
            "FASTAPI_GUARD_AGENT_API_KEY must be set when "
            "FASTAPI_GUARD_ENABLE_AGENT=true"
        )
    if enable_agent and not project_id:
        raise RuntimeError(
            "FASTAPI_GUARD_AGENT_PROJECT_ID must be set when "
            "FASTAPI_GUARD_ENABLE_AGENT=true"
        )

    config_kwargs = {
        "rate_limit": int(os.getenv("RATE_LIMIT", 100)),
        "rate_limit_window": int(os.getenv("RATE_LIMIT_WINDOW", 60)),
        "enable_redis": get_bool_env("ENABLE_REDIS", True),
        "redis_url": os.getenv("REDIS_URL", "redis://localhost:6379"),
        "trusted_proxies": resolve_trusted_proxies(),
        "blocked_user_agents": get_csv_env("BLOCKED_USER_AGENTS") or ["curl", "wget"],
        "auto_ban_threshold": int(os.getenv("AUTO_BAN_THRESHOLD", 10)),
        "auto_ban_duration": int(os.getenv("AUTO_BAN_DURATION", 3600)),
        "enable_penetration_detection": get_bool_env(
            "ENABLE_PENETRATION_DETECTION", True
        ),
        "custom_log_file": None,
        "enable_rate_limiting": get_bool_env("ENABLE_RATE_LIMITING", True),
        "enable_agent": enable_agent,
        "agent_api_key": api_key or None,
        "agent_project_id": project_id or None,
        "agent_endpoint": os.getenv(
            "FASTAPI_GUARD_AGENT_ENDPOINT", "https://api.guard-core.com/api/v1"
        ).rstrip("/"),
        "agent_buffer_size": int(os.getenv("FASTAPI_GUARD_AGENT_BUFFER_SIZE", 5000)),
        "agent_flush_interval": int(
            os.getenv("FASTAPI_GUARD_AGENT_FLUSH_INTERVAL", 2)
        ),
        "agent_enable_events": get_bool_env(
            "FASTAPI_GUARD_AGENT_ENABLE_EVENTS", True
        ),
        "agent_enable_metrics": get_bool_env(
            "FASTAPI_GUARD_AGENT_ENABLE_METRICS", True
        ),
        "enable_cors": False,
    }

    model_fields = getattr(SecurityConfig, "model_fields", {})

    if "agent_project_encryption_key" in model_fields:
        config_kwargs["agent_project_encryption_key"] = (
            os.getenv("FASTAPI_GUARD_AGENT_PROJECT_ENCRYPTION_KEY", "").strip()
            or None
        )
    if "fail_secure" in model_fields:
        config_kwargs["fail_secure"] = get_bool_env(
            "FASTAPI_GUARD_FAIL_SECURE", True
        )

    return SecurityConfig(**config_kwargs)


security_config = build_security_config()
guard = SecurityDecorator(security_config)
