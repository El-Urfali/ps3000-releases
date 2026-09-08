Fixes the Firmware Update card getting stuck on "Restarting".

The update itself always worked — the card simply stopped watching one moment
too early and never noticed the machine come back. It now waits through the
restart, says so while it waits, and reloads itself onto the new version.

Also fixes the Setup page sometimes still showing the old layout right after an
update, on a tablet that had cached it.

Your calibration, WiFi settings and saved run logs are kept.
