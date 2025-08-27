import logging


def setup_logging() -> None:
    logging.basicConfig(
        filename="log.txt",
        level=logging.INFO,
        format="%(message)s",
        encoding="utf-8",
    )
