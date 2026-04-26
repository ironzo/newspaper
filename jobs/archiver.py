import os
import shutil
from datetime import datetime, timedelta

ROOT_DIR    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HTML_PATH   = os.path.join(ROOT_DIR, "temp_storage", "paper_final.html")
ARCHIVE_DIR = os.path.join(ROOT_DIR, "archive")


def save_to_archive() -> str | None:
    if not os.path.exists(HTML_PATH) or os.path.getsize(HTML_PATH) == 0:
        return None
    os.makedirs(ARCHIVE_DIR, exist_ok=True)
    date_str = datetime.now().strftime("%Y-%m-%d")
    dest = os.path.join(ARCHIVE_DIR, f"{date_str}.html")
    shutil.copy2(HTML_PATH, dest)
    print(f"Paper archived to {dest}")
    return dest


def load_recent_summaries(n: int = 3) -> str:
    if not os.path.exists(ARCHIVE_DIR):
        return ""
    files = sorted(
        [f for f in os.listdir(ARCHIVE_DIR) if f.endswith(".html")],
        reverse=True,
    )[:n]
    if not files:
        return ""
    from bs4 import BeautifulSoup
    parts = []
    for fname in files:
        path = os.path.join(ARCHIVE_DIR, fname)
        with open(path, "r", encoding="utf-8") as f:
            soup = BeautifulSoup(f.read(), "html.parser")
        text = soup.get_text(separator="\n").strip()
        date = fname.replace(".html", "")
        parts.append(f"### Edition from {date}\n{text[:3000]}")
    return "\n\n".join(parts)


def prune_archive(keep_weeks: int = 12) -> None:
    if not os.path.exists(ARCHIVE_DIR):
        return
    cutoff = datetime.now() - timedelta(weeks=keep_weeks)
    for fname in os.listdir(ARCHIVE_DIR):
        if not fname.endswith(".html"):
            continue
        try:
            date = datetime.strptime(fname.replace(".html", ""), "%Y-%m-%d")
            if date < cutoff:
                os.remove(os.path.join(ARCHIVE_DIR, fname))
                print(f"Pruned old archive: {fname}")
        except ValueError:
            pass
