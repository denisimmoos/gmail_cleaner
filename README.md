# Gmail Cleaner

A powerful, secure command-line tool for searching, previewing, and cleaning your Gmail inbox with AI-powered search capabilities and robust safety features.

## Features

- 🔍 **Advanced Search** - Full Gmail search operator support with date ranges, subject, sender, and body text
- 🤖 **AI-Powered Search** - Generate complex search queries using natural language (OpenAI, Gemini, or DeepSeek)
- 📋 **Rich Email Display** - Clean tabular output with emoji indicators for attachments and content preview
- 🗑️ **Safe Deletion Options** - Move to trash or permanent delete with multiple confirmation safeguards
- 🚫 **Ignore Patterns** - Filter out unwanted senders using `ignore_patterns.inc` file with simple strings or regex patterns
- 🔒 **Security First** - Secure token storage with proper file permissions, rate limiting, and retry logic
- 📎 **Attachment Detection** - Identify emails with attachments and their types (PDF, Word, Excel, images, etc.)

## Installation

### 1. Clone and Setup Virtual Environment

```bash
# Clone the repository
git clone <repository-url>
cd gmail-cleaner

# Create virtual environment
python3 -m venv .gmail_cleaner

# Activate it
source .gmail_cleaner/bin/activate  # On Windows: .gmail_cleaner\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

Required packages:
- `google-auth`, `google-auth-oauthlib`, `google-auth-httplib2`
- `google-api-python-client`
- `openai` (optional, for OpenAI support)
- `google-generativeai` (optional, for Gemini support)
- `requests` (optional, for DeepSeek support)

### 3. Gmail API Setup (One Time)

1. Go to [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
2. Click **CREATE CREDENTIALS** → **OAuth client ID**
3. Application type: **Desktop application**
4. Name: **Gmail Cleaner**
5. Click **CREATE**
6. Click **DOWNLOAD JSON**
7. Save as `credentials.json` in the `.gmail_env/` directory (created automatically on first run)

The tool will create a `.gmail_env/` directory with secure permissions (700) and store your credentials and tokens there.

### 4. AI Provider Setup (Optional)

Set your API key as an environment variable:

```bash
# For OpenAI
export OPENAI_API_KEY='your-key-here'

# For Google Gemini
export GEMINI_API_KEY='your-key-here'

# For DeepSeek (default)
export DEEPSEEK_API_KEY='your-key-here'
```

## Usage

### Basic Search Examples

```bash
# Search by subject
./gmail_cleaner.py --subject "newsletter" --after 2024/01/01

# Search by sender
./gmail_cleaner.py --sender "newsletter@example.com" --max 50

# Search with date range
./gmail_cleaner.py --before 2023/12/31 --after 2023/01/01 --has-attachment

# Search in body text
./gmail_cleaner.py --body "meeting reminder"
```

### AI-Powered Search

```bash
# Use default AI prompt (promotional content)
./gmail_cleaner.py --ai

# Custom AI prompt with DeepSeek (default)
./gmail_cleaner.py --ai "find all emails about conference calls" --max 200

# Use different AI providers
./gmail_cleaner.py --ai "old newsletters" --ai-provider openai
./gmail_cleaner.py --ai "promotional emails" --ai-provider gemini

# Show full email content
./gmail_cleaner.py --ai "important updates" --show-full
```

### Safe Deletion Operations

```bash
# Preview what would be deleted (always recommended first!)
./gmail_cleaner.py --subject "old newsletter" --before 2023/01/01 --trash --dry-run

# Move to trash (safe)
./gmail_cleaner.py --subject "newsletter" --after 2020/01/01 --trash

# Permanent deletion (use with extreme caution!)
./gmail_cleaner.py --ai "spammy newsletters" --permanent --dry-run  # Preview first
./gmail_cleaner.py --ai "spammy newsletters" --permanent            # Actually delete
```

## Ignore Patterns Management

The `ignore_patterns.inc` file is automatically created in your current directory the first time you run the script. 
This file allows you to filter out unwanted senders automatically.

### File Location and Auto-Discovery

The script automatically searches for `ignore_patterns.inc` in:
1. Current working directory
2. Parent directories (up to 3 levels deep)

If no file is found, a sample file is created automatically.

### Creating and Managing Ignore Patterns

```bash
# Show current ignore patterns
./gmail_cleaner.py --show-ignored

# Add a simple string pattern
./gmail_cleaner.py --add-ignore "newsletter@spam.com"

# Add a regex pattern
./gmail_cleaner.py --add-ignore ".*@.*\.spam\.com$" --ignore-regex

# Use custom ignore file
./gmail_cleaner.py --subject "newsletter" --ignore-file custom.inc

# Temporarily disable ignore patterns
./gmail_cleaner.py --subject "newsletter" --no-ignore
```

### Sample `ignore_patterns.inc` File

The script creates this sample file automatically:

```text
# Gmail Cleaner - Ignored Patterns List
# Add email addresses or patterns to ignore (one per line)
# Lines starting with # are comments
# Use /pattern/ for regex matching (case-insensitive)

# Examples - Simple strings (partial matches):
newsletter@example.com          # Exact email
@spamdomain.com                 # Any email from this domain
no-reply@                        # Any no-reply address
notifications@                   # Any notification address

# Examples - Regex patterns (enclosed in //):
/.*@.*\.spam\.com$/            # Any email from .spam.com domains
/^noreply-.*@/                   # noreply-* addresses
/@mail\./                        # Contains @mail.
/@marketing\./                   # Contains @marketing.
/@newsletter\./                  # Contains @newsletter.

# System emails to ignore (simple strings):
mailer-daemon@
postmaster@

# Add your own patterns below:
```

### How Ignore Patterns Work

The ignore system supports two types of patterns:

1. **Simple String Patterns**: Case-insensitive partial matches
   - `newsletter@example.com` - matches any sender containing this exact string
   - `@spamdomain.com` - matches any email from this domain
   - `no-reply@` - matches any no-reply address

2. **Regex Patterns**: Enclosed in `/` for advanced matching
   - `/.*@.*\.spam\.com$/` - matches any email ending with .spam.com
   - `/^noreply-.*@/` - matches addresses starting with noreply-
   - `/@marketing\./` - matches any sender containing @marketing.

## Configuration Files

### Environment Directory (`.gmail_env/`)

- `credentials.json` - Your OAuth client credentials (600 permissions)
- `token.pickle` - Securely stored authentication token (600 permissions)

### Ignore Patterns File (`ignore_patterns.inc`)

- Created automatically on first run
- Located in your current working directory
- Supports both simple strings and regex patterns
- Lines starting with `#` are comments
- Regex patterns must be enclosed in `/`

## Safety Features

- ✅ **Dry Run Mode** - Preview deletions before executing
- ✅ **Multiple Confirmations** - Extra prompts for large batches and permanent deletions
- ✅ **Rate Limiting** - Prevents API quota exhaustion
- ✅ **Retry Logic** - Automatic retries with exponential backoff
- ✅ **Secure Token Storage** - Proper file permissions (600/700)
- ✅ **Ignore Patterns** - Filter out unwanted senders automatically using `ignore_patterns.inc`

## Command Line Options

### Search Options
| Option | Description |
|--------|-------------|
| `--before YYYY/MM/DD` | Search emails before date |
| `--after YYYY/MM/DD` | Search emails after date |
| `--subject TEXT` | Search in subject line |
| `--body TEXT` | Search in email body |
| `--sender EMAIL` | Search by sender |
| `--has-attachment` | Only emails with attachments |
| `--max N` | Maximum results (default: 100) |
| `--no-ignore` | Temporarily disable ignore patterns |

### AI Options
| Option | Description |
|--------|-------------|
| `--ai [PROMPT]` | Use AI to generate search query |
| `--ai-provider {openai,gemini,deepseek}` | AI provider (default: deepseek) |

### Actions
| Option | Description |
|--------|-------------|
| `--trash` | Move matching emails to trash |
| `--permanent` | Permanently delete (use with caution!) |
| `--dry-run` | Show what would be deleted |

### Display Options
| Option | Description |
|--------|-------------|
| `--show-full` | Show full email content |
| `--debug` | Enable debug logging |

### Ignore Management
| Option | Description |
|--------|-------------|
| `--ignore-file FILE` | Custom ignore patterns file (default: `ignore_patterns.inc`) |
| `--show-ignored` | Show current ignore patterns |
| `--add-ignore PATTERN` | Add pattern to ignore file |
| `--ignore-regex` | Used with `--add-ignore` to indicate pattern is regex |

## Examples

### Common Use Cases

```bash
# Find and trash old newsletters
./gmail_cleaner.py --subject "newsletter" --before 2023/01/01 --trash --dry-run
./gmail_cleaner.py --subject "newsletter" --before 2023/01/01 --trash

# Delete promotional emails from 2022, ignoring your regular senders
./gmail_cleaner.py --ai "promotional emails from 2022" --permanent --dry-run
./gmail_cleaner.py --ai "promotional emails from 2022" --permanent

# Find all emails with PDF attachments
./gmail_cleaner.py --has-attachment --body "filename:pdf"

# Clean up old notifications, ignoring system emails
./gmail_cleaner.py --subject "notification" --before 2023/06/01 --trash

# Search with multiple criteria
./gmail_cleaner.py --sender "@company.com" --after 2024/01/01 --has-attachment --max 500

# Add commonly ignored senders to patterns file
./gmail_cleaner.py --add-ignore "newsletter@"
./gmail_cleaner.py --add-ignore "/.*@.*\.spam\.com$/" --ignore-regex

# Preview what your ignore patterns are filtering
./gmail_cleaner.py --show-ignored

# Use a different ignore file for specific searches
./gmail_cleaner.py --subject "newsletter" --ignore-file work-patterns.inc
```

## Output Format

The tool displays emails in a clean table format:

```
┌─────┬─────────────────┬───────────────────────────────────┬──────────────────────────────────────────┬────────────────────────────────────────────┬──────────┐
│  #  │      Date       │              Sender               │                 Subject                  │                    Body                    │  Attach  │
├─────┼─────────────────┼───────────────────────────────────┼──────────────────────────────────────────┼────────────────────────────────────────────┼──────────┤
│  1  │ 2024-01-15 10:30│ newsletter@example.com            │ Weekly Newsletter - January 15           │ Check out our latest updates and ftures... │    📕    │
│  2  │ 2024-01-14 15:45│ notifications@social.com          │ You have 5 new notifications             │ John commented on your post: "Grea...      │    ❌    │
│  3  │ 2024-01-13 09:20│ team@company.com                  │ Meeting agenda for Friday                │ Please review the attached documen...      │   📎📎   │
└─────┴─────────────────┴───────────────────────────────────┴──────────────────────────────────────────┴────────────────────────────────────────────┴──────────┘

📎 Attachment Summary:
   📕 PDF: 1 emails
   📎📎 Multi: 1 emails
   ❌ None: 1 emails
   
   📊 Total with attachments: 2 emails
   📊 Total emails: 3 emails
```

## Security Notes

- All tokens and credentials are stored with strict file permissions (600/700)
- OAuth 2.0 used for authentication - no passwords stored
- Rate limiting prevents API abuse
- Dry runs available for all destructive operations
- Multiple confirmations required for permanent deletion
- Query sanitization prevents injection attacks
- Ignore patterns file is created with secure permissions (600 on Unix systems)

## File Structure

```
gmail-cleaner/
├── gmail_cleaner.py           # Main entry point
├── lib/
│   ├── auth.py                # Gmail authentication
│   ├── ai_providers.py        # AI providers (OpenAI, Gemini, DeepSeek)
│   ├── processor.py           # Email processing
│   ├── delete_manager.py      # Deletion with safety features
│   ├── display.py             # Rich table formatting
│   ├── ignore_manager.py      # Ignore patterns management
│   ├── prompts.py             # User confirmation dialogs
│   ├── decoder.py             # Email content decoding
│   ├── models.py              # Data models
│   ├── utils.py               # Utility functions
│   └── config.py              # Configuration constants
├── .gmail_env/                # Secure credentials directory
│   ├── credentials.json       # OAuth client credentials
│   └── token.pickle           # Authentication token
├── ignore_patterns.inc        # Auto-created ignore patterns file
└── requirements.txt           # Python dependencies
```

## License

This project is licensed under the GPL License - see the LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
