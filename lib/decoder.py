"""Email content decoding utilities"""

import base64
import re
import quopri
from html import unescape

from .config import logger


class EmailDecoder:
    """Robust email content decoder"""

    @staticmethod
    def decode_base64(data: str) -> str:
        """Safely decode base64 data with error handling"""
        if not data:
            return ""

        try:
            padded_data = data
            missing_padding = len(data) % 4
            if missing_padding:
                padded_data += "=" * (4 - missing_padding)

            decoded_bytes = base64.urlsafe_b64decode(padded_data.encode("ASCII"))

            for encoding in ["utf-8", "latin-1", "cp1252", "iso-8859-1"]:
                try:
                    return decoded_bytes.decode(encoding)
                except UnicodeDecodeError:
                    continue

            return decoded_bytes.decode("utf-8", errors="replace")
        except Exception as e:
            logger.debug(f"Base64 decode error: {e}")
            return ""

    @staticmethod
    def decode_quoted_printable(data: str) -> str:
        """Decode quoted-printable encoding"""
        try:
            return quopri.decodestring(data.encode()).decode("utf-8", errors="replace")
        except Exception:
            return data

    @staticmethod
    def clean_html(html_content: str) -> str:
        """Extract text from HTML content"""
        html_content = re.sub(
            r"<script[^>]*>.*?</script>", "", html_content, flags=re.DOTALL
        )
        html_content = re.sub(
            r"<style[^>]*>.*?</style>", "", html_content, flags=re.DOTALL
        )
        html_content = unescape(html_content)
        html_content = re.sub(r"<br\s*/?>", "\n", html_content)
        html_content = re.sub(r"</p>", "\n\n", html_content)
        html_content = re.sub(r"</div>", "\n", html_content)
        html_content = re.sub(r"<[^>]+>", " ", html_content)
        html_content = re.sub(r"\n\s+\n", "\n\n", html_content)
        html_content = re.sub(r" +", " ", html_content)
        return html_content.strip()
