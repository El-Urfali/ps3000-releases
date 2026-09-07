# Power Serve — firmware releases

Public distribution point for Power Serve machine firmware. **Binaries and release
notes only.** Source, schematics and the BOM stay private in `El-Urfali/ps3000`.

Nothing here is secret, and nothing here needs a GitHub account to download.

---

## Layout

```
<target>/manifest.json          what the machine's Firmware Update button reads
<target>/<version>/firmware.bin     the application image
<target>/<version>/bootloader.bin   \
<target>/<version>/partitions.bin    |  needed only by the USB flasher
<target>/<version>/boot_app0.bin    /
flash/index.html                the USB browser flasher (GitHub Pages)
flash/manifest-<target>.json    what the flasher reads
tools/make_release.py           builds all of the above from a .pio build
```

`<target>` is the firmware's own `PS_TARGET_NAME`. Today: **`v1_partner`**.

---

## 🔴 The target field is a safety interlock, not a label

Every Power Serve on every network answers to `PS3000.local`, and until now
nothing identified which machine was about to be overwritten.

The machine reads `manifest.json`, compares `target` against its own compiled-in
`PS_TARGET_NAME`, and **refuses the update on any mismatch.** A `ps1500_v2`
binary cannot install itself on a V1 machine — the V2 pin map asserts `TEN_EN`
at boot on V1 wiring, which is a 3.0 N·m motor driving a ballscrew with nobody
touching it.

Publishing a binary under the wrong target directory defeats this. Do not do it.

---

## Cutting a release

From this repo's root, with a finished PlatformIO build:

```powershell
python tools\make_release.py `
    --env v1_partner `
    --version 1.1.0 `
    --commit <sha> `
    --pio-build "C:\...\PS3000_Main\.pio\build\v1_partner" `
    --notes notes.md
```

Then read the script's output. **Check the build stamp it recovered from the
image against the boot banner of the machine you built it on** before pushing —
that stamp is the only proof that the published `.bin` came from the source tree
you think it did. It is how the partner's machine was identified as running
`4a36d3d` and not the beta.

```powershell
git add -A
git commit -m "v1_partner 1.1.0"
git push
```

A machine sees the new version within one press of **Check for update**. There is
no cache to wait out — `raw.githubusercontent.com` serves the committed file.

---

## Two ways firmware gets onto a machine

| | Path | When |
|---|---|---|
| **1** | **Firmware Update button**, Setup page → FIRMWARE | Normal. Machine pulls it over WiFi by itself. Requires firmware ≥ 1.0.0 already installed. |
| **2** | **USB flasher**, `flash/index.html` on GitHub Pages | The first install, and recovery. Chrome or Edge on a laptop, USB cable, no software to install. |

Path 2 is the way back from a bad update, so it is never removed and its page
stays published.

### 🔴 The flasher is PINNED, and `make_release.py` does not move it

`flash/manifest-<target>.json` names one specific version, and cutting a release
leaves it alone. That is deliberate: **if a published release turns out not to
boot, recovery must not install the very image that caused it.** The flasher
serves a version known to come up on hardware.

Move it only with `--set-flasher`, and only after that version has actually run
on a machine. Every run prints what the flasher currently installs, so the pin is
never invisible.

### What survives either path

NVS (`ps3000`, `ps3000wifi`) and LittleFS are not written by either. **Load-cell
calibration, pedal calibration, WiFi credentials and stored run logs all
survive.** Those namespace names are frozen for exactly this reason.

---

## Pointing a machine somewhere else

The manifest URL is compiled into the firmware, but can be overridden per machine
from the serial console without a reflash:

```
fwurl                        show the URL in use
fwurl <https://...json>      override, stored in NVS
fwurl default                back to the compiled-in URL
```

Useful for testing a release on a bench machine before it goes to a partner.

---

## Version numbers

Plain semver, `MAJOR.MINOR.PATCH`. The machine compares numerically, so `1.10.0`
is newer than `1.9.0`. `min_version` in the manifest lets a release refuse to
install onto a build too old to handle it — leave it at the oldest version the
upgrade is actually safe from.
