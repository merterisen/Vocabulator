import fitz

def extract_texts_from_pdf(filepath):
    with fitz.open(filepath) as doc:
        texts = [page.get_text() for page in doc]
    return texts