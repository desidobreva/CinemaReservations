from datetime import datetime, timedelta, UTC

def test_confirm_reservation(client):
    # register user
    r = client.post("/auth/register", json={"email": "u@u.com", "username": "u1", "password": "pass1234"})
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # трябва да имаме provider/admin за създаване на movie/hall/screening.
    # за теста можеш временно да seed-неш provider в init_db или да позволиш ADMIN create.
    # Тук приемаме, че admin съществува: username=admin pass=admin1234
    admin_login = client.post(
    "/auth/login",
    data={"username": "admin", "password": "admin1234"},
    headers={"Content-Type": "application/x-www-form-urlencoded"},)
    assert admin_login.status_code == 200, admin_login.text
    admin_token = admin_login.json()["access_token"]

    admin_token = admin_login.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # create movie
    m = client.post("/cinema/movies", json={"title": "Movie", "description": "", "category": "Action"}, headers=admin_headers)
    movie_id = m.json()["id"]

    # create hall
    h = client.post("/cinema/halls", json={"name": "Hall 1", "rows": 5, "cols": 5}, headers=admin_headers)
    hall_id = h.json()["id"]

    # create screening in future
    starts_at = (datetime.now(UTC) + timedelta(hours=2)).isoformat()
    s = client.post("/cinema/screenings", json={"movie_id": movie_id, "hall_id": hall_id, "starts_at": starts_at}, headers=admin_headers)
    screening_id = s.json()["id"]

    # create reservation
    res = client.post("/reservations", json={"screening_id": screening_id, "seats": [{"seat_row": 1, "seat_col": 1}], "notes": ""}, headers=headers)
    assert res.status_code == 200
    reservation_id = res.json()["id"]
    assert res.json()["status"] == "PENDING"

    # confirm (simulate payment)
    conf = client.post(f"/reservations/{reservation_id}/confirm", json={"method": "stripe_mock"}, headers=headers)
    assert conf.status_code == 200
    assert conf.json()["status"] == "CONFIRMED"
