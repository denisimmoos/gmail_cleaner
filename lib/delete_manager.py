"""Email deletion management"""

import time
from typing import List, Dict

from googleapiclient.errors import HttpError

from .utils import rate_limiter
from .config import BATCH_SIZE, MAX_RETRIES, INITIAL_RETRY_DELAY, logger


class DeleteManager:
    """Manages email deletion with safety features"""

    def __init__(self, service):
        self.service = service
        self.deleted_count = 0
        self.failed_count = 0

    def delete_emails(
        self,
        message_ids: List[str],
        permanent: bool = False,
        dry_run: bool = False,
        batch_size: int = BATCH_SIZE,
    ) -> Dict[str, int]:
        """Delete emails with progress tracking"""
        if dry_run:
            logger.info(
                f"🔍 DRY RUN: Would {'permanently delete' if permanent else 'trash'} {len(message_ids)} emails"
            )
            return {"deleted": 0, "failed": 0, "dry_run": len(message_ids)}

        action = "PERMANENTLY DELETE" if permanent else "TRASH"
        logger.info(f"🗑️  Starting {action} of {len(message_ids)} emails...")

        for i in range(0, len(message_ids), batch_size):
            batch = message_ids[i : i + batch_size]
            self._process_batch(batch, permanent)
            progress = min(i + batch_size, len(message_ids))
            logger.info(f"Progress: {progress}/{len(message_ids)} emails processed")

        logger.info(
            f"✅ Complete: {self.deleted_count} deleted, {self.failed_count} failed"
        )
        return {"deleted": self.deleted_count, "failed": self.failed_count}

    def _process_batch(self, batch_ids: List[str], permanent: bool):
        """Process a single batch"""
        if permanent:
            try:
                rate_limiter.wait_if_needed()
                self.service.users().messages().batchDelete(
                    userId="me", body={"ids": batch_ids}
                ).execute()
                self.deleted_count += len(batch_ids)
            except HttpError as e:
                logger.error(f"Batch delete failed: {e}")
                self._process_batch_fallback(batch_ids, permanent)
        else:
            self._process_batch_fallback(batch_ids, permanent)

    def _process_batch_fallback(self, batch_ids: List[str], permanent: bool):
        """Fallback to individual processing"""
        for msg_id in batch_ids:
            for attempt in range(MAX_RETRIES):
                try:
                    rate_limiter.wait_if_needed()
                    if permanent:
                        self.service.users().messages().delete(
                            userId="me", id=msg_id
                        ).execute()
                    else:
                        self.service.users().messages().trash(
                            userId="me", id=msg_id
                        ).execute()
                    self.deleted_count += 1
                    break
                except HttpError as e:
                    if e.resp.status in [429, 500, 503] and attempt < MAX_RETRIES - 1:
                        wait = INITIAL_RETRY_DELAY * (2**attempt)
                        time.sleep(wait)
                    else:
                        logger.error(f"Failed to delete {msg_id}: {e}")
                        self.failed_count += 1
                except Exception as e:
                    logger.error(f"Unexpected error deleting {msg_id}: {e}")
                    self.failed_count += 1
                    break
