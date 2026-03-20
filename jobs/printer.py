from weasyprint import HTML
import cups
import os

# Convert html to pdf
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def convert_html_to_pdf():
    HTML(filename=os.path.join(ROOT_DIR, "temp_storage", "paper_final.html")).write_pdf(os.path.join(ROOT_DIR, "temp_storage", "paper_final.pdf"))
    return os.path.join(ROOT_DIR, "temp_storage", "paper_final.pdf")

# Print pdf
def print_pdf(pdf_path: str):
    conn = cups.Connection()
    printers = conn.getPrinters()
    printer_name = list(printers.keys())[0]

    options = {"copies" : "1", 
                "sides": "two-sided-long-edge",
                "ColorModel": "Gray"
            }

    job_id = conn.printFile(printer_name, pdf_path, "My Printing", options)
    return (f"Job submitted: {job_id}")

def print_paper():
    pdf_path = convert_html_to_pdf()
    print(print_pdf(pdf_path))
    
if __name__ == "__main__":
    print_paper()