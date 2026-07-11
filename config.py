import os

from dotenv import load_dotenv


load_dotenv()


CLIENT_ID = os.getenv("DHAN_CLIENT_ID", "").strip()
ACCESS_TOKEN = os.getenv("DHAN_ACCESS_TOKEN", "").strip()


def validate_dhan_credentials() -> None:
    missing: list[str] = []

    if not CLIENT_ID:
        missing.append("DHAN_CLIENT_ID")

    if not ACCESS_TOKEN:
        missing.append("DHAN_ACCESS_TOKEN")

    if missing:
        missing_values = ", ".join(missing)

        raise RuntimeError(
            f"Missing required Dhan environment variables: {missing_values}"
        )