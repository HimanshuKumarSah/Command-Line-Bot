from livekit_main import entrypoint
from livekit.agents import WorkerOptions, cli
import threading
import time

# def background_task():
#     while True:
#         time.sleep(1)


def main():
    # t = threading.Thread(target=background_task, daemon=True)
    # t.start()

    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))

if __name__ == "__main__":
    main()