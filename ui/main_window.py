import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import config
from ui.components import FileSelector, ResultTable
from core.pdf_processor import extract_text
from core.nlp_engine import NLPEngine

class Vocabulator:
    def __init__(self, root):
        self.root = root
        self.root.title(config.WINDOW_TITLE)
        self.root.geometry(config.WINDOW_SIZE)
        
        # State
        self.current_df = None
        self.status_text = tk.StringVar(value="Ready")
        self.language_var = tk.StringVar(value="German")
        
        self._build_ui() # Run _build_ui auto

    def _build_ui(self):
        # 1. Select PDF
        self.file_selector = FileSelector(self.root, "1. Select PDF", [("PDF Files", "*.pdf")])
        self.file_selector.pack(fill="x", padx=10, pady=5)

        # Component for Language and Known Words Sections Side by Side
        frame_options = tk.Frame(self.root)
        frame_options.pack(fill="x", padx=10, pady=5)
        
        # 2. Language
        frame_language = tk.LabelFrame(frame_options, text="2. Language", padx=10, pady=10)
        frame_language.pack(side="left", fill="both", expand=True, padx=(0, 5))
        
        combo = ttk.Combobox(frame_language, textvariable=self.language_var, values=list(config.SPACY_MODELS.keys()), state="readonly")
        combo.pack(fill="x")

        # 3. Known Words
        self.known_words = FileSelector(frame_options, "3. Known Words (Optional)", [("Excel/CSV", "*.csv *.xlsx")], width=15)
        self.known_words.pack(side="right", fill="both", expand=True, padx=(5, 0))

        # RUN Button
        self.run_button = tk.Button(self.root, text="RUN", command=self.start_processing, height=2)
        self.run_button.pack(fill="x", padx=20, pady=10)

        # Progress Bar
        self.progress_bar = ttk.Progressbar(self.root, mode='indeterminate')
        self.progress_bar.pack(fill="x", padx=10)
        tk.Label(self.root, textvariable=self.status_text, fg="blue").pack(pady=5)

        # Results Area
        self.result_table = ResultTable(self.root, "Preview (Top 50)")
        self.result_table.pack(fill="both", expand=True, padx=10, pady=5)

        # Export Buttons
        frame_export = tk.Frame(self.root, pady=10)
        frame_export.pack(fill="x")
        tk.Button(frame_export, text="Export CSV", command=lambda: self.export("csv")).pack(side="left", padx=20, expand=True)
        tk.Button(frame_export, text="Export Excel", command=lambda: self.export("excel")).pack(side="right", padx=20, expand=True)

    def start_processing(self):
        pdf_path = self.file_selector.get_path()
        if not pdf_path:
            messagebox.showerror("Error", "Please select a PDF file first.")
            return

        # Lock UI
        self.run_button.config(state="disabled")
        self.progress_bar.start(10)
        
        # Start Thread
        thread = threading.Thread(target=self._process_logic, args=(pdf_path,))
        thread.daemon = True
        thread.start()

    def _process_logic(self, pdf_path):
        """
        Runs in background thread. Orchestrates the Core classes.
        """
        try:
            # Setup NLPEngine
            self.status_text.set("Loading AI Model...")
            nlpengine = NLPEngine(self.language_var.get())
            nlpengine.load_model()

            # Load Known Words
            self.status_text.set("Loading known words...")
            known_path = self.known_words.get_path()
            known_set = nlpengine.load_known_words(known_path)

            # Read PDF
            self.status_text.set("Reading PDF...")
            pages = extract_text(pdf_path)

            # Analyze
            self.status_text.set(f"Extracting words from {len(pages)} pages...")
            self.current_df = nlpengine.process_text_pages(pages, known_set)

            # Update UI (Must be done on main thread)
            self.root.after(0, self._on_success)

        except Exception as e:
            self.root.after(0, lambda: self._on_error(str(e)))

    def _on_success(self):
        self.progress_bar.stop()
        self.run_button.config(state="normal")
        self.status_text.set("Analysis Complete!")
        self.result_table.update_data(self.current_df)

    def _on_error(self, error_msg):
        self.progress_bar.stop()
        self.run_button.config(state="normal")
        self.status_text.set("Error Occurred")
        messagebox.showerror("Processing Error", error_msg)

    def export(self, format_type):
        if self.current_df is None:
            return
            
        try:
            if format_type == "csv":
                f = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")])
                if f: 
                    self.current_df.to_csv(f, index=False)
            else:
                f = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel", "*.xlsx")])
                if f: 
                    self.current_df.to_excel(f, index=False)
                
            if f: messagebox.showinfo("Success", f"Saved to {format_type.upper()}")
            
        except Exception as e:
            messagebox.showerror("Export Error", str(e))