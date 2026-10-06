import os


def get_int(name: str, default: int) -> int:
    value = os.getenv(name)

    if value is None:
        return default

    try:
        return int(value)
    except ValueError:
        return default


def get_float(name: str, default: float) -> float:
    value = os.getenv(name)

    if value is None:
        return default

    try:
        return float(value)
    except ValueError:
        return default


def get_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)

    if value is None:
        return default

    return value.lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


SERVICE_HOST = os.getenv(
    "SERVICE_HOST",
    "127.0.0.1",
)

REQUEST_TIMEOUT_SECONDS = get_float(
    "REQUEST_TIMEOUT_SECONDS",
    3.0,
)

DEFAULT_LATENCY_MS = get_int(
    "DEFAULT_LATENCY_MS",
    0,
)

DEFAULT_FAILURE_RATE = get_float(
    "DEFAULT_FAILURE_RATE",
    0.0,
)