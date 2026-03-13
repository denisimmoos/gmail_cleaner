"""Gmail authentication module"""
import os
import sys
import json
from pathlib import Path
from typing import Any

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import set_user_agent

from .config import SCOPES, USER_AGENT, logger
from .utils import SecureTokenStorage

class GmailAuthenticator:
    """Handles Gmail authentication with improved security"""

    def __init__(self):
        self.gmail_env_path = self._find_or_create_env()
        self.token_path = self.gmail_env_path / 'token.pickle'
        self.credentials_path = self.gmail_env_path / 'credentials.json'

    def _find_or_create_env(self) -> Path:
        """Find or create .gmail_env directory"""
        possible_paths = [
            Path('.gmail_env'),
            Path.cwd() / '.gmail_env',
            Path.home() / '.gmail_env'
        ]

        for path in possible_paths:
            if path.exists() and path.is_dir():
                return path

        new_path = Path('.gmail_env')
        new_path.mkdir(mode=0o700, exist_ok=True)
        logger.info(f"Created {new_path}/ with secure permissions")
        return new_path

    def check_credentials(self) -> bool:
        """Validate credentials.json"""
        if not self.credentials_path.exists():
            return False

        try:
            with open(self.credentials_path, 'r') as f:
                creds = json.load(f)

            if 'installed' in creds:
                client_id = creds['installed'].get('client_id', '')
                if client_id and '.apps.googleusercontent.com' in client_id:
                    if os.name == 'posix':
                        os.chmod(self.credentials_path, 0o600)
                    return True
        except Exception as e:
            logger.error(f"Invalid credentials.json: {e}")

        return False

    def print_setup_instructions(self):
        """Print one-time setup instructions"""
        print("\n🚀 QUICK SETUP (ONE TIME ONLY):")
        print("1. Go to: https://console.cloud.google.com/apis/credentials")
        print("2. Click 'CREATE CREDENTIALS' → 'OAuth client ID'")
        print("3. Application type: 'Desktop application'")
        print("4. Name: 'Gmail Cleaner'")
        print("5. Click 'CREATE'")
        print("6. Click 'DOWNLOAD JSON'")
        print(f"7. Save as: {self.credentials_path}")
        print("\n💡 File will be saved with secure permissions (600)")
        sys.exit(1)

    def authenticate(self) -> Any:
        """Main authentication flow"""
        if not self.check_credentials():
            self.print_setup_instructions()

        creds = SecureTokenStorage.load_token(self.token_path)

        if creds and creds.valid:
            logger.info("✅ Using saved token")
            return build('gmail', 'v1', credentials=creds)

        if creds and creds.expired and creds.refresh_token:
            logger.info("🔄 Refreshing expired token...")
            try:
                creds.refresh(Request())
            except Exception:
                creds = None

        if not creds:
            logger.info("\n🔐 Browser opening for login...")
            flow = InstalledAppFlow.from_client_secrets_file(
                str(self.credentials_path),
                SCOPES
            )
            creds = flow.run_local_server(
                port=0,
                open_browser=True,
                authorization_prompt_message=(
                    "Please login and authorize access to Gmail.\n"
                    "After authorization, return to this terminal."
                ),
            )

        if SecureTokenStorage.save_token(self.token_path, creds):
            logger.info(f"✅ Token saved securely: {self.token_path}")

        service = build('gmail', 'v1', credentials=creds)
        set_user_agent(service._http, USER_AGENT)
        return service
