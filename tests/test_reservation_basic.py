"""Basic reservation behavior tests."""


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


def test_reservation_screening_not_found(client):
    user_headers = _register_user(client, "a1@example.com", "u_a1")
    r = client.post(
        "/reservations",
        json={"screening_id": 999999, "seats": [{"seat_row": 1, "seat_col": 1}], "notes": ""},
        headers=user_headers,
    )
    assert r.status_code == 404


def test_reservation_seat_out_of_bounds(client):
    admin = _admin_headers(client)
    # create movie, hall and screening
    m = client.post("/cinema/movies", json={"title": "M", "description": "", "category": "Action"}, headers=admin)
    movie_id = m.json()["id"]
    h = client.post("/cinema/halls", json={"name": "H", "rows": 2, "cols": 2}, headers=admin)
    hall_id = h.json()["id"]
    starts_at = (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat()
    s = client.post("/cinema/screenings", json={"movie_id": movie_id, "hall_id": hall_id, "starts_at": starts_at}, headers=admin)
    screening_id = s.json()["id"]

    user = _register_user(client, "b1@example.com", "u_b1")
    r = client.post(
        "/reservations",
        json={"screening_id": screening_id, "seats": [{"seat_row": 3, "seat_col": 1}], "notes": ""},
        headers=user,
    )
    assert r.status_code == 400
    assert "Seat out of hall bounds" in r.text


def test_reservation_double_booking(client):
    admin = _admin_headers(client)
    # create movie/hall/screening
    m = client.post("/cinema/movies", json={"title": "M2", "description": "", "category": "Drama"}, headers=admin)
    movie_id = m.json()["id"]
    h = client.post("/cinema/halls", json={"name": "H2", "rows": 5, "cols": 5}, headers=admin)
    hall_id = h.json()["id"]
    starts_at = (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat()
    s = client.post("/cinema/screenings", json={"movie_id": movie_id, "hall_id": hall_id, "starts_at": starts_at}, headers=admin)
    screening_id = s.json()["id"]

    user1 = _register_user(client, "c1@example.com", "u_c1")
    res1 = client.post(
        "/reservations",
        json={"screening_id": screening_id, "seats": [{"seat_row": 1, "seat_col": 1}], "notes": ""},
        headers=user1,
    )
    assert res1.status_code == 200

    user2 = _register_user(client, "c2@example.com", "u_c2")
    res2 = client.post(
        "/reservations",
        json={"screening_id": screening_id, "seats": [{"seat_row": 1, "seat_col": 1}], "notes": ""},
        headers=user2,
    )
    assert res2.status_code == 409
