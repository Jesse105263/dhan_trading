from datetime import datetime, timedelta

from services.database import get_connection
from services.scheduler_models import SchedulerLock


class SchedulerRepository:
    def acquire(
        self,
        lock_name: str,
        owner_token: str,
        acquired_at: datetime,
        ttl_seconds: int,
    ) -> bool:
        expires_at = acquired_at + timedelta(
            seconds=ttl_seconds
        )

        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO scheduler_locks
                    (
                        lock_name,
                        owner_token,
                        acquired_at,
                        heartbeat_at,
                        expires_at
                    )
                    VALUES
                    (%s, %s, %s, %s, %s)
                    ON CONFLICT (lock_name)
                    DO UPDATE SET
                        owner_token = EXCLUDED.owner_token,
                        acquired_at = EXCLUDED.acquired_at,
                        heartbeat_at = EXCLUDED.heartbeat_at,
                        expires_at = EXCLUDED.expires_at
                    WHERE scheduler_locks.expires_at
                        <= EXCLUDED.acquired_at
                    RETURNING owner_token;
                    """,
                    (
                        lock_name,
                        owner_token,
                        acquired_at,
                        acquired_at,
                        expires_at,
                    ),
                )

                result = cursor.fetchone()

            connection.commit()

        return (
            result is not None
            and str(result[0]) == owner_token
        )

    def heartbeat(
        self,
        lock_name: str,
        owner_token: str,
        heartbeat_at: datetime,
        ttl_seconds: int,
    ) -> bool:
        expires_at = heartbeat_at + timedelta(
            seconds=ttl_seconds
        )

        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE scheduler_locks
                    SET
                        heartbeat_at = %s,
                        expires_at = %s
                    WHERE lock_name = %s
                      AND owner_token = %s;
                    """,
                    (
                        heartbeat_at,
                        expires_at,
                        lock_name,
                        owner_token,
                    ),
                )

                updated = cursor.rowcount == 1

            connection.commit()

        return updated

    def release(
        self,
        lock_name: str,
        owner_token: str,
    ) -> bool:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    DELETE FROM scheduler_locks
                    WHERE lock_name = %s
                      AND owner_token = %s;
                    """,
                    (
                        lock_name,
                        owner_token,
                    ),
                )

                deleted = cursor.rowcount == 1

            connection.commit()

        return deleted

    def get(
        self,
        lock_name: str,
    ) -> SchedulerLock | None:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT
                        lock_name,
                        owner_token,
                        acquired_at,
                        heartbeat_at,
                        expires_at
                    FROM scheduler_locks
                    WHERE lock_name = %s;
                    """,
                    (lock_name,),
                )

                result = cursor.fetchone()

        if result is None:
            return None

        return SchedulerLock(
            lock_name=str(result[0]),
            owner_token=str(result[1]),
            acquired_at=result[2],
            heartbeat_at=result[3],
            expires_at=result[4],
        )
