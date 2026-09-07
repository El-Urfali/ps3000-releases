# Updating your Power Serve

Two things to know before either method:

- **Take the string off the machine.** Both methods restart the controller.
- **Your settings are kept.** Load-cell calibration, pedal calibration, WiFi and
  saved run logs all survive an update. Only the program is replaced.

---

## Normal updates — from the machine itself

No cable, no computer. Any tablet or phone already on the shop network.

1. Open **http://PS3000.local/** on the tablet.
2. Tap the **⚙** cog in the top strip.
3. Scroll down to **FIRMWARE**.
4. Tap **Check for update**.
5. If it says a new version is available, tap **Install**, then tap it again to
   confirm.
6. Wait. The bar fills, the machine restarts, and the page comes back on its own
   after about a minute.

**Do not cut power while it is installing.**

### If Check refuses

| It says | What it means |
|---|---|
| *not on a network — the machine must be joined to shop WiFi* | The machine is hosting its own hotspot instead of being on the shop network. It cannot reach the internet that way. Reconnect it to shop WiFi. |
| *run or tension hold active* | Stop the run or release the tension hold first. |
| *up to date* | You already have the newest published version. |
| *REFUSED — that release is for '…'* | A safety check did its job: that release is built for a different machine. **Do not try to work around this.** Tell Alan. |
| *no release published for this machine yet* | Nothing has been published. Nothing is wrong. |

---

## First install, and recovery — over USB

You need this exactly twice: once to install the update button in the first
place, and again only if an update ever leaves the machine unable to start.

**Requirements:** a laptop running **Chrome or Edge** (not Safari, not Firefox,
not an iPad or phone), and a **data** USB cable — a charge-only cable will not
work.

1. Take the string off. Motor and driver power **off**.
2. Plug the USB cable from the laptop into the controller board.
3. Open the flasher page **(link below)** and click **Connect & Install**.
4. Pick the serial port. On Windows it is usually `COM3`–`COM9`, listed as
   *Silicon Labs* or *CP210x*. If nothing is listed, the cable is charge-only.
5. Wait for it to finish. The board restarts by itself.
6. Open **http://PS3000.local/** → **⚙** → **FIRMWARE** and check the version.

If the board will not start flashing: hold **BOOT**, tap **EN** (or **RST**),
release **BOOT**, and click Install again.

> **Flasher page:** https://el-urfali.github.io/ps3000-releases/flash/
>
> **Bookmark it.** It is the way back from any bad update.

---

## What to send Alan if something goes wrong

From the tablet, all three are one tap each:

- **http://PS3000.local/status** — the machine's full state, including the
  build stamp of what is actually running.
- **http://PS3000.local/download/cond** — the conditioning run log.
- **http://PS3000.local/download/creep** — the creep log.

Save the page or screenshot it. The build stamp in `/status` is the single most
useful line — it says exactly which firmware is running, which is not always
what anyone expects.
