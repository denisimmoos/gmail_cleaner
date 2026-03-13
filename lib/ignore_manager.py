"""Manage ignored senders for Gmail Cleaner"""

import os
import re
from pathlib import Path
from typing import List, Set, Pattern, Optional
from .config import logger


class IgnoreManager:
    """Manages ignored senders list"""

    def __init__(self, ignore_file: Optional[str] = None):
        """Initialize ignore manager

        Args:
            ignore_file: Path to ignore patterns file (default: ignore_patterns.inc)
        """
        self.ignore_file = self._find_ignore_file(ignore_file or "ignore_patterns.inc")
        self.ignore_patterns: List[Pattern] = []
        self.ignore_strings: Set[str] = set()
        self.load_ignore_list()

    def _find_ignore_file(self, filename: str) -> Path:
        """Find ignore file in current directory or parent directories"""
        # Start from current working directory
        current_dir = Path.cwd()

        # Look in current directory and parents (up to 3 levels)
        for _ in range(4):
            potential_path = current_dir / filename
            if potential_path.exists():
                logger.debug(f"Found ignore file: {potential_path}")
                return potential_path
            current_dir = current_dir.parent

        # If not found, create in current directory
        default_path = Path.cwd() / filename
        logger.info(f"Creating new ignore file: {default_path}")
        return default_path

    def load_ignore_list(self) -> None:
        """Load and parse ignore patterns from file"""
        if not self.ignore_file.exists():
            self._create_sample_ignore_file()
            return

        try:
            with open(self.ignore_file, "r", encoding="utf-8") as f:
                lines = f.readlines()

            self.ignore_patterns = []
            self.ignore_strings = set()

            for line_num, line in enumerate(lines, 1):
                line = line.strip()

                # Skip empty lines and comments
                if not line or line.startswith("#"):
                    continue

                # Check if it's a regex pattern (enclosed in /.../)
                if line.startswith("/") and line.endswith("/") and len(line) > 2:
                    try:
                        pattern = re.compile(line[1:-1], re.IGNORECASE)
                        self.ignore_patterns.append(pattern)
                        logger.debug(f"Added regex pattern: {line}")
                    except re.error as e:
                        logger.warning(
                            f"Invalid regex pattern at line {line_num}: {line} - {e}"
                        )
                else:
                    # Regular string match (case-insensitive)
                    self.ignore_strings.add(line.lower())
                    logger.debug(f"Added string pattern: {line}")

            logger.info(
                f"Loaded {len(self.ignore_strings)} string patterns and {len(self.ignore_patterns)} regex patterns from {self.ignore_file}"
            )

        except Exception as e:
            logger.error(f"Error loading ignore file: {e}")

    def _create_sample_ignore_file(self) -> None:
        """Create a sample ignore patterns file"""
        sample_content = """# Gmail Cleaner - Ignored Patterns List
# Add email addresses or patterns to ignore (one per line)
# Lines starting with # are comments
# Use /pattern/ for regex matching (case-insensitive)

# Examples - Simple strings (partial matches):
newsletter@example.com          # Exact email
@spamdomain.com                 # Any email from this domain
no-reply@                        # Any no-reply address
notifications@                   # Any notification address

# Examples - Regex patterns (enclosed in //):
/.*@.*\\.spam\\.com$/            # Any email from .spam.com domains
/^noreply-.*@/                   # noreply-* addresses
/@mail\\./                        # Contains @mail.
/@marketing\\./                   # Contains @marketing.
/@newsletter\\./                  # Contains @newsletter.

# System emails to ignore (simple strings):
mailer-daemon@
postmaster@

# Add your own patterns below:
"""
        try:
            with open(self.ignore_file, "w", encoding="utf-8") as f:
                f.write(sample_content)
            logger.info(f"Created sample ignore file: {self.ignore_file}")

            # Set file permissions to read/write for owner only on Unix
            if os.name == "posix":
                os.chmod(self.ignore_file, 0o600)

        except Exception as e:
            logger.error(f"Failed to create sample ignore file: {e}")

    def should_ignore(self, sender: str) -> bool:
        """Check if a sender should be ignored

        Args:
            sender: Email sender string (e.g., "Name <email@example.com>")

        Returns:
            bool: True if sender should be ignored
        """
        if not sender or sender == "Unknown":
            return False

        sender_lower = sender.lower()

        # Check exact string matches (case-insensitive)
        for ignore_string in self.ignore_strings:
            if ignore_string in sender_lower:
                logger.debug(f"Ignoring '{sender}' - matches string: {ignore_string}")
                return True

        # Check regex patterns
        for pattern in self.ignore_patterns:
            if pattern.search(sender):
                logger.debug(f"Ignoring '{sender}' - matches regex: {pattern.pattern}")
                return True

        return False

    def filter_emails(self, emails: List) -> List:
        """Filter out emails from ignored senders

        Args:
            emails: List of EmailInfo objects

        Returns:
            List: Filtered list excluding ignored senders
        """
        if not self.ignore_strings and not self.ignore_patterns:
            return emails

        filtered = []
        ignored_count = 0

        for email in emails:
            if self.should_ignore(email.sender):
                ignored_count += 1
                logger.debug(f"Ignored email: {email.subject} from {email.sender}")
            else:
                filtered.append(email)

        if ignored_count > 0:
            logger.info(f"Ignored {ignored_count} emails from ignored patterns")

        return filtered

    def add_pattern(self, pattern: str, is_regex: bool = False) -> bool:
        """Add a pattern to the ignore file

        Args:
            pattern: Pattern to ignore
            is_regex: True if pattern is a regex

        Returns:
            bool: True if added successfully
        """
        try:
            # Format the line
            if is_regex:
                if not (pattern.startswith("/") and pattern.endswith("/")):
                    pattern = f"/{pattern}/"
            else:
                # Remove any existing formatting
                pattern = pattern.lower().strip()

            # Append to file
            with open(self.ignore_file, "a", encoding="utf-8") as f:
                f.write(f"\n{pattern}  # Added by user")

            # Reload the ignore list
            self.load_ignore_list()
            logger.info(f"Added pattern '{pattern}' to ignore list")
            return True

        except Exception as e:
            logger.error(f"Failed to add pattern to ignore list: {e}")
            return False

    def show_patterns(self) -> None:
        """Display current ignore patterns"""
        print(f"\n📋 Current Ignore Patterns (from {self.ignore_file}):")

        if self.ignore_strings:
            print("\n  String patterns (partial matches):")
            for pattern in sorted(self.ignore_strings):
                print(f"    • {pattern}")

        if self.ignore_patterns:
            print("\n  Regex patterns:")
            for pattern in self.ignore_patterns:
                print(f"    • /{pattern.pattern}/")

        if not self.ignore_strings and not self.ignore_patterns:
            print("\n  No patterns configured.")
