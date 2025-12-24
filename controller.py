import threading
from tkinter import filedialog
from managers.nlp_manager import NLPManager
from managers.pdf_manager import extract_texts_from_pdf
from managers.llm_manager import LLMManager
import config
import math

class VocabulatorController:
    """Bridge between ui and core Services."""
    def __init__(self, ui):
        self.ui = ui
        self.output_df = None # dataframe is stored here


    # =================================================================
    # GLOBAL FUNCTIONS
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
            self.ui.show_error("Error", "Please select a PDF file.")
            return
        
        if not language:
            self.ui.show_error("Error", "Please select a language.")
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
        if self.output_df is None or self.output_df.empty:
            self.ui.show_error("Error", "No words found. Please run NLP first.")
            return

        language = self.ui.language.get()
        translate_language = self.ui.translate_language.get()

        llm_model = self.ui.llm_model.get()
        api_key = self.ui.api_key.get()

        if not llm_model:
            self.ui.show_error("Error", "Please select a LLM Model.")
            return
        
        if not translate_language:
            self.ui.show_error("Error", "Please select a translation language.")
            return
        
        if not api_key:
            self.ui.show_error("Error", "Please enter an API Key.")
            return
        
        llm_model_config = config.LLM_MODELS.get(llm_model)

        if llm_model_config:
            total_words = len(self.output_df)
            batch_size = config.LLM_BATCH_SIZE
            num_batches = math.ceil(total_words / batch_size)

            # Heuristic Estimation
            fixed_prompt_overhead = 250
            per_word_input_tokens = 5

            input_tokens = (num_batches * fixed_prompt_overhead) + (total_words * per_word_input_tokens)
            output_tokens = total_words * 80 # ~80 tokens per word (JSON Structure + Sentence + Translation)

            input_price_per_1m = llm_model_config.get("input_price", 0)
            output_price_per_1m = llm_model_config.get("output_price", 0)

            estimated_cost = (input_tokens / 1_000_000 * input_price_per_1m) + (output_tokens / 1_000_000 * output_price_per_1m)

            if estimated_cost < 0.01:
                estimated_cost_text = "< $0.01"
            else:
                estimated_cost_text = f"~${estimated_cost:.2f}"
            
            llm_confirmation_message = (
                f"You are about to process ~{input_tokens + output_tokens} tokens using {llm_model}.\n\n"
                f"Estimated Cost: {estimated_cost_text} USD\n"
                "(Based on token usage estimates)\n\n"
                "Do you want to proceed?"
            )

            if not self.ui.show_confirmation("Confirm Cost", llm_confirmation_message):
                return

        # Lock UI
        self.ui.lock_ui()

        # Start Thread
        thread = threading.Thread(
            target=self._llm_logic_thread,
            args=(llm_model, api_key, language, translate_language)
        )
        thread.daemon = True
        thread.start()
    

    def remove_threshold(self):
        if self.output_df is None:
            self.ui.show_error("Warning", "No data to filter.")
            return
        
        try:
            threshold_str = self.ui.count_threshold.get()
            threshold = int(threshold_str)
        except ValueError:
            self.ui.show_error("Error", "Please enter a number.")
            return
        
        if self.ui.show_confirmation("Confirm Threshold", f"This will remove words with count less equal than {threshold} ?"):
             original_count = len(self.output_df)

             self.output_df = self.output_df[self.output_df['count'] > threshold]

             new_count = len(self.output_df)
             
             self.ui.update_preview(self.output_df)
             self.ui.show_info("Success", f"Removed {original_count - new_count} words. Remaining: {new_count}") 


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
    # LOCAL FUNCTIONS
    # =================================================================
    

    def _nlp_logic_thread(self, pdf_path, language, known_words_path, include_articles):
        try:
            self._update_status("Loading NLP Model...")
            
            nlp_manager = NLPManager(language)
            nlp_manager.load_model()

            self._update_status("Loading known words...")
            known_words = nlp_manager.load_known_words(known_words_path)

            self._update_status("Reading PDF...")
            texts = extract_texts_from_pdf(pdf_path)

            self._update_status(f"Extracting words from {len(texts)} pages...")
            
            nlp_output_df = nlp_manager.extract_words(texts, known_words, include_articles=include_articles)
            
            self._on_nlp_success(nlp_output_df)

        except Exception as e:
            self._on_nlp_error(str(e))
    

    def _llm_logic_thread(self, llm_model, api_key, language, translate_language):
        try:
            self._update_status("Connecting to LLM...")
            llm_manager = LLMManager(llm_model, api_key)

            self._update_status("Creating translates and sentences...")
            llm_output_df = llm_manager.create_translates(self.output_df, language, translate_language, update_callback=self._update_status)

            self._on_llm_success(llm_output_df)

        except Exception as e:
            self._on_llm_error(str(e))



    def _update_status(self, message):
        self.ui.root.after(0, lambda: self.ui.update_status(message))



    def _on_nlp_success(self, output_df):
        def callback():
            self.output_df = output_df
            self.ui.update_preview(output_df)
            self.ui.update_status("NLP Complete!")
            self.ui.unlock_ui()
        
        self.ui.root.after(0, callback)



    def _on_nlp_error(self, error_msg):
        def callback():
            self.ui.update_status("Error Occurred During NLP")
            self.ui.unlock_ui()
            self.ui.show_error("Processing Error During NLP", error_msg)
            
        self.ui.root.after(0, callback)
    


    def _on_llm_success(self, output_df):
        def callback():
            self.output_df = output_df
            self.ui.update_preview(output_df)
            self.ui.update_status("LLM Complete!")
            self.ui.unlock_ui()
        
        self.ui.root.after(0, callback)

    

    def _on_llm_error(self, error_msg):
        def callback():
            self.ui.update_status("Error Occurred During LLM")
            self.ui.unlock_ui()
            self.ui.show_error("Processing Error During LLM", error_msg)
            
        self.ui.root.after(0, callback)

    
    