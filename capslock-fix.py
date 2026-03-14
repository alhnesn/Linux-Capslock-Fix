#!/usr/bin/env python3
import evdev
from evdev import UInput, ecodes as e
import select
import time


def get_keyboards():
    """
    Find and return all real keyboards (excluding our virtual device).

    Return:
        keyboards: evdev.InputDevice list of keyboards
    """
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
    """Grab all available keyboards. Returns dict of path -> InputDevice."""
    grabbed = dict(already_grabbed) if already_grabbed else {}
    for kbd in get_keyboards():
        if kbd.path not in grabbed:
            try:
                kbd.grab()
                grabbed[kbd.path] = kbd
            except (OSError, IOError):
                pass
    return grabbed


# Wait for at least one keyboard
keyboards = grab_all()
while not keyboards:
    time.sleep(0.5)
    keyboards = grab_all()

# Build virtual device from first keyboard's capabilities
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
        # Periodically check for new keyboards
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
                if err.errno == 19:  # ENODEV - keyboard unplugged
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
