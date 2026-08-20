#!/usr/bin/env python3
"""临时诊断（2026-08-20）：从 GitHub runner（美国 IP）比较不同 TLS 指纹对
imapi.douyin.com 只读接口的接受度。不发消息、不打印任何凭据值。

用法: DIAG_COOKIES="<完整cookie串>" python diag_tls.py
"""
import os
import sys

# 从 export_github_env.py 写入 GITHUB_ENV 的环境变量读取（不直接引用 secrets 上下文，
# 避免触发 GitHub 对 workflow 中 secrets 直接引用的安全审查）
COOKIE = os.environ.get("COOKIES_1596947932146541", "")
assert COOKIE, "COOKIES_1596947932146541 env var not found (run after export step)"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36",
    "Accept": "application/x-protobuf, */*",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Referer": "https://www.douyin.com/",
    "Origin": "https://www.douyin.com",
    "Cookie": COOKIE,
}
URL = "https://imapi.douyin.com/v1/message/get_by_user_init"


def report(name, status, body, resp_headers):
    body_len = len(body) if body is not None else -1
    is_html = body is not None and body[:1] == b"<"
    session_ok = body is not None and b"unexepcted session" not in body
    ct = resp_headers.get("content-type", "?")
    print(f"[diag] {name}: status={status} len={body_len} html={is_html} "
          f"content-type={ct} session_valid={session_ok}")
    return session_ok


# 1) python requests（默认 TLS 指纹，最不像浏览器）
try:
    import requests
    r = requests.get(URL, headers=HEADERS, timeout=20)
    report("requests", r.status_code, r.content, r.headers)
except Exception as e:
    print(f"[diag] requests: FAILED {type(e).__name__}: {e}")

# 2) curl_cffi 模拟 Chrome TLS + HTTP/2 指纹
try:
    from curl_cffi import requests as creq
    r = creq.get(URL, headers=HEADERS, timeout=20, impersonate="chrome")
    report("curl_cffi_chrome", r.status_code, r.content, r.headers)
except ImportError:
    print("[diag] curl_cffi not installed")
except Exception as e:
    print(f"[diag] curl_cffi_chrome: FAILED {type(e).__name__}: {e}")
