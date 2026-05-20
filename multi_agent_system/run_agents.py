import signal
import subprocess
import sys
import time
import os

import asyncio

from services.kafka_service import ensure_topics
from common.utils import retry_async


AGENT_MODULES = [
    "agents.classification_agent",
    "agents.billing_agent",
    "agents.tech_agent",
    "agents.audit_agent",
    "agents.escalation_agent",
]


def main() -> int:
    processes: list[subprocess.Popen] = []

    def shutdown(*_args):
        print("\nStopping agent processes...")
        for process in processes:
            if process.poll() is None:
                process.terminate()
        for process in processes:
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
        return

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    python = sys.executable
    print(f"Using Python: {python}")

    child_env = os.environ.copy()
    child_env.setdefault("KAFKA_BOOTSTRAP", "localhost:29092")

    asyncio.run(retry_async(ensure_topics, retries=10, delay=2.0, bootstrap_servers=child_env["KAFKA_BOOTSTRAP"]))

    for module in AGENT_MODULES:
        print(f"Starting {module}...")
        process = subprocess.Popen([python, "-m", module], env=child_env)
        processes.append(process)

    try:
        while True:
            exited = [p for p in processes if p.poll() is not None]
            if exited:
                print("One or more agent processes exited. Shutting down remaining processes.")
                shutdown()
                return 1
            time.sleep(1)
    except KeyboardInterrupt:
        shutdown()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
