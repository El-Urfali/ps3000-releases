#!/usr/bin/env python3
"""
make_release.py — turn a PlatformIO build into a publishable Power Serve release.

Run it from the ps3000-releases repo root, pointing at a finished .pio build.

    python tools\\make_release.py ^
        --env v1_partner ^
        --version 1.1.0 ^
        --pio-build "C:\\...\\PS3000_Main\\.pio\\build\\v1_partner" ^
        --commit 4a36d3d0 ^
        --notes notes.md

What it does:
  1. Copies firmware.bin, bootloader.bin, partitions.bin (+ boot_app0.bin from the
     framework) into <target>/<version>/.
  2. Computes size, MD5 and SHA-256 of firmware.bin.
     🔴 MD5 is the one the ESP32 checks (Update.setMD5). SHA-256 is for humans.
  3. Writes <target>/manifest.json  — what the machine's Firmware Update button reads.
  4. Writes flash/manifest-<target>.json — what the USB browser flasher reads.

🔴 The target name written into the manifest MUST equal PS_TARGET_NAME in the
firmware. The machine refuses any manifest whose target does not match its own.
That is the only thing stopping a V2 binary landing on a V1 machine.
"""

import argparse
import hashlib
import json
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

RAW_BASE = "https://raw.githubusercontent.com/{owner}/{repo}/main"

# The four images a serial (USB) flash writes, and where they go.
# NVS (0x9000) and LittleFS are NOT in this list, so calibration, WiFi
# credentials and stored run logs all survive a USB re-flash.
SERIAL_PARTS = [
    ("bootloader.bin", 0x1000),
    ("partitions.bin", 0x8000),
    ("boot_app0.bin", 0xE000),
    ("firmware.bin", 0x10000),
]


def digest(path: Path):
    md5, sha = hashlib.md5(), hashlib.sha256()
    size = 0
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            md5.update(chunk)
            sha.update(chunk)
            size += len(chunk)
    return size, md5.hexdigest(), sha.hexdigest()


def find_boot_app0(explicit: str | None) -> Path:
    if explicit:
        p = Path(explicit)
        if not p.is_file():
            sys.exit(f"boot_app0.bin not found at {p}")
        return p
    home = Path.home() / ".platformio" / "packages"
    hits = sorted(home.glob("framework-arduinoespressif32*/tools/partitions/boot_app0.bin"))
    if not hits:
        sys.exit(
            "Could not find boot_app0.bin under ~/.platformio/packages.\n"
            "Pass it explicitly with --boot-app0 <path>."
        )
    return hits[-1]


MONTHS = rb"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)"
DATE_RE = re.compile(MONTHS + rb" [ 0-9]\d \d{4}\x00")
TIME_RE = re.compile(rb"\d\d:\d\d:\d\d\x00")


def build_stamps(firmware: Path):
    """Recover every __DATE__ / __TIME__ pair compiled into the image.

    This is the same string the boot banner and /status "build" field report, so
    it proves after the fact which source tree produced a published .bin.

    🔴 TWO TRAPS, both found 2026-09-07 the first time this was run for real:
      1. __DATE__ and __TIME__ are SEPARATE string literals. They are not
         adjacent in rodata, so a regex for "<date> <time>" matches nothing.
         They must be found independently and paired by proximity.
      2. The image contains SEVERAL date literals — the prebuilt ESP-IDF
         libraries carry their own. Only the NEWEST is the application's,
         because the app is the last thing compiled.
    All candidates are returned so the choice can be seen rather than trusted.
    """
    blob = firmware.read_bytes()
    found = []
    for m in DATE_RE.finditer(blob):
        date = " ".join(m.group(0)[:-1].decode().split())
        t = TIME_RE.search(blob[max(0, m.start() - 64): m.end() + 64])
        if not t:
            continue
        stamp = f"{date} {t.group(0)[:-1].decode()}"
        try:
            when = datetime.strptime(stamp, "%b %d %Y %H:%M:%S")
        except ValueError:
            continue
        found.append((when, f"{m.group(0)[:-1].decode()} {t.group(0)[:-1].decode()}"))
    found.sort()
    return [s for _, s in found]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--env", required=True, help="PlatformIO env name, e.g. v1_partner")
    ap.add_argument("--target", help="PS_TARGET_NAME (defaults to --env)")
    ap.add_argument("--version", required=True, help="semver, e.g. 1.1.0")
    ap.add_argument("--pio-build", required=True, help="path to .pio/build/<env>")
    ap.add_argument("--commit", default="", help="git commit the build came from")
    ap.add_argument("--notes", help="markdown/text file of release notes")
    ap.add_argument("--min-version", default="0.0.0",
                    help="refuse to install onto anything older than this")
    ap.add_argument("--boot-app0", help="override path to boot_app0.bin")
    ap.add_argument("--owner", default="El-Urfali")
    ap.add_argument("--repo", default="ps3000-releases")
    ap.add_argument("--root", default=".", help="ps3000-releases repo root")
    args = ap.parse_args()

    target = args.target or args.env
    root = Path(args.root).resolve()
    build = Path(args.pio_build)
    if not build.is_dir():
        sys.exit(f"No such build directory: {build}")

    dest = root / target / args.version
    dest.mkdir(parents=True, exist_ok=True)

    # ---- collect the four images -------------------------------------------
    for name, _ in SERIAL_PARTS:
        src = find_boot_app0(args.boot_app0) if name == "boot_app0.bin" else build / name
        if not src.is_file():
            sys.exit(f"Missing {name} — expected at {src}")
        shutil.copy2(src, dest / name)

    firmware = dest / "firmware.bin"
    size, md5, sha256 = digest(firmware)
    stamps = build_stamps(firmware)
    stamp = stamps[-1] if stamps else None

    notes = ""
    if args.notes:
        notes = Path(args.notes).read_text(encoding="utf-8").strip()

    base = RAW_BASE.format(owner=args.owner, repo=args.repo)
    url = f"{base}/{target}/{args.version}/firmware.bin"

    # ---- manifest the MACHINE reads ----------------------------------------
    manifest = {
        "schema": 1,
        "target": target,
        "version": args.version,
        "min_version": args.min_version,
        "url": url,
        "size": size,
        "md5": md5,
        "sha256": sha256,
        "build": stamp,
        "commit": args.commit,
        "published": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "notes": notes,
    }
    (root / target / "manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )

    # ---- manifest the USB BROWSER FLASHER reads ----------------------------
    # ESP Web Tools format. All four parts, standard offsets — this is a full
    # serial upload, identical to what PlatformIO writes, and it resets the OTA
    # boot selector back to app0 via boot_app0.bin.
    web = {
        "name": f"Power Serve — {target} {args.version}",
        "version": args.version,
        "new_install_prompt_erase": False,
        "builds": [
            {
                "chipFamily": "ESP32",
                "parts": [
                    {"path": f"../{target}/{args.version}/{name}", "offset": off}
                    for name, off in SERIAL_PARTS
                ],
            }
        ],
    }
    (root / "flash" / f"manifest-{target}.json").write_text(
        json.dumps(web, indent=2) + "\n", encoding="utf-8"
    )

    print(f"target      {target}")
    print(f"version     {args.version}")
    print(f"commit      {args.commit or '(not recorded)'}")
    if stamps:
        print(f"build stamp {stamp}   <- the application")
        for other in stamps[:-1]:
            print(f"            {other}   (prebuilt library, ignore)")
    else:
        print("build stamp (not found in image)")
    print(f"size        {size:,} bytes")
    print(f"md5         {md5}")
    print(f"sha256      {sha256}")
    print(f"written     {dest}")
    print()
    print("🔴 Check the build stamp against the boot banner of the machine you")
    print("   built this from before you push. It is the only proof of lineage.")


if __name__ == "__main__":
    main()
