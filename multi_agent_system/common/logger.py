import logging
import structlog
import sys
from pythonjsonlogger import jsonlogger
from common.settings import settings


def setup_logging():
    """Configure structured logging for production."""
    
    if settings.LOG_FORMAT == "json":
        # JSON logging for production
        logHandler = logging.StreamHandler(sys.stdout)
        formatter = jsonlogger.JsonFormatter()
        logHandler.setFormatter(formatter)
        
        logger = logging.getLogger()
        logger.addHandler(logHandler)
        logger.setLevel(settings.LOG_LEVEL)
    else:
        # Plain text logging for development
        logging.basicConfig(
            level=settings.LOG_LEVEL,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )

    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str):
    """Get a structlog logger instance."""
    return structlog.get_logger(name)
