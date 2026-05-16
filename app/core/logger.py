import logging
import os
import sys

LOG_DIR = "logs"

# CREATE LOG DIRECTORY
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# CREATE LOGGER
logger = logging.getLogger("ai_voice_agent")

logger.setLevel(logging.INFO)

# PREVENT DUPLICATE LOGS
logger.handlers.clear()

# LOG FORMAT
formatter = logging.Formatter(
    "%(asctime)s | %(levelname)s | %(message)s"
)

# FILE HANDLER
file_handler = logging.FileHandler(
    f"{LOG_DIR}/app.log",
    encoding="utf-8"
)

file_handler.setFormatter(formatter)

# CONSOLE HANDLER
console_handler = logging.StreamHandler(sys.stdout)

console_handler.setFormatter(formatter)

# ADD HANDLERS
logger.addHandler(file_handler)
logger.addHandler(console_handler)