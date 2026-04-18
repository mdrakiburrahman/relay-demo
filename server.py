import json
import logging
import time

import websocket

from common.relay import create_listen_url, create_sas_token, fqdn, load_config


def _serve_once(cfg: dict) -> None:
    ns = fqdn(cfg)
    token = create_sas_token(ns, cfg["path"], cfg["keyrule"], cfg["key"])
    wss_uri = create_listen_url(ns, cfg["path"], token)

    ws = websocket.create_connection(wss_uri)
    ws.settimeout(1.0)
    logging.info("Listening on Azure Relay: wss://%s/$hc/%s", ns, cfg["path"])
    try:
        while True:
            try:
                raw = ws.recv()
            except websocket.WebSocketTimeoutException:
                continue
            if raw is None or raw == "":
                logging.warning("Control channel closed by peer.")
                return
            cmd = json.loads(raw)
            req = cmd.get("request")
            if not req:
                logging.debug("Ignoring non-request frame: %s", cmd)
                continue
            logging.info("Received request:\n%s", json.dumps(req, indent=2))

            opws = ws
            if "method" not in req:
                opws = websocket.create_connection(req["address"])
                cmd = json.loads(opws.recv())
                req = cmd["request"]

            if req.get("body"):
                body = opws.recv()
                try:
                    body = json.loads(body)
                    logging.info("Payload (JSON):\n%s", json.dumps(body, indent=2))
                except json.JSONDecodeError:
                    logging.info("Payload (raw):\n%s", body)

            resp = {
                "requestId": req["id"],
                "body": json.dumps(True),
                "statusCode": 200,
                "responseHeaders": {"Content-Type": "application/json"},
            }
            opws.send(json.dumps({"response": resp}))
            opws.send('{"message": "Hello from the Azure Relay server listener!"}')
            if opws is not ws:
                opws.close()
    finally:
        try:
            ws.close()
        except Exception:
            pass


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s.%(msecs)03d - %(levelname)s - %(message)s",
        datefmt="%H:%M:%S",
    )
    cfg = load_config()
    backoff = 1
    while True:
        try:
            _serve_once(cfg)
            backoff = 1
        except KeyboardInterrupt:
            logging.info("Exiting listener.")
            return
        except Exception as e:
            logging.warning("Listener error (%s: %s). Reconnecting in %ds…",
                            type(e).__name__, e, backoff)
            time.sleep(backoff)
            backoff = min(backoff * 2, 30)


if __name__ == "__main__":
    main()
