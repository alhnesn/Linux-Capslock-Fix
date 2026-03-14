#!/usr/bin/env python3
import subprocess
import sys
import os


if os.geteuid() != 0:
    print("Run as root: sudo python ./install.py")
    sys.exit(1)


try:
    import evdev
    from evdev import UInput, ecodes as e
except ImportError:

    if subprocess.run("apt").returncode == 0:
        subprocess.run(["apt","install","-y","python3-evdev"])
        import evdev
        from evdev import UInput, ecodes as e

    elif subprocess.run("dnf").returncode == 0:
        subprocess.run(["dnf","install","-y","python3-evdev"])
        import evdev
        from evdev import UInput, ecodes as e

    elif subprocess.run("pacman").returncode == 0:
        subprocess.run(["pacman","-S","--noconfirm","python3-evdev"])
        import evdev
        from evdev import UInput, ecodes as e

    else:
        print("Unknown package manager. Install python3-evdev manually")
        sys.exit(1)


# Stop already running fix to prevent grabbing fixed virtual keyboard
subprocess.run(["systemctl","stop","capslock-fix.service"])
subprocess.run(["systemctl","disable","capslock-fix.service"])



print("Creating script...")

script_content = """#!/usr/bin/env python3
import evdev
from evdev import UInput, ecodes as e
import select
import time


def get_keyboards():
    devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
    keyboards = [
        d for d in devices
        if d.name != "capslock-fixed"
        and e.EV_KEY in d.capabilities()
        and e.KEY_CAPSLOCK in d.capabilities()[e.EV_KEY]
        and e.KEY_A in d.capabilities()[e.EV_KEY]
    ]
    return keyboards


def grab_all(already_grabbed=None):
    grabbed = dict(already_grabbed) if already_grabbed else {}
    for kbd in get_keyboards():
        if kbd.path not in grabbed:
            try:
                kbd.grab()
                grabbed[kbd.path] = kbd
            except (OSError, IOError):
                pass
    return grabbed


keyboards = grab_all()
while not keyboards:
    time.sleep(0.5)
    keyboards = grab_all()

first = list(keyboards.values())[0]
ui = UInput(
    {
        e.EV_KEY: first.capabilities()[e.EV_KEY],
        e.EV_MSC: [e.MSC_SCAN],
        e.EV_LED: [e.LED_NUML, e.LED_CAPSL, e.LED_SCROLLL],
    },
    name="capslock-fixed",
)

last_scan = time.monotonic()

try:
    while True:
        now = time.monotonic()
        if now - last_scan > 2:
            last_scan = now
            keyboards = grab_all(keyboards)

        fd_to_path = {kbd.fd: path for path, kbd in keyboards.items()}
        fds = list(fd_to_path.keys())
        if not fds:
            time.sleep(0.5)
            keyboards = grab_all()
            continue

        readable, _, _ = select.select(fds, [], [], 2)
        for fd in readable:
            path = fd_to_path.get(fd)
            kbd = keyboards.get(path) if path else None
            if kbd is None:
                continue
            try:
                for event in kbd.read():
                    if event.type == e.EV_KEY and event.code == e.KEY_CAPSLOCK:
                        if event.value == 1:
                            ui.write(e.EV_KEY, e.KEY_CAPSLOCK, 1)
                            ui.syn()
                            ui.write(e.EV_KEY, e.KEY_CAPSLOCK, 0)
                            ui.syn()
                    else:
                        ui.write(event.type, event.code, event.value)
                        if event.type == e.EV_SYN:
                            ui.syn()
            except OSError as err:
                if err.errno == 19:
                    del keyboards[path]
                else:
                    raise

except KeyboardInterrupt:
    pass

finally:
    for kbd in keyboards.values():
        try:
            kbd.ungrab()
        except OSError:
            pass
    ui.close()
"""


script_path = "/usr/local/bin/capslock-fix.py"
try:
    with open(script_path, "w") as f:
        f.write(script_content)

    os.chmod(script_path, 0o755)

except Exception as e:
    print(f"An error occurred: {e}")


print("Creating service...")

service_content = """
[Unit]
Description=Caps Lock Instant Toggle Fix
Before=display-manager.service

[Service]
Type=simple
ExecStart=/usr/bin/python3 /usr/local/bin/capslock-fix.py
Restart=always
RestartSec=2

[Install]
WantedBy=multi-user.target
"""

service_path = "/etc/systemd/system/capslock-fix.service"
try:
    with open(service_path, "w") as f:
        f.write(service_content)


except Exception as e:
    print(f"An error occurred: {e}")


subprocess.run(["systemctl","daemon-reload"])
subprocess.run(["systemctl","enable","capslock-fix.service"])
subprocess.run(["systemctl","start","capslock-fix.service"])

print("Done! Check status: ")
print("sudo systemctl status capslock-fix.service")
