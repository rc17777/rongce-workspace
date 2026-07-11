#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Baidu cloud OCR/document parsing client.

This is the low-level adapter used by production OCR pipelines. It supports the
verified Baidu high-accuracy OCR endpoint now, and keeps a configurable adapter
slot for Baidu Intelligent Document Parsing / PaddleOCR-VL because that endpoint
is exposed through Baidu's logged-in console and may vary by service version.
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

ENDPOINTS = {
    "general_basic": "https://aip.baidubce.com/rest/2.0/ocr/v1/general_basic",
    "accurate_basic": "https://aip.baidubce.com/rest/2.0/ocr/v1/accurate_basic",
    "accurate": "https://aip.baidubce.com/rest/2.0/ocr/v1/accurate",
}


def load_env(path: Path = ENV_PATH) -> dict[str, str]:
    data: dict[str, str] = {}
    if path.exists():
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            data[key.strip()] = value.strip()
    for key in [
        "BAIDU_OCR_APP_ID",
        "BAIDU_OCR_API_KEY",
        "BAIDU_OCR_SECRET_KEY",
        "BAIDU_DOC_PARSE_ENDPOINT",
    ]:
        if os.environ.get(key):
            data[key] = os.environ[key]
    return data


def get_access_token(env: dict[str, str]) -> dict[str, Any]:
    api_key = env.get("BAIDU_OCR_API_KEY")
    secret_key = env.get("BAIDU_OCR_SECRET_KEY")
    if not api_key or not secret_key:
        raise RuntimeError("Missing BAIDU_OCR_API_KEY or BAIDU_OCR_SECRET_KEY")
    resp = requests.post(
        TOKEN_URL,
        params={
            "grant_type": "client_credentials",
            "client_id": api_key,
            "client_secret": secret_key,
        },
        timeout=20,
    )
    payload = resp.json()
    if resp.status_code != 200 or "access_token" not in payload:
        safe = {k: v for k, v in payload.items() if k not in {"access_token", "refresh_token"}}
        raise RuntimeError(f"Failed to get access token: HTTP {resp.status_code} {safe}")
    return payload


def image_to_base64(path: Path) -> str:
    return base64.b64encode(path.read_bytes()).decode("ascii")


def call_ocr_image(
    image_path: Path,
    token: str,
    endpoint_name: str = "accurate_basic",
    endpoint_url: str | None = None,
) -> dict[str, Any]:
    url = endpoint_url or ENDPOINTS.get(endpoint_name)
    if not url:
        raise RuntimeError(f"Unknown endpoint: {endpoint_name}")
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
        timeout=90,
    )
    payload = resp.json()
    if resp.status_code != 200 or "error_code" in payload:
        raise RuntimeError(f"Baidu OCR failed: HTTP {resp.status_code} {payload}")
    return payload


def call_doc_parse_image(image_path: Path, token: str, env: dict[str, str]) -> dict[str, Any]:
    """Call configurable Baidu document parsing endpoint.

    Set BAIDU_DOC_PARSE_ENDPOINT in config/ocr_cloud.env after copying the exact
    PaddleOCR-VL/document-parse endpoint from Baidu's online API debugger.
    Most Baidu OCR endpoints accept the same image base64 form field; if the
    selected service requires different fields, adjust this function only.
    """
    endpoint = env.get("BAIDU_DOC_PARSE_ENDPOINT", "").strip()
    if not endpoint:
        raise RuntimeError(
            "BAIDU_DOC_PARSE_ENDPOINT is not configured. "
            "Use accurate_basic now, or paste the PaddleOCR-VL endpoint from Baidu console into config/ocr_cloud.env."
        )
    return call_ocr_image(image_path, token, endpoint_name="custom_doc_parse", endpoint_url=endpoint)


def extract_text(payload: dict[str, Any]) -> str:
    if "words_result" in payload:
        return "\n".join(str(item.get("words", "")) for item in payload.get("words_result", []))
    # Fallback for structured document parsing outputs; keep JSON nearby for full fidelity.
    text_parts: list[str] = []
    for key in ["results", "result", "body", "data", "pages"]:
        value = payload.get(key)
        if isinstance(value, list):
            text_parts.extend(_walk_text(value))
        elif isinstance(value, dict):
            text_parts.extend(_walk_text(value))
    return "\n".join(x for x in text_parts if x)


def _walk_text(value: Any) -> list[str]:
    out: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            if key.lower() in {"text", "words", "content", "markdown"} and isinstance(item, str):
                out.append(item)
            else:
                out.extend(_walk_text(item))
    elif isinstance(value, list):
        for item in value:
            out.extend(_walk_text(item))
    return out


def summarize_payload(payload: dict[str, Any]) -> dict[str, Any]:
    probs = [x.get("probability", {}).get("average") for x in payload.get("words_result", [])]
    probs = [p for p in probs if isinstance(p, (int, float))]
    return {
        "words_result_num": payload.get("words_result_num", len(payload.get("words_result", []))),
        "chars": len(extract_text(payload)),
        "avg_probability": round(sum(probs) / len(probs), 6) if probs else None,
        "keys": sorted(payload.keys()),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["token", "ocr-image", "doc-parse-image"])
    parser.add_argument("--image", type=Path)
    parser.add_argument("--endpoint", default="accurate_basic", choices=["general_basic", "accurate_basic", "accurate"])
    parser.add_argument("--out-json", type=Path)
    parser.add_argument("--out-txt", type=Path)
    args = parser.parse_args()

    env = load_env()
    token_payload = get_access_token(env)
    token = token_payload["access_token"]

    if args.command == "token":
        print(json.dumps({"ok": True, "expires_in": token_payload.get("expires_in")}, ensure_ascii=False, indent=2))
        return 0

    if not args.image or not args.image.exists():
        raise RuntimeError("--image is required and must exist")

    if args.command == "ocr-image":
        payload = call_ocr_image(args.image, token, args.endpoint)
    else:
        payload = call_doc_parse_image(args.image, token, env)

    text = extract_text(payload)
    if args.out_json:
        args.out_json.parent.mkdir(parents=True, exist_ok=True)
        args.out_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    if args.out_txt:
        args.out_txt.parent.mkdir(parents=True, exist_ok=True)
        args.out_txt.write_text(text, encoding="utf-8")
    print(json.dumps({"ok": True, **summarize_payload(payload)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
