"""Service CRUD over the JSON API."""
from conftest import svc


def test_empty_list(client):
    r = client.get("/api/services")
    assert r.status_code == 200
    assert r.json() == []


def test_create_then_get(client):
    r = client.post("/api/services", json=svc())
    assert r.status_code == 201, r.text
    assert r.json()["name"] == "Jellyfin"

    r = client.get("/api/services/jellyfin")
    assert r.status_code == 200
    assert r.json()["description"] == "Media server"


def test_create_persists_yaml_on_disk(client):
    client.post("/api/services", json=svc())
    written = client.data_dir / "services" / "jellyfin.yaml"
    assert written.exists(), "service should be written as YAML on disk"
    assert "Jellyfin" in written.read_text()


def test_get_missing_returns_404(client):
    assert client.get("/api/services/nope").status_code == 404


def test_update(client):
    client.post("/api/services", json=svc())
    r = client.put("/api/services/jellyfin", json=svc(name="Jellyfin HD"))
    assert r.status_code == 200
    assert client.get("/api/services/jellyfin").json()["name"] == "Jellyfin HD"


def test_delete(client):
    client.post("/api/services", json=svc())
    assert client.delete("/api/services/jellyfin").status_code == 204
    assert client.get("/api/services/jellyfin").status_code == 404
    assert not (client.data_dir / "services" / "jellyfin.yaml").exists()


def test_filter_by_category(client):
    client.post("/api/services", json=svc(id="a", name="A", category="media"))
    client.post("/api/services", json=svc(id="b", name="B", category="dev"))
    ids = [s["id"] for s in client.get("/api/services?category=media").json()]
    assert ids == ["a"]


def test_filter_by_tag(client):
    client.post("/api/services", json=svc(id="a", name="A", tags=["video"]))
    client.post("/api/services", json=svc(id="b", name="B", tags=["git"]))
    ids = [s["id"] for s in client.get("/api/services?tag=git").json()]
    assert ids == ["b"]


def test_search_query(client):
    client.post("/api/services", json=svc(id="a", name="Jellyfin"))
    client.post("/api/services", json=svc(id="b", name="Gitea"))
    ids = [s["id"] for s in client.get("/api/services?q=jelly").json()]
    assert ids == ["a"]
