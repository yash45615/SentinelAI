from app.middleware.security import SecurityMiddleware


def test_security_middleware_exists():
    assert SecurityMiddleware is not None


def test_security_middleware_has_request_history():
    middleware = SecurityMiddleware(None)

    assert hasattr(middleware, "request_history")


def test_security_middleware_request_history_is_empty():
    middleware = SecurityMiddleware(None)

    assert len(middleware.request_history) == 0