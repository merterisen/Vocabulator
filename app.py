import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import fitz  # PyMuPDF
import spacy
import re
from collections import Counter
import pandas as pd
from spellchecker import SpellChecker
import io
from pathlib import Path
from typing import List, Dict, Optional, Any
from spacy.language import Language
import threading

SUPPORTED_LANGUAGES = {
    "English": {"spacy": "en_core_web_sm", "spellchecker": "en"},
    "German (Deutsch)": {"spacy": "de_core_news_sm", "spellchecker": "de"},
}

STOPWORDS_INFO_TEXT = (
    "Stopwords are very common words like 'and', 'the', 'is' or their equivalents "
    "in other languages. Removing them helps focus on the more meaningful "
    "words in the text."
)

SPELLCHECK_INFO_TEXT = (
    "Spell checking removes words not found in the selected language's dictionary, "
    "helping to filter out noise, proper nouns, or typographical errors.\n\n"
)

# A simple cache for loaded spaCy models
SPACY_MODEL_CACHE = {}

# Global variable to hold the last results DataFrame for downloading
LAST_DF_RESULTS = None



def load_spacy_model(model_name: str) -> Optional[Language]:
    """Loads and caches a spaCy language model."""

    if model_name in SPACY_MODEL_CACHE:
        return SPACY_MODEL_CACHE[model_name]
    
    try: # Try to load the model
        nlp = spacy.load(model_name)
        SPACY_MODEL_CACHE[model_name] = nlp
        return nlp
    except OSError: # Show an error if the model isn't downloaded
        messagebox.showerror(
            "Model Not Found",
            f"SpaCy model '{model_name}' not found. \n\n"
            f"Please download it by running: \n"
            f"python -m spacy download {model_name}"
        )
        return None

def extract_text_from_pdf(pdf_bytes: bytes) -> Optional[str]:
    """Extracts raw text from PDF bytes."""

    try:
        with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
            raw_text = "".join(page.get_text("text") for page in doc)
        
        if not raw_text.strip():
            messagebox.showwarning("Empty PDF", "No text could be extracted from the PDF, or the file is empty.")
            return None
        
        return raw_text
    
    except Exception as e:
        messagebox.showerror("PDF Error", f"Error reading PDF file: {e}")
        return None

def lemmatize_text(raw_text: str, nlp: Language, remove_stopwords: bool) -> List[str]:
    """Cleans, tokenizes, and lemmatizes text using spaCy."""
    
    # Word characters, whitespace, and hyphens.
    cleaned_text = re.sub(r"[^\w\s-]", "", raw_text)
    cleaned_text = re.sub(r"\s+", " ", cleaned_text).strip()

    spacy_doc = nlp(cleaned_text)

    # Tokenize, lemmatize, and filter
    lemmas = [word.lemma_.lower() for word in spacy_doc if word.is_alpha and len(word.lemma_) > 1]

    if remove_stopwords:
        stop_words = nlp.Defaults.stop_words
        lemmas = [lemma for lemma in lemmas if lemma not in stop_words]

    return lemmas

def apply_spellcheck(lemmas: List[str], spellchecker_code: Optional[str]) -> List[str]:
    """Filters a list of lemmas against a dictionary, if available."""
    
    if not spellchecker_code:
        return lemmas
    
    try:
        spell = SpellChecker(language=spellchecker_code)
        known_words = spell.known(lemmas)
        filtered_lemmas = [lemma for lemma in lemmas if lemma in known_words]

        if lemmas and not filtered_lemmas:
            messagebox.showwarning(
                "Spellcheck Warning",
                "Spell checking filtered out all words. This might be due to "
                "limited dictionary coverage. Proceeding with words before spell check."
            )
            return lemmas
        
        return filtered_lemmas

    except Exception as e:
        messagebox.showwarning(
            "Spellcheck Error",
            f"Could not apply spell checking for '{spellchecker_code}': {e}. "
            "Skipping spell check."
        )
        return lemmas

def to_excel(df: pd.DataFrame) -> bytes:
    """Converts a DataFrame to an in-memory Excel file (bytes)."""

    output = io.BytesIO()

    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='WordAnalysis')

    return output.getvalue()

def generate_word_frequency(
    pdf_bytes: bytes, 
    language_details: Dict[str, Any], 
    remove_stopwords: bool, 
    enable_spellcheck: bool,
    status_label: ttk.Label
) -> Optional[pd.DataFrame]:
    """
    Main orchestration function to process PDF bytes into a word frequency DataFrame.
    """
    def update_status(message):
        # We need to update the GUI from the main thread
        root.after(0, lambda: status_label.config(text=message))

    update_status("Reading PDF file...")
    raw_text = extract_text_from_pdf(pdf_bytes)
    if not raw_text:
        return None

    update_status("Loading language model...")
    spacy_model_name = language_details["spacy"]
    nlp = load_spacy_model(spacy_model_name)
    if not nlp:
        return None # Error already shown by load_spacy_model

    update_status("Processing text with spaCy...")
    lemmas = lemmatize_text(raw_text, nlp, remove_stopwords)
    if not lemmas:
        messagebox.showwarning("No Words", "No processable words found after initial filtering.")
        return None

    meaningful_lemmas = lemmas

    if enable_spellcheck:
        update_status("Applying spell checking...")
        spellchecker_code = language_details.get("spellchecker")
        meaningful_lemmas = apply_spellcheck(lemmas, spellchecker_code)

    if not meaningful_lemmas:
        messagebox.showwarning("No Words", "No words remained after all processing steps.")
        return None

    update_status("Counting word frequencies...")
    df = pd.DataFrame(
        Counter(meaningful_lemmas).items(),
        columns=['Word', 'Count']
    ).sort_values(by="Count", ascending=False).reset_index(drop=True)
    
    update_status("Analysis complete!")
    return df


# --- Button Functions  --- #

root = tk.Tk()
root.title("Vocabulator")
root.geometry("800x600")

def run_analysis_thread(
    pdf_bytes, lang_details, remove_sw, enable_sp, 
    status_label, analyze_btn, results_tree, 
    download_excel_btn, download_csv_btn
):
    """
    This function runs the heavy processing in a separate thread
    to avoid freezing the GUI.
    """

    global LAST_DF_RESULTS
    try:
        # Disable button during analysis
        analyze_btn.config(state="disabled")
        
        df_results = generate_word_frequency(
            pdf_bytes,
            lang_details,
            remove_sw,
            enable_sp,
            status_label
        )
        
        LAST_DF_RESULTS = df_results
        
        def update_gui_with_results():
            # Clear previous results
            for item in results_tree.get_children():
                results_tree.delete(item)

            if df_results is not None and not df_results.empty:
                # Populate treeview with new results (top 200)
                for i, row in df_results.head(200).iterrows():
                    results_tree.insert("", "end", values=(row["Word"], row["Count"]))
                
                status_label.config(text=f"Analysis complete! Showing top 200 of {len(df_results)} words.")
                # Enable download buttons
                download_excel_btn.config(state="normal")
                download_csv_btn.config(state="normal")
                
            elif df_results is not None and df_results.empty:
                status_label.config(text="Analysis complete, but no words were found.")
                download_excel_btn.config(state="disabled")
                download_csv_btn.config(state="disabled")
            else:
                # Error messages are handled inside the functions
                status_label.config(text="Analysis failed. Check popup messages.")
                download_excel_btn.config(state="disabled")
                download_csv_btn.config(state="disabled")
        
        root.after(0, update_gui_with_results)

    except Exception as e:
        messagebox.showerror("Unhandled Error", f"An unexpected error occurred: {e}")
        root.after(0, lambda: status_label.config(text="Error!"))
    finally:
        # Re-enable button
        root.after(0, lambda: analyze_btn.config(state="normal"))

def analyze_pdf():
    """Handles the 'Analyze PDF' button click."""

    global LAST_DF_RESULTS

    LAST_DF_RESULTS = None # Clear old results
    
    pdf_path = selected_pdf_path_var.get()
    if not pdf_path:
        messagebox.showwarning("No File", "Please select a PDF file first.")
        return

    # Get options from GUI
    lang_name = language_var.get()
    lang_details = SUPPORTED_LANGUAGES[lang_name]
    remove_sw = remove_stopwords_var.get()
    enable_sp = enable_spellcheck_var.get()

    try:
        with open(pdf_path, "rb") as f:
            pdf_bytes = f.read()
    except Exception as e:
        messagebox.showerror("File Error", f"Could not read file: {e}")
        return

    # Clear results tree
    for item in results_tree.get_children():
        results_tree.delete(item)
    
    # Run the analysis in a new thread
    analysis_thread = threading.Thread(
        target=run_analysis_thread,
        args=(
            pdf_bytes, lang_details, remove_sw, enable_sp,
            status_label, analyze_button, results_tree,
            download_excel_btn, download_csv_btn
        ),
        daemon=True # So it closes when the app closes
    )
    analysis_thread.start()

def select_pdf_file():
    """Opens a file dialog to select a PDF."""
    filepath = filedialog.askopenfilename(
        title="Select a PDF file",
        filetypes=[("PDF Files", "*.pdf")]
    )
    if filepath:
        selected_pdf_path_var.set(filepath)
        # Store the file stem for download names
        original_filename_stem.set(Path(filepath).stem)

def download_as_excel():
    if LAST_DF_RESULTS is None:
        messagebox.showwarning("No Data", "No results to download.")
        return
    
    filename_stem = original_filename_stem.get()
    save_path = filedialog.asksaveasfilename(
        title="Save as Excel",
        initialfile=f"{filename_stem}_words.xlsx",
        defaultextension=".xlsx",
        filetypes=[("Excel Files", "*.xlsx")]
    )
    
    if save_path:
        try:
            excel_data = to_excel(LAST_DF_RESULTS)
            with open(save_path, "wb") as f:
                f.write(excel_data)
            messagebox.showinfo("Success", f"File saved to:\n{save_path}")
        except Exception as e:
            messagebox.showerror("Save Error", f"Could not save Excel file: {e}")

def download_as_csv():
    if LAST_DF_RESULTS is None:
        messagebox.showwarning("No Data", "No results to download.")
        return

    filename_stem = original_filename_stem.get()
    save_path = filedialog.asksaveasfilename(
        title="Save as CSV",
        initialfile=f"{filename_stem}_words.csv",
        defaultextension=".csv",
        filetypes=[("CSV (UTF-8)", "*.csv")]
    )
    
    if save_path:
        try:
            LAST_DF_RESULTS.to_csv(save_path, index=False, encoding='utf-8')
            messagebox.showinfo("Success", f"File saved to:\n{save_path}")
        except Exception as e:
            messagebox.showerror("Save Error", f"Could not save CSV file: {e}")



# --- GUI layout ---

# Use a main frame with padding
main_frame = ttk.Frame(root, padding="10")
main_frame.pack(fill="both", expand=True)



# --- 1. Options Frame ---
options_frame = ttk.LabelFrame(main_frame, text="1. Configuration", padding="10")
options_frame.pack(fill="x", expand=False, pady=5)
options_frame.columnconfigure(1, weight=1)

# File Selection
ttk.Button(options_frame, text="Select PDF", command=select_pdf_file).grid(row=0, column=0, padx=5, pady=5, sticky="w")
selected_pdf_path_var = tk.StringVar(value="No file selected.")
original_filename_stem = tk.StringVar()
ttk.Label(options_frame, textvariable=selected_pdf_path_var, relief="sunken", padding=(5,2)).grid(row=0, column=1, padx=5, pady=5, sticky="we")

# Language Selection
ttk.Label(options_frame, text="Language:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
language_var = tk.StringVar(value="English")
lang_menu = ttk.Combobox(
    options_frame, 
    textvariable=language_var, 
    values=list(SUPPORTED_LANGUAGES.keys()),
    state="readonly",
    width=15
)
lang_menu.grid(row=1, column=1, padx=5, pady=5, sticky="w")

# Checkboxes
options_inner_frame = ttk.Frame(options_frame)
options_inner_frame.grid(row=2, column=0, columnspan=2, pady=5, sticky="w")

remove_stopwords_var = tk.BooleanVar(value=True)
ttk.Checkbutton(
    options_inner_frame, 
    text="Remove stopwords", 
    variable=remove_stopwords_var
).pack(side="left", padx=5)
ttk.Button(
    options_inner_frame, 
    text="?", 
    width=2, 
    command=lambda: messagebox.showinfo("What are Stopwords?", STOPWORDS_INFO_TEXT)
).pack(side="left")

enable_spellcheck_var = tk.BooleanVar(value=True)
ttk.Checkbutton(
    options_inner_frame, 
    text="Apply spell checking (filters non-dictionary words)", 
    variable=enable_spellcheck_var
).pack(side="left", padx=(20, 5))
ttk.Button(
    options_inner_frame, 
    text="?", 
    width=2, 
    command=lambda: messagebox.showinfo("What is Spell Checking?", SPELLCHECK_INFO_TEXT)
).pack(side="left")



# --- 2. Analysis Button & Status ---
analysis_frame = ttk.Frame(main_frame)
analysis_frame.pack(fill="x", expand=False, pady=5)
analysis_frame.columnconfigure(0, weight=1)

analyze_button = ttk.Button(analysis_frame, text="Analyze PDF", command=analyze_pdf, style="Accent.TButton")
analyze_button.grid(row=0, column=0, padx=5, pady=5, sticky="we")

status_label = ttk.Label(analysis_frame, text="Ready. Select a PDF and click Analyze.", anchor="e")
status_label.grid(row=0, column=1, padx=5, pady=5, sticky="e")



# --- 3. Results Frame ---
results_frame = ttk.LabelFrame(main_frame, text="2. Results (Top 200)", padding="10")
results_frame.pack(fill="both", expand=True, pady=5)

# Treeview (table) for results
tree_frame = ttk.Frame(results_frame)
tree_frame.pack(fill="both", expand=True)

results_tree = ttk.Treeview(tree_frame, columns=("Word", "Count"), show="headings")
results_tree.heading("Word", text="Word")
results_tree.heading("Count", text="Count")
results_tree.column("Word", width=300, stretch=True)
results_tree.column("Count", width=100, stretch=False, anchor="center")

# Scrollbar
scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=results_tree.yview)
results_tree.configure(yscrollcommand=scrollbar.set)

scrollbar.pack(side="right", fill="y")
results_tree.pack(side="left", fill="both", expand=True)



# --- 4. Download Frame ---
download_frame = ttk.Frame(main_frame)
download_frame.pack(fill="x", expand=False, pady=5)
download_frame.columnconfigure(0, weight=1)
download_frame.columnconfigure(1, weight=1)

download_excel_btn = ttk.Button(
    download_frame, 
    text="Download Results as Excel", 
    command=download_as_excel, 
    state="disabled"
)
download_excel_btn.grid(row=0, column=0, padx=5, pady=5, sticky="we")

download_csv_btn = ttk.Button(
    download_frame, 
    text="Download Results as CSV", 
    command=download_as_csv, 
    state="disabled"
)
download_csv_btn.grid(row=0, column=1, padx=5, pady=5, sticky="we")



if __name__ == "__main__":
    style = ttk.Style()
    style.configure("Accent.TButton", font=("Arial", 10, "bold"))
    
    root.mainloop()