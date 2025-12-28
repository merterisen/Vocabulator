import tkinter as tk
from tkinter import messagebox
import traceback
from ui.ui import VocabulatorUI
from controller import VocabulatorController

def handle_exception(exc_type, exc_value, exc_traceback):
    """Global handler for exceptions in the Tkinter event loop."""

    error_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    print(error_msg)
    messagebox.showerror("Unexpected Error", f"An internal error occurred:\n\n{exc_value}")

if __name__ == "__main__":
    root = tk.Tk()
    
    # This captures all errors occurring within the Tkinter main loop
    root.report_callback_exception = handle_exception
    
    try:
        ui = VocabulatorUI(root)
        controller = VocabulatorController(ui)
        ui.set_controller(controller)
        root.mainloop()
        
    except Exception as e:
        # This captures errors during startup/initialization
        handle_exception(type(e), e, e.__traceback__)