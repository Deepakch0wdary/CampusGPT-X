import logging
import sys
from pathlib import Path
from app.core.config import settings

# Resolve paths
BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent
WORKSPACE_ROOT = BACKEND_ROOT.parent.parent
LOG_DIR = WORKSPACE_ROOT / "logs"
LOG_FILE = LOG_DIR / "backend.log"

def setup_logging() -> None:
    """Configures system-wide logging to output to stdout and log file."""
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        print(f"Warning: Could not create log directory {LOG_DIR}: {e}", file=sys.stderr)

    log_level_name = settings.LOG_LEVEL.upper()
    log_level = getattr(logging, log_level_name, logging.INFO)

    # Output handlers
    handlers = [logging.StreamHandler(sys.stdout)]

    if LOG_DIR.exists():
        try:
            handlers.append(logging.FileHandler(LOG_FILE, encoding="utf-8"))
        except Exception as e:
            print(f"Warning: Could not write to log file {LOG_FILE}: {e}", file=sys.stderr)

    # Basic logger configuration
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
        handlers=handlers,
        force=True
    )
    
    logger = logging.getLogger("campusgpt")
    logger.info(f"Logging initialized with level: {log_level_name}")
