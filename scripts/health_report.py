from services.database import get_connection


def main() -> None:
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    run_id,
                    status,
                    started_at,
                    completed_at,
                    snapshot_count,
                    feature_count
                FROM pipeline_runs
                ORDER BY started_at DESC
                LIMIT 1;
                """
            )

            latest_run = cursor.fetchone()

            if latest_run is None:
                print("No pipeline runs found.")
                return

            cursor.execute(
                """
                SELECT
                    stage_name,
                    status,
                    duration_ms,
                    records_requested,
                    records_received,
                    records_written,
                    data_freshness_seconds
                FROM stage_metrics
                WHERE run_id = %s
                ORDER BY started_at;
                """,
                (latest_run[0],),
            )

            metrics = cursor.fetchall()

            cursor.execute(
                """
                SELECT COUNT(*)
                FROM pipeline_failures
                WHERE run_id = %s;
                """,
                (latest_run[0],),
            )

            failure_result = cursor.fetchone()

    failure_count = (
        int(failure_result[0])
        if failure_result is not None
        else 0
    )

    print("DHAN PLATFORM HEALTH REPORT")
    print("=" * 60)
    print(f"Run ID: {latest_run[0]}")
    print(f"Status: {latest_run[1]}")
    print(f"Started: {latest_run[2]}")
    print(f"Completed: {latest_run[3]}")
    print(f"Snapshots: {latest_run[4]}")
    print(f"Features: {latest_run[5]}")
    print(f"Failures: {failure_count}")
    print("")
    print("Stage Metrics")
    print("-" * 60)

    for metric in metrics:
        print(
            f"{metric[0]} | "
            f"status={metric[1]} | "
            f"duration_ms={metric[2]} | "
            f"requested={metric[3]} | "
            f"received={metric[4]} | "
            f"written={metric[5]} | "
            f"freshness_seconds={metric[6]}"
        )


if __name__ == "__main__":
    main()