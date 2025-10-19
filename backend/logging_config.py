import logging
from logging.handlers import RotatingFileHandler
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Any

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

REQUEST_LOG_FILE = LOG_DIR / "requests.log"
MAX_LOG_SIZE = 10 * 1024 * 1024
BACKUP_COUNT = 5

def setup_request_logger():
    logger = logging.getLogger("request_logger")
    logger.setLevel(logging.INFO)
    logger.propagate = False
    
    if logger.handlers:
        return logger
    
    handler = RotatingFileHandler(
        REQUEST_LOG_FILE,
        maxBytes=MAX_LOG_SIZE,
        backupCount=BACKUP_COUNT,
        encoding='utf-8'
    )
    
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    handler.setFormatter(formatter)
    
    logger.addHandler(handler)
    
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger

request_logger = setup_request_logger()

def log_request_details(method: str, path: str, client_ip: str, headers: dict, query_params: Optional[dict] = None, body: Optional[dict] = None):
    log_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "method": method,
        "path": path,
        "client_ip": client_ip,
        "headers": dict(headers),
        "query_params": query_params or {},
        "body": body or {}
    }
    
    request_logger.info(f"REQUEST | {json.dumps(log_data, default=str)}")
    return log_data

def log_response_details(method: str, path: str, status_code: int, response_body: Optional[Any] = None, duration_ms: Optional[float] = None):
    log_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "method": method,
        "path": path,
        "status_code": status_code,
        "duration_ms": duration_ms,
        "response_body": response_body
    }
    
    request_logger.info(f"RESPONSE | {json.dumps(log_data, default=str)}")
    return log_data

def log_error_details(method: str, path: str, error: str, traceback: Optional[str] = None):
    log_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "method": method,
        "path": path,
        "error": error,
        "traceback": traceback
    }
    
    request_logger.error(f"ERROR | {json.dumps(log_data, default=str)}")
    return log_data
