"""Email processing module"""

import time
from typing import Dict, Optional
from email.utils import parsedate_to_datetime

from googleapiclient.errors import HttpError

from .models import EmailInfo
from .decoder import EmailDecoder
from .utils import rate_limiter
from .config import MAX_RETRIES, INITIAL_RETRY_DELAY, MAX_PREVIEW_LENGTH, logger


class EmailProcessor:
    """Process and extract email information"""

    def __init__(self, service):
        self.service = service
        self.decoder = EmailDecoder()

    def get_full_email_body(self, payload: Dict) -> str:
        """Extract full email body with encoding detection"""
        if payload.get("body", {}).get("data"):
            data = payload["body"]["data"]
            decoded = self.decoder.decode_base64(data)
            if payload.get("mimeType") == "text/html":
                decoded = self.decoder.clean_html(decoded)
            return decoded

        if payload.get("parts"):
            for part in payload["parts"]:
                if part.get("mimeType") == "text/plain":
                    return self.get_full_email_body(part)
                if part.get("parts"):
                    nested = self.get_full_email_body(part)
                    if nested:
                        return nested

            for part in payload["parts"]:
                if part.get("mimeType") == "text/html":
                    html_content = self.get_full_email_body(part)
                    return self.decoder.clean_html(html_content)

        return ""

    def _extract_attachments(self, parts):
        """Recursively extract attachments from message parts"""
        attachments = []
        for part in parts:
            if part.get("filename"):
                attachments.append(part)
            if part.get("parts"):
                attachments.extend(self._extract_attachments(part["parts"]))
        return attachments

    def get_email_info(self, message_id: str) -> Optional[EmailInfo]:
        """Get detailed email information with retries"""
        for attempt in range(MAX_RETRIES):
            try:
                rate_limiter.wait_if_needed()
                msg = (
                    self.service.users()
                    .messages()
                    .get(userId="me", id=message_id, format="full")
                    .execute()
                )

                headers = {
                    h["name"]: h["value"] for h in msg["payload"].get("headers", [])
                }

                # Parse date
                date_str = headers.get("Date", "No Date")
                try:
                    date_obj = parsedate_to_datetime(date_str)
                    formatted_date = date_obj.strftime("%Y-%m-%d %H:%M")
                except Exception:
                    formatted_date = date_str[:25]

                full_body = self.get_full_email_body(msg["payload"])
                preview = self._smart_truncate(full_body, MAX_PREVIEW_LENGTH)

                # Check attachments
                has_attachments = False
                attachment_names = []
                attachment_types = []

                if "parts" in msg["payload"]:
                    attachment_parts = self._extract_attachments(
                        msg["payload"]["parts"]
                    )
                    if attachment_parts:
                        has_attachments = True
                        for part in attachment_parts:
                            attachment_names.append(part["filename"])
                            attachment_types.append(part.get("mimeType", "unknown"))

                return EmailInfo(
                    id=message_id,
                    subject=headers.get("Subject", "No Subject"),
                    sender=headers.get("From", "Unknown"),
                    date=formatted_date,
                    preview=preview,
                    full_body=full_body,
                    thread_id=msg["threadId"],
                    size_estimate=int(msg.get("sizeEstimate", 0)),
                    has_attachments=has_attachments,
                    attachment_names=attachment_names,
                    attachment_types=attachment_types,
                )

            except HttpError as e:
                if e.resp.status in [429, 500, 503] and attempt < MAX_RETRIES - 1:
                    wait_time = INITIAL_RETRY_DELAY * (2**attempt)
                    logger.warning(f"API error, retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"Failed to fetch email {message_id}: {e}")
                    return None
            except Exception as e:
                logger.error(f"Unexpected error for {message_id}: {e}")
                return None
        return None

    def _smart_truncate(self, text: str, length: int) -> str:
        """Truncate text at word boundaries"""
        if len(text) <= length:
            return text
        truncated = text[:length]
        last_space = truncated.rfind(" ")
        if last_space > length * 0.8:
            truncated = truncated[:last_space]
        return truncated + "..."
