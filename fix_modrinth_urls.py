#!/usr/bin/env python3
"""Patch all Modrinth .pw.toml files to include direct download URLs."""
import json
import os
import re
import urllib.request
import urllib.error
from pathlib import Path

PACKWIZ_DIR = Path("/home/firefloc/serveur/mod_serv_env/nexamon")
MODRINTH_API = "https://api.modrinth.com/v2"
HEADERS = {"User-Agent": "nexamon-packwiz/1.0 (firefloc)"}

def get_version(version_id):
    """Fetch a single version from Modrinth."""
    req = urllib.request.Request(
        f"{MODRINTH_API}/version/{version_id}",
        headers=HEADERS
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())

def get_versions_batch(version_ids):
    """Fetch multiple versions from Modrinth."""
    ids_json = json.dumps(version_ids)
    req = urllib.request.Request(
        f"{MODRINTH_API}/versions?ids={urllib.request.quote(ids_json)}",
        headers=HEADERS
    )
    with urllib.request.urlopen(req) as resp:
        versions = json.loads(resp.read())
        return {v["id"]: v for v in versions}

def extract_modrinth_info(toml_content):
    """Extract mod-id and version from a .pw.toml file."""
    mod_id = re.search(r'mod-id\s*=\s*"([^"]+)"', toml_content)
    version = re.search(r'version\s*=\s*"([^"]+)"', toml_content)
    has_url = re.search(r'url\s*=\s*"([^"]*)"', toml_content)
    if mod_id and version:
        url_val = has_url.group(1) if has_url else None
        return mod_id.group(1), version.group(1), url_val
    return None, None, None

def patch_toml(toml_path, download_url):
    """Add or replace the url field in the [download] section."""
    with open(toml_path, "r") as f:
        content = f.read()

    # If there's already a url with value, skip
    if re.search(r'url\s*=\s*"https?://', content):
        return False

    # Remove empty mode line
    content = re.sub(r'mode\s*=\s*""\n', '', content)

    # Add url before hash-format in [download] section
    content = re.sub(
        r'(\[download\]\n)',
        f'\\1url = "{download_url}"\n',
        content
    )

    with open(toml_path, "w") as f:
        f.write(content)
    return True

def main():
    # Collect all .pw.toml files that use Modrinth and lack a download URL
    to_fix = []  # (path, version_id)

    for subdir in ["mods", "resourcepacks", "shaderpacks"]:
        dir_path = PACKWIZ_DIR / subdir
        if not dir_path.exists():
            continue
        for f in sorted(os.listdir(dir_path)):
            if not f.endswith(".pw.toml"):
                continue
            fpath = dir_path / f
            with open(fpath) as fh:
                content = fh.read()
            mod_id, version_id, existing_url = extract_modrinth_info(content)
            if version_id and (not existing_url or existing_url == ""):
                to_fix.append((fpath, version_id))

    print(f"Found {len(to_fix)} files needing Modrinth URL fix")

    if not to_fix:
        print("Nothing to do!")
        return

    # Batch fetch versions (max 100 per request)
    all_version_ids = [vid for _, vid in to_fix]
    version_cache = {}

    for i in range(0, len(all_version_ids), 100):
        batch = all_version_ids[i:i+100]
        print(f"  Fetching batch {i//100 + 1} ({len(batch)} versions)...")
        try:
            results = get_versions_batch(batch)
            version_cache.update(results)
        except urllib.error.HTTPError as e:
            print(f"  API error: {e.code} — trying one by one")
            for vid in batch:
                try:
                    v = get_version(vid)
                    version_cache[v["id"]] = v
                except Exception as ex:
                    print(f"    Failed {vid}: {ex}")

    # Patch files
    fixed = 0
    failed = 0
    for fpath, version_id in to_fix:
        vdata = version_cache.get(version_id)
        if not vdata:
            print(f"  SKIP (no API data): {fpath.name}")
            failed += 1
            continue

        # Find primary file URL
        target_file = None
        for f in vdata.get("files", []):
            if f.get("primary", False):
                target_file = f
                break
        if not target_file and vdata.get("files"):
            target_file = vdata["files"][0]

        if not target_file or not target_file.get("url"):
            print(f"  SKIP (no file URL): {fpath.name}")
            failed += 1
            continue

        url = target_file["url"]
        if patch_toml(fpath, url):
            fixed += 1
        else:
            print(f"  SKIP (already has URL): {fpath.name}")

    print(f"\nDone! Fixed: {fixed}, Skipped/Failed: {failed}")

if __name__ == "__main__":
    main()
