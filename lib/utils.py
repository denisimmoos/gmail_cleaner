"""Utility functions for Gmail Cleaner"""
import os
import time
import pickle
from pathlib import Path
from datetime import datetime
from typing import List, Optional

from google.oauth2.credentials import Credentials
from googleapiclient.errors import HttpError

from .config import API_CALLS_PER_SECOND, logger

class RateLimiter:
    """Simple rate limiter for API calls"""

    def __init__(self, calls_per_second: int = 5):
        self.calls_per_second = calls_per_second
        self.min_interval = 1.0 / calls_per_second
        self.last_call_time = 0

    def wait_if_needed(self):
        """Wait if we're making API calls too quickly"""
        current_time = time.time()
        time_since_last = current_time - self.last_call_time

        if time_since_last < self.min_interval:
            sleep_time = self.min_interval - time_since_last
            time.sleep(sleep_time)

        self.last_call_time = time.time()

# Global rate limiter
rate_limiter = RateLimiter(API_CALLS_PER_SECOND)

class SecureTokenStorage:
    """Secure token storage with file permissions"""

    @staticmethod
    def save_token(token_path: Path, creds: Credentials) -> bool:
        """Save token with secure permissions"""
        try:
            temp_path = token_path.with_suffix('.tmp')
            with open(temp_path, 'wb') as token:
                pickle.dump(creds, token)

            if os.name == 'posix':
                os.chmod(temp_path, 0o600)

            temp_path.rename(token_path)
            return True
        except Exception as e:
            logger.error(f"Failed to save token securely: {e}")
            return False

    @staticmethod
    def load_token(token_path: Path) -> Optional[Credentials]:
        """Load token if it exists and has secure permissions"""
        if not token_path.exists():
            return None

        if os.name == 'posix':
            mode = os.stat(token_path).st_mode
            if mode & 0o077:
                logger.warning(f"⚠️  Token file has unsafe permissions. Fixing...")
                os.chmod(token_path, 0o600)

        try:
            with open(token_path, 'rb') as token:
                return pickle.load(token)
        except Exception as e:
            logger.error(f"Failed to load token: {e}")
            return None

def build_query(args) -> Optional[str]:
    """Build search query with proper escaping"""
    query_parts = []

    if args.before:
        try:
            date = datetime.strptime(args.before, '%Y/%m/%d')
            query_parts.append(f'before:{date.strftime("%Y/%m/%d")}')
        except ValueError:
            logger.error(f"Invalid before date: {args.before} (use YYYY/MM/DD)")
            return None

    if args.after:
        try:
            date = datetime.strptime(args.after, '%Y/%m/%d')
            query_parts.append(f'after:{date.strftime("%Y/%m/%d")}')
        except ValueError:
            logger.error(f"Invalid after date: {args.after} (use YYYY/MM/DD)")
            return None

    if args.subject:
        safe_subject = args.subject.replace('"', '\\"')
        query_parts.append(f'subject:"{safe_subject}"')

    if args.body:
        query_parts.append(args.body)

    if args.sender:
        safe_sender = args.sender.replace('"', '\\"')
        query_parts.append(f'from:"{safe_sender}"')

    if args.has_attachment:
        query_parts.append('has:attachment')

    if not query_parts:
        logger.error("No search criteria provided")
        return None

    return ' '.join(query_parts)

def get_email_ids(service, query: str, max_results: int = 100) -> List[str]:
    """Get matching email IDs with pagination support"""
    message_ids = []
    page_token = None

    try:
        while len(message_ids) < max_results:
            rate_limiter.wait_if_needed()

            results = service.users().messages().list(
                userId='me',
                q=query,
                maxResults=min(500, max_results - len(message_ids)),
                pageToken=page_token
            ).execute()

            batch_ids = [msg['id'] for msg in results.get('messages', [])]
            message_ids.extend(batch_ids)

            page_token = results.get('nextPageToken')
            if not page_token or not batch_ids:
                break

        return message_ids[:max_results]

    except HttpError as e:
        logger.error(f'API error: {e}')
        if "gmail.googleapis.com" in str(e):
            logger.error("\n🔧 Enable Gmail API:")
            logger.error("https://console.cloud.google.com/apis/library/gmail.googleapis.com")
        return []
