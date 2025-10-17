"""
File Logging Configuration
Creates clean, readable log files for debugging
"""
import logging
import sys
from pathlib import Path
from datetime import datetime
from logging.handlers import RotatingFileHandler
import structlog


def setup_file_logging():
    """
    Set up file logging with rotation and clean formatting
    """
    # Create logs directory
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Create timestamped log file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"podcast_generation_{timestamp}.log"
    
    # Keep only last 5 log files
    cleanup_old_logs(log_dir, keep=5)
    
    # Configure file handler with rotation
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=3
    )
    file_handler.setLevel(logging.INFO)
    
    # Create clean formatter
    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)-30s | %(message)s',
        datefmt='%H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    
    # Add to root logger
    root_logger = logging.getLogger()
    root_logger.addHandler(file_handler)
    
    # Also configure structlog to write to file
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
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    print(f"[LOGGING] Logging to: {log_file.absolute()}")
    print(f"[LOGGING] View logs at: {log_dir.absolute()}")
    
    return log_file


def cleanup_old_logs(log_dir: Path, keep: int = 5):
    """
    Keep only the most recent log files
    """
    log_files = sorted(
        log_dir.glob("podcast_generation_*.log"),
        key=lambda p: p.stat().st_mtime,
        reverse=True
    )
    
    # Delete old files
    for old_file in log_files[keep:]:
        try:
            old_file.unlink()
            print(f"[CLEANUP] Cleaned up old log: {old_file.name}")
        except Exception as e:
            print(f"[WARNING] Could not delete {old_file.name}: {e}")


def log_section(title: str):
    """
    Log a clear section separator
    """
    logger = structlog.get_logger()
    separator = "=" * 80
    logger.info(separator)
    logger.info(f"  {title}")
    logger.info(separator)


def log_step(step_num: int, description: str, status: str = "START"):
    """
    Log a clear step in the process
    """
    logger = structlog.get_logger()
    logger.info(f"STEP {step_num}: {description} [{status}]")
