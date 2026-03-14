#!/usr/bin/env python3
import subprocess
import os
import sys


if os.geteuid() != 0:
    print("Run as root: sudo python ./uninstall.py")
    sys.exit(1)


subprocess.run(["systemctl", "stop", "capslock-fix.service"])
subprocess.run(["systemctl", "disable", "capslock-fix.service"])

service_path = "/etc/systemd/system/capslock-fix.service"
script_path = "/usr/local/bin/capslock-fix.py"

for path in [service_path, script_path]:
    if os.path.exists(path):
        os.remove(path)
        print(f"Removed {path}")

subprocess.run(["systemctl", "daemon-reload"])

print("Done. Capslock fix has been uninstalled.")
