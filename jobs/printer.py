import os
import subprocess
import cups

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HTML_PATH = os.path.join(ROOT_DIR, "temp_storage", "paper_final.html")
PDF_PATH  = os.path.join(ROOT_DIR, "temp_storage", "paper_final.pdf")

# Chrome / Chromium paths to try (macOS + Linux)
CHROME_CANDIDATES = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
    "google-chrome",
    "chromium-browser",
    "chromium",
]


def _find_chrome() -> str | None:
    for path in CHROME_CANDIDATES:
        if os.path.isabs(path):
            if os.path.exists(path):
                return path
        else:
            result = subprocess.run(["which", path], capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.strip()
    return None


def convert_html_to_pdf_chrome(chrome: str) -> str:
    """High-quality PDF via Chrome headless — preserves all CSS perfectly."""
    subprocess.run([
        chrome,
        "--headless=new",
        "--disable-gpu",
        "--no-sandbox",
        "--print-to-pdf-no-header",
        "--virtual-time-budget=5000",
        f"--print-to-pdf={PDF_PATH}",
        f"file://{HTML_PATH}",
    ], check=True, capture_output=True)
    return PDF_PATH


def convert_html_to_pdf_weasyprint() -> str:
    """Fallback: weasyprint (less accurate CSS rendering)."""
    from weasyprint import HTML
    HTML(filename=HTML_PATH).write_pdf(PDF_PATH)
    return PDF_PATH


def convert_html_to_pdf() -> str:
    chrome = _find_chrome()
    if chrome:
        print(f"Using Chrome headless: {chrome}")
        return convert_html_to_pdf_chrome(chrome)
    print("Chrome not found, falling back to weasyprint.")
    return convert_html_to_pdf_weasyprint()



def print_pdf(pdf_path: str) -> str:
    conn = cups.Connection()
    printers = conn.getPrinters()
    if not printers:
        return "No printers found."
    printer_name = list(printers.keys())[0]
    options = {
        "copies": "1",
        "sides": "two-sided-long-edge",
        "ColorModel": "Gray",
    }
    job_id = conn.printFile(printer_name, pdf_path, "The IRs", options)
    return f"Job submitted: {job_id}"


def print_paper():
    if not os.path.exists(HTML_PATH) or os.path.getsize(HTML_PATH) == 0:
        print(f"Cannot print: {HTML_PATH} not found or empty.")
        return
    print("Converting HTML to PDF...")
    pdf_path = convert_html_to_pdf()
    print("Sending to printer...")
    result = print_pdf(pdf_path)
    print(result)


if __name__ == "__main__":
    print_paper()
