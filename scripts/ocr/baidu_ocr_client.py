#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Minimal Baidu OCR client utilities.

Reads credentials from config/ocr_cloud.env by default. The module avoids
printing secrets and can be imported by OCR pipelines later.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import sys
from pathlib import Path
from typing import Any

import requests

sys.stdout.reconfigure(encoding="utf-8")

WORKSPACE = Path(r"C:\Users\scrccpa\.openclaw\workspace")
ENV_PATH = WORKSPACE / "config" / "ocr_cloud.env"
TOKEN_URL = "https://aip.baidubce.com/oauth/2.0/token"


def load_env(path: Path = ENV_PATH) -> dict[str, str]:
    data: dict[str, str] = {}
    if path.exists():
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            data[key.strip()] = value.strip()
    for key in ["BAIDU_OCR_APP_ID", "BAIDU_OCR_API_KEY", "BAIDU_OCR_SECRET_KEY"]:
        if os.environ.get(key):
            data[key] = os.environ[key]
    return data


def get_access_token(env: dict[str, str]) -> dict[str, Any]:
    api_key = env.get("BAIDU_OCR_API_KEY")
    secret_key = env.get("BAIDU_OCR_SECRET_KEY")
    if not api_key or not secret_key:
        raise RuntimeError("Missing BAIDU_OCR_API_KEY or BAIDU_OCR_SECRET_KEY")
    params = {
        "grant_type": "client_credentials",
        "client_id": api_key,
        "client_secret": secret_key,
    }
    resp = requests.post(TOKEN_URL, params=params, timeout=20)
    try:
        payload = resp.json()
    except Exception as exc:
        raise RuntimeError(f"Token response is not JSON: HTTP {resp.status_code}") from exc
    if resp.status_code != 200 or "access_token" not in payload:
        safe = {k: v for k, v in payload.items() if k not in {"access_token", "refresh_token"}}
        raise RuntimeError(f"Failed to get access token: HTTP {resp.status_code} {safe}")
    return payload


def image_to_base64(path: Path) -> str:
    return base64.b64encode(path.read_bytes()).decode("ascii")


def call_accurate_basic(image_path: Path, token: str) -> dict[str, Any]:
    """Call Baidu OCR high-accuracy general endpoint for a single image."""
    url = "https://aip.baidubce.com/rest/2.0/ocr/v1/accurate_basic"
    data = {
        "image": image_to_base64(image_path),
        "detect_direction": "true",
        "paragraph": "true",
        "probability": "true",
    }
    resp = requests.post(
        url,
        params={"access_token": token},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data=data,
        timeout=60,
    )
    payload = resp.json()
    if resp.status_code != 200 or "error_code" in payload:
        raise RuntimeError(f"Baidu OCR failed: HTTP {resp.status_code} {payload}")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["token", "accurate-basic"])
    parser.add_argument("--image", type=Path, help="Image path for accurate-basic")
    args = parser.parse_args()

    env = load_env()
    if args.command == "token":
        token = get_access_token(env)
        print(json.dumps({
            "ok": True,
            "app_id_present": bool(env.get("BAIDU_OCR_APP_ID")),
            "expires_in": token.get("expires_in"),
            "scope": token.get("scope", "")[:160],
        }, ensure_ascii=False, indent=2))
        return 0

    if args.command == "accurate-basic":
        if not args.image or not args.image.exists():
            raise RuntimeError("--image is required and must exist")
        token = get_access_token(env)["access_token"]
        payload = call_accurate_basic(args.image, token)
        print(json.dumps({
            "ok": True,
            "words_result_num": payload.get("words_result_num"),
            "sample": payload.get("words_result", [])[:8],
        }, ensure_ascii=False, indent=2))
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
