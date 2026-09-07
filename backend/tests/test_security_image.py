from fastapi.testclient import TestClient
from IDscnr.backend.main import app

client = TestClient(app)


def test_image_path_rejected_outside_allowed():
    r = client.get('/image', params={'path': r'C:\notallowed\bad.jpg.enc'})
    assert r.status_code == 403