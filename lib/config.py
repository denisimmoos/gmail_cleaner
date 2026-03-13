"""Configuration constants for Gmail Cleaner"""

import logging
from typing import List


# Logging setup
def setup_logging(debug: bool = False):
    """Configure logging"""
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


logger = logging.getLogger(__name__)

# API Scopes
SCOPES: List[str] = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.modify",
    "https://mail.google.com/",
]

# Default prompts
DEFAULT_AI_PROMPT = "search for automatically generated text of non human origin, promotional text, newsletters, and similar content that I might want to bulk delete from my Gmail inbox"

# Processing constants
BATCH_SIZE = 100
MAX_RETRIES = 3
INITIAL_RETRY_DELAY = 1
MAX_PREVIEW_LENGTH = 120
USER_AGENT = "GmailCleaner/2.0"
API_CALLS_PER_SECOND = 5

# Display constants
DISPLAY_NUM_WIDTH = 5
DISPLAY_DATE_WIDTH = 17
DISPLAY_SENDER_WIDTH = 35
DISPLAY_SUBJECT_WIDTH = 40
DISPLAY_ATTACH_WIDTH = 10
DISPLAY_BODY_WIDTH = 60

__version__ = "2.0.0"
