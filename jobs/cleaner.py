# TODO: Create a job to clean data from temp files on startup.
import os
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PLACEHOLDER_FILES = [
    "raw_news.md",
    "summarized_paper.md",
    "paper_final.html",
    "paper_final.pdf",
]

def clean_temp_files():
    temp_dir = os.path.join(ROOT_DIR, "temp_storage")
    os.makedirs(temp_dir, exist_ok=True)
    for filename in os.listdir(temp_dir):
        filepath = os.path.join(temp_dir, filename)
        if os.path.isfile(filepath):
            os.remove(filepath)
    for filename in PLACEHOLDER_FILES:
        open(os.path.join(temp_dir, filename), "w").close()

if __name__ == "__main__":
    clean_temp_files()