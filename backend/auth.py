import base64
import hmac
import json
import time
from typing import Optional, Dict
from fastapi import HTTPException, Request


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _b64url_decode(s: str) -> bytes:
    pad = '=' * (-len(s) % 4)
    return base64.urlsafe_b64decode(s + pad)


def create_jwt(payload: Dict, secret: str) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    h_b64 = _b64url(json.dumps(header, separators=(',', ':')).encode())
    p_b64 = _b64url(json.dumps(payload, separators=(',', ':')).encode())
    signing = f"{h_b64}.{p_b64}".encode()
    sig = hmac.new(secret.encode(), signing, digestmod="sha256").digest()
    return f"{h_b64}.{p_b64}.{_b64url(sig)}"


def verify_jwt(token: str, secret: str) -> Dict:
    try:
        h_b64, p_b64, s_b64 = token.split('.')
        signing = f"{h_b64}.{p_b64}".encode()
        expected = hmac.new(secret.encode(), signing, digestmod="sha256").digest()
        if not hmac.compare_digest(expected, _b64url_decode(s_b64)):
            raise HTTPException(status_code=401, detail="Invalid token signature")
        payload = json.loads(_b64url_decode(p_b64).decode())
        if 'exp' in payload and time.time() > float(payload['exp']):
            raise HTTPException(status_code=401, detail="Token expired")
        return payload
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token format")


def get_bearer_token(request: Request) -> Optional[str]:
    auth = request.headers.get('Authorization')
    if not auth or not auth.lower().startswith('bearer '):
        return None
    return auth.split(' ', 1)[1].strip()