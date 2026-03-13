"""Data models for Gmail Cleaner"""
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class EmailInfo:
    """Structured email information"""
    id: str
    subject: str
    sender: str
    date: str
    preview: str
    full_body: str
    thread_id: str
    size_estimate: int
    has_attachments: bool
    attachment_names: List[str] = None
    attachment_types: List[str] = None
