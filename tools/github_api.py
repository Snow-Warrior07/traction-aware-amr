"""Use the configured Git credential helper without logging credentials.

Only the exact GitHub host is queried. API output never includes credentials.
"""
import argparse
import json
import os
import subprocess
import urllib.error
import urllib.request
from pathlib import Path


def credential():
    env = dict(os.environ, GCM_INTERACTIVE="never", GIT_TERMINAL_PROMPT="0")
    result = subprocess.run(
        ["git", "credential", "fill"], input="protocol=https\nhost=github.com\n\n",
        text=True, capture_output=True, env=env, timeout=30,
    )
    fields = dict(line.split("=", 1) for line in result.stdout.splitlines() if "=" in line)
    if not fields.get("password"):
        raise RuntimeError("No existing GitHub credential was available from Git Credential Manager.")
    return fields["password"]


def request(path, method="GET", data=None):
    payload = json.dumps(data).encode() if data is not None else None
    headers = {"Authorization": "Bearer " + credential(),
               "Accept": "application/vnd.github+json", "User-Agent": "traction-aware-amr",
               "X-GitHub-Api-Version": "2022-11-28"}
    req = urllib.request.Request("https://api.github.com" + path, payload, headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=40) as response:
            body = response.read()
            return json.loads(body) if body else {"status": response.status}
    except urllib.error.HTTPError as error:
        body = error.read().decode()
        raise RuntimeError(f"GitHub API HTTP {error.code}: {body[:600]}") from None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["account", "repo", "create", "runs", "pages", "enable-pages", "release"])
    parser.add_argument("--owner", default="Snow-Warrior07")
    parser.add_argument("--repo", default="traction-aware-amr")
    args = parser.parse_args()
    base = f"/repos/{args.owner}/{args.repo}"
    if args.action == "account":
        user = request("/user")
        print(json.dumps({"login": user["login"], "url": user["html_url"]}))
    elif args.action == "create":
        result = request("/user/repos", "POST", {"name": args.repo, "private": False,
            "description": "Software-only traction-aware warehouse rover: linear/nonlinear control, ROS 2, virtual PCB, and live tests."})
        print(json.dumps({"url": result["html_url"], "default_branch": result["default_branch"]}))
    elif args.action == "repo":
        result = request(base)
        print(json.dumps({"url": result["html_url"], "default_branch": result["default_branch"], "private": result["private"]}))
    elif args.action == "runs":
        result = request(base + "/actions/runs?per_page=5")
        print(json.dumps([{"id": r["id"], "status": r["status"], "conclusion": r["conclusion"],
            "url": r["html_url"], "sha": r["head_sha"]} for r in result["workflow_runs"]], indent=2))
    elif args.action == "pages":
        print(json.dumps(request(base + "/pages")))
    elif args.action == "enable-pages":
        print(json.dumps(request(base + "/pages", "POST", {"build_type": "workflow"})))
    elif args.action == "release":
        text = (Path(__file__).resolve().parents[1] / "docs" / "release-notes.md").read_text(encoding="utf-8")
        result = request(base + "/releases", "POST", {"tag_name": "v0.1.0", "name": "v0.1.0: verified virtual rover", "body": text})
        print(json.dumps({"url": result["html_url"]}))


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"{type(error).__name__}: {error}")
        raise SystemExit(1)
