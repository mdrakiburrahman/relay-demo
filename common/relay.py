import base64
import hashlib
import hmac
import json
import math
import time
import urllib.parse
from pathlib import Path

CONFIG_PATH = Path(__file__).resolve().parent.parent / "config.json"


def hmac_sha256(key: bytes, msg: bytes) -> bytes:
    return hmac.new(key=key, msg=msg, digestmod=hashlib.sha256).digest()


def create_sas_token(service_namespace: str, entity_path: str, sas_key_name: str, sas_key: str,
                     ttl_seconds: int = 60 * 60 * 48) -> str:
    uri = f"http://{service_namespace}/{entity_path}"
    encoded_uri = urllib.parse.quote(uri, safe="")
    expiry = math.floor(time.time()) + ttl_seconds
    signature = f"{encoded_uri}\n{expiry}".encode("utf-8")
    digest = hmac_sha256(sas_key.encode("utf-8"), signature)
    sig = urllib.parse.quote(base64.b64encode(digest))
    return f"SharedAccessSignature sr={encoded_uri}&sig={sig}&se={expiry}&skn={sas_key_name}"


def create_listen_url(service_namespace: str, entity_path: str, token: str | None = None) -> str:
    url = f"wss://{service_namespace}/$hc/{entity_path}?sb-hc-action=listen&sb-hc-id=123456"
    if token:
        url += "&sb-hc-token=" + urllib.parse.quote(token)
    return url


def create_http_send_url(service_namespace: str, entity_path: str, token: str | None = None) -> str:
    url = f"https://{service_namespace}/{entity_path}?sb-hc-action=connect&sb-hc-id=123456"
    if token:
        url += "&sb-hc-token=" + urllib.parse.quote(token)
    return url


def load_config(path: Path = CONFIG_PATH) -> dict:
    if not path.exists():
        raise FileNotFoundError(
            f"config.json not found at {path}. See README for the az CLI setup block."
        )
    with open(path, "r", encoding="utf-8-sig") as f:
        cfg = json.load(f)
    for k in ("namespace", "path", "keyrule", "key"):
        if k not in cfg or not cfg[k]:
            raise ValueError(f"config.json missing required field: {k}")
    return cfg


def fqdn(cfg: dict) -> str:
    return f"{cfg['namespace']}.servicebus.windows.net"
