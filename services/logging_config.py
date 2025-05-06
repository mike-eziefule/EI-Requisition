from loguru import logger

def setup_logging():
    logger.add(
        "logs/requisition.log",
        rotation="1 MB",
        retention="7 days",
        level="INFO",
        format="{time} - {level} - {message}",
    )
