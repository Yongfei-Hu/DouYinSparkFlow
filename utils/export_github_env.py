import json
import os
import sys
from http.cookies import CookieError, SimpleCookie


def fail(message: str) -> None:
    print(message, file=sys.stderr)
    raise SystemExit(1)


def to_dotenv_value(value: str) -> str:
    # Keep .env single-line values by escaping real line breaks.
    return value.replace("\r", "").replace("\n", "\\n")


def append_github_env_block(env_file, key: str, value: str) -> None:
    env_file.write(f"{key}<<__ENV_EOF__\n")
    env_file.write(value)
    env_file.write("\n__ENV_EOF__\n")


def as_env_string(value) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False)


def as_config_value(key: str, value) -> str:
    env_value = as_env_string(value)
    if not key.upper().startswith("COOKIES_") or not env_value.strip():
        return env_value

    try:
        json.loads(env_value)
    except json.JSONDecodeError:
        # Legacy API deployments stored a Cookie request header in this Secret.
        cookies = SimpleCookie()
        try:
            cookies.load(env_value)
        except CookieError:
            fail(f"{key} must contain Cookie JSON or a Cookie request header")
        if not cookies:
            fail(f"{key} must contain Cookie JSON or a Cookie request header")
        env_value = json.dumps(
            [
                {
                    "name": name,
                    "value": cookie.value,
                    "domain": ".douyin.com",
                    "path": "/",
                }
                for name, cookie in cookies.items()
            ],
            ensure_ascii=False,
        )
    # Derived JSON differs from the original Secret and needs its own log mask.
    masked_value = env_value.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")
    print(f"::add-mask::{masked_value}", flush=True)
    return env_value


def format_key_list(keys) -> str:
    if not keys:
        return "(none)"
    return ", ".join(sorted(str(key) for key in keys))


def main() -> None:
    vars_raw = os.getenv("VARS_JSON", "{}")
    secrets_raw = os.getenv("SECRETS_JSON", "{}")
    github_env = os.getenv("GITHUB_ENV")

    if not github_env:
        fail("GITHUB_ENV is not set")

    try:
        vars_map = json.loads(vars_raw)
    except json.JSONDecodeError as exc:
        fail(f"VARS_JSON is not valid JSON: {exc}")

    try:
        secrets_map = json.loads(secrets_raw)
    except json.JSONDecodeError as exc:
        fail(f"SECRETS_JSON is not valid JSON: {exc}")

    if not isinstance(vars_map, dict):
        fail("VARS_JSON must be a JSON object")
    if not isinstance(secrets_map, dict):
        fail("SECRETS_JSON must be a JSON object")

    dotenv_map = {}
    vars_keys = list(vars_map.keys())
    secrets_keys = list(secrets_map.keys())

    with open(github_env, "a", encoding="utf-8") as env_file:
        for key, value in vars_map.items():
            env_value = as_config_value(str(key), value)
            append_github_env_block(env_file, str(key), env_value)
            dotenv_map[str(key)] = env_value

        for key, value in secrets_map.items():
            env_value = as_config_value(str(key), value)
            append_github_env_block(env_file, str(key), env_value)
            dotenv_map[str(key)] = env_value

    dotenv_lines = [f"{key}={to_dotenv_value(value)}" for key, value in dotenv_map.items()]
    with open(".env", "w", encoding="utf-8") as dotenv_file:
        dotenv_file.write("\n".join(dotenv_lines) + "\n")

    print(
        "Exported all variables from VARS_JSON and SECRETS_JSON; .env refreshed."
    )
    print(f"VARS_JSON exported ({len(vars_keys)}): {format_key_list(vars_keys)}")
    print(
        "SECRETS_JSON exported "
        f"({len(secrets_keys)}): {format_key_list(secrets_keys)}"
    )


if __name__ == "__main__":
    main()
