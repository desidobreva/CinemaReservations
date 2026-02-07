from datetime import datetime, timedelta, timezone


def _admin_headers(client):
    r = client.post(
        "/auth/login",
        data={"username": "admin", "password": "admin1234"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert r.status_code == 200
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def _register_user(client, email, username):
    r = client.post("/auth/register", json={"email": email, "username": username, "password": "pass1234"})
    assert r.status_code == 200
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def _create_screening(client, admin, suffix, start_offset_hours=2):
    m = client.post(
        "/cinema/movies",
        json={"title": f"Movie-{suffix}", "description": "", "category": "Action"},
        headers=admin,
    )
    movie_id = m.json()["id"]
    h = client.post(
        "/cinema/halls",
        json={"name": f"Hall-{suffix}", "rows": 5, "cols": 5},
        headers=admin,
    )
    hall_id = h.json()["id"]
    starts_at = (datetime.now(timezone.utc) + timedelta(hours=start_offset_hours)).isoformat()
    s = client.post(
        "/cinema/screenings",
        json={"movie_id": movie_id, "hall_id": hall_id, "starts_at": starts_at},
        headers=admin,
    )
    return s.json()["id"]


def test_provider_approve_and_decline(client):
    admin = _admin_headers(client)

    # register two users: one will reserve, the other will be promoted to provider
    user = _register_user(client, "p1@example.com", "user_p1")
    provider_candidate = _register_user(client, "prov@example.com", "prov1")

    # create screening and reservation
    screening_id = _create_screening(client, admin, "prov-1")
    r = client.post("/reservations", json={"screening_id": screening_id, "seats": [{"seat_row": 1, "seat_col": 1}], "notes": ""}, headers=user)
    assert r.status_code == 200
    reservation_id = r.json()["id"]

    # promote provider_candidate to PROVIDER via admin
    users = client.get("/admin/users", headers=admin).json()
    prov_info = next(u for u in users if u["username"] == "prov1")
    prov_id = prov_info["id"]
    patch = client.patch(f"/admin/users/{prov_id}/role", json={"role": "PROVIDER"}, headers=admin)
    assert patch.status_code == 200

    # provider approves reservation
    prov_headers = provider_candidate
    approve = client.post(f"/provider/reservations/{reservation_id}/approve", headers=prov_headers)
    assert approve.status_code == 200, approve.text
    assert approve.json()["status"] == "CONFIRMED"

    # create another reservation to decline
    r2 = client.post("/reservations", json={"screening_id": screening_id, "seats": [{"seat_row": 1, "seat_col": 2}], "notes": ""}, headers=user)
    assert r2.status_code == 200
    res2_id = r2.json()["id"]

    decline = client.post(f"/provider/reservations/{res2_id}/decline", headers=prov_headers)
    assert decline.status_code == 200, decline.text
    assert decline.json()["status"] == "CANCELED"


def test_admin_confirm_reservation(client):
    admin = _admin_headers(client)
    user = _register_user(client, "p2@example.com", "user_p2")

    screening_id = _create_screening(client, admin, "admin-confirm")
    r = client.post("/reservations", json={"screening_id": screening_id, "seats": [{"seat_row": 2, "seat_col": 2}], "notes": ""}, headers=user)
    assert r.status_code == 200
    reservation_id = r.json()["id"]

    conf = client.post(f"/admin/reservations/{reservation_id}/confirm", headers=admin)
    assert conf.status_code == 200
    assert conf.json()["status"] == "CONFIRMED"
