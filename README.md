# Daily Newspaper Generator

A personal daily newspaper — automatically scraped, written by AI, and printed every morning.

The pipeline scrapes news from Telegram channels, processes it with an LLM into a formatted newspaper, renders it as HTML, converts to PDF, and sends it to a physical printer.

## How It Works

```
Telegram channels → raw news → AI sections → deduplicate → HTML layout → PDF → print
```

1. **Scrape** — pulls posts from configured Telegram channels into `temp_storage/raw_news.md`
2. **Summarize** — LLM writes each newspaper section from the raw feed
3. **Deduplicate** — LLM removes duplicate stories across sections
4. **Layout** — HTML is rendered with a newspaper-style CSS and a two-column layout
5. **Print** — Chrome headless converts HTML to PDF; CUPS sends it to the printer

## Sections

| Section | Description |
|---|---|
| Політика та гарячі новини | Politics & breaking news |
| Будапешт | Local Budapest news |
| Економіка | Economics |
| Фінанси | Finance & markets |
| Технології та ШІ | Technology & AI |
| Інше | Other |

## Project Structure

```
news/
├── main.py                  # Entry point
├── pipeline/
│   └── run.py               # Streamline workflow (default mode)
├── agent/
│   └── invoke.py            # LLM agent wrapper (OpenAI-compatible API)
├── jobs/
│   ├── scraper.py           # Telegram scraper
│   ├── cleaner.py           # Clears temp_storage before each run
│   ├── layout.py            # Post-processes HTML (two-column split, cost footer)
│   └── printer.py           # HTML → PDF via Chrome headless, then CUPS print
├── prompts/                 # System prompts and CSS for each section
├── temp_storage/            # Intermediate files (gitignored)
│   ├── raw_news.md
│   ├── summarized_paper.md
│   ├── paper_final.html
│   └── paper_final.pdf
├── telegram_channels.md     # List of Telegram channel usernames to scrape
├── user_preferences.md      # Optional: reader preferences injected into prompts
└── .env                     # API keys and model config (gitignored)
```

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

Chrome or Chromium must also be installed for PDF conversion (fallback: `weasyprint`).

### 2. Configure environment

Create a `.env` file in the project root:

```env
OPENAI_API_KEY=your_key_here
OPENAI_BASE_URL=https://api.openai.com
MODEL_NAME=gpt-4o-mini
MODEL_INPUT_PRICE_PER_1M=0.15
MODEL_OUTPUT_PRICE_PER_1M=0.60
```

### 3. Configure Telegram channels

Edit `telegram_channels.md` — one channel username per line (without `@`):

```
channel_username
another_channel
```

### 4. (Optional) Add reader preferences

Create `user_preferences.md` with any personal preferences — they will be appended to the section prompts.

### 5. Run manually

```bash
python3 main.py
```

## Modes

Controlled by the `MODE` variable in `main.py`:

| Mode | Description |
|---|---|
| `streamline` | Python drives the workflow; model only writes text. Reliable, works with smaller models. **(default)** |
| `agent` | Model drives the workflow via tool calls. Experimental, requires a capable model. |

## Automatic Daily Printing (macOS)

To run every morning at 7:30 automatically, set up a `launchd` job. See `LAUNCHD_SETUP.md` for full instructions (gitignored — contains local paths and credentials).

Quick reference:

```bash
# Check if the job is loaded
launchctl list | grep com.news.daily

# View logs
cat /tmp/news_daily.log
cat /tmp/news_daily_err.log
```

## Requirements

- Python 3.10+
- Google Chrome / Chromium (for PDF rendering)
- CUPS-compatible printer
- OpenAI-compatible API access
