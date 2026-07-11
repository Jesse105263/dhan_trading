from app.logging_config import configure_logging
from services.production_pipeline import (
    build_production_pipeline,
)


def main() -> None:
    configure_logging()
    pipeline = build_production_pipeline()
    pipeline.start()


if __name__ == "__main__":
    main()
