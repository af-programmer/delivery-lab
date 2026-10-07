"""delivery-lab - Power Tech 2026.

This is the project file we started in the first class.
If your own app.py is different, that is fine - keep yours.
"""

APP_NAME = "delivery-lab"
VERSION = "dev"


def health_payload():
    """Return the health status of the service."""
    return {
        "status": "ok",
        "version": "dev",
    }


def greet(name):
    """Return a greeting for the given name."""
    return f"Hello, {name}! Welcome to {APP_NAME}."


def main():
    print(greet("Power Tech"))


if __name__ == "__main__":
    main()