import os
os.environ["LIVEKIT_DISABLE_LOCAL_INFERENCE"] = "1"

from dotenv import load_dotenv

from livekit import agents
from livekit.agents import (
    AgentSession,
    Agent,
    RoomInputOptions,
    TurnHandlingOptions,
)

from livekit.plugins import (
    google,
    noise_cancellation,
    silero,
)

from Jarvis_window_CTRL import (
    open,
    close,
    folder_file,
    search_google,
    open_website,
    control_browser,
    send_whatsapp_message,
    send_messenger_message,
    send_snapchat_message,
)

from Jarvis_prompts import (
    behavior_prompts,
    Reply_prompts,
)

from Jarvis_google_search import (
    google_search,
    get_current_datetime,
)

from jarvis_get_whether import (
    get_weather,
)

from Jarvis_file_opner import (
    Play_file,
)

from keyboard_mouse_CTRL import (
    move_cursor_tool,
    mouse_click_tool,
    scroll_cursor_tool,
    type_text_tool,
    press_key_tool,
    swipe_gesture_tool,
    press_hotkey_tool,
    control_volume_tool,

    # WINDOWS CONTROL
    control_brightness_tool,
    window_control_tool,
    open_windows_tool,
    power_control_tool,

    # FILE CONTROL
    file_control_tool,

    # BROWSER CONTROL
    browser_control_tool,

    # CLIPBOARD
    clipboard_tool,

    # SCREENSHOT
    screenshot_tool,

    # SYSTEM
    system_info_tool,

    # APPLICATION
    launch_app_tool,
)


load_dotenv()


# ============================================================
# MAYA ASSISTANT
# ============================================================

class Assistant(Agent):

    def __init__(self) -> None:

        super().__init__(
            instructions=behavior_prompts,

            tools=[
                # EXISTING JARVIS TOOLS
                send_whatsapp_message,
                send_messenger_message,
                send_snapchat_message,

                search_google,
                open_website,
                control_browser,

                google_search,
                get_current_datetime,
                get_weather,

                open,
                close,
                folder_file,

                Play_file,

                # MOUSE / KEYBOARD
                move_cursor_tool,
                mouse_click_tool,
                scroll_cursor_tool,

                type_text_tool,
                press_key_tool,
                press_hotkey_tool,

                swipe_gesture_tool,

                control_volume_tool,

                # WINDOWS CONTROL
                control_brightness_tool,
                window_control_tool,
                open_windows_tool,
                power_control_tool,

                # FILE CONTROL
                file_control_tool,

                # BROWSER CONTROL
                browser_control_tool,

                # CLIPBOARD
                clipboard_tool,

                # SCREENSHOT
                screenshot_tool,

                # SYSTEM INFORMATION
                system_info_tool,

                # APPLICATION LAUNCHER
                launch_app_tool,
            ],
        )


# ============================================================
# ENTRYPOINT
# ============================================================

async def entrypoint(ctx: agents.JobContext):

    print("")
    print("========================================")
    print("              MAYA AI")
    print("========================================")
    print("Starting Maya...")
    print("")

    # ========================================================
    # VAD (Optimized for Clear Audio)
    # ========================================================

    try:
        vad = silero.VAD.load(
            min_speech_duration=0.20,
            min_silence_duration=0.55,    # Prevents cutting off mid-sentence
            prefix_padding_duration=0.20, # Keeps starting words smooth
        )

        print("[MAYA] VAD loaded successfully.")

    except Exception as e:
        print("[MAYA WARNING] VAD could not be loaded:")
        print(e)
        vad = None


    # ========================================================
    # REALTIME MODEL
    # ========================================================

    try:
        realtime_model = google.beta.realtime.RealtimeModel(
            voice="Aoede",
            instructions=behavior_prompts,
            modalities=["AUDIO"],
            temperature=0.6,
        )

        print("[MAYA] Realtime model loaded successfully.")

    except Exception as e:
        print("")
        print("========================================")
        print("[MAYA ERROR] Realtime model failed")
        print("========================================")
        print(e)
        print("")
        return


    # ========================================================
    # TURN HANDLING
    # ========================================================

    try:
        turn_handling = TurnHandlingOptions(
            endpointing={
                "mode": "fixed",
                "min_delay": 0.50,
                "max_delay": 1.80,
            },
            interruption={
                "enabled": True,
                "mode": "vad",
                "min_duration": 0.50,
                "min_words": 1,
                "false_interruption_timeout": 1.2,
                "resume_false_interruption": True,
                "discard_audio_if_uninterruptible": True,
            },
            preemptive_generation={
                "enabled": True,
                "preemptive_tts": False,
                "max_speech_duration": 10.0,
                "max_retries": 2,
            },
        )

        print("[MAYA] Turn handling configured.")

    except Exception as e:
        print("[MAYA WARNING] Turn handling configuration failed:")
        print(e)
        turn_handling = None


    # ========================================================
    # CREATE SESSION
    # ========================================================

    try:
        session_arguments = {
            "llm": realtime_model,
        }

        if vad is not None:
            session_arguments["vad"] = vad

        if turn_handling is not None:
            session_arguments["turn_handling"] = turn_handling

        session = AgentSession(
            **session_arguments
        )

        print("[MAYA] Agent session created.")

    except Exception as e:
        print("")
        print("========================================")
        print("[MAYA ERROR] Agent session creation failed")
        print("========================================")
        print(e)
        print("")
        return


    # ========================================================
    # START SESSION & CONNECT
    # ========================================================

    try:
        await session.start(
            room=ctx.room,
            agent=Assistant(),
            room_input_options=RoomInputOptions(
                noise_cancellation=noise_cancellation.BVC(), # Noise removal
                video_enabled=False,
            ),
        )

        print("[MAYA] Session started.")

    except Exception as e:
        print("")
        print("========================================")
        print("[MAYA ERROR] Session start failed")
        print("========================================")
        print(e)
        print("")
        return


    try:
        await ctx.connect()
        print("[MAYA] Connected to LiveKit room.")

    except Exception as e:
        print("")
        print("========================================")
        print("[MAYA ERROR] Room connection failed")
        print("========================================")
        print(e)
        print("")
        return


    # ========================================================
    # INITIAL GREETING
    # ========================================================

    try:
        await session.generate_reply(
            instructions=Reply_prompts
        )

        print("")
        print("========================================")
        print("          MAYA IS READY")
        print("          LISTENING...")
        print("========================================")
        print("")

    except Exception as e:
        print("")
        print("[MAYA WARNING] Initial reply failed:")
        print(e)
        print("")
        print("Maya session will continue running.")
        print("")


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    print("")
    print("========================================")
    print("              MAYA AI")
    print("========================================")
    print("LiveKit Agent Console")
    print("Starting...")
    print("")

    try:
        agents.cli.run_app(
            agents.WorkerOptions(
                entrypoint_fnc=entrypoint
            )
        )

    except KeyboardInterrupt:
        print("")
        print("[MAYA] Stopped by user.")
        print("")

    except Exception as e:
        print("")
        print("========================================")
        print("[MAYA FATAL ERROR]")
        print("========================================")
        print(e)
        print("")
        print("[MAYA] Check the error above.")