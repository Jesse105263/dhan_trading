import unittest
from typing import Any

from services.pipeline import Pipeline
from services.stage import Stage


class FakePipelineRunRepository:
    def __init__(self) -> None:
        self.started = False
        self.completed = False
        self.failed = False

    def start_run(
        self,
        run_id,
        started_at,
    ) -> None:
        self.started = True

    def complete_run(
        self,
        run_id,
        completed_at,
    ) -> None:
        self.completed = True

    def fail_run(
        self,
        run_id,
        completed_at,
    ) -> None:
        self.failed = True


class FakeFailureRepository:
    def __init__(self) -> None:
        self.failures = []

    def insert(
        self,
        failure,
    ) -> int:
        self.failures.append(failure)
        return len(self.failures)

    def count_for_run(
        self,
        run_id,
    ) -> int:
        return sum(
            1
            for failure in self.failures
            if failure.run_id == run_id
        )


class SuccessfulStage(Stage):
    def __init__(self) -> None:
        super().__init__(
            "Successful Stage"
        )

    def run(
        self,
        context: dict[str, Any],
    ) -> None:
        context["smoke_test"] = "passed"


class FailingStage(Stage):
    def __init__(
        self,
        message: str = "Expected failure",
    ) -> None:
        super().__init__(
            "Failing Stage"
        )
        self.message = message

    def run(
        self,
        context: dict[str, Any],
    ) -> None:
        raise RuntimeError(
            self.message
        )


class PipelineSmokeTest(
    unittest.TestCase
):
    def test_successful_pipeline(
        self,
    ) -> None:
        run_repository = (
            FakePipelineRunRepository()
        )
        failure_repository = (
            FakeFailureRepository()
        )

        pipeline = Pipeline(
            stages=[SuccessfulStage()],
            run_repository=run_repository,
            failure_repository=(
                failure_repository
            ),
        )

        pipeline.start()

        self.assertTrue(
            run_repository.started
        )
        self.assertTrue(
            run_repository.completed
        )
        self.assertFalse(
            run_repository.failed
        )
        self.assertEqual(
            len(
                failure_repository.failures
            ),
            0,
        )
        self.assertEqual(
            pipeline.context[
                "pipeline_status"
            ],
            "COMPLETED",
        )
        self.assertEqual(
            pipeline.context[
                "smoke_test"
            ],
            "passed",
        )

    def test_failed_pipeline_persists_failure(
        self,
    ) -> None:
        run_repository = (
            FakePipelineRunRepository()
        )
        failure_repository = (
            FakeFailureRepository()
        )

        pipeline = Pipeline(
            stages=[FailingStage()],
            run_repository=run_repository,
            failure_repository=(
                failure_repository
            ),
        )

        with self.assertRaises(
            RuntimeError
        ):
            pipeline.start()

        self.assertTrue(
            run_repository.started
        )
        self.assertFalse(
            run_repository.completed
        )
        self.assertTrue(
            run_repository.failed
        )
        self.assertEqual(
            len(
                failure_repository.failures
            ),
            1,
        )

        failure = (
            failure_repository
            .failures[0]
        )

        self.assertEqual(
            failure.stage_name,
            "Failing Stage",
        )
        self.assertEqual(
            failure.error_type,
            "RuntimeError",
        )
        self.assertFalse(
            failure.retryable
        )
        self.assertEqual(
            pipeline.context[
                "pipeline_status"
            ],
            "FAILED",
        )

    def test_failure_message_is_sanitized(
        self,
    ) -> None:
        run_repository = (
            FakePipelineRunRepository()
        )
        failure_repository = (
            FakeFailureRepository()
        )

        pipeline = Pipeline(
            stages=[
                FailingStage(
                    "access-token="
                    "secret-token-value"
                )
            ],
            run_repository=run_repository,
            failure_repository=(
                failure_repository
            ),
        )

        with self.assertRaises(
            RuntimeError
        ):
            pipeline.start()

        stored_message = (
            failure_repository
            .failures[0]
            .error_message
        )

        self.assertNotIn(
            "secret-token-value",
            stored_message,
        )
        self.assertIn(
            "[REDACTED]",
            stored_message,
        )

    def test_timeout_is_retryable(
        self,
    ) -> None:
        class TimeoutStage(Stage):
            def __init__(self) -> None:
                super().__init__(
                    "Timeout Stage"
                )

            def run(
                self,
                context: dict[str, Any],
            ) -> None:
                raise TimeoutError(
                    "Request timeout"
                )

        run_repository = (
            FakePipelineRunRepository()
        )
        failure_repository = (
            FakeFailureRepository()
        )

        pipeline = Pipeline(
            stages=[TimeoutStage()],
            run_repository=run_repository,
            failure_repository=(
                failure_repository
            ),
        )

        with self.assertRaises(
            TimeoutError
        ):
            pipeline.start()

        self.assertTrue(
            failure_repository
            .failures[0]
            .retryable
        )


if __name__ == "__main__":
    unittest.main()