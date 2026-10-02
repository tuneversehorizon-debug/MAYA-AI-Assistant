import os
import subprocess
import logging
import sys
import asyncio
import webbrowser
import urllib.parse

from fuzzywuzzy import process

try:
    import pyautogui
except ImportError:
    pyautogui = None

try:
    from livekit.agents import function_tool
except ImportError:
    def function_tool(func):
        return func

try:
    import win32gui
    import win32con
except ImportError:
    win32gui = None
    win32con = None

try:
    import pygetwindow as gw
except ImportError:
    gw = None


# ============================================================
# LOGGING
# ============================================================

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================
# APPLICATION MAP
# ============================================================

APP_MAPPINGS = {
    "notepad": "notepad.exe",
    "calculator": "calc.exe",
    "calc": "calc.exe",

    "cmd": "cmd.exe",
    "command prompt": "cmd.exe",

    "terminal": "wt.exe",
    "windows terminal": "wt.exe",

    "powershell": "powershell.exe",
    "power shell": "powershell.exe",

    "control panel": "control.exe",
    "task manager": "taskmgr.exe",
    "paint": "mspaint.exe",
    "wordpad": "write.exe",

    "snipping tool": "snippingtool.exe",
    "screenshot": "snippingtool.exe",

    "explorer": "explorer.exe",
    "file explorer": "explorer.exe",

    "device manager": "devmgmt.msc",
    "disk management": "diskmgmt.msc",
    "resource monitor": "resmon.exe",
    "event viewer": "eventvwr.msc",
    "registry editor": "regedit.exe",
    "services": "services.msc",

    "camera": "microsoft.windows.camera:",
    "store": "ms-windows-store:",
    "microsoft store": "ms-windows-store:",
    "photos": "ms-photos:",
    "clock": "ms-clock:",
    "alarm": "ms-clock:",
    "stopwatch": "ms-clock:",

    "calendar": "outlookcal:",
    "mail": "outlookmail:",
    "weather": "bingweather:",
    "maps": "bingmaps:",
    "voice recorder": "soundrecorder:",
    "sticky notes": "stikynot.exe",

    "settings": "ms-settings:",
    "wifi settings": "ms-settings:network-wifi",
    "bluetooth settings": "ms-settings:bluetooth",
    "display settings": "ms-settings:display",
    "sound settings": "ms-settings:sound",
    "battery settings": "ms-settings:powersleep",
    "storage settings": "ms-settings:storagesense",
    "windows update": "ms-settings:windowsupdate",
    "apps settings": "ms-settings:appsfeatures",

    "chrome": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "google chrome": r"C:\Program Files\Google\Chrome\Application\chrome.exe",

    "edge": "msedge.exe",
    "microsoft edge": "msedge.exe",

    "brave": "brave.exe",
    "firefox": "firefox.exe",

    "vs code": r"C:\Users\Meg Electronics\AppData\Local\Programs\Microsoft VS Code\Code.exe",
    "vscode": r"C:\Users\Meg Electronics\AppData\Local\Programs\Microsoft VS Code\Code.exe",

    "postman": r"C:\Users\Meg Electronics\AppData\Local\Postman\Postman.exe",

    "git bash": r"C:\Program Files\Git\git-bash.exe",

    "vlc": r"C:\Program Files\VideoLAN\VLC\vlc.exe",
    "vlc player": r"C:\Program Files\VideoLAN\VLC\vlc.exe",

    "spotify": "spotify:",

    "whatsapp": "https://web.whatsapp.com/",
    "telegram": "telegram:",
    "discord": "discord:",
    "messenger": "https://www.messenger.com/",
    "instagram": "https://www.instagram.com/",
    "snapchat": "https://web.snapchat.com/",

    "youtube": "https://www.youtube.com/",
    "facebook": "https://www.facebook.com/",
    "twitter": "https://x.com/",
    "x": "https://x.com/",
    "linkedin": "https://www.linkedin.com/",
    "gmail": "https://mail.google.com/",
}


# ============================================================
# LAUNCH HELPER
# ============================================================

async def launch_target(target: str) -> bool:
    try:

        if target.startswith(("http://", "https://")):
            await asyncio.to_thread(
                webbrowser.open,
                target
            )
            return True

        if target.endswith(":") or target.startswith("ms-"):
            subprocess.Popen(
                ["cmd", "/c", "start", "", target],
                shell=False
            )
            return True

        if os.path.exists(target):
            subprocess.Popen(
                [target],
                shell=False
            )
            return True

        subprocess.Popen(
            target,
            shell=True
        )

        return True

    except Exception as e:
        logger.error(f"Launch error: {e}")
        return False


# ============================================================
# WINDOW FOCUS
# ============================================================

async def focus_window(title_keyword: str) -> bool:

    if not gw:
        return False

    await asyncio.sleep(1.5)

    title_keyword = title_keyword.lower().strip()

    try:

        for window in gw.getAllWindows():

            title = (window.title or "").lower()

            if title_keyword in title:

                try:

                    if window.isMinimized:
                        window.restore()

                    window.activate()

                    return True

                except Exception:
                    pass

    except Exception as e:

        logger.warning(
            f"Window focus error: {e}"
        )

    return False


# ============================================================
# FILE / FOLDER INDEX
# ============================================================

async def index_items(base_dirs):

    item_index = []

    for base_dir in base_dirs:

        if not os.path.exists(base_dir):
            continue

        try:

            for root, dirs, files in os.walk(base_dir):

                for d in dirs:

                    item_index.append({
                        "name": d,
                        "path": os.path.join(root, d),
                        "type": "folder"
                    })

                for f in files:

                    item_index.append({
                        "name": f,
                        "path": os.path.join(root, f),
                        "type": "file"
                    })

        except Exception as e:

            logger.warning(
                f"Indexing error: {e}"
            )

    logger.info(
        f"Indexed {len(item_index)} items."
    )

    return item_index


async def search_item(
    query,
    index,
    item_type
):

    filtered = [
        item
        for item in index
        if item["type"] == item_type
    ]

    choices = [
        item["name"]
        for item in filtered
    ]

    if not choices:
        return None

    try:

        result = process.extractOne(
            query,
            choices
        )

        if not result:
            return None

        best_match, score = result

        logger.info(
            f"Matched '{query}' -> "
            f"'{best_match}' ({score})"
        )

        if score >= 70:

            for item in filtered:

                if item["name"] == best_match:
                    return item

    except Exception as e:

        logger.warning(
            f"Search error: {e}"
        )

    return None


# ============================================================
# FILE ACTIONS
# ============================================================

async def open_folder(path):

    try:

        if not os.path.exists(path):
            return

        os.startfile(path)

        await asyncio.sleep(1)

        await focus_window(
            os.path.basename(path)
        )

    except Exception as e:

        logger.error(
            f"Folder open error: {e}"
        )


async def play_file(path):

    try:

        if not os.path.exists(path):
            return

        os.startfile(path)

        await asyncio.sleep(1)

        await focus_window(
            os.path.basename(path)
        )

    except Exception as e:

        logger.error(
            f"File open error: {e}"
        )


async def create_folder(path):

    try:

        os.makedirs(
            path,
            exist_ok=True
        )

        return (
            f"Folder create ho gaya: {path}"
        )

    except Exception as e:

        return (
            f"Folder create nahi hua: {e}"
        )


async def rename_item(
    old_path,
    new_path
):

    try:

        os.rename(
            old_path,
            new_path
        )

        return (
            f"Naam change kar diya: {new_path}"
        )

    except Exception as e:

        return (
            f"Rename fail: {e}"
        )


async def delete_item(path):

    try:

        if os.path.isdir(path):
            os.rmdir(path)

        else:
            os.remove(path)

        return (
            f"Deleted: {path}"
        )

    except Exception as e:

        return (
            f"Delete fail: {e}"
        )


# ============================================================
# OPEN APPLICATION
# ============================================================

@function_tool
async def open(app_title: str) -> str:

    try:

        app_title = (
            app_title
            .lower()
            .strip()
        )

        remove_words = [
            "open",
            "khol",
            "kholna",
            "khol do",
            "launch",
            "start",
            "app",
            "application"
        ]

        for word in remove_words:

            app_title = app_title.replace(
                word,
                ""
            )

        app_title = app_title.strip()

        target = APP_MAPPINGS.get(
            app_title
        )

        if not target:

            choices = list(
                APP_MAPPINGS.keys()
            )

            result = process.extractOne(
                app_title,
                choices
            )

            if result:

                best_match, score = result

                if score >= 80:

                    target = APP_MAPPINGS[
                        best_match
                    ]

                    app_title = best_match

        if not target:

            target = app_title

        logger.info(
            f"Opening: {app_title} -> {target}"
        )

        success = await launch_target(
            target
        )

        if not success:

            return (
                f"App open nahi ho paya: "
                f"{app_title}"
            )

        await focus_window(
            app_title
        )

        return (
            f"App open kar diya: "
            f"{app_title}"
        )

    except Exception as e:

        logger.exception(
            "Open tool error"
        )

        return (
            f"App open karte waqt error: {e}"
        )


# ============================================================
# CLOSE APPLICATION
# ============================================================

@function_tool
async def close(window_title: str) -> str:

    if not win32gui:

        return (
            "pywin32 install nahi hai."
        )

    try:

        keyword = (
            window_title
            .lower()
            .strip()
        )

        closed = False

        def enum_handler(
            hwnd,
            _
        ):

            nonlocal closed

            if not win32gui.IsWindowVisible(
                hwnd
            ):
                return

            title = (
                win32gui.GetWindowText(hwnd)
                or ""
            )

            if keyword in title.lower():

                win32gui.PostMessage(
                    hwnd,
                    win32con.WM_CLOSE,
                    0,
                    0
                )

                closed = True

        win32gui.EnumWindows(
            enum_handler,
            None
        )

        if closed:

            return (
                f"{window_title} "
                f"band kar diya."
            )

        return (
            f"{window_title} ki "
            f"window nahi mili."
        )

    except Exception as e:

        return (
            f"Window close error: {e}"
        )


# ============================================================
# FILE / FOLDER COMMAND
# ============================================================

@function_tool
async def folder_file(
    command: str
) -> str:

    try:

        folders_to_index = [
            "D:/"
        ]

        index = await index_items(
            folders_to_index
        )

        command_lower = (
            command
            .lower()
            .strip()
        )

        if "create folder" in command_lower:

            folder_name = (
                command_lower
                .replace(
                    "create folder",
                    ""
                )
                .strip()
            )

            if not folder_name:
                return (
                    "Folder ka naam batao."
                )

            path = os.path.join(
                "D:/",
                folder_name
            )

            return await create_folder(
                path
            )

        if "rename" in command_lower:

            parts = (
                command_lower
                .replace(
                    "rename",
                    "",
                    1
                )
                .strip()
                .split(
                    " to ",
                    1
                )
            )

            if len(parts) == 2:

                old_name = parts[0].strip()
                new_name = parts[1].strip()

                item = (
                    await search_item(
                        old_name,
                        index,
                        "folder"
                    )
                    or
                    await search_item(
                        old_name,
                        index,
                        "file"
                    )
                )

                if item:

                    new_path = os.path.join(
                        os.path.dirname(
                            item["path"]
                        ),
                        new_name
                    )

                    return await rename_item(
                        item["path"],
                        new_path
                    )

            return (
                "Rename command valid nahi hai."
            )

        if "delete" in command_lower:

            item = (
                await search_item(
                    command,
                    index,
                    "folder"
                )
                or
                await search_item(
                    command,
                    index,
                    "file"
                )
            )

            if item:

                return await delete_item(
                    item["path"]
                )

            return (
                "Delete karne ke liye "
                "item nahi mila."
            )

        if (
            "folder" in command_lower
            or
            "open folder" in command_lower
        ):

            item = await search_item(
                command,
                index,
                "folder"
            )

            if item:

                await open_folder(
                    item["path"]
                )

                return (
                    f"Folder opened: "
                    f"{item['name']}"
                )

            return "Folder nahi mila."

        item = await search_item(
            command,
            index,
            "file"
        )

        if item:

            await play_file(
                item["path"]
            )

            return (
                f"File opened: "
                f"{item['name']}"
            )

        return (
            "Kuch bhi match nahi hua."
        )

    except Exception as e:

        logger.exception(
            "folder_file error"
        )

        return (
            f"File/folder command error: {e}"
        )


# ============================================================
# GOOGLE SEARCH
# ============================================================

@function_tool
async def search_google(
    query: str
) -> str:

    try:

        query = query.strip()

        encoded_query = (
            urllib.parse.quote(query)
        )

        search_url = (
            "https://www.google.com/search?q="
            + encoded_query
        )

        await asyncio.to_thread(
            webbrowser.open,
            search_url
        )

        return (
            f"Google par '{query}' "
            f"search kar diya."
        )

    except Exception as e:

        return (
            f"Google search fail: {e}"
        )


# ============================================================
# OPEN WEBSITE
# ============================================================

@function_tool
async def open_website(
    url: str
) -> str:

    try:

        url = url.strip()

        if not url.startswith(
            (
                "http://",
                "https://"
            )
        ):

            url = (
                "https://"
                + url
            )

        await asyncio.to_thread(
            webbrowser.open,
            url
        )

        return (
            f"Website open ho gayi: {url}"
        )

    except Exception as e:

        return (
            f"Website open nahi hui: {e}"
        )


# ============================================================
# BROWSER CONTROL
# ============================================================

@function_tool
async def control_browser(
    action: str
) -> str:

    if not pyautogui:

        return (
            "pyautogui installed nahi hai."
        )

    try:

        action = (
            action
            .lower()
            .strip()
        )

        if (
            "new" in action
            or
            "new tab" in action
            or
            "open tab" in action
        ):

            pyautogui.hotkey(
                "ctrl",
                "t"
            )

            return "Naya tab khol diya."

        if (
            "close" in action
            or
            "band" in action
        ):

            pyautogui.hotkey(
                "ctrl",
                "w"
            )

            return "Current tab band kar diya."

        if (
            "down" in action
            or
            "neeche" in action
        ):

            pyautogui.scroll(-6)

            return (
                "Page neeche scroll kar diya."
            )

        if (
            "up" in action
            or
            "upar" in action
        ):

            pyautogui.scroll(6)

            return (
                "Page upar scroll kar diya."
            )

        if (
            "back" in action
            or
            "piche" in action
        ):

            pyautogui.hotkey(
                "alt",
                "left"
            )

            return (
                "Previous page par chale gaye."
            )

        return (
            f"Unknown browser action: {action}"
        )

    except Exception as e:

        return (
            f"Browser control error: {e}"
        )


# ============================================================
# WHATSAPP
# ============================================================

@function_tool
async def send_whatsapp_message(
    contact_name: str,
    message: str
) -> str:

    if not pyautogui:

        return (
            "pyautogui installed nahi hai."
        )

    try:

        contact_name = str(
            contact_name
        ).strip()

        message = str(
            message
        ).strip()

        if not contact_name:

            return (
                "Contact name missing hai."
            )

        if not message:

            return (
                "Message empty hai."
            )

        await asyncio.to_thread(
            webbrowser.open,
            "https://web.whatsapp.com/"
        )

        await asyncio.sleep(8)

        pyautogui.hotkey(
            "ctrl",
            "alt",
            "/"
        )

        await asyncio.sleep(2)

        pyautogui.write(
            contact_name,
            interval=0.03
        )

        await asyncio.sleep(2)

        pyautogui.press(
            "enter"
        )

        await asyncio.sleep(2)

        pyautogui.write(
            message,
            interval=0.02
        )

        await asyncio.sleep(0.5)

        pyautogui.press(
            "enter"
        )

        return (
            f"WhatsApp par "
            f"{contact_name} ko message bhej diya."
        )

    except Exception as e:

        logger.exception(
            "WhatsApp error"
        )

        return (
            f"WhatsApp error: {e}"
        )


# ============================================================
# MESSENGER
# ============================================================

@function_tool
async def send_messenger_message(
    contact_name: str,
    message: str
) -> str:

    if not pyautogui:

        return (
            "pyautogui installed nahi hai."
        )

    try:

        await asyncio.to_thread(
            webbrowser.open,
            "https://www.messenger.com/"
        )

        await asyncio.sleep(7)

        pyautogui.hotkey(
            "ctrl",
            "k"
        )

        await asyncio.sleep(1)

        pyautogui.write(
            str(contact_name),
            interval=0.03
        )

        await asyncio.sleep(2)

        pyautogui.press(
            "enter"
        )

        await asyncio.sleep(2)

        pyautogui.write(
            str(message),
            interval=0.02
        )

        await asyncio.sleep(0.5)

        pyautogui.press(
            "enter"
        )

        return (
            f"Messenger par "
            f"{contact_name} ko message bhej diya."
        )

    except Exception as e:

        return (
            f"Messenger error: {e}"
        )


# ============================================================
# SNAPCHAT
# ============================================================

@function_tool
async def send_snapchat_message(
    contact_name: str,
    message: str
) -> str:

    if not pyautogui:

        return (
            "pyautogui installed nahi hai."
        )

    try:

        await asyncio.to_thread(
            webbrowser.open,
            "https://web.snapchat.com/"
        )

        await asyncio.sleep(7)

        pyautogui.hotkey(
            "ctrl",
            "k"
        )

        await asyncio.sleep(1)

        pyautogui.write(
            str(contact_name),
            interval=0.03
        )

        await asyncio.sleep(2)

        pyautogui.press(
            "enter"
        )

        await asyncio.sleep(2)

        pyautogui.write(
            str(message),
            interval=0.02
        )

        await asyncio.sleep(0.5)

        pyautogui.press(
            "enter"
        )

        return (
            f"Snapchat par "
            f"{contact_name} ko message bhej diya."
        )

    except Exception as e:

        return (
            f"Snapchat error: {e}"
        )