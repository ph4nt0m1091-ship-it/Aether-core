import getpass
import sys

from security.secret_store import (
    SecretStore
)


def main():

    if len(
        sys.argv
    ) != 2:

        print(
            "Usage:"
        )

        print(
            "  python configure_secret.py "
            "<secret_name>"
        )

        return 1

    name = (
        sys.argv[1]
        .strip()
        .lower()
    )

    store = (
        SecretStore()
    )

    print(
        f"Configuring Aether secret: {name}"
    )

    value = getpass.getpass(
        "Secret value "
        "(input hidden): "
    )

    if not value:

        print(
            "No secret was entered."
        )

        return 1

    confirm = getpass.getpass(
        "Enter it again: "
    )

    if value != confirm:

        print(
            "Values did not match."
        )

        return 1

    store.set(
        name,
        value
    )

    print(
        "Secret encrypted and stored."
    )

    print(
        "The secret value was not displayed."
    )

    return 0


if __name__ == "__main__":

    raise SystemExit(
        main()
    )