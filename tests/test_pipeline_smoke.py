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


class SuccessfulStage(Stage):
    def __init__(self) -> None:
        super().__init__("Successful Stage")

    def run(
        self,
        context: dict[str, Any],
    ) -> None:
        context["smoke_test"] = "passed"


class FailingStage(Stage):
    def __init__(self) -> None:
        super().__init__("Failing Stage")

    def run(
        self,
        context: dict[str, Any],
    ) -> None:
        raise RuntimeError("Expected failure")


class PipelineSmokeTest(unittest.TestCase):
    def test_successful_pipeline(self) -> None:
        repository = FakePipelineRunRepository()

        pipeline = Pipeline(
            stages=[SuccessfulStage()],
            run_repository=repository,
        )

        pipeline.start()

        self.assertTrue(repository.started)
        self.assertTrue(repository.completed)
        self.assertFalse(repository.failed)
        self.assertEqual(
            pipeline.context["pipeline_status"],
            "COMPLETED",
        )
        self.assertEqual(
            pipeline.context["smoke_test"],
            "passed",
        )

    def test_failed_pipeline(self) -> None:
        repository = FakePipelineRunRepository()

        pipeline = Pipeline(
            stages=[FailingStage()],
            run_repository=repository,
        )

        with self.assertRaises(RuntimeError):
            pipeline.start()

        self.assertTrue(repository.started)
        self.assertFalse(repository.completed)
        self.assertTrue(repository.failed)
        self.assertEqual(
            pipeline.context["pipeline_status"],
            "FAILED",
        )


if __name__ == "__main__":
    unittest.main()