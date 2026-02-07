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


def _create_screening(client, admin, rows=5, cols=5, start_offset_hours=2):
    # use unique names to avoid conflicts when creating multiple items in tests
    suffix = str(int(datetime.now(timezone.utc).timestamp() * 1000))
    m = client.post(
        "/cinema/movies",
        json={"title": f"MovieX-{suffix}", "description": "", "category": "Action"},
        headers=admin,
    )
    movie_id = m.json()["id"]
    h = client.post(
        "/cinema/halls",
        json={"name": f"HallX-{suffix}", "rows": rows, "cols": cols},
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


def test_confirm_after_screening_started(client):
    admin = _admin_headers(client)
    # screening in the past
    screening_id = _create_screening(client, admin, start_offset_hours=-1)

    user = _register_user(client, "r1@example.com", "u_r1")
    res = client.post("/reservations", json={"screening_id": screening_id, "seats": [{"seat_row": 1, "seat_col": 1}], "notes": ""}, headers=user)
    assert res.status_code == 200
    reservation_id = res.json()["id"]

    conf = client.post(f"/reservations/{reservation_id}/confirm", json={"method": "stripe_mock"}, headers=user)
    assert conf.status_code == 400
    assert "Screening already started" in conf.text


def test_cancel_reservation_by_owner(client):
    admin = _admin_headers(client)
    screening_id = _create_screening(client, admin, start_offset_hours=3)

    user = _register_user(client, "r2@example.com", "u_r2")
    res = client.post("/reservations", json={"screening_id": screening_id, "seats": [{"seat_row": 2, "seat_col": 2}], "notes": ""}, headers=user)
    assert res.status_code == 200
    reservation_id = res.json()["id"]

    cancel = client.post(f"/reservations/{reservation_id}/cancel", headers=user)
    assert cancel.status_code == 200
    assert cancel.json()["status"] == "CANCELED"
    assert cancel.json()["tickets"] == []


def test_reschedule_reservation(client):
    admin = _admin_headers(client)
    s1 = _create_screening(client, admin, start_offset_hours=2)
    s2 = _create_screening(client, admin, start_offset_hours=4)

    user = _register_user(client, "r3@example.com", "u_r3")
    res = client.post("/reservations", json={"screening_id": s1, "seats": [{"seat_row": 1, "seat_col": 1}], "notes": ""}, headers=user)
    assert res.status_code == 200
    old_id = res.json()["id"]

    payload = {"new_screening_id": s2, "seats": [{"seat_row": 1, "seat_col": 1}], "notes": "rescheduled"}
    new_res = client.post(f"/reservations/{old_id}/reschedule", json=payload, headers=user)
    assert new_res.status_code == 200
    assert new_res.json()["screening_id"] == s2

    # old reservation should be canceled
    old = client.get(f"/reservations/{old_id}", headers=user)
    assert old.status_code == 200
    assert old.json()["status"] == "CANCELED"


def test_confirm_forbidden_for_other_user(client):
    admin = _admin_headers(client)
    screening_id = _create_screening(client, admin, start_offset_hours=2)

    user1 = _register_user(client, "r4@example.com", "u_r4")
    res = client.post("/reservations", json={"screening_id": screening_id, "seats": [{"seat_row": 1, "seat_col": 2}], "notes": ""}, headers=user1)
    assert res.status_code == 200
    reservation_id = res.json()["id"]

    user2 = _register_user(client, "r5@example.com", "u_r5")
    conf = client.post(f"/reservations/{reservation_id}/confirm", json={"method": "stripe_mock"}, headers=user2)
    assert conf.status_code == 403
