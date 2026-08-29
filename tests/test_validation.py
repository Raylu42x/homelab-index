"""ID validation and path-traversal safety.

Service ids become filenames (`{id}.yaml`), so anything that escapes the data
directory is a real problem, not a cosmetic one.
"""
import pytest
from conftest import svc


@pytest.mark.parametrize("bad_id", [
    "../escape", "../../etc/passwd", "a/b", "a\\b", "", " ", "has space",
    "semi;colon", "dot.dot", "quote'", "star*",
])
def test_rejects_unsafe_ids(client, bad_id):
    r = client.post("/api/services", json=svc(id=bad_id))
    assert r.status_code == 422, f"id {bad_id!r} should be rejected, got {r.status_code}"


@pytest.mark.parametrize("good_id", ["a", "jellyfin", "uptime-kuma", "with_underscore", "abc123"])
def test_accepts_safe_ids(client, good_id):
    assert client.post("/api/services", json=svc(id=good_id)).status_code == 201


def test_traversal_id_writes_nothing_outside_data_dir(client):
    client.post("/api/services", json=svc(id="../pwned"))
    assert not (client.data_dir.parent / "pwned.yaml").exists()


def test_traversal_on_get_is_not_served(client):
    r = client.get("/api/services/..%2F..%2Fetc%2Fpasswd")
    assert r.status_code in (404, 422), r.status_code


def test_missing_required_name_is_422(client):
    r = client.post("/api/services", json={"id": "x"})
    assert r.status_code == 422
