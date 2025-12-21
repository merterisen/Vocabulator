import fitz

def extract_texts_from_pdf(filepath):
    try:
        with fitz.open(filepath) as doc:
            texts = [page.get_text() for page in doc]
        return texts
    except Exception as e:
        raise e