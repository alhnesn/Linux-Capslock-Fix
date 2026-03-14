# Linux Caps Lock Fix

Fork of [TreeOfSelf/Linux-Capslock-Fix](https://github.com/TreeOfSelf/Linux-Capslock-Fix) with fixes for boot race conditions and multi-keyboard support.

## The Problem
By default, Linux distributions mimic old physical typewriters in the way Caps lock works:
* **ON:** Activates immediately when you press the key down.
* **OFF:** Activates only once you **release** the key.

This "delay" often leads to `HEllo` style typos where the first two letters of a word are capitalized because you haven't lifted your finger off the Caps Lock key fast enough.
This script makes the toggle instant for both states.

## What's different from the original?

- **Boot race condition fix:** The original script waits for a keypress before grabbing the keyboard, which causes a race condition with Wayland compositors (GNOME/Mutter, Niri, etc). The compositor loses keyboard input until you switch TTY. This fork grabs all keyboards immediately on startup and starts `Before=display-manager.service` so the virtual device is ready before the compositor starts.
- **Multi-keyboard support:** The original only grabs one keyboard. This fork grabs all connected keyboards and automatically picks up new ones when plugged in.

## **Why not [Linux-CapsLock-Delay-Fixer](https://github.com/hexvalid/Linux-CapsLock-Delay-Fixer)?**
Because, that repo has an annoying bug where if you press Capslock and a button with a modifier (like ".") it will act like a shift (and type something like ">"). It also only works on X11, not Wayland.

## Quick Install
```bash
curl -O https://raw.githubusercontent.com/alhnesn/Linux-Capslock-Fix/main/install.py
chmod +x install.py
sudo python3 ./install.py
```

## Manual Install

### 1. Install dependency

**Debian/Ubuntu:**
```bash
sudo apt install python3-evdev
```

**Fedora/RHEL:**
```bash
sudo dnf install python3-evdev
```

**Arch:**
```bash
sudo pacman -S python-evdev
```

### 2. Create the script
```bash
sudo nano /usr/local/bin/capslock-fix.py
```
Paste the code from `capslock-fix.py`

### 3. Create service
```bash
sudo nano /etc/systemd/system/capslock-fix.service
```

Paste:
```ini
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
```

Save and exit.

### 4. Enable service
```bash
sudo systemctl daemon-reload
sudo systemctl enable capslock-fix.service
sudo systemctl start capslock-fix.service
```

## Check status
```bash
sudo systemctl status capslock-fix.service
```

Done. Runs on boot automatically.

## Uninstall
```bash
sudo python3 ./uninstall.py
```