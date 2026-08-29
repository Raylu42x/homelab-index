"""Category and page CRUD, plus the aggregates the UI derives from services."""
from conftest import svc


def test_category_crud(client):
    cat = {"id": "media", "name": "Media"}
    assert client.post("/api/categories", json=cat).status_code == 201
    assert client.get("/api/categories/media").json()["name"] == "Media"

    r = client.put("/api/categories/media", json={"id": "media", "name": "Media & TV"})
    assert r.status_code == 200
    assert client.get("/api/categories/media").json()["name"] == "Media & TV"

    assert client.delete("/api/categories/media").status_code == 204
    assert client.get("/api/categories/media").status_code == 404


def test_page_crud(client):
    page = {"id": "runbook", "title": "Runbook", "content": "# Steps"}
    r = client.post("/api/pages", json=page)
    assert r.status_code == 201, r.text
    assert client.get("/api/pages/runbook").status_code == 200
    assert client.delete("/api/pages/runbook").status_code == 204


def test_servers_are_derived_from_services_not_stored(client):
    """The README's core claim: servers aren't a separate file, they're derived."""
    client.post("/api/services", json=svc(id="a", name="A", server="nas-01"))
    client.post("/api/services", json=svc(id="b", name="B", server="nas-01"))
    client.post("/api/services", json=svc(id="c", name="C", server="pi-02"))

    from app import aggregates, storage
    grouped = aggregates.group_by_server(storage.list_services())
    assert sorted(grouped) == ["nas-01", "pi-02"]
    assert sorted(s.id for s in grouped["nas-01"]) == ["a", "b"]


def test_domains_are_derived_from_urls(client):
    client.post("/api/services", json=svc(id="a", name="A",
                                          public_url="https://media.example.com"))
    client.post("/api/services", json=svc(id="b", name="B",
                                          public_url="https://git.example.com"))
    from app import aggregates, storage
    domains = aggregates.group_by_domain(storage.list_services())
    assert "media.example.com" in domains
    assert "git.example.com" in domains


def test_stats_count_services_and_categories(client):
    client.post("/api/categories", json={"id": "media", "name": "Media"})
    client.post("/api/services", json=svc(id="a", name="A", category="media"))
    client.post("/api/services", json=svc(id="b", name="B", category="media"))
    from app import aggregates, storage
    stats = aggregates.compute_stats(storage.list_services(), storage.list_categories())
    assert stats["total_services"] == 2
    assert stats["categories"] == 1
    assert stats["public_services"] == 0
