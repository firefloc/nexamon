#!/usr/bin/env python3
"""
Build 3 packwiz packs (low/base/ultra) from a single source repo.

Each .pw.toml has a 'tier' field:
  tier = "core"   → in Low + Base + Ultra
  tier = "base"   → in Base + Ultra
  tier = "ultra"  → in Ultra only

If no tier field, defaults:
  side = "both" → "core" (server mod, required everywhere)
  side = "client" → "base"

Configs live in configs/{core,base,ultra}/config/...
  Merged into each pack's root based on tier.

Shaderpacks follow tier rules like mods (base = Base+Ultra, ultra = Ultra only).

Usage: python3 build_packs.py [--tag]
  --tag   Auto-assign tier fields to all .pw.toml files (first run)
"""
import hashlib
import json
import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).parent

# ── Default tier assignments for client-only mods ──
CORE_CLIENT_PREFIXES = {
    "sodium", "indium", "entityculling", "immediatelyfast", "moreculling",
    "modmenu", "controlling", "keybind_fix", "keybindsgalore",
    "tooltipfix", "defaultoptions", "searchables", "reeses-sodium",
    "sodiumextras", "sodiumleafculling", "sodiumoptionsapi",
    "sodiumoptionsmodcompat", "ferritecore", "krypton", "lithium",
    "modernfix", "debugify", "notenoughcrashes", "stackdeobfuscator",
}

ULTRA_CLIENT_PREFIXES: set[str] = set()  # iris & euphoria moved to base

CORE_RP_FILES = {
    "cobblemon-interface.pw.toml",
    "cobblemon-interface-modded.pw.toml",
    "cobbleverse-rp.pw.toml",
    "cobbleverse-rctmod-rp.pw.toml",
    "cutil-nerf-tooltips.pw.toml",
    "low-fire.pw.toml",
}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def read_field(path: Path, field: str) -> str | None:
    for line in path.read_text().splitlines():
        stripped = line.strip()
        if stripped.startswith(field) and "=" in stripped:
            key = stripped.split("=", 1)[0].strip()
            if key == field:
                return stripped.split("=", 1)[1].strip().strip('"')
    return None


def read_download_hash(path: Path) -> str | None:
    """Read the sha256 download hash from a .pw.toml [download] section."""
    in_download = False
    for line in path.read_text().splitlines():
        stripped = line.strip()
        if stripped == "[download]":
            in_download = True
            continue
        if stripped.startswith("[") and in_download:
            break
        if in_download and "=" in stripped:
            key = stripped.split("=", 1)[0].strip()
            if key == "hash":
                return stripped.split("=", 1)[1].strip().strip('"')
    return None


def set_tier(path: Path, tier: str):
    content = path.read_text()
    lines = content.splitlines()
    for i, line in enumerate(lines):
        if line.strip().startswith("tier") and "=" in line:
            key = line.split("=", 1)[0].strip()
            if key == "tier":
                lines[i] = f'tier = "{tier}"'
                path.write_text("\n".join(lines) + "\n")
                return
    insert_after = None
    for i, line in enumerate(lines):
        key = line.split("=", 1)[0].strip() if "=" in line else ""
        if key == "side":
            insert_after = i
            break
        if key == "filename":
            insert_after = i
    if insert_after is not None:
        lines.insert(insert_after + 1, f'tier = "{tier}"')
    else:
        lines.insert(min(3, len(lines)), f'tier = "{tier}"')
    path.write_text("\n".join(lines) + "\n")


def filename_matches(filename: str, prefixes: set) -> bool:
    name_lower = filename.lower().replace(".pw.toml", "")
    return any(name_lower.startswith(p) for p in prefixes)


def auto_tag_tier(path: Path, is_rp: bool = False) -> str:
    if is_rp:
        tier = "core" if path.name in CORE_RP_FILES else "base"
        set_tier(path, tier)
        return tier
    side = read_field(path, "side") or "both"
    if side == "both":
        tier = "core"
    elif filename_matches(path.name, CORE_CLIENT_PREFIXES):
        tier = "core"
    elif filename_matches(path.name, ULTRA_CLIENT_PREFIXES):
        tier = "ultra"
    else:
        tier = "base"
    set_tier(path, tier)
    return tier


def get_tier(path: Path, default_side: str = "both") -> str:
    tier = read_field(path, "tier")
    if tier and tier in ("core", "base", "ultra"):
        return tier
    side = read_field(path, "side") or default_side
    return "core" if side == "both" else "base"


def collect_config_files(config_tier_dir: Path) -> list[tuple[str, Path]]:
    """Collect all files under configs/<tier>/ returning (relative_path, absolute_path)."""
    results = []
    if not config_tier_dir.exists():
        return results
    for root, dirs, files in os.walk(config_tier_dir):
        for f in files:
            abs_path = Path(root) / f
            rel_path = abs_path.relative_to(config_tier_dir)
            results.append((str(rel_path), abs_path))
    return results


def build_index_toml(metafiles: list[tuple[str, str]],
                     regular_files: list[tuple[str, str]]) -> str:
    """Build index.toml. metafiles = .pw.toml entries, regular_files = config/etc entries."""
    lines = ['hash-format = "sha256"', '']
    for fpath, fhash in sorted(metafiles):
        lines.append("[[files]]")
        lines.append(f'file = "{fpath}"')
        lines.append(f'hash = "{fhash}"')
        lines.append("metafile = true")
        lines.append("")
    for fpath, fhash in sorted(regular_files):
        lines.append("[[files]]")
        lines.append(f'file = "{fpath}"')
        lines.append(f'hash = "{fhash}"')
        lines.append("")
    return "\n".join(lines)


def build_pack_toml(name: str, index_hash: str) -> str:
    return f'''name = "{name}"
author = "firefloc"
version = "1.0.0"
pack-format = "packwiz:1.1.0"

[index]
file = "index.toml"
hash-format = "sha256"
hash = "{index_hash}"

[versions]
fabric = "0.18.4"
minecraft = "1.21.1"
'''


def build_pack(pack_name: str, pack_dir: Path, mod_files: list[Path],
               rp_files: list[Path], sp_files: list[Path],
               config_files: list[tuple[str, Path]]):
    if pack_dir.exists():
        shutil.rmtree(pack_dir)
    pack_dir.mkdir(parents=True)

    metafile_entries = []
    regular_entries = []

    # Copy .pw.toml metafiles (mods, resourcepacks, shaderpacks)
    for subdir_name, files in [("mods", mod_files), ("resourcepacks", rp_files), ("shaderpacks", sp_files)]:
        if not files:
            continue
        out_dir = pack_dir / subdir_name
        out_dir.mkdir()
        for src in files:
            dst = out_dir / src.name
            shutil.copy2(src, dst)
            h = sha256_file(dst)
            metafile_entries.append((f"{subdir_name}/{src.name}", h))

    # Copy config files (regular files, not metafiles)
    for rel_path, src in config_files:
        dst = pack_dir / rel_path
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        h = sha256_file(dst)
        regular_entries.append((rel_path, h))

    # Generate integrity manifest (mod hashes + critical config hashes)
    mod_hashes = {}
    for src in mod_files:
        fn = read_field(src, "filename")
        dl_hash = read_download_hash(src)
        if fn and dl_hash:
            mod_hashes[fn] = dl_hash

    # Resolve critical config hashes from the built pack
    critical_config_hashes = {}
    critical_json = pack_dir / "critical_configs.json"
    if critical_json.exists():
        crit_data = json.loads(critical_json.read_text())
        config_base = pack_dir / "config"
        for pattern in crit_data.get("paths", []):
            if pattern.endswith("/"):
                dir_path = config_base / pattern
                if dir_path.exists():
                    for root, _, files in os.walk(dir_path):
                        for f in files:
                            abs_p = Path(root) / f
                            rel_p = str(abs_p.relative_to(config_base))
                            critical_config_hashes[rel_p] = sha256_file(abs_p)
            else:
                file_path = config_base / pattern
                if file_path.exists():
                    critical_config_hashes[pattern] = sha256_file(file_path)

    # Datapacks via Paxi: config/paxi/datapacks/*.zip
    datapack_hashes = {}
    paxi_dp_dir = pack_dir / "config" / "paxi" / "datapacks"
    if paxi_dp_dir.exists():
        for f in sorted(paxi_dp_dir.iterdir()):
            if f.is_file():
                datapack_hashes[f.name] = sha256_file(f)

    integrity = {
        "mods": mod_hashes,
        "datapacks": datapack_hashes,
        "critical_configs": critical_config_hashes,
    }
    integrity_content = json.dumps(integrity, indent=2, sort_keys=True) + "\n"
    integrity_path = pack_dir / "nexamon_integrity.json"
    integrity_path.write_text(integrity_content)
    regular_entries.append(("nexamon_integrity.json", sha256_bytes(integrity_content.encode())))

    # Generate index.toml
    index_content = build_index_toml(metafile_entries, regular_entries)
    (pack_dir / "index.toml").write_text(index_content)
    index_hash = sha256_bytes(index_content.encode())

    # Generate pack.toml
    pack_content = build_pack_toml(pack_name, index_hash)
    (pack_dir / "pack.toml").write_text(pack_content)

    return len(mod_files), len(rp_files), len(sp_files), len(config_files)


def main():
    do_tag = "--tag" in sys.argv

    mods_dir = ROOT / "mods"
    rp_dir = ROOT / "resourcepacks"
    sp_dir = ROOT / "shaderpacks"
    configs_dir = ROOT / "configs"

    all_mods = sorted(mods_dir.glob("*.pw.toml"))
    all_rps = sorted(rp_dir.glob("*.pw.toml")) if rp_dir.exists() else []
    all_sps = sorted(sp_dir.glob("*.pw.toml")) if sp_dir.exists() else []

    # Tag files if requested
    if do_tag:
        print("=== Tagging .pw.toml files with tier field ===")
        for m in all_mods:
            auto_tag_tier(m)
        for rp in all_rps:
            auto_tag_tier(rp, is_rp=True)
        for sp in all_sps:
            set_tier(sp, "ultra")
        print(f"  Tagged {len(all_mods)} mods + {len(all_rps)} RPs + {len(all_sps)} shaderpacks")

    # Classify mods
    core_mods, base_mods, ultra_mods = [], [], []
    for mod in all_mods:
        tier = get_tier(mod)
        {"core": core_mods, "base": base_mods, "ultra": ultra_mods}[tier].append(mod)

    core_rps, base_rps = [], []
    for rp in all_rps:
        tier = get_tier(rp, default_side="client")
        (core_rps if tier == "core" else base_rps).append(rp)

    # Classify shaderpacks by tier
    base_sps, ultra_sps = [], []
    for sp in all_sps:
        tier = get_tier(sp, default_side="client")
        if tier in ("core", "base"):
            base_sps.append(sp)
        else:
            ultra_sps.append(sp)

    # Collect config files by tier
    core_configs = collect_config_files(configs_dir / "core")
    base_configs = collect_config_files(configs_dir / "base")
    ultra_configs = collect_config_files(configs_dir / "ultra")

    # Summary
    print(f"\n=== Classification ===")
    print(f"  Mods     → core: {len(core_mods)}, base: {len(base_mods)}, ultra: {len(ultra_mods)}")
    print(f"  RPs      → core: {len(core_rps)}, base: {len(base_rps)}")
    print(f"  SPs      → base: {len(base_sps)}, ultra: {len(ultra_sps)}")
    print(f"  Configs  → core: {len(core_configs)}, base: {len(base_configs)}, ultra: {len(ultra_configs)}")

    print(f"\n  BASE-only client mods ({len(base_mods)}):")
    for m in sorted(base_mods):
        print(f"    {m.name}")

    print(f"\n  ULTRA-only ({len(ultra_mods)} mods, {len(ultra_configs)} configs):")
    for m in sorted(ultra_mods):
        print(f"    {m.name}")

    # Build packs
    print(f"\n=== Building packs ===")

    # LOW: core only
    nm, nr, ns, nc = build_pack(
        "Nexamon Low", ROOT / "low",
        core_mods, core_rps, [],
        core_configs,
    )
    print(f"  low/   → {nm} mods, {nr} RPs, {ns} shaders, {nc} configs")

    # BASE: core + base (includes base shaderpacks)
    nm, nr, ns, nc = build_pack(
        "Nexamon", ROOT / "base",
        core_mods + base_mods, core_rps + base_rps, base_sps,
        core_configs + base_configs,
    )
    print(f"  base/  → {nm} mods, {nr} RPs, {ns} shaders, {nc} configs")

    # ULTRA: everything
    nm, nr, ns, nc = build_pack(
        "Nexamon Ultra", ROOT / "ultra",
        core_mods + base_mods + ultra_mods, core_rps + base_rps, base_sps + ultra_sps,
        core_configs + base_configs + ultra_configs,
    )
    print(f"  ultra/ → {nm} mods, {nr} RPs, {ns} shaders, {nc} configs")

    print(f"\n  Low:   https://firefloc.github.io/nexamon/low/pack.toml")
    print(f"  Base:  https://firefloc.github.io/nexamon/base/pack.toml")
    print(f"  Ultra: https://firefloc.github.io/nexamon/ultra/pack.toml")


if __name__ == "__main__":
    main()
