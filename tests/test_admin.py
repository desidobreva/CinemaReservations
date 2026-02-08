"""Admin-related integration tests."""


def _login_admin(client):
    r = client.post("/auth/login", data={"username": "admin", "password": "admin1234"}, headers={"Content-Type": "application/x-www-form-urlencoded"})
    assert r.status_code == 200
    token = r.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_admin_can_list_users(client):
    headers = _login_admin(client)
    r = client.get("/admin/users", headers=headers)
    assert r.status_code == 200


def test_admin_role_change_user_provider(client):
    # create user
    reg = client.post("/auth/register", json={"email": "x@x.com", "username": "x1", "password": "pass1234"})
    assert reg.status_code == 200

    headers = _login_admin(client)
    users = client.get("/admin/users", headers=headers).json()
    target = next(u for u in users if u["username"] == "x1")

    # change role -> PROVIDER
    upd = client.patch(f"/admin/users/{target['id']}/role", json={"role": "PROVIDER"}, headers=headers)
    assert upd.status_code == 200
    assert upd.json()["role"] == "PROVIDER"