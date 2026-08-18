import time

from brain import Brain
from memory import Memory

VERSION = "0.9.1 Intent Analyzer"


def boot():

    print("=" * 50)
    print("                AETHER")
    print(f"              Version {VERSION}")
    print("=" * 50)

    print("\nInitializing Core...")
    time.sleep(0.5)

    print("Loading Memory...")
    time.sleep(0.5)

    print("Loading Skills...")
    time.sleep(0.5)

    print("Checking Systems...")
    time.sleep(0.5)

    print("\n✓ Core Online")
    print("\nGood evening.")
    print("I'm Aether.")
    print("Ready to build something amazing.\n")


def main():

    boot()

    memory = Memory()

    brain = Brain(
        memory
    )

    brain.skill_manager.start_background_services()

    try:

        while True:

            user_input = input(
                "You: "
            )

            if (
                user_input.lower()
                == "exit"
            ):

                print(
                    "Aether: Goodbye."
                )

                break

            memory.remember(
                user_input
            )

            response = brain.think(
                user_input
            )

            print(
                response
            )

    finally:

        brain.skill_manager.stop_background_services()


if __name__ == "__main__":

    main()