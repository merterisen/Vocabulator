import fitz

def extract_texts_from_pdf(filepath):
    doc = fitz.open(filepath)
    texts = [page.get_text() for page in doc]
    doc.close()
    return texts