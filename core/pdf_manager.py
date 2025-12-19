import fitz

def extract_text(filepath):
    doc = fitz.open(filepath)
    pages_text = [page.get_text() for page in doc]
    doc.close()
    return pages_text