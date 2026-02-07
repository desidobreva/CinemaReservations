from datetime import datetime, timedelta, UTC

def _login_admin(client):
    r = client.post("/auth/login", data={"username": "admin", "password": "admin1234"}, headers={"Content-Type": "application/x-www-form-urlencoded"})
    assert r.status_code == 200
    token = r.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_movie_crud(client):
    headers = _login_admin(client)

    # create
    r = client.post("/cinema/movies", json={"title": "M1", "description": "d", "category": "Action"}, headers=headers)
    assert r.status_code == 200
    mid = r.json()["id"]

    # get
    g = client.get(f"/cinema/movies/{mid}")
    assert g.status_code == 200

    # update
    u = client.put(f"/cinema/movies/{mid}", json={"title": "M1-Edited"}, headers=headers)
    assert u.status_code == 200
    assert u.json()["title"] == "M1-Edited"

    # delete (трябва да мине ако няма прожекции)
    d = client.delete(f"/cinema/movies/{mid}", headers=headers)
    assert d.status_code == 200


def test_screening_crud(client):
    headers = _login_admin(client)

    # movie + hall
    m = client.post("/cinema/movies", json={"title": "M2", "description": "", "category": "Drama"}, headers=headers)
    h = client.post("/cinema/halls", json={"name": "Hall CRUD", "rows": 5, "cols": 5}, headers=headers)
    assert m.status_code == 200 and h.status_code == 200
    movie_id = m.json()["id"]
    hall_id = h.json()["id"]

    # create screening
    starts = (datetime.now(UTC) + timedelta(hours=3)).isoformat()
    s = client.post("/cinema/screenings", json={"movie_id": movie_id, "hall_id": hall_id, "starts_at": starts}, headers=headers)
    assert s.status_code == 200
    sid = s.json()["id"]

    # update time
    starts2 = (datetime.now(UTC) + timedelta(hours=4)).isoformat()
    u = client.put(f"/cinema/screenings/{sid}", json={"starts_at": starts2}, headers=headers)
    assert u.status_code == 200

    # delete
    d = client.delete(f"/cinema/screenings/{sid}", headers=headers)
    assert d.status_code == 200
