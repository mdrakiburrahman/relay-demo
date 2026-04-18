import json
import logging

import requests

from common.relay import create_http_send_url, create_sas_token, fqdn, load_config


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s.%(msecs)03d - %(levelname)s - %(message)s",
        datefmt="%H:%M:%S",
    )
    cfg = load_config()
    ns = fqdn(cfg)

    print("Type a message and press Enter to send (Ctrl+C to quit).")
    try:
        while True:
            try:
                message = input("Message to send: ").strip()
            except EOFError:
                break
            if not message:
                continue
            url = create_http_send_url(
                ns, cfg["path"],
                create_sas_token(ns, cfg["path"], cfg["keyrule"], cfg["key"]),
            )
            try:
                r = requests.post(
                    url,
                    headers={"Content-Type": "application/json"},
                    data=json.dumps({"message": message}),
                    timeout=10,
                )
                logging.info("HTTP status: %s", r.status_code)
                try:
                    logging.info("Response (JSON):\n%s", json.dumps(r.json(), indent=2))
                except ValueError:
                    logging.info("Response (raw):\n%s", r.text)
            except Exception as e:
                logging.error("Request failed: %s", e)
    except KeyboardInterrupt:
        print()
        logging.info("Exiting client.")


if __name__ == "__main__":
    main()
