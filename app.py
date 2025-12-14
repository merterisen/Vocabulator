import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import fitz  # PyMuPDF
import spacy
import pandas as pd
import threading
import sys

class Vocabulator:
    def __init__(self, root):
        self.root = root
        self.root.title("Vocabulator")
        self.root.geometry("600x650")

        # Configuration variables
        self.filepath = tk.StringVar()
        self.known_words_filepath = tk.StringVar() 
        self.language = tk.StringVar(value="German")
        self.status = tk.StringVar(value="Ready")
        self.df_result = None

        # Language Model Mapping
        self.models = {
            "German": "de_core_news_sm",
            "French": "fr_core_news_sm",
            "Spanish": "es_core_news_sm"
        }

        self._setup_ui()

    def _setup_ui(self):
        # 1. File Selection Frame
        frame_file = tk.LabelFrame(self.root, text="1. Select PDF Book", padx=10, pady=10)
        frame_file.pack(fill="x", padx=10, pady=5)

        tk.Entry(frame_file, textvariable=self.filepath, width=50).pack(side="left", padx=5)
        tk.Button(frame_file, text="Browse", command=self.browse_file).pack(side="left")

        # Container for Language and Known Words (Side by Side)
        frame_options = tk.Frame(self.root)
        frame_options.pack(fill="x", padx=10, pady=5)

        # 2. Language Selection Frame (Left Side)
        frame_lang = tk.LabelFrame(frame_options, text="2. Select Language", padx=10, pady=10)
        frame_lang.pack(side="left", fill="both", expand=True, padx=(0, 5))

        languages = list(self.models.keys())
        dropdown = ttk.Combobox(frame_lang, textvariable=self.language, values=languages, state="readonly")
        dropdown.current(0)
        dropdown.pack(fill="x", padx=5, pady=5)

        # 3. Known Words Filter Frame (Right Side)
        frame_known = tk.LabelFrame(frame_options, text="3. Known Words (Optional)", padx=10, pady=10)
        frame_known.pack(side="right", fill="both", expand=True, padx=(5, 0))

        tk.Entry(frame_known, textvariable=self.known_words_filepath, width=15).pack(side="left", padx=5, fill="x", expand=True)
        tk.Button(frame_known, text="Upload", command=self.browse_known_file).pack(side="left")

        # 4. Main Action Button
        frame_action = tk.Frame(self.root, pady=5)
        frame_action.pack(fill="x", padx=10)
        
        # Centered button with fixed width
        btn_run = tk.Button(frame_action, text="RUN VOCABULATOR", command=self.start_extraction_thread, height=2, width=30)
        btn_run.pack() 

        # 5. Status & Progress
        self.progress_bar = ttk.Progressbar(self.root, mode='indeterminate')
        self.progress_bar.pack(fill="x", padx=10, pady=(10, 0))
        
        tk.Label(self.root, textvariable=self.status, fg="blue").pack(pady=5)

        # 6. Preview Area
        frame_preview = tk.LabelFrame(self.root, text="Preview (Top 50 words)", padx=10, pady=10)
        frame_preview.pack(fill="both", expand=True, padx=10, pady=5)

        # Columns
        self.tree = ttk.Treeview(frame_preview, columns=("Word", "Count"), show="headings")
        self.tree.heading("Word", text="Word (Lemma)")
        self.tree.heading("Count", text="Frequency")
        
        # Center align the count column
        self.tree.column("Count", anchor="center", width=100)
        self.tree.column("Word", anchor="w")
        
        self.tree.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(frame_preview, orient="vertical", command=self.tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=scrollbar.set)

        # 7. Export Buttons
        frame_export = tk.Frame(self.root, pady=10)
        frame_export.pack(fill="x")
        tk.Button(frame_export, text="Export to CSV", command=lambda: self.export_data("csv")).pack(side="left", padx=20, expand=True)
        tk.Button(frame_export, text="Export to Excel", command=lambda: self.export_data("excel")).pack(side="right", padx=20, expand=True)

    def browse_file(self):
        filename = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")])
        if filename:
            self.filepath.set(filename)

    def browse_known_file(self):
        filename = filedialog.askopenfilename(filetypes=[("Excel or CSV", "*.csv *.xlsx *.xls")])
        if filename:
            self.known_words_filepath.set(filename)

    def show_error_safe(self, title, message):
        """Thread-safe way to show error messages."""
        self.root.after(0, lambda: messagebox.showerror(title, message))

    def start_extraction_thread(self):
        if not self.filepath.get():
            messagebox.showerror("Error", "Please upload a PDF file first.")
            return
        
        # Disable UI elements during processing
        self.progress_bar.start(10)
        self.status.set("Loading NLP model...")
        
        # Run in separate thread
        thread = threading.Thread(target=self.process_pdf)
        thread.daemon = True
        thread.start()

    def process_pdf(self):
        try:
            selected_lang = self.language.get()
            model_name = self.models[selected_lang]

            # --- STEP 0: Load Known Words (if any) ---
            known_words = set()
            k_path = self.known_words_filepath.get()
            if k_path:
                self.status.set("Loading known words filter...")
                try:
                    if k_path.endswith(('.xls', '.xlsx')):
                        df_k = pd.read_excel(k_path)
                    else:
                        # Assume CSV
                        df_k = pd.read_csv(k_path)
                    
                    # Heuristic: Find the column that contains words
                    # If there's a column named "Word" (case insensitive), use it.
                    # Otherwise, use the first column.
                    target_col = None
                    for col in df_k.columns:
                        if "word" in str(col).lower():
                            target_col = col
                            break
                    
                    if target_col is None:
                        target_col = df_k.columns[0] # Default to first column
                    
                    # Convert to set for O(1) lookup
                    # We convert everything to lowercase strings
                    known_words = set(df_k[target_col].astype(str).str.lower().str.strip())
                    
                    print(f"Loaded {len(known_words)} known words.")

                except Exception as e:
                    self.show_error_safe("Known Words Error", f"Could not read filter file: {str(e)}")
                    self.root.after(0, self.reset_ui)
                    return

            # --- STEP 1: Load Spacy Model ---
            try:
                nlp = spacy.load(model_name, disable=["ner", "parser"])
            except OSError:
                self.show_error_safe("Model Not Found", 
                                     f"Model '{model_name}' not found.\n\nPlease run:\npython -m spacy download {model_name}")
                self.root.after(0, self.reset_ui)
                return

            # --- STEP 2: Extract Text from PDF ---
            self.status.set("Reading PDF...")
            try:
                doc = fitz.open(self.filepath.get())
                pages_text = [page.get_text() for page in doc]
            except Exception as e:
                self.show_error_safe("PDF Error", f"Could not read PDF: {str(e)}")
                self.root.after(0, self.reset_ui)
                return
            
            # --- STEP 3: NLP Processing ---
            self.status.set(f"Analyzing {len(pages_text)} pages... this may take time.")
            
            word_freq = {}
            valid_pos = {"NOUN", "VERB", "ADJ", "ADV"} 

            for doc in nlp.pipe(pages_text, batch_size=20):
                for token in doc:
                    if (token.is_alpha and 
                        not token.is_stop and 
                        len(token.lemma_) > 2 and
                        token.pos_ in valid_pos):
                        
                        lemma = token.lemma_.lower()
                        
                        # FILTER: Skip if word is in known_words
                        if lemma in known_words:
                            continue

                        if lemma in word_freq:
                            word_freq[lemma] += 1
                        else:
                            word_freq[lemma] = 1

            # Create DataFrame
            data = list(word_freq.items())
            self.df_result = pd.DataFrame(data, columns=['word', 'count'])
            
            if not self.df_result.empty:
                self.df_result = self.df_result.sort_values(by='count', ascending=False)
            
            self.root.after(0, self.update_preview)

        except Exception as e:
            self.show_error_safe("Processing Error", str(e))
            self.root.after(0, self.reset_ui)

    def update_preview(self):
        self.progress_bar.stop()
        self.status.set("Extraction Complete!")
        
        # Clear current list
        for i in self.tree.get_children():
            self.tree.delete(i)

        # Insert top 50
        if self.df_result is not None and not self.df_result.empty:
            for _, row in self.df_result.head(50).iterrows():
                self.tree.insert("", "end", values=(row['word'], row['count']))
        else:
            self.status.set("No valid vocabulary found.")

    def reset_ui(self):
        self.progress_bar.stop()
        self.status.set("Ready")

    def export_data(self, filetype):
        if self.df_result is None or self.df_result.empty:
            messagebox.showwarning("Warning", "No data to export.")
            return

        try:
            if filetype == "csv":
                f = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")])
                if f:
                    self.df_result.to_csv(f, index=False)
                    messagebox.showinfo("Success", "Saved to CSV")
            
            elif filetype == "excel":
                try:
                    import openpyxl
                except ImportError:
                    messagebox.showerror("Missing Dependency", "Please install 'openpyxl' to export to Excel:\npip install openpyxl")
                    return

                f = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel", "*.xlsx")])
                if f:
                    self.df_result.to_excel(f, index=False)
                    messagebox.showinfo("Success", "Saved to Excel")
                    
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to save file:\n{str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = Vocabulator(root)
    root.mainloop()