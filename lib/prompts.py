"""User prompts and confirmation dialogs for Gmail Cleaner"""

from .config import logger


def confirm_deletion(email_count: int, permanent: bool = False) -> bool:
    """Get user confirmation for deletion operation

    Args:
        email_count: Number of emails to be deleted
        permanent: True for permanent deletion, False for trash

    Returns:
        bool: True if user confirmed, False otherwise
    """
    action = "permanently delete" if permanent else "move to trash"

    print(f"\n📧 You are about to {action} {email_count} email(s).")

    if permanent:
        print("\n⚠️  WARNING: Permanent deletion cannot be undone!")
        confirm = input("\nType 'PERMANENTLY DELETE' to confirm: ").strip()

        if confirm != "PERMANENTLY DELETE":
            logger.info("❌ Permanent deletion cancelled.")
            return False

        # Double confirmation for large batches
        if email_count > 100:
            confirm2 = input(
                f"⚠️  This is a large batch ({email_count} emails). "
                f"Type the number {email_count} to confirm: "
            ).strip()
            if confirm2 != str(email_count):
                logger.info("❌ Permanent deletion cancelled.")
                return False
    else:
        # Trash operation confirmation
        confirm = (
            input(f"\nMove {email_count} email(s) to trash? (yes/no): ").strip().lower()
        )
        if confirm not in ["yes", "y"]:
            logger.info("❌ Trash operation cancelled.")
            return False

        # Additional warning for large trash batches
        if email_count > 100:
            confirm2 = (
                input(
                    f"⚠️  This is a large batch ({email_count} emails). "
                    f"Type 'YES' to confirm: "
                )
                .strip()
                .upper()
            )
            if confirm2 != "YES":
                logger.info("❌ Trash operation cancelled.")
                return False

    return True
