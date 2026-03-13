"""Display formatting for email results"""
import re
from typing import List

from .models import EmailInfo
from .config import (
    DISPLAY_NUM_WIDTH, DISPLAY_DATE_WIDTH, DISPLAY_SENDER_WIDTH,
    DISPLAY_SUBJECT_WIDTH, DISPLAY_ATTACH_WIDTH, DISPLAY_BODY_WIDTH
)

def remove_emojis(text: str) -> str:
    """Remove emojis and other special characters from text"""
    if not text:
        return text

    emoji_pattern = re.compile("["
        u"\U0001F600-\U0001F64F"  # emoticons
        u"\U0001F300-\U0001F5FF"  # symbols & pictographs
        u"\U0001F680-\U0001F6FF"  # transport & map symbols
        u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
        u"\U00002702-\U000027B0"
        u"\U000024C2-\U0001F251"
        u"\U0001f926-\U0001f937"
        u"\U00010000-\U0010ffff"
        u"\u200d"
        u"\u2640-\u2642"
        u"\u2600-\u2B55"
        u"\u23cf"
        u"\u23e9"
        u"\u231a"
        u"\ufe0f"  # variation selector
        u"\u3030"
        "]+", flags=re.UNICODE)

    return emoji_pattern.sub(r'', text)

def get_attachment_icon(email: EmailInfo) -> str:
    """Get attachment icon based on actual attachment file types"""
    if not email.has_attachments or not email.attachment_names:
        return "❌"

    # If multiple attachments, return multi icon
    if len(email.attachment_names) > 1:
        return "📎📎"

    # Get the first attachment name and type
    filename = email.attachment_names[0].lower()
    filetype = email.attachment_types[0].lower() if email.attachment_types else ""

    # Check by file extension
    if filename.endswith('.pdf') or 'pdf' in filetype:
        return "📕"
    elif filename.endswith(('.jpg', '.jpeg', '.jfif')) or 'jpeg' in filetype:
        return "🖼️"
    elif filename.endswith('.png') or 'png' in filetype:
        return "🖼️"
    elif filename.endswith(('.gif', '.bmp', '.webp')) or 'image' in filetype:
        return "🖼️"
    elif filename.endswith(('.doc', '.docx')) or 'word' in filetype or 'document' in filetype:
        return "📘"
    elif filename.endswith(('.xls', '.xlsx')) or 'excel' in filetype or 'spreadsheet' in filetype:
        return "📗"
    elif filename.endswith(('.zip', '.rar', '.7z', '.tar', '.gz')) or 'archive' in filetype or 'compressed' in filetype:
        return "🗜️"
    elif filename.endswith(('.mp3', '.wav', '.flac', '.aac', '.ogg')) or 'audio' in filetype:
        return "🎵"
    elif filename.endswith(('.mp4', '.avi', '.mov', '.mkv', '.wmv')) or 'video' in filetype:
        return "🎬"
    else:
        return "📎"

def wrap_text(text: str, width: int) -> List[str]:
    """Simple text wrapping based on character count"""
    if not text:
        return [""]

    if len(text) <= width:
        return [text]

    lines = []
    words = text.split(' ')
    current_line = ""

    for word in words:
        if len(current_line) + len(word) + 1 <= width:
            if current_line:
                current_line += " " + word
            else:
                current_line = word
        else:
            if current_line:
                lines.append(current_line)
            # If word itself is longer than width, split it
            if len(word) > width:
                for i in range(0, len(word), width):
                    lines.append(word[i:i+width])
                current_line = ""
            else:
                current_line = word

    if current_line:
        lines.append(current_line)

    return lines

def display_emails(email_list: List[EmailInfo], show_full: bool = False):
    """Display results with full body text in a properly aligned table"""
    if not email_list:
        print("No emails found.")
        return

    print(f"\n📧 Found {len(email_list)} emails:\n")

    # Use fixed body width
    body_width = DISPLAY_BODY_WIDTH

    # Print top border
    print("┌" + "─" * DISPLAY_NUM_WIDTH + "┬" + "─" * DISPLAY_DATE_WIDTH + "┬" +
          "─" * DISPLAY_SENDER_WIDTH + "┬" + "─" * DISPLAY_SUBJECT_WIDTH + "┬" +
          "─" * body_width + "┬" + "─" * DISPLAY_ATTACH_WIDTH + "┐")

    # Print header row
    print(f"│{'#':^{DISPLAY_NUM_WIDTH}}│{'Date':^{DISPLAY_DATE_WIDTH}}│{'Sender':^{DISPLAY_SENDER_WIDTH}}│"
          f"{'Subject':^{DISPLAY_SUBJECT_WIDTH}}│{'Body':^{body_width}}│{'Attach':^{DISPLAY_ATTACH_WIDTH}}│")

    # Print separator
    print("├" + "─" * DISPLAY_NUM_WIDTH + "┼" + "─" * DISPLAY_DATE_WIDTH + "┼" +
          "─" * DISPLAY_SENDER_WIDTH + "┼" + "─" * DISPLAY_SUBJECT_WIDTH + "┼" +
          "─" * body_width + "┼" + "─" * DISPLAY_ATTACH_WIDTH + "┤")

    # Track attachment statistics with icons
    attachment_stats = {
        "📕 PDF": 0,
        "📘 Word": 0,
        "📗 Excel": 0,
        "🖼️ JPG": 0,
        "🖼️ PNG": 0,
        "🗜️ Archive": 0,
        "🎵 Audio": 0,
        "🎬 Video": 0,
        "📎 Other": 0,
        "📎📎 Multi": 0,
        "❌ None": 0
    }

    # Print each email
    for i, email in enumerate(email_list, 1):
        # Clean body text and remove emojis
        clean_body = email.full_body.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
        clean_body = ' '.join(clean_body.split())
        clean_body = remove_emojis(clean_body)

        # Remove emojis from sender and subject
        clean_sender = remove_emojis(email.sender)
        clean_subject = remove_emojis(email.subject)

        # Truncate body to 128 chars if needed
        if len(clean_body) > 128:
            clean_body = clean_body[:125] + "..."

        # Format date
        date_str = email.date[:16] if len(email.date) > 16 else email.date

        # Get attachment icon and update statistics
        if not email.has_attachments:
            attach_icon = "❌"
            attachment_stats["❌ None"] += 1
        else:
            attach_icon = get_attachment_icon(email)

            # Update statistics based on actual icon and filename
            if attach_icon == "📕":
                attachment_stats["📕 PDF"] += 1
            elif attach_icon == "📘":
                attachment_stats["📘 Word"] += 1
            elif attach_icon == "📗":
                attachment_stats["📗 Excel"] += 1
            elif attach_icon == "🖼️":
                # Determine if it's JPG or PNG from actual filename
                if email.attachment_names and len(email.attachment_names) == 1:
                    filename = email.attachment_names[0].lower()
                    if filename.endswith(('.jpg', '.jpeg', '.jfif')):
                        attachment_stats["🖼️ JPG"] += 1
                    elif filename.endswith('.png'):
                        attachment_stats["🖼️ PNG"] += 1
                    else:
                        attachment_stats["🖼️ JPG"] += 1
                else:
                    attachment_stats["🖼️ JPG"] += 1
            elif attach_icon == "🗜️":
                attachment_stats["🗜️ Archive"] += 1
            elif attach_icon == "🎵":
                attachment_stats["🎵 Audio"] += 1
            elif attach_icon == "🎬":
                attachment_stats["🎬 Video"] += 1
            elif attach_icon == "📎📎":
                attachment_stats["📎📎 Multi"] += 1
            else:  # 📎 Other
                attachment_stats["📎 Other"] += 1

        # Wrap text for multi-line display
        sender_lines = wrap_text(clean_sender, DISPLAY_SENDER_WIDTH)
        subject_lines = wrap_text(clean_subject, DISPLAY_SUBJECT_WIDTH)
        body_lines = wrap_text(clean_body, body_width)

        # Determine maximum number of lines needed
        max_lines = max(len(sender_lines), len(subject_lines), len(body_lines), 1)

        # Pad lines to ensure all columns have same number of lines
        sender_lines += [''] * (max_lines - len(sender_lines))
        subject_lines += [''] * (max_lines - len(subject_lines))
        body_lines += [''] * (max_lines - len(body_lines))

        # Print each line of the email
        for line_num in range(max_lines):
            # Format each column
            if line_num == 0:
                num_field = f"{i:^{DISPLAY_NUM_WIDTH}}"
                date_field = f"{date_str:^{DISPLAY_DATE_WIDTH}}"
            else:
                num_field = f"{'':^{DISPLAY_NUM_WIDTH}}"
                date_field = f"{'':^{DISPLAY_DATE_WIDTH}}"

            sender_field = f"{sender_lines[line_num]:<{DISPLAY_SENDER_WIDTH}}"
            subject_field = f"{subject_lines[line_num]:<{DISPLAY_SUBJECT_WIDTH}}"
            body_field = f"{body_lines[line_num]:<{body_width}}"

            # Handle attachment column (only on first line)
            if line_num == 0:
                # Calculate proper padding for emoji (which takes 2 widths)
                if attach_icon in ["❌", "📕", "📘", "📗", "🖼️", "🗜️", "🎵", "🎬", "📎"]:
                    # Single emoji - needs 4 spaces on each side (2+4+4=10)
                    attach_field = f"    {attach_icon}    "
                elif attach_icon == "📎📎":
                    # Double emoji - needs 3 spaces on each side (4+3+3=10)
                    attach_field = f"   {attach_icon}   "
                else:
                    # Fallback
                    attach_field = f"    {attach_icon}    "
            else:
                attach_field = f"{'':^{DISPLAY_ATTACH_WIDTH}}"

            # Print row with proper separators
            print(f"│{num_field}│{date_field}│{sender_field}│{subject_field}│{body_field}│{attach_field}│")

        # Print separator between emails (except after the last one)
        if i < len(email_list):
            print("├" + "─" * DISPLAY_NUM_WIDTH + "┼" + "─" * DISPLAY_DATE_WIDTH + "┼" +
                  "─" * DISPLAY_SENDER_WIDTH + "┼" + "─" * DISPLAY_SUBJECT_WIDTH + "┼" +
                  "─" * body_width + "┼" + "─" * DISPLAY_ATTACH_WIDTH + "┤")

    # Print bottom border
    print("└" + "─" * DISPLAY_NUM_WIDTH + "┴" + "─" * DISPLAY_DATE_WIDTH + "┴" +
          "─" * DISPLAY_SENDER_WIDTH + "┴" + "─" * DISPLAY_SUBJECT_WIDTH + "┴" +
          "─" * body_width + "┴" + "─" * DISPLAY_ATTACH_WIDTH + "┘")

    # Print attachment summary with icons
    print("\n📎 Attachment Summary:")
    total_with_attachments = 0

    # Print all non-zero stats
    for category, count in attachment_stats.items():
        if count > 0:
            print(f"   {category}: {count} emails")
            if category != "❌ None":
                total_with_attachments += count

    print(f"\n   {'📊 Total with attachments:':<25} {total_with_attachments} emails")
    print(f"   {'📊 Total emails:':<25} {len(email_list)} emails")

    if show_full:
        print("\n" + "═" * 120)
        for i, email in enumerate(email_list, 1):
            print(f"\n📧 Email #{i} - Full Unmodified Content")
            print(f"From:    {email.sender}")
            print(f"Subject: {email.subject}")
            print(f"Date:    {email.date}")
            print(f"Size:    {email.size_estimate} bytes")

            # Show actual attachment types if available
            if email.has_attachments:
                attach_icon = get_attachment_icon(email)
                if email.attachment_names:
                    print(f"Attachments: Yes {attach_icon} ({', '.join(email.attachment_names)})")
                else:
                    print(f"Attachments: Yes {attach_icon}")
            else:
                print(f"Attachments: No ❌")

            print("\nContent:")
            print("─" * 40)
            print(email.full_body)
            print("─" * 40)

            if i < len(email_list):
                print("\n" + "─" * 120)
