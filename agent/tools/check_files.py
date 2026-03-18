import os

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(os.path.dirname(CURRENT_DIR))

check_file_tool = {
    "type": "function",
    "function": {
        "name": "check_file",
        "description": "Checks if a file exists and returns its content. Paths are relative to the project root (e.g. 'temp_storage/raw_news.md').",
        "parameters": {
            "type": "object",
            "properties": {
                "file_name": { "type": "string" }
            },
            "required": ["file_name"]
        }
    }
}

def check_file(file_name: str) -> str:
    file_name = file_name.lstrip("/")
    path = os.path.join(ROOT_DIR, file_name)
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return f"File {file_name} not found"
