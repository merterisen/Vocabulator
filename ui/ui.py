import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import config

class VocabulatorUI:
    """
    Responsible for:
        - Displaying widgets
        - Getting user input
        - Calling the Controller, when buttons are clicked
    """

    def __init__(self, root):
        self.root = root
        self.controller = None # Will be set by app.py
        
        self.root.title(config.WINDOW_TITLE)
        self.root.geometry(config.WINDOW_SIZE)
        
        # --- State Variables ---
        self.status = tk.StringVar(value="Ready")
        self.language = tk.StringVar(value="German")
        self.include_articles = tk.BooleanVar(value=False)
        self.pdf_file_path = tk.StringVar()
        self.known_words_file_path = tk.StringVar()

        # LLM Variables
        self.api_key = tk.StringVar()
        
        # Build the UI
        self._build_ui()




    def _build_ui(self):

        # Tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(side="top", fill="both", expand=True, padx=10, pady=5)

        # NLP Tab
        self.nlp_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.nlp_tab, text='NLP')
        self._build_nlp_tab(self.nlp_tab)

        # LLM Tab
        self.llm_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.llm_tab, text='LLM')
        self._build_llm_tab(self.llm_tab)

        self._build_status_bar() # should be written before _build_preview()

        # Preview
        self.preview_frame = tk.LabelFrame(self.root, text="Preview (Top 50)", padx=10, pady=10)
        self.preview_frame.pack(side="bottom", fill="both", expand=True, padx=10, pady=10)
        self._build_preview(self.preview_frame)

        



    def _build_nlp_tab(self, parent):
        # SECTION 1: SELECT PDF
        select_pdf_frame = tk.LabelFrame(parent, text="1. Select PDF", padx=10, pady=10)
        select_pdf_frame.pack(side='top', fill="x", padx=10, pady=5)

        self.select_pdf_entry = tk.Entry(select_pdf_frame, textvariable=self.pdf_file_path, state='readonly')
        self.select_pdf_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))

        select_pdf_button = tk.Button(select_pdf_frame, text="Browse", command=lambda: self.controller.browse_pdf())
        select_pdf_button.pack(side="left")


        # CONTAINER for Language and Known Words
        container_frame = tk.Frame(parent)
        container_frame.pack(side='top', fill="x", padx=10, pady=5)
        

        # SECTION 2: LANGUAGE SELECTION
        select_language_frame = tk.LabelFrame(container_frame, text="2. Select Language", padx=10, pady=10)
        select_language_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))
        
        select_language_combobox = ttk.Combobox(select_language_frame, textvariable=self.language, values=list(config.LANGUAGES.keys()), state="readonly")
        select_language_combobox.pack(fill="x")

        include_articles_checkbutton = tk.Checkbutton(select_language_frame, text="Include Articles", variable=self.include_articles)
        include_articles_checkbutton.pack(anchor="w")


        # SECTION 3: KNOWN WORDS FILE
        known_words_frame = tk.LabelFrame(container_frame, text="3. Select Known Words (Optional)", padx=10, pady=10)
        known_words_frame.pack(side="right", fill="both", expand=True, padx=(5, 0))

        self.known_words_entry = tk.Entry(known_words_frame, textvariable=self.known_words_file_path, state='readonly')
        self.known_words_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))

        known_words_button = tk.Button(known_words_frame, text="Browse", command=lambda: self.controller.browse_known_words())
        known_words_button.pack(side="left")


        # SECTION 4: RUN BUTTON
        self.run_button = tk.Button(parent, text="RUN", command=lambda: self.controller.run_nlp(), height=2, bg="#e1e1e1") 
        self.run_button.pack(side='top', fill="x", padx=20, pady=(10, 5))

        self.progress_bar = ttk.Progressbar(parent, mode='indeterminate')
        self.progress_bar.pack(fill="x", padx=20, pady=(0, 10))




    def _build_llm_tab(self, parent):
        # SECTION 1: SELECT LLM MODEL
        select_llm_frame = tk.LabelFrame(parent, text="1. Select LLM Model", padx=10, pady=10)
        select_llm_frame.pack(side='top', fill="x", padx=10, pady=5)

        self.select_llm_combobox = ttk.Combobox(select_llm_frame, values=list(config.LLM_MODELS.keys()), state="readonly")
        self.select_llm_combobox.pack(fill="x")

        # SECTION 2: ENTER API KEY
        api_key_frame = tk.LabelFrame(parent, text="2. Enter API Key", padx=10, pady=10)
        api_key_frame.pack(side='top', fill="x", padx=10, pady=5)

        self.api_key_entry = tk.Entry(api_key_frame, state='normal')
        self.api_key_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))




    def _build_status_bar(self):
        status_frame = tk.Frame(self.root, bd=1, relief='sunken')
        status_frame.pack(side="bottom", fill="x")

        status_label = tk.Label(status_frame, textvariable=self.status, fg="blue", anchor="w")
        status_label.pack(side="left", padx=10, pady=2)




    def _build_preview(self, parent):
        # Export Buttons
        export_frame = tk.Frame(parent, pady=5)
        export_frame.pack(side="bottom", fill="x")

        export_csv_button = tk.Button(export_frame, text="Export CSV", command=lambda: self.controller.export_data("csv"))
        export_csv_button.pack(side="left", padx=20, expand=True)
        
        export_excel_button = tk.Button(export_frame, text="Export Excel", command=lambda: self.controller.export_data("excel"))
        export_excel_button.pack(side="right", padx=20, expand=True)

        # Preview Table
        scrollbar = ttk.Scrollbar(parent, orient="vertical")
        scrollbar.pack(side="right", fill="y")

        # Initializing with default columns, but they will be overwritten dynamically when new columns are added.
        self.preview_table = ttk.Treeview(parent, columns=("Word", "Count", "Type"), show="headings", yscrollcommand=scrollbar.set)
        self.preview_table.pack(side="left", fill="both", expand=True)
        
        scrollbar.config(command=self.preview_table.yview)



    # =================================================================
    # Functions called by Controller
    # =================================================================

    def set_controller(self, controller):
        """Connection to the VocabulatorController"""
        self.controller = controller


    def update_status(self, message):
        self.status.set(message)


    def set_pdf_path(self, path):
        self.pdf_file_path.set(path)


    def set_known_words_path(self, path):
        self.known_words_file_path.set(path)


    def update_table(self, dataframe):
        """Clears and repopulates the treeview dynamically based on DataFrame columns."""
        
        for item in self.preview_table.get_children():
            self.preview_table.delete(item)
            
        if dataframe is None or dataframe.empty:
            return

        # Dynamic Column Generation
        cols = list(dataframe.columns)
        self.preview_table["columns"] = cols
        
        for col in cols:
            self.preview_table.heading(col, text=col, anchor="w")
            self.preview_table.column(col, anchor="w")

        # Insert head(50) to preview_table
        for _, row in dataframe.head(50).iterrows():
            self.preview_table.insert("", "end", values=list(row))


    def show_error(self, title, message):
        messagebox.showerror(title, message)


    def show_info(self, title, message):
        messagebox.showinfo(title, message)


    def show_warning(self, title, message):
        messagebox.showwarning(title, message)


    def lock_ui(self):
        self.run_button.config(state="disabled")
        self.progress_bar.start(10)


    def unlock_ui(self):
        self.progress_bar.stop()
        self.run_button.config(state="normal")