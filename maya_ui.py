"""
maya_ui.py
"""

import os
import sys
import threading
import subprocess
import webview
import requests

# Set API Key directly
RAW_API_KEY = "AQ.Ab8RN6ICNf4RS5bko8FJKWUZKtbjBFQf5l4aDZlmHikBkD1OKg"

AGENT_CMD = [sys.executable, "-u", "agent.py", "console"]
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
agent_process = None


class Api:
    """Exposed to JavaScript as window.pywebview.api"""

    def ask_maya(self, query: str) -> str:
        """Handles text input sent from HUD UI using direct REST API."""
        if not query or not query.strip():
            return "Please enter a valid message."

        # Fixed REST endpoint using standard v1 version and stable gemini-1.5-flash model
        url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={RAW_API_KEY}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [{
                "parts": [{"text": query}]
            }]
        }

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            res_json = response.json()

            if response.status_code == 200:
                # Extract clean response text
                return res_json['candidates'][0]['content']['parts'][0]['text']
            else:
                error_msg = res_json.get('error', {}).get('message', 'Unknown API Error')
                return f"Google API Error: {error_msg}"
        except Exception as e:
            return f"Network Error: {str(e)}"


def stream_agent_output(window):
    global agent_process
    if agent_process is None or agent_process.stdout is None:
        return

    for raw_line in iter(agent_process.stdout.readline, ""):
        if not raw_line:
            break
        line = raw_line.rstrip()
        print(line)

        if not line.strip():
            continue

        if line.startswith("MAYA_CHAT::"):
            parts = line.split("::", 2)
            if len(parts) == 3:
                _, role, text = parts
                safe_role = role.replace("\\", "\\\\").replace("'", "\\'")
                safe_text = text.replace("\\", "\\\\").replace("'", "\\'")
                js = f"window.addMayaChat && window.addMayaChat('{safe_role}', '{safe_text}');"
            else:
                continue
        else:
            safe = line.replace("\\", "\\\\").replace("'", "\\'")
            js = f"window.updateMayaStatus && window.updateMayaStatus('{safe}');"

        try:
            window.evaluate_js(js)
        except Exception:
            pass


def start_agent():
    global agent_process
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"

    agent_process = subprocess.Popen(
        AGENT_CMD,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        stdin=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1,
        cwd=BASE_DIR,
        env=env,
    )


def main():
    html_path = os.path.join(BASE_DIR, "maya_ui.html")
    api = Api()

    start_agent()

    window = webview.create_window(
        title="MAYA",
        url=html_path,
        js_api=api,
        width=1280,
        height=800,
        min_size=(900, 620),
        background_color="#050810",
        easy_drag=True,
    )

    threading.Thread(target=stream_agent_output, args=(window,), daemon=True).start()
    webview.start(debug=False)

    if agent_process is not None and agent_process.poll() is None:
        agent_process.terminate()


if __name__ == "__main__":
    main()