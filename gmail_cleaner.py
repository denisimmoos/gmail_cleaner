#!/usr/bin/env python3
"""
Gmail Search CLI Tool - Secure, Robust, and User-Friendly
With full text preview, multiple AI providers, and safe deletion options
"""

import sys
import argparse
import importlib.util
from pathlib import Path

# Add lib directory to path
lib_path = Path(__file__).parent / "lib"
sys.path.insert(0, str(lib_path))

# Now import from lib modules
from lib.auth import GmailAuthenticator  # noqa: E402
from lib.processor import EmailProcessor  # noqa: E402
from lib.delete_manager import DeleteManager  # noqa: E402
from lib.display import display_emails  # noqa: E402
from lib.ai_providers import AISearchFactory  # noqa: E402
from lib.ignore_manager import IgnoreManager  # noqa: E402
from lib.config import DEFAULT_AI_PROMPT, setup_logging, logger  # noqa: E402
from lib.utils import build_query, get_email_ids  # noqa: E402
from lib.prompts import confirm_deletion  # noqa: E402


# Check for required packages before proceeding
def check_dependencies():
    """Check if required packages are installed"""
    required_packages = {
        "google": "google-auth",
        "google.auth": "google-auth",
        "googleapiclient": "google-api-python-client",
        "openai": "openai",
        "google.generativeai": "google-generativeai",
        "requests": "requests",
    }

    missing_packages = []

    for module_name, package_name in required_packages.items():
        spec = importlib.util.find_spec(module_name.split(".")[0])
        if spec is None:
            missing_packages.append(package_name)

    if missing_packages:
        print("\n❌ Missing required Python packages!\n")
        print("Please set up a virtual environment and install dependencies:\n")
        print("1. Create a virtual environment:")
        print("   python3 -m venv .gmail_cleaner\n")
        print("2. Activate it:")
        print("   source .gmail_cleaner/bin/activate\n")
        print("3. Install required packages:")
        print(f"   pip install {' '.join(set(missing_packages))}\n")
        print("   Or install all at once:")
        print("   pip install -r requirements.txt\n")
        print("4. Then run the script again")
        sys.exit(1)


# Run dependency check
check_dependencies()


def create_parser():
    """Create argument parser"""
    parser = argparse.ArgumentParser(
        description="Gmail Cleaner - Safely manage and clean your Gmail inbox",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Search and preview
  %(prog)s --subject "newsletter" --after 2024/01/01
  %(prog)s --sender "newsletter@example.com" --max 50

  # AI-powered search
  %(prog)s --ai "find all promotional emails" --max 200

  # Safe deletion (move to trash)
  %(prog)s --subject "old newsletter" --before 2023/01/01 --trash

  # Permanent deletion (use with caution!)
  %(prog)s --ai "spammy newsletters" --permanent --dry-run  # Preview first
  %(prog)s --ai "spammy newsletters" --permanent            # Actually delete

  # Use different AI providers
  %(prog)s --ai "find newsletters" --ai-provider gemini --trash
  %(prog)s --ai "find promotions" --ai-provider deepseek --trash

  # Ignore patterns from file
  %(prog)s --subject "newsletter"                         # Use default ignore_patterns.inc
  %(prog)s --subject "newsletter" --ignore-file custom.inc # Use custom ignore file
  %(prog)s --subject "newsletter" --no-ignore              # Temporarily disable ignore
        """,
    )

    # Search options
    search_group = parser.add_argument_group("Search Options")
    search_group.add_argument("--before", help="Before date YYYY/MM/DD")
    search_group.add_argument("--after", help="After date YYYY/MM/DD")
    search_group.add_argument("--subject", help="Search in subject line")
    search_group.add_argument("--body", help="Search in email body")
    search_group.add_argument("--sender", help="Search by sender email or name")
    search_group.add_argument(
        "--has-attachment", action="store_true", help="Only emails with attachments"
    )
    search_group.add_argument(
        "--max", type=int, default=100, help="Maximum results (default: 100)"
    )
    search_group.add_argument(
        "--no-ignore",
        action="store_true",
        help="Temporarily disable ignore patterns from file",
    )

    # AI options
    ai_group = parser.add_argument_group("AI-Powered Search")
    ai_group.add_argument(
        "--ai",
        nargs="?",
        const=DEFAULT_AI_PROMPT,
        metavar="PROMPT",
        help="Use AI to generate search query",
    )
    ai_group.add_argument(
        "--ai-provider",
        choices=["openai", "gemini", "deepseek"],
        default="deepseek",
        help="AI provider to use (default: deepseek)",
    )

    # Action options
    action_group = parser.add_argument_group("Actions")
    action_group.add_argument(
        "--trash", action="store_true", help="Move matching emails to trash"
    )
    action_group.add_argument(
        "--permanent",
        action="store_true",
        help="PERMANENTLY delete emails (bypass trash) - USE WITH CAUTION",
    )
    action_group.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be deleted without actually deleting",
    )

    # Display options
    display_group = parser.add_argument_group("Display Options")
    display_group.add_argument(
        "--show-full", action="store_true", help="Show full email content in results"
    )
    display_group.add_argument(
        "--debug", action="store_true", help="Enable debug logging"
    )

    # Ignore file management
    ignore_group = parser.add_argument_group("Ignore Patterns Management")
    ignore_group.add_argument(
        "--ignore-file",
        metavar="FILE",
        help="Custom ignore patterns file (default: ignore_patterns.inc)",
    )
    ignore_group.add_argument(
        "--show-ignored", action="store_true", help="Show current ignore patterns"
    )
    ignore_group.add_argument(
        "--add-ignore",
        metavar="PATTERN",
        help="Add pattern to ignore file (use /pattern/ for regex)",
    )
    ignore_group.add_argument(
        "--ignore-regex",
        action="store_true",
        help="Used with --add-ignore to indicate pattern is regex",
    )

    return parser


def main():
    """Main entry point"""
    parser = create_parser()
    args = parser.parse_args()

    # Set debug logging if requested
    if args.debug:
        setup_logging(debug=True)

    # Initialize ignore manager (with custom file if provided)
    ignore_mgr = IgnoreManager(args.ignore_file)

    # Handle ignore list management commands
    if args.show_ignored:
        ignore_mgr.show_patterns()
        return 0

    if args.add_ignore:
        if ignore_mgr.add_pattern(args.add_ignore, args.ignore_regex):
            print(f"✅ Added pattern '{args.add_ignore}' to {ignore_mgr.ignore_file}")
        else:
            print(f"❌ Failed to add pattern '{args.add_ignore}' to ignore list")
        return 0

    # Validate search criteria
    if not any(
        [
            args.before,
            args.after,
            args.subject,
            args.body,
            args.sender,
            args.ai,
            args.has_attachment,
        ]
    ):
        parser.error("No search criteria provided. Use --help for options.")

    # AI-powered search
    if args.ai:
        logger.info(f"📝 AI prompt: '{args.ai}'")
        ai_provider = AISearchFactory.create(args.ai_provider)
        if not ai_provider:
            logger.error(f"❌ Failed to initialize {args.ai_provider} provider")
            return 1
        ai_query = ai_provider.generate_query(args.ai)
        if ai_query:
            logger.info(f"📝 Generated query: {ai_query}")
            args.body = ai_query
        else:
            logger.error(
                "❌ AI search failed. Check your API key or try regular search."
            )
            return 1

    # Build the final query
    query = build_query(args)
    if not query:
        return 1

    logger.info(f"🔍 Searching: {query}")

    # Authenticate and get service
    try:
        auth = GmailAuthenticator()
        service = auth.authenticate()
    except Exception as e:
        logger.error(f"Authentication failed: {e}")
        return 1

    # Get matching email IDs
    message_ids = get_email_ids(service, query, args.max)
    if not message_ids:
        logger.info("No matches found.")
        return 0

    # Process emails to get full info
    logger.info(f"📥 Fetching details for {len(message_ids)} emails...")
    processor = EmailProcessor(service)

    email_list = []
    for i, msg_id in enumerate(message_ids, 1):
        if i % 10 == 0:
            logger.info(f"Progress: {i}/{len(message_ids)} emails fetched")

        email_info = processor.get_email_info(msg_id)
        if email_info:
            email_list.append(email_info)

    # Filter out ignored patterns (unless --no-ignore is used)
    if not args.no_ignore:
        original_count = len(email_list)
        email_list = ignore_mgr.filter_emails(email_list)
        if len(email_list) < original_count:
            logger.info(
                f"Filtered out {original_count - len(email_list)} emails matching ignore patterns"
            )

    # Display results
    display_emails(email_list=email_list, show_full=args.show_full)

    # Handle deletion if requested
    if args.trash or args.permanent:
        # Skip confirmation for dry runs
        if not args.dry_run:
            if not confirm_deletion(len(email_list), permanent=args.permanent):
                return 0

        delete_mgr = DeleteManager(service)

        # Execute deletion
        results = delete_mgr.delete_emails(
            [e.id for e in email_list], permanent=args.permanent, dry_run=args.dry_run
        )

        if args.dry_run:
            logger.info(
                f"\n🔍 DRY RUN COMPLETE: Would have processed {results['dry_run']} emails"
            )
        else:
            action = "permanently deleted" if args.permanent else "moved to trash"
            logger.info(f"\n✅ Done: {results['deleted']} emails {action}")
            if results["failed"] > 0:
                logger.warning(f"⚠️  Failed to delete {results['failed']} emails")

    else:
        # No delete action, show how to delete
        print("\n💡 To delete these emails:")
        print("   --trash     : Move to trash (safe)")
        print("   --permanent : Permanently delete (use with caution)")

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Operation cancelled by user")
