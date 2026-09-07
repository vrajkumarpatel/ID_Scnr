import time
from concurrent.futures import ThreadPoolExecutor
from fastapi.testclient import TestClient
from IDscnr.backend.main import app

client = TestClient(app)


def _ingest_once():
    files = { 'front': ('front.jpg', b'fakejpegbytes', 'image/jpeg') }
    r = client.post('/scan/ingest', files=files)
    assert r.status_code == 200


def test_perf_ingest_concurrent_smoke():
    start = time.perf_counter()
    with ThreadPoolExecutor(max_workers=5) as ex:
        futs = [ex.submit(_ingest_once) for _ in range(10)]
        for f in futs:
            f.result()
    dur = time.perf_counter() - start
    assert dur < 10