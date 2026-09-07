from fastapi.testclient import TestClient
from IDscnr.backend.main import app
from IDscnr.backend.auth import create_jwt

client = TestClient(app)


def test_health_ok():
    r = client.get('/health')
    assert r.status_code == 200
    assert r.json().get('status') == 'ok'


def test_scan_ingest_and_get_guest():
    # send minimal image bytes as front file
    files = {
        'front': ('front.jpg', b'fakejpegbytes', 'image/jpeg')
    }
    r = client.post('/scan/ingest', files=files)
    assert r.status_code == 200
    guest = r.json()
    gid = guest['id']
    # fetch guest by id
    r2 = client.get(f'/guest/{gid}')
    assert r2.status_code == 200
    assert r2.json()['id'] == gid


def test_dnr_add_and_match_and_pms_write_override():
    # create a guest first
    files = { 'front': ('front.jpg', b'fakejpegbytes', 'image/jpeg') }
    r = client.post('/scan/ingest', files=files)
    assert r.status_code == 200
    g = r.json()
    gid = g['id']
    # add DNR entry for same identity
    form = {
        'first_name': g.get('first_name'),
        'last_name': g.get('last_name'),
        'dob': g.get('dob'),
        'id_number': g.get('id_number'),
        'notes': 'test'
    }
    r2 = client.post('/dnr', data=form)
    assert r2.status_code == 200
    # attempt PMS write should signal conflict (409) or ok (depends on tier)
    r3 = client.post('/pms/write', params={'guest_id': gid})
    if r3.status_code == 409:
        # override should pass
        r4 = client.post('/pms/write', params={'guest_id': gid, 'override_dnr': True, 'override_reason': 'test'})
        assert r4.status_code == 200
        assert r4.json().get('status') == 'ok'
    else:
        # non-strong match; should be ok
        assert r3.status_code == 200


def test_settings_update_requires_admin_auth():
    # Without token should be forbidden
    r = client.post('/settings/update', data={'dark_mode': True})
    assert r.status_code == 403
    # With admin token should succeed
    secret = 'dev-secret-change-me'
    token = create_jwt({ 'sub': 'tester', 'role': 'admin', 'exp': int(__import__('time').time()) + 600 }, secret)
    r2 = client.post('/settings/update', data={'dark_mode': False}, headers={'Authorization': f'Bearer {token}'})
    assert r2.status_code == 200
    assert r2.json().get('settings', {}).get('dark_mode') is False