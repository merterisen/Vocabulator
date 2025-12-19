import threading
from tkinter import filedialog
from core.nlp_manager import NLPManager
from core.pdf_manager import extract_text

class VocabulatorController:
    """Bridge between ui and core Services."""
    def __init__(self, view):
        self.view = view
        self.current_dataframe = None 


    # =================================================================
    # UI EVENTS
    # =================================================================

    def browse_pdf(self):
        filename = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")])
        if filename:
            self.view.set_pdf_path(filename)


    def browse_known_words(self):
        filename = filedialog.askopenfilename(filetypes=[("Excel/CSV", "*.csv *.xlsx")])
        if filename:
            self.view.set_known_words_path(filename)


    def run_analysis(self):
        pdf_path = self.view.pdf_file_path.get()
        language = self.view.language.get()
        include_articles = self.view.include_articles.get()
        known_words_path = self.view.known_words_file_path.get()
        
        if not pdf_path:
            self.view.show_error("Error", "Please select a PDF file first.")
            return

        # Lock UI
        self.view.lock_ui()
        
        # Start Thread
        thread = threading.Thread(
            target=self._process_logic_thread, 
            args=(pdf_path, language, known_words_path, include_articles)
        )
        thread.daemon = True
        thread.start()


    def export_data(self, format_type):
        """Exports the current dataframe to CSV or Excel."""

        if self.current_dataframe is None:
            self.view.show_warning("Warning", "No data to export.")
            return
            
        try:
            if format_type == "csv":
                f = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")])
                if f: 
                    self.current_dataframe.to_csv(f, index=False)
                    self.view.show_info("Success", "Saved to CSV")
            else: # excel
                f = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel", "*.xlsx")])
                if f: 
                    self.current_dataframe.to_excel(f, index=False)
                    self.view.show_info("Success", "Saved to Excel")
            
        except Exception as e:
            self.view.show_error("Export Error", str(e))


    # =================================================================
    # BACKGROUND LOGIC
    # =================================================================

    def _process_logic_thread(self, pdf_path, language, known_words_path, include_articles):
        """
        Runs in background thread. Calls Services.
        """
        try:
            self._update_status_safe("Loading AI Model...")
            
            manager = NLPManager(language)
            manager.load_model()

            self._update_status_safe("Loading known words...")
            known_set = manager.load_known_words(known_words_path)

            self._update_status_safe("Reading PDF...")
            pages = extract_text(pdf_path)

            self._update_status_safe(f"Extracting words from {len(pages)} pages...")
            
            result_df = manager.process_text_pages(pages, known_set, include_articles=include_articles)
            
            self._on_analysis_success_safe(result_df)

        except Exception as e:
            self._on_analysis_error_safe(str(e))


    # =================================================================
    # THREAD-SAFE UI UPDATES
    # =================================================================

    def _update_status_safe(self, message):
        self.view.root.after(0, lambda: self.view.update_status(message))

    def _on_analysis_success_safe(self, df):
        def callback():
            self.current_dataframe = df # Save state in controller
            self.view.update_table(df)
            self.view.update_status("Analysis Complete!")
            self.view.unlock_ui()
        
        self.view.root.after(0, callback)

    def _on_analysis_error_safe(self, error_msg):
        def callback():
            self.view.update_status("Error Occurred")
            self.view.unlock_ui()
            self.view.show_error("Processing Error", error_msg)
            
        self.view.root.after(0, callback)