import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import config
from core.pdf_processor import extract_text
from core.nlp_engine import NLPEngine

class Vocabulator:
    def __init__(self, root):
        self.root = root
        self.root.title(config.WINDOW_TITLE)
        self.root.geometry(config.WINDOW_SIZE)
        
        # --- State Variables ---
        self.current_df = None
        self.status = tk.StringVar(value="Ready")
        self.language = tk.StringVar(value="German")
        self.include_articles = tk.BooleanVar(value=False)
        
        # Variables to store file paths
        self.pdf_file_path = tk.StringVar()
        self.known_words_file_path = tk.StringVar()
        
        self._build_ui() # Run _build_ui() at start

    def _build_ui(self):
        """
        Creates all the visual elements (widgets) on the screen.
        """
        
        # SECTION 1: SELECT PDF
        select_pdf_frame = tk.LabelFrame(self.root, text="1. Select PDF", padx=10, pady=10)
        select_pdf_frame.pack(fill="x", padx=10, pady=5)

        self.select_pdf_entry = tk.Entry(select_pdf_frame, textvariable=self.pdf_file_path, state='readonly')
        self.select_pdf_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))

        select_pdf_button = tk.Button(select_pdf_frame, text="Browse", command=self._browse_pdf)
        select_pdf_button.pack(side="left")


        # CONTAINER for Language and Known Words side-by-side
        container_frame = tk.Frame(self.root)
        container_frame.pack(fill="x", padx=10, pady=5)

        
        # SECTION 2: LANGUAGE SELECTION (Left Side)
        select_language_frame = tk.LabelFrame(container_frame, text="2. Select Language", padx=10, pady=10)
        select_language_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))
        
        select_language_combobox = ttk.Combobox(select_language_frame, textvariable=self.language, values=list(config.LANGUAGES.keys()), state="readonly")
        select_language_combobox.pack(fill="x")

        include_articles_checkbutton = tk.Checkbutton(select_language_frame, text="Include Articles", variable=self.include_articles, onvalue=True, offvalue=False)
        include_articles_checkbutton.pack(anchor="w")


        # SECTION 3: KNOWN WORDS FILE (Right Side)
        known_words_frame = tk.LabelFrame(container_frame, text="3. Select Known Words (Optional)", padx=10, pady=10)
        known_words_frame.pack(side="right", fill="both", expand=True, padx=(5, 0))

        self.known_words_entry = tk.Entry(known_words_frame, textvariable=self.known_words_file_path, state='readonly')
        self.known_words_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))

        known_words_button = tk.Button(known_words_frame, text="Browse", command=self._browse_known_words)
        known_words_button.pack(side="left")


        # SECTION 4: RUN BUTTON AND STATUS
        self.run_button = tk.Button(self.root, text="RUN", command=self.start_processing, height=2, bg="#e1e1e1") 
        self.run_button.pack(fill="x", padx=20, pady=10)

        self.progress_bar = ttk.Progressbar(self.root, mode='indeterminate')
        self.progress_bar.pack(fill="x", padx=10)
        
        status_label = tk.Label(self.root, textvariable=self.status, fg="blue")
        status_label.pack(pady=5)


        # SECTION 5: RESULTS TABLE
        results_frame = tk.LabelFrame(self.root, text="Preview (Top 50)", padx=10, pady=10)
        results_frame.pack(fill="both", expand=True, padx=10, pady=5)

        results_scrollbar = ttk.Scrollbar(results_frame, orient="vertical")
        results_scrollbar.pack(side="right", fill="y")

        self.results_table = ttk.Treeview(results_frame, columns=("Word", "Count"), show="headings", yscrollcommand=results_scrollbar.set)
        self.results_table.heading("Word", text="Word")
        self.results_table.heading("Count", text="Frequency")
        self.results_table.column("Word", anchor="w")
        self.results_table.column("Count", anchor="center", width=100)
        self.results_table.pack(side="left", fill="both", expand=True)
        
        results_scrollbar.config(command=self.results_table.yview)


        # SECTION 6: EXPORT BUTTONS
        export_frame = tk.Frame(self.root, pady=10)
        export_frame.pack(fill="x")
        
        export_csv_button = tk.Button(export_frame, text="Export CSV", command=lambda: self.export_data("csv"))
        export_csv_button.pack(side="left", padx=20, expand=True)
        
        export_excel_button = tk.Button(export_frame, text="Export Excel", command=lambda: self.export_data("excel"))
        export_excel_button.pack(side="right", padx=20, expand=True)




    # =================================================================
    # HELPER FUNCTIONS
    # =================================================================

    def _browse_pdf(self):
        filename = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")])
        if filename:
            self.pdf_file_path.set(filename)

    def _browse_known_words(self):
        filename = filedialog.askopenfilename(filetypes=[("Excel/CSV", "*.csv *.xlsx")])
        if filename:
            self.known_words_file_path.set(filename)

    def _update_table(self, dataframe):
        """Clears the table and adds new rows"""
        # 1. Clear existing tables
        for item in self.results_table.get_children():
            self.results_table.delete(item)
            
        if dataframe is None or dataframe.empty:
            return

        # 2. Insert top 50 rows
        for _, row in dataframe.head(50).iterrows():
            self.results_table.insert("", "end", values=(row['word'], row['count']))


    # =================================================================
    # LOGIC FUNCTIONS
    # =================================================================

    def start_processing(self):
        # Get path directly from the variable we bound to the Entry widget
        pdf_path = self.pdf_file_path.get()
        
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
            self.status.set("Loading AI Model...")
            nlpengine = NLPEngine(self.language.get())
            nlpengine.load_model()

            # Load Known Words (Getting path from variable)
            self.status.set("Loading known words...")
            known_path = self.known_words_file_path.get()
            known_set = nlpengine.load_known_words(known_path)

            # Read PDF
            self.status.set("Reading PDF...")
            pages = extract_text(pdf_path)

            # Analyze
            self.status.set(f"Extracting words from {len(pages)} pages...")
            self.current_df = nlpengine.process_text_pages(pages, known_set, include_articles=self.include_articles.get())

            # Update UI (Must be done on main thread)
            self.root.after(0, self._on_success)

        except Exception as e:
            self.root.after(0, lambda: self._on_error(str(e)))

    def _on_success(self):
        self.progress_bar.stop()
        self.run_button.config(state="normal")
        self.status.set("Analysis Complete!")
        self._update_table(self.current_df)

    def _on_error(self, error_msg):
        self.progress_bar.stop()
        self.run_button.config(state="normal")
        self.status.set("Error Occurred")
        messagebox.showerror("Processing Error", error_msg)

    def export_data(self, format_type):
        if self.current_df is None:
            messagebox.showwarning("Warning", "No data to export. Run analysis first.")
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