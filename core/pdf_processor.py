import fitz  # PyMuPDF

class PdfProcessor:
    """
    Responsible solely for extracting raw text from PDF files.
    """
    
    def extract_text(self, filepath):
        """
        Opens a PDF and returns a list of strings (one per page).
        """
        # No try/except needed here. If this fails, the error will 
        # bubble up to the UI, which is already listening for errors.
        doc = fitz.open(filepath)
        pages_text = [page.get_text() for page in doc]
        doc.close()
        return pages_text