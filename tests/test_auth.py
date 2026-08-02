from server.app import app


def test_dashboard_redirects_to_login():
    app.config.update(TESTING=True, SESSION_COOKIE_SECURE=False)
    client = app.test_client()

    response = client.get("/")

    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_api_requires_authentication():
    app.config.update(TESTING=True, SESSION_COOKIE_SECURE=False)
    client = app.test_client()

    response = client.get("/api/data")

    assert response.status_code == 401
    assert response.get_json()["error"] == "Autenticação necessária."


def test_login_and_logout_flow():
    app.config.update(TESTING=True, SESSION_COOKIE_SECURE=False)
    client = app.test_client()

    invalid = client.post("/login", data={"username": "admin", "password": "errada"})
    assert invalid.status_code == 401

    valid = client.post(
        "/login",
        data={"username": "admin", "password": "000000", "next": "/"},
        follow_redirects=False,
    )
    assert valid.status_code == 302
    assert valid.headers["Location"].endswith("/")

    dashboard = client.get("/")
    assert dashboard.status_code == 200
    assert b"Colheiteira" in dashboard.data

    logout = client.get("/logout")
    assert logout.status_code == 302

    protected_again = client.get("/api/settings")
    assert protected_again.status_code == 401


def test_health_remains_public():
    app.config.update(TESTING=True, SESSION_COOKIE_SECURE=False)
    client = app.test_client()

    response = client.get("/health")

    assert response.status_code in {200, 503}

def test_login_rejects_external_next_url():
    app.config.update(TESTING=True, SESSION_COOKIE_SECURE=False)
    client = app.test_client()

    response = client.post(
        "/login",
        data={
            "username": "admin",
            "password": "000000",
            "next": "https://example.org/phishing",
        },
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/")

