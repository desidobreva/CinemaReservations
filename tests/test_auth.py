def test_register_and_login(client):
    r = client.post("/auth/register", json={"email": "a@b.com", "username": "user1", "password": "pass1234"})
    assert r.status_code == 200
    assert r.json()["token_type"] == "bearer"
    assert r.json()["access_token"]

    r2 = client.post(
        "/auth/login",
        data={"username": "user1", "password": "pass1234"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert r2.status_code == 200
    assert r2.json()["token_type"] == "bearer"
    assert r2.json()["access_token"]

    bad = client.post(
        "/auth/login",
        data={"username": "user1", "password": "wrong"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert bad.status_code == 401
