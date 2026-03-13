"""Gmail Cleaner Library - Core functionality for Gmail management"""
from .models import EmailInfo
from .auth import GmailAuthenticator
from .processor import EmailProcessor
from .delete_manager import DeleteManager
from .display import display_emails
from .ai_providers import AISearchFactory
from .config import setup_logging, logger
from .prompts import confirm_deletion

__all__ = [
    'EmailInfo',
    'GmailAuthenticator',
    'EmailProcessor',
    'DeleteManager',
    'display_emails',
    'AISearchFactory',
    'setup_logging',
    'logger',
    'confirm_deletion'
]
