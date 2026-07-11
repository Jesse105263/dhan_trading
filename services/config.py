import os
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class PostgresSettings:
    host: str
    port: int
    dbname: str
    user: str
    password: str


@dataclass(frozen=True)
class RedisSettings:
    host: str
    port: int
    db: int


@dataclass(frozen=True)
class DhanSettings:
    client_id: str
    access_token: str


def _required_environment_variable(name: str) -> str:
    value = os.getenv(name, "").strip()

    if not value:
        raise RuntimeError(
            f"Missing required environment variable: {name}"
        )

    return value


POSTGRES_SETTINGS = PostgresSettings(
    host=_required_environment_variable("POSTGRES_HOST"),
    port=int(_required_environment_variable("POSTGRES_PORT")),
    dbname=_required_environment_variable("POSTGRES_DB"),
    user=_required_environment_variable("POSTGRES_USER"),
    password=_required_environment_variable("POSTGRES_PASSWORD"),
)

REDIS_SETTINGS = RedisSettings(
    host=os.getenv("REDIS_HOST", "localhost").strip(),
    port=int(os.getenv("REDIS_PORT", "6379")),
    db=int(os.getenv("REDIS_DB", "0")),
)

DHAN_SETTINGS = DhanSettings(
    client_id=_required_environment_variable("DHAN_CLIENT_ID"),
    access_token=_required_environment_variable("DHAN_ACCESS_TOKEN"),
)

POSTGRES = {
    "host": POSTGRES_SETTINGS.host,
    "port": POSTGRES_SETTINGS.port,
    "dbname": POSTGRES_SETTINGS.dbname,
    "user": POSTGRES_SETTINGS.user,
    "password": POSTGRES_SETTINGS.password,
}