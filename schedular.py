import subprocess
import sys
import time
from datetime import datetime
INTERVAL = 2 * 60 * 60  
def run_main():
    print("=" * 60)
    print(f"Starting run at {datetime.now():%Y-%m-%d %H:%M:%S}")

    try:
        subprocess.run(
            [sys.executable, "main.py"],
            check=True
        )
        print("Run completed successfully.")

    except subprocess.CalledProcessError as e:
        print(f"Run failed with exit code {e.returncode}")

    except Exception as e:
        print(f"Unexpected error: {e}")

    print("=" * 60)
    print()


def main():
    print("Scheduler started.")
    print("Running main.py every 2 hours...\n")

    while True:
        run_main()

        print("Sleeping for 2 hours...\n")
        time.sleep(INTERVAL)


if __name__ == "__main__":
    main()