import threading
from tkinter import filedialog
from core.nlp_manager import NLPManager
from core.pdf_manager import extract_texts_from_pdf

class VocabulatorController:
    """Bridge between ui and core Services."""
    def __init__(self, ui):
        self.ui = ui
        self.output_df = None # dataframe is stored here


    # =================================================================
    # UI EVENTS
    # =================================================================

    def browse_pdf(self):
        filename = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")])
        if filename:
            self.ui.set_pdf_path(filename)


    def browse_known_words(self):
        filename = filedialog.askopenfilename(filetypes=[("Excel/CSV", "*.csv *.xlsx")])
        if filename:
            self.ui.set_known_words_path(filename)


    def run_nlp(self):
        pdf_file_path = self.ui.pdf_file_path.get()
        language = self.ui.language.get()
        include_articles = self.ui.include_articles.get()
        known_words_file_path = self.ui.known_words_file_path.get()
        
        if not pdf_file_path:
            self.ui.show_error("Error", "Please select a PDF file first.")
            return

        # Lock UI
        self.ui.lock_ui()
        
        # Start Thread
        thread = threading.Thread(
            target=self._nlp_logic_thread, 
            args=(pdf_file_path, language, known_words_file_path, include_articles)
        )
        thread.daemon = True
        thread.start()


    def run_llm(self):
        pass


    def export_data(self, format_type):
        if self.output_df is None:
            self.ui.show_warning("Warning", "No data to export.")
            return
            
        try:
            if format_type == "csv":
                f = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")])
                if f: 
                    self.output_df.to_csv(f, index=False)
                    self.ui.show_info("Success", "Saved to CSV")
            else: # excel
                f = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel", "*.xlsx")])
                if f: 
                    self.output_df.to_excel(f, index=False)
                    self.ui.show_info("Success", "Saved to Excel")
            
        except Exception as e:
            self.ui.show_error("Export Error", str(e))



    # =================================================================
    # BACKGROUND LOGIC
    # =================================================================
    

    def _nlp_logic_thread(self, pdf_path, language, known_words_path, include_articles):
        try:
            self._update_status("Loading AI Model...")
            
            nlp_manager = NLPManager(language)
            nlp_manager.load_model()

            self._update_status("Loading known words...")
            known_set = nlp_manager.load_known_words(known_words_path)

            self._update_status("Reading PDF...")
            texts = extract_texts_from_pdf(pdf_path)

            self._update_status(f"Extracting words from {len(texts)} pages...")
            
            nlp_output_df = nlp_manager.extract_words(texts, known_set, include_articles=include_articles)
            
            self._on_nlp_success(nlp_output_df)

        except Exception as e:
            self._on_nlp_error(str(e))



    # =================================================================
    # THREAD-SAFE UI UPDATES
    # =================================================================

    def _update_status(self, message):
        self.ui.root.after(0, lambda: self.ui.update_status(message))


    def _on_nlp_success(self, output_df):
        def callback():
            self.output_df = output_df
            self.ui.update_table(output_df)
            self.ui.update_status("NLP Complete!")
            self.ui.unlock_ui()
        
        self.ui.root.after(0, callback)


    def _on_nlp_error(self, error_msg):
        def callback():
            self.ui.update_status("Error Occurred")
            self.ui.unlock_ui()
            self.ui.show_error("Processing Error", error_msg)
            
        self.ui.root.after(0, callback)
    


    def _on_llm_success(self, output_df):
        def callback():
            self.output_df = output_df
            self.ui.update_table(output_df)
            self.ui.update_status("LLM Complete!")
            self.ui.unlock_ui()
        
        self.ui.root.after(0, callback)

    
    def _on_llm_error(self, error_msg):
        def callback():
            self.ui.update_status("Error Occurred")
            self.ui.unlock_ui()
            self.ui.show_error("Processing Error", error_msg)
            
        self.ui.root.after(0, callback)

    
    