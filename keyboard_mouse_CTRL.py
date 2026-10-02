import asyncio
import ctypes
import os
import shutil
import subprocess
import urllib.parse
import webbrowser

from datetime import datetime
from pathlib import Path
from typing import List

import pyautogui
import pyperclip

from pynput.keyboard import Key, Controller as KeyboardController
from pynput.mouse import Button, Controller as MouseController

from livekit.agents import function_tool


# ============================================================
# MAYA CONTROLLER
# ============================================================

class MayaController:

    def __init__(self):

        self.active = True

        self.keyboard = KeyboardController()
        self.mouse = MouseController()

        self.special_keys = {

            # BASIC
            "enter": Key.enter,
            "return": Key.enter,

            "space": Key.space,
            "spacebar": Key.space,

            "tab": Key.tab,

            # MODIFIERS
            "shift": Key.shift,
            "ctrl": Key.ctrl,
            "control": Key.ctrl,

            "alt": Key.alt,
            "altgr": Key.alt_gr,

            # ESC / EDIT
            "esc": Key.esc,
            "escape": Key.esc,

            "backspace": Key.backspace,
            "back": Key.backspace,

            "delete": Key.delete,
            "del": Key.delete,

            # ARROWS
            "up": Key.up,
            "arrow_up": Key.up,

            "down": Key.down,
            "arrow_down": Key.down,

            "left": Key.left,
            "arrow_left": Key.left,

            "right": Key.right,
            "arrow_right": Key.right,

            # LOCK / CASE
            "caps_lock": Key.caps_lock,
            "capslock": Key.caps_lock,

            # WINDOWS
            "win": Key.cmd,
            "windows": Key.cmd,
            "windows_key": Key.cmd,
            "cmd": Key.cmd,

            # NAVIGATION
            "home": Key.home,
            "end": Key.end,

            "page_up": Key.page_up,
            "pageup": Key.page_up,

            "page_down": Key.page_down,
            "pagedown": Key.page_down,

            "insert": Key.insert,

            # FUNCTION KEYS
            **{
                f"f{i}": getattr(Key, f"f{i}")
                for i in range(1, 13)
            }
        }


    # ========================================================
    # LOG
    # ========================================================

    def log(self, text):

        try:

            with open(
                "control_log.txt",
                "a",
                encoding="utf-8"
            ) as f:

                f.write(
                    f"{datetime.now()}: {text}\n"
                )

        except Exception:
            pass


    # ========================================================
    # WINDOWS COMMAND
    # ========================================================

    def run(self, command):

        try:

            subprocess.Popen(
                command,
                shell=True
            )

            return True

        except Exception as e:

            self.log(
                f"Command failed: {e}"
            )

            return False


    # ========================================================
    # KEY RESOLVER
    # ========================================================

    def key(self, name):

        name = str(
            name
        ).lower().strip()

        return self.special_keys.get(
            name,
            name
        )


# ============================================================
# CONTROLLER INSTANCE
# ============================================================

controller = MayaController()


# ============================================================
# MOUSE MOVE
# ============================================================

@function_tool
async def move_cursor_tool(
    direction: str,
    distance: int = 100
):

    try:

        x, y = controller.mouse.position

        d = str(
            direction
        ).lower().strip()

        distance = max(
            1,
            int(distance)
        )

        if d == "left":
            x -= distance

        elif d == "right":
            x += distance

        elif d == "up":
            y -= distance

        elif d == "down":
            y += distance

        else:
            return "Invalid mouse direction."

        controller.mouse.position = (
            x,
            y
        )

        controller.log(
            f"Mouse moved {d} {distance}"
        )

        return f"Mouse moved {d}."

    except Exception as e:

        controller.log(
            f"Mouse move error: {e}"
        )

        return f"Mouse move error: {e}"


# ============================================================
# MOUSE CLICK
# ============================================================

@function_tool
async def mouse_click_tool(
    button: str = "left"
):

    try:

        b = str(
            button
        ).lower().strip()

        if b == "left":

            controller.mouse.click(
                Button.left
            )

        elif b == "right":

            controller.mouse.click(
                Button.right
            )

        elif b == "middle":

            controller.mouse.click(
                Button.middle
            )

        elif b in (
            "double",
            "double_click",
            "double click"
        ):

            controller.mouse.click(
                Button.left,
                2
            )

        else:

            return "Invalid mouse button."

        controller.log(
            f"Mouse click: {b}"
        )

        return f"{b} click done."

    except Exception as e:

        controller.log(
            f"Mouse click error: {e}"
        )

        return f"Mouse click error: {e}"


# ============================================================
# SCROLL
# ============================================================

@function_tool
async def scroll_cursor_tool(
    direction: str,
    amount: int = 5
):

    try:

        d = str(
            direction
        ).lower().strip()

        amount = max(
            1,
            int(amount)
        )

        if d == "up":

            pyautogui.scroll(
                amount
            )

        elif d == "down":

            pyautogui.scroll(
                -amount
            )

        else:

            return "Invalid scroll direction."

        return f"Scrolled {d}."

    except Exception as e:

        return f"Scroll error: {e}"


# ============================================================
# RELIABLE TEXT TYPING
# ============================================================

async def reliable_paste(text: str):

    """
    Reliable Windows text input.

    Main method:
        Clipboard -> Ctrl+V

    Fallback:
        pyautogui.write()

    Multiple paste attempts are used because some applications
    are slow to accept clipboard data.
    """

    text = str(text)

    if not text:
        return False


    # --------------------------------------------------------
    # Save clipboard
    # --------------------------------------------------------

    try:

        old_clipboard = pyperclip.paste()

    except Exception:

        old_clipboard = ""


    try:

        # ----------------------------------------------------
        # Put text in clipboard
        # ----------------------------------------------------

        pyperclip.copy(text)

        await asyncio.sleep(0.25)


        # ----------------------------------------------------
        # First paste
        # ----------------------------------------------------

        pyautogui.hotkey(
            "ctrl",
            "v"
        )

        await asyncio.sleep(0.45)


        # ----------------------------------------------------
        # Normally one paste is enough
        # ----------------------------------------------------

        return True


    except Exception as first_error:

        controller.log(
            f"First paste failed: {first_error}"
        )


        # ----------------------------------------------------
        # FALLBACK
        # ----------------------------------------------------

        try:

            pyautogui.write(
                text,
                interval=0.01
            )

            await asyncio.sleep(0.25)

            return True

        except Exception as second_error:

            controller.log(
                f"Typing fallback failed: {second_error}"
            )

            return False


    finally:

        # ----------------------------------------------------
        # Restore clipboard AFTER everything is finished
        # ----------------------------------------------------

        await asyncio.sleep(0.20)

        try:

            pyperclip.copy(
                old_clipboard
            )

        except Exception:
            pass


# ============================================================
# TYPE TEXT
# ============================================================

@function_tool
async def type_text_tool(
    text: str
):

    """
    High reliability text typing.

    Recommended for:
        - Notepad
        - WhatsApp
        - Messenger
        - Browser
        - Search boxes
        - Chat boxes
        - Email
        - Documents

    Uses clipboard paste first and keyboard fallback second.
    """

    try:

        text = str(text)

        if not text:

            return "Nothing to type."


        controller.log(
            f"Typing started: {text}"
        )


        # ----------------------------------------------------
        # Small delay so target window gets focus
        # ----------------------------------------------------

        await asyncio.sleep(
            0.20
        )


        # ----------------------------------------------------
        # Try reliable clipboard typing
        # ----------------------------------------------------

        success = await reliable_paste(
            text
        )


        if success:

            controller.log(
                f"Typing completed: {text}"
            )

            return (
                f"Typed successfully: {text}"
            )


        return (
            "I could not type the text."
        )


    except Exception as e:

        controller.log(
            f"Typing error: {e}"
        )

        return (
            f"Text typing failed: {e}"
        )


# ============================================================
# TYPE TEXT SLOW MODE
# ============================================================

@function_tool
async def type_text_slow_tool(
    text: str,
    interval: float = 0.03
):

    """
    Useful when an application does not handle clipboard
    paste correctly.
    """

    try:

        text = str(text)

        if not text:

            return "Nothing to type."

        interval = max(
            0.001,
            min(
                0.2,
                float(interval)
            )
        )

        pyautogui.write(
            text,
            interval=interval
        )

        return (
            "Text typed using slow keyboard mode."
        )

    except Exception as e:

        controller.log(
            f"Slow typing error: {e}"
        )

        return (
            f"Slow typing failed: {e}"
        )


# ============================================================
# PRESS KEY
# ============================================================

@function_tool
async def press_key_tool(
    key: str
):

    try:

        k = controller.key(
            key
        )

        controller.keyboard.press(
            k
        )

        controller.keyboard.release(
            k
        )

        controller.log(
            f"Key pressed: {key}"
        )

        return f"Key {key} pressed."

    except Exception as e:

        controller.log(
            f"Key error: {e}"
        )

        return f"Key error: {e}"


# ============================================================
# HOTKEY
# ============================================================

@function_tool
async def press_hotkey_tool(
    keys: List[str]
):

    pressed = []

    try:

        if not keys:

            return "No keys provided."


        resolved = [
            controller.key(k)
            for k in keys
        ]


        # ----------------------------------------------------
        # Press
        # ----------------------------------------------------

        for k in resolved:

            controller.keyboard.press(
                k
            )

            pressed.append(k)


        # ----------------------------------------------------
        # Small delay
        # ----------------------------------------------------

        await asyncio.sleep(
            0.05
        )


        # ----------------------------------------------------
        # Release in reverse order
        # ----------------------------------------------------

        for k in reversed(
            pressed
        ):

            controller.keyboard.release(
                k
            )


        controller.log(
            "Hotkey: "
            + " + ".join(
                str(x)
                for x in keys
            )
        )

        return (
            "Hotkey pressed: "
            + " + ".join(
                str(x)
                for x in keys
            )
        )


    except Exception as e:

        # ----------------------------------------------------
        # Emergency release
        # ----------------------------------------------------

        for k in reversed(
            pressed
        ):

            try:

                controller.keyboard.release(
                    k
                )

            except Exception:
                pass


        controller.log(
            f"Hotkey error: {e}"
        )

        return f"Hotkey error: {e}"


# ============================================================
# COMMON HOTKEY TOOL
# ============================================================

@function_tool
async def common_hotkey_tool(
    action: str
):

    """
    Common keyboard shortcuts.

    Examples:
        copy
        paste
        cut
        select all
        undo
        redo
        save
        save as
        find
        new
        open
        print
        close
        refresh
        task manager
        screenshot
    """

    try:

        a = str(
            action
        ).lower().strip()


        shortcuts = {

            "copy":
                ["ctrl", "c"],

            "paste":
                ["ctrl", "v"],

            "cut":
                ["ctrl", "x"],

            "select all":
                ["ctrl", "a"],

            "select_all":
                ["ctrl", "a"],

            "undo":
                ["ctrl", "z"],

            "redo":
                ["ctrl", "y"],

            "save":
                ["ctrl", "s"],

            "save as":
                ["ctrl", "shift", "s"],

            "find":
                ["ctrl", "f"],

            "new":
                ["ctrl", "n"],

            "new window":
                ["ctrl", "n"],

            "new tab":
                ["ctrl", "t"],

            "close tab":
                ["ctrl", "w"],

            "reopen tab":
                ["ctrl", "shift", "t"],

            "refresh":
                ["f5"],

            "hard refresh":
                ["ctrl", "f5"],

            "print":
                ["ctrl", "p"],

            "open":
                ["ctrl", "o"],

            "close":
                ["alt", "f4"],

            "switch window":
                ["alt", "tab"],

            "task manager":
                ["ctrl", "shift", "esc"],

            "file explorer":
                ["win", "e"],

            "settings":
                ["win", "i"],

            "run":
                ["win", "r"],

            "search":
                ["win", "s"],

            "show desktop":
                ["win", "d"],

            "lock":
                ["win", "l"],

            "screenshot":
                ["win", "shift", "s"],

            "clipboard history":
                ["win", "v"],

            "emoji":
                ["win", "."],

            "start menu":
                ["win"],
        }


        if a not in shortcuts:

            return (
                f"Unknown shortcut: {action}"
            )


        keys = shortcuts[a]


        for key in keys:

            controller.keyboard.press(
                controller.key(key)
            )


        await asyncio.sleep(
            0.05
        )


        for key in reversed(keys):

            controller.keyboard.release(
                controller.key(key)
            )


        return (
            f"Shortcut {action} completed."
        )


    except Exception as e:

        return (
            f"Shortcut error: {e}"
        )


# ============================================================
# SWIPE
# ============================================================

@function_tool
async def swipe_gesture_tool(
    direction: str
):

    try:

        w, h = pyautogui.size()

        x = w // 2
        y = h // 2

        d = str(
            direction
        ).lower().strip()


        if d == "up":

            pyautogui.moveTo(
                x,
                y + 200
            )

            pyautogui.dragTo(
                x,
                y - 200,
                0.5
            )


        elif d == "down":

            pyautogui.moveTo(
                x,
                y - 200
            )

            pyautogui.dragTo(
                x,
                y + 200,
                0.5
            )


        elif d == "left":

            pyautogui.moveTo(
                x + 200,
                y
            )

            pyautogui.dragTo(
                x - 200,
                y,
                0.5
            )


        elif d == "right":

            pyautogui.moveTo(
                x - 200,
                y
            )

            pyautogui.dragTo(
                x + 200,
                y,
                0.5
            )


        else:

            return "Invalid swipe direction."


        return "Swipe complete."


    except Exception as e:

        return f"Swipe error: {e}"


# ============================================================
# VOLUME PERCENT
# ============================================================

def set_volume_percent(
    percent: int
):

    percent = max(
        0,
        min(
            100,
            int(percent)
        )
    )

    try:

        from pycaw.pycaw import (
            AudioUtilities,
            IAudioEndpointVolume
        )

        from comtypes import CLSCTX_ALL

        device = (
            AudioUtilities.GetSpeakers()
        )

        interface = device.Activate(
            IAudioEndpointVolume._iid_,
            CLSCTX_ALL,
            None
        )

        volume = interface.QueryInterface(
            IAudioEndpointVolume
        )

        volume.SetMasterVolumeLevelScalar(
            percent / 100.0,
            None
        )

        return True

    except Exception as e:

        controller.log(
            f"Volume percentage error: {e}"
        )

        return False


# ============================================================
# VOLUME CONTROL
# ============================================================

@function_tool
async def control_volume_tool(
    action: str,
    value: int = 5
):

    try:

        a = str(
            action
        ).lower().strip()

        value = max(
            1,
            int(value)
        )


        if a in (
            "up",
            "increase",
            "badhao",
            "raise",
            "louder"
        ):

            pyautogui.press(
                "volumeup",
                presses=value,
                interval=0.03
            )

            return "Volume increased."


        if a in (
            "down",
            "decrease",
            "kam",
            "lower",
            "quieter"
        ):

            pyautogui.press(
                "volumedown",
                presses=value,
                interval=0.03
            )

            return "Volume decreased."


        if a in (
            "mute",
            "silent"
        ):

            pyautogui.press(
                "volumemute"
            )

            return "Volume muted."


        if a == "unmute":

            pyautogui.press(
                "volumemute"
            )

            return "Volume unmuted."


        if a in (
            "set",
            "percent"
        ):

            percent = max(
                0,
                min(
                    100,
                    int(value)
                )
            )

            ok = set_volume_percent(
                percent
            )

            if ok:

                return (
                    f"Volume set to "
                    f"{percent}%."
                )

            return (
                "Could not set exact volume."
            )


        return "Unknown volume action."


    except Exception as e:

        return f"Volume error: {e}"


# ============================================================
# BRIGHTNESS
# ============================================================

def set_brightness(
    percent: int
):

    percent = max(
        0,
        min(
            100,
            int(percent)
        )
    )

    ps = f"""
$b={percent};

Get-CimInstance `
-Namespace root/WMI `
-ClassName WmiMonitorBrightnessMethods |

ForEach-Object {{
    $_.WmiSetBrightness(1,$b)
}}
"""

    try:

        result = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                ps
            ],
            capture_output=True,
            text=True,
            timeout=10
        )

        return (
            result.returncode == 0
        )

    except Exception as e:

        controller.log(
            f"Brightness error: {e}"
        )

        return False


def change_brightness(
    delta: int
):

    ps = """
(Get-CimInstance
-Namespace root/WMI
-ClassName WmiMonitorBrightness).CurrentBrightness
"""

    try:

        result = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                ps
            ],
            capture_output=True,
            text=True,
            timeout=8
        )

        lines = [
            x.strip()
            for x in result.stdout.splitlines()
            if x.strip()
        ]

        if not lines:

            return False

        current = int(
            lines[0]
        )

        new_value = max(
            0,
            min(
                100,
                current + delta
            )
        )

        return set_brightness(
            new_value
        )

    except Exception as e:

        controller.log(
            f"Brightness change error: {e}"
        )

        return False


# ============================================================
# BRIGHTNESS TOOL
# ============================================================

@function_tool
async def control_brightness_tool(
    action: str,
    value: int = 10
):

    try:

        a = str(
            action
        ).lower().strip()

        value = max(
            1,
            int(value)
        )


        if a in (
            "set",
            "percent",
            "brightness"
        ):

            percent = max(
                0,
                min(
                    100,
                    value
                )
            )

            if set_brightness(
                percent
            ):

                return (
                    f"Brightness set to "
                    f"{percent}%."
                )

            return (
                "Windows could not control "
                "this display's brightness."
            )


        if a in (
            "up",
            "increase",
            "badhao",
            "raise"
        ):

            if change_brightness(
                value
            ):

                return "Brightness increased."

            return "Could not change brightness."


        if a in (
            "down",
            "decrease",
            "kam",
            "lower"
        ):

            if change_brightness(
                -value
            ):

                return "Brightness decreased."

            return "Could not change brightness."


        return "Unknown brightness action."


    except Exception as e:

        return f"Brightness error: {e}"


# ============================================================
# WINDOW CONTROL
# ============================================================

@function_tool
async def window_control_tool(
    action: str
):

    try:

        a = str(
            action
        ).lower().strip()


        if a in (
            "minimize",
            "minimise",
            "minimize window",
            "minimise window"
        ):

            pyautogui.hotkey(
                "win",
                "down"
            )

            return "Current window minimized."


        if a in (
            "maximize",
            "maximise",
            "maximize window",
            "maximise window"
        ):

            pyautogui.hotkey(
                "win",
                "up"
            )

            return "Current window maximized."


        if a in (
            "restore",
            "restore window"
        ):

            pyautogui.hotkey(
                "win",
                "up"
            )

            return "Window restored."


        if a in (
            "close",
            "close window",
            "close_window"
        ):

            pyautogui.hotkey(
                "alt",
                "f4"
            )

            return "Current window closed."


        if a in (
            "switch",
            "next",
            "alt_tab",
            "switch window",
            "next window"
        ):

            pyautogui.hotkey(
                "alt",
                "tab"
            )

            return "Switched window."


        if a in (
            "previous",
            "previous window"
        ):

            pyautogui.hotkey(
                "alt",
                "shift",
                "tab"
            )

            return "Switched to previous window."


        if a in (
            "desktop",
            "show_desktop",
            "show desktop",
            "minimize all",
            "minimise all",
            "minimize_all",
            "minimise_all",
            "all windows minimize",
            "minimize all windows"
        ):

            pyautogui.hotkey(
                "win",
                "d"
            )

            return "Desktop shown / all windows minimized."


        if a in (
            "snap left",
            "left window",
            "window left"
        ):

            pyautogui.hotkey(
                "win",
                "left"
            )

            return "Window moved left."


        if a in (
            "snap right",
            "right window",
            "window right"
        ):

            pyautogui.hotkey(
                "win",
                "right"
            )

            return "Window moved right."


        return "Unknown window action."


    except Exception as e:

        return f"Window control error: {e}"


# ============================================================
# OPEN WINDOWS
# ============================================================

@function_tool
async def open_windows_tool(
    target: str
):

    try:

        t = str(
            target
        ).lower().strip()


        commands = {

            "settings":
                "start ms-settings:",

            "wifi":
                "start ms-settings:network-wifi",

            "wi-fi":
                "start ms-settings:network-wifi",

            "bluetooth":
                "start ms-settings:bluetooth",

            "sound":
                "start ms-settings:sound",

            "audio":
                "start ms-settings:sound",

            "display":
                "start ms-settings:display",

            "windows update":
                "start ms-settings:windowsupdate",

            "network":
                "start ms-settings:network",

            "apps":
                "start ms-settings:appsfeatures",

            "personalization":
                "start ms-settings:personalization",

            "privacy":
                "start ms-settings:privacy",

            "accounts":
                "start ms-settings:accounts",

            "task manager":
                "taskmgr",

            "control panel":
                "control",

            "device manager":
                "devmgmt.msc",

            "file explorer":
                "explorer.exe",

            "explorer":
                "explorer.exe",

            "calculator":
                "calc.exe",

            "calc":
                "calc.exe",

            "notepad":
                "notepad.exe",

            "paint":
                "mspaint.exe",

            "terminal":
                "wt.exe",

            "powershell":
                "powershell.exe",

            "cmd":
                "cmd.exe"
        }


        if t in commands:

            controller.run(
                commands[t]
            )

            return f"Opened {target}."


        if os.path.exists(
            target
        ):

            os.startfile(
                target
            )

            return f"Opened {target}."


        pyautogui.hotkey(
            "win",
            "s"
        )

        await asyncio.sleep(
            0.7
        )


        pyperclip.copy(
            target
        )

        pyautogui.hotkey(
            "ctrl",
            "v"
        )

        await asyncio.sleep(
            0.7
        )

        pyautogui.press(
            "enter"
        )

        return (
            f"Searching Windows for {target}."
        )


    except Exception as e:

        return f"Open Windows error: {e}"


# ============================================================
# POWER CONTROL
# ============================================================

@function_tool
async def power_control_tool(
    action: str,
    confirm: bool = False
):

    try:

        a = str(
            action
        ).lower().strip()


        if a in (
            "lock",
            "lock pc",
            "lock_pc",
            "lock computer",
            "lock_computer"
        ):

            result = ctypes.windll.user32.LockWorkStation()

            if result:

                return "PC locked."

            return "Windows could not lock the PC."


        if a in (
            "sleep",
            "sleep pc",
            "sleep computer"
        ):

            controller.run(
                "rundll32.exe "
                "powrprof.dll,SetSuspendState "
                "0,1,0"
            )

            return "PC is going to sleep."


        if a in (
            "restart",
            "reboot"
        ):

            if not confirm:

                return (
                    "Restart requires confirmation. "
                    "Say confirm restart."
                )

            controller.run(
                "shutdown /r /t 5"
            )

            return (
                "Restart scheduled in 5 seconds."
            )


        if a in (
            "shutdown",
            "poweroff",
            "power off"
        ):

            if not confirm:

                return (
                    "Shutdown requires confirmation. "
                    "Say confirm shutdown."
                )

            controller.run(
                "shutdown /s /t 5"
            )

            return (
                "Shutdown scheduled in 5 seconds."
            )


        if a in (
            "cancel shutdown",
            "cancel_shutdown",
            "cancel"
        ):

            controller.run(
                "shutdown /a"
            )

            return (
                "Pending shutdown cancelled."
            )


        if a in (
            "signout",
            "sign out",
            "logoff",
            "logout"
        ):

            if not confirm:

                return (
                    "Sign out requires confirmation. "
                    "Say confirm sign out."
                )

            controller.run(
                "shutdown /l"
            )

            return "Signing out."


        return "Unknown power action."


    except Exception as e:

        return f"Power control error: {e}"


# ============================================================
# FILE CONTROL
# ============================================================

@function_tool
async def file_control_tool(
    action: str,
    path: str,
    destination: str = "",
    new_name: str = ""
):

    try:

        a = str(
            action
        ).lower().strip()


        p = Path(
            os.path.expandvars(
                os.path.expanduser(
                    path
                )
            )
        )


        if a in (
            "open",
            "launch"
        ):

            os.startfile(
                str(p)
            )

            return f"Opened {p}."


        if a in (
            "create_folder",
            "mkdir"
        ):

            p.mkdir(
                parents=True,
                exist_ok=True
            )

            return (
                f"Folder created: {p}"
            )


        if a == "copy":

            if not destination:

                return (
                    "Destination is required."
                )

            d = Path(
                os.path.expandvars(
                    os.path.expanduser(
                        destination
                    )
                )
            )

            if p.is_dir():

                shutil.copytree(
                    p,
                    d,
                    dirs_exist_ok=True
                )

            else:

                shutil.copy2(
                    p,
                    d
                )

            return f"Copied {p}."


        if a == "move":

            if not destination:

                return (
                    "Destination is required."
                )

            shutil.move(
                str(p),
                destination
            )

            return f"Moved {p}."


        if a == "rename":

            if not new_name:

                return (
                    "New name is required."
                )

            p.rename(
                p.parent / new_name
            )

            return (
                f"Renamed to {new_name}."
            )


        if a == "list":

            if not p.exists():

                return (
                    "Path does not exist."
                )

            items = list(
                p.iterdir()
            )[:100]

            if not items:

                return (
                    "Folder is empty."
                )

            return "\n".join(
                str(x)
                for x in items
            )


        if a == "delete":

            try:

                from send2trash import (
                    send2trash
                )

                send2trash(
                    str(p)
                )

                return (
                    "Moved to Recycle Bin."
                )

            except ImportError:

                return (
                    "Install send2trash "
                    "for safe Recycle Bin deletion."
                )


        return "Unknown file action."


    except Exception as e:

        return (
            f"File operation failed: {e}"
        )


# ============================================================
# BROWSER CONTROL
# ============================================================

@function_tool
async def browser_control_tool(
    action: str,
    value: str = ""
):

    try:

        a = str(
            action
        ).lower().strip()


        if a in (
            "open",
            "website",
            "url"
        ):

            url = value.strip()

            if not url.startswith(
                (
                    "http://",
                    "https://"
                )
            ):

                url = (
                    "https://" + url
                )

            webbrowser.open(
                url
            )

            return (
                f"Opened {url}."
            )


        if a in (
            "search",
            "google"
        ):

            url = (
                "https://www.google.com/search?q="
                + urllib.parse.quote(
                    value
                )
            )

            webbrowser.open(
                url
            )

            return (
                f"Searching for {value}."
            )


        if a == "back":

            pyautogui.hotkey(
                "alt",
                "left"
            )


        elif a == "forward":

            pyautogui.hotkey(
                "alt",
                "right"
            )


        elif a == "refresh":

            pyautogui.press(
                "f5"
            )


        elif a in (
            "close_tab",
            "close tab"
        ):

            pyautogui.hotkey(
                "ctrl",
                "w"
            )


        elif a in (
            "new_tab",
            "new tab"
        ):

            pyautogui.hotkey(
                "ctrl",
                "t"
            )


        elif a in (
            "next_tab",
            "next tab"
        ):

            pyautogui.hotkey(
                "ctrl",
                "tab"
            )


        elif a in (
            "previous_tab",
            "previous tab"
        ):

            pyautogui.hotkey(
                "ctrl",
                "shift",
                "tab"
            )


        elif a in (
            "reopen tab",
            "reopen_tab"
        ):

            pyautogui.hotkey(
                "ctrl",
                "shift",
                "t"
            )


        else:

            return "Unknown browser action."


        return (
            f"Browser action {a} completed."
        )


    except Exception as e:

        return f"Browser control error: {e}"


# ============================================================
# CLIPBOARD
# ============================================================

@function_tool
async def clipboard_tool(
    action: str
):

    try:

        a = str(
            action
        ).lower().strip()


        if a == "copy":

            pyautogui.hotkey(
                "ctrl",
                "c"
            )


        elif a == "paste":

            pyautogui.hotkey(
                "ctrl",
                "v"
            )


        elif a in (
            "select_all",
            "select all"
        ):

            pyautogui.hotkey(
                "ctrl",
                "a"
            )


        elif a == "undo":

            pyautogui.hotkey(
                "ctrl",
                "z"
            )


        elif a == "redo":

            pyautogui.hotkey(
                "ctrl",
                "y"
            )


        elif a == "cut":

            pyautogui.hotkey(
                "ctrl",
                "x"
            )


        else:

            return "Unknown clipboard action."


        return f"{a} completed."


    except Exception as e:

        return f"Clipboard error: {e}"


# ============================================================
# SCREENSHOT
# ============================================================

@function_tool
async def screenshot_tool():

    try:

        folder = (
            Path.home()
            / "Pictures"
            / "Maya Screenshots"
        )

        folder.mkdir(
            parents=True,
            exist_ok=True
        )


        file = (
            folder
            / (
                "screenshot_"
                + datetime.now().strftime(
                    "%Y%m%d_%H%M%S"
                )
                + ".png"
            )
        )


        pyautogui.screenshot(
            str(file)
        )


        return (
            f"Screenshot saved to {file}."
        )


    except Exception as e:

        return f"Screenshot error: {e}"


# ============================================================
# SYSTEM INFORMATION
# ============================================================

@function_tool
async def system_info_tool():

    try:

        import psutil

        cpu = psutil.cpu_percent(
            interval=0.5
        )

        ram = (
            psutil.virtual_memory().percent
        )

        disk = (
            psutil.disk_usage(
                os.environ.get(
                    "SystemDrive",
                    "C:"
                ) + "\\"
            ).percent
        )


        return (
            f"CPU {cpu}% | "
            f"RAM {ram}% | "
            f"Disk {disk}%"
        )


    except ImportError:

        return (
            "Install psutil for "
            "system information."
        )


    except Exception as e:

        return (
            f"System information error: {e}"
        )


# ============================================================
# APPLICATION LAUNCHER
# ============================================================

@function_tool
async def launch_app_tool(
    app: str
):

    apps = {

        "chrome":
            "start chrome",

        "google chrome":
            "start chrome",

        "edge":
            "start msedge",

        "microsoft edge":
            "start msedge",

        "notepad":
            "notepad.exe",

        "calculator":
            "calc.exe",

        "calc":
            "calc.exe",

        "paint":
            "mspaint.exe",

        "explorer":
            "explorer.exe",

        "file explorer":
            "explorer.exe",

        "task manager":
            "taskmgr",

        "terminal":
            "wt.exe",

        "windows terminal":
            "wt.exe",

        "powershell":
            "powershell.exe",

        "cmd":
            "cmd.exe"
    }


    app_name = str(
        app
    ).lower().strip()


    cmd = apps.get(
        app_name
    )


    if not cmd:

        return (
            f"No direct launcher "
            f"configured for {app}."
        )


    controller.run(
        cmd
    )


    return (
        f"Launching {app}."
    )


# ============================================================
# WINDOWS SHORTCUTS
# ============================================================

@function_tool
async def windows_shortcut_tool(
    shortcut: str
):

    try:

        s = str(
            shortcut
        ).lower().strip()


        if s in (
            "desktop",
            "show desktop",
            "minimize all",
            "minimise all",
            "minimize_all"
        ):

            pyautogui.hotkey(
                "win",
                "d"
            )

            return (
                "Desktop shown."
            )


        if s in (
            "task manager",
            "task_manager"
        ):

            pyautogui.hotkey(
                "ctrl",
                "shift",
                "esc"
            )

            return (
                "Task Manager opened."
            )


        if s in (
            "file explorer",
            "file_explorer",
            "explorer"
        ):

            pyautogui.hotkey(
                "win",
                "e"
            )

            return (
                "File Explorer opened."
            )


        if s in (
            "settings",
            "windows settings"
        ):

            pyautogui.hotkey(
                "win",
                "i"
            )

            return (
                "Windows Settings opened."
            )


        if s in (
            "run",
            "run dialog"
        ):

            pyautogui.hotkey(
                "win",
                "r"
            )

            return (
                "Run dialog opened."
            )


        if s in (
            "search",
            "windows search"
        ):

            pyautogui.hotkey(
                "win",
                "s"
            )

            return (
                "Windows Search opened."
            )


        if s in (
            "lock",
            "lock pc",
            "lock computer"
        ):

            ctypes.windll.user32.LockWorkStation()

            return (
                "PC locked."
            )


        if s in (
            "notifications",
            "notification center",
            "action center"
        ):

            pyautogui.hotkey(
                "win",
                "n"
            )

            return (
                "Notifications opened."
            )


        if s in (
            "clipboard history",
            "clipboard"
        ):

            pyautogui.hotkey(
                "win",
                "v"
            )

            return (
                "Clipboard history opened."
            )


        if s in (
            "emoji",
            "emoji panel"
        ):

            pyautogui.hotkey(
                "win",
                "."
            )

            return (
                "Emoji panel opened."
            )


        if s in (
            "screenshot",
            "screen snip"
        ):

            pyautogui.hotkey(
                "win",
                "shift",
                "s"
            )

            return (
                "Screenshot tool opened."
            )


        if s in (
            "quick settings",
            "quick settings menu"
        ):

            pyautogui.hotkey(
                "win",
                "a"
            )

            return (
                "Quick Settings opened."
            )


        if s in (
            "start",
            "start menu"
        ):

            pyautogui.press(
                "win"
            )

            return (
                "Start menu opened."
            )


        return (
            "Unknown Windows shortcut."
        )


    except Exception as e:

        return (
            f"Windows shortcut error: {e}"
        )


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    print(
        "MAYA keyboard_mouse_CTRL loaded successfully."
    )