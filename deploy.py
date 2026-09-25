"""
Deploy des Ordners site/ auf Netlify (Zip-Upload per API).

    python build.py
    python deploy.py

Token: NETLIFY_AUTH_TOKEN aus tools/_deploy/.env (nicht im Repo).
Beim ersten Lauf wird die Site angelegt und ihre ID in netlify-site.json gemerkt.
"""
import io
import json
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).parent
SITE_NAME = "rothgmbh-swk-aufmass"
SITE_FILE = ROOT / "netlify-site.json"
API = "https://api.netlify.com/api/v1"


def token():
    for line in (ROOT.parent / "_deploy" / ".env").read_text(encoding="utf-8").splitlines():
        if line.startswith("NETLIFY_AUTH_TOKEN="):
            return line.split("=", 1)[1].strip().strip('"')
    raise SystemExit("NETLIFY_AUTH_TOKEN fehlt in tools/_deploy/.env")


def call(method, path, tok, data=None, ctype="application/json"):
    req = urllib.request.Request(API + path, data=data, method=method,
                                 headers={"Authorization": f"Bearer {tok}", "Content-Type": ctype})
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read() or b"{}")


def main():
    tok = token()
    if SITE_FILE.exists():
        site = json.loads(SITE_FILE.read_text(encoding="utf-8"))
    else:
        s = call("POST", "/sites", tok, json.dumps({"name": SITE_NAME}).encode())
        site = {"id": s["id"], "name": s["name"], "url": s["ssl_url"] or s["url"]}
        SITE_FILE.write_text(json.dumps(site, indent=2), encoding="utf-8")
        print("Site angelegt:", site["url"])

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted((ROOT / "site").iterdir()):
            z.write(f, f.name)
    d = call("POST", f"/sites/{site['id']}/deploys", tok, buf.getvalue(), "application/zip")
    print("Deploy:", d.get("state"), d.get("id"), "->", site["url"])


if __name__ == "__main__":
    main()
