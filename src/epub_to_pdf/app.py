# -*- coding: utf-8 -*-
"""
EPUB to PDF Converter - Graphical User Interface.

A modern drag-and-drop GUI for converting EPUB files to PDF format,
optimized for subsequent Mistral OCR processing.
"""

import sys
import threading
from pathlib import Path
from tkinter import filedialog, messagebox
import tkinter as tk
from tkinter import ttk
from typing import Optional

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    DND_AVAILABLE = True
except ImportError:
    DND_AVAILABLE = False

from . import __version__
from .converter import (
    ConversionError,
    ConversionMethod,
    convert_epub_to_pdf,
    get_available_methods,
    get_log_file_path,
)


class EPUBToPDFApp:
    """Main application window for EPUB to PDF conversion."""

    WINDOW_WIDTH = 700
    WINDOW_HEIGHT = 600
    DROP_ZONE_HEIGHT = 150

    def __init__(self):
        """Initialize the application."""
        # Create main window with drag-and-drop support if available
        if DND_AVAILABLE:
            self.root = TkinterDnD.Tk()
        else:
            self.root = tk.Tk()

        self.root.title(f"EPUB to PDF Converter v{__version__}")
        self.root.geometry(f"{self.WINDOW_WIDTH}x{self.WINDOW_HEIGHT}")
        self.root.minsize(500, 400)
        self.root.resizable(True, True)

        # Configure style
        self.style = ttk.Style()
        self._configure_style()

        # State variables
        self.current_file: Optional[Path] = None
        self.is_converting = False
        self.selected_method = tk.StringVar(value="auto")

        # Build UI
        self._create_widgets()

        # Check available methods
        self._check_available_methods()

    def _configure_style(self):
        """Configure ttk styles for the application."""
        self.style.configure("Title.TLabel", font=("Segoe UI", 16, "bold"))
        self.style.configure("Subtitle.TLabel", font=("Segoe UI", 10))
        self.style.configure("Status.TLabel", font=("Segoe UI", 9))
        self.style.configure("DropZone.TFrame", relief="ridge", borderwidth=2)
        self.style.configure("Convert.TButton", font=("Segoe UI", 11, "bold"))

    def _create_widgets(self):
        """Create and layout all widgets."""
        # Main container with padding
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title section
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill=tk.X, pady=(0, 15))

        ttk.Label(
            title_frame,
            text="EPUB to PDF Converter",
            style="Title.TLabel"
        ).pack(anchor=tk.W)

        ttk.Label(
            title_frame,
            text="Optimized for Mistral OCR processing",
            style="Subtitle.TLabel"
        ).pack(anchor=tk.W)

        # Drop zone
        self._create_drop_zone(main_frame)

        # File info section
        self._create_file_info(main_frame)

        # Options section
        self._create_options(main_frame)

        # Progress section
        self._create_progress_section(main_frame)

        # Log viewer section
        self._create_log_viewer(main_frame)

        # Buttons section
        self._create_buttons(main_frame)

        # Status bar
        self._create_status_bar(main_frame)

    def _create_drop_zone(self, parent: ttk.Frame):
        """Create the drag-and-drop zone."""
        drop_frame = ttk.Frame(parent, style="DropZone.TFrame")
        drop_frame.pack(fill=tk.X, pady=(0, 15))

        # Inner frame for content
        inner_frame = ttk.Frame(drop_frame, padding="30")
        inner_frame.pack(fill=tk.BOTH, expand=True)

        # Drop zone canvas for visual feedback
        self.drop_canvas = tk.Canvas(
            inner_frame,
            height=self.DROP_ZONE_HEIGHT,
            bg="#f5f5f5",
            highlightthickness=2,
            highlightbackground="#cccccc"
        )
        self.drop_canvas.pack(fill=tk.X)

        # Draw drop zone content
        self._draw_drop_zone_content()

        # Bind click to open file dialog
        self.drop_canvas.bind("<Button-1>", lambda e: self._browse_file())

        # Enable drag-and-drop if available
        if DND_AVAILABLE:
            self.drop_canvas.drop_target_register(DND_FILES)
            self.drop_canvas.dnd_bind("<<Drop>>", self._on_drop)
            self.drop_canvas.dnd_bind("<<DragEnter>>", self._on_drag_enter)
            self.drop_canvas.dnd_bind("<<DragLeave>>", self._on_drag_leave)

    def _draw_drop_zone_content(self, highlight: bool = False):
        """Draw the content inside the drop zone."""
        self.drop_canvas.delete("all")

        # Background color
        bg_color = "#e3f2fd" if highlight else "#f5f5f5"
        self.drop_canvas.configure(bg=bg_color)

        # Get canvas dimensions
        width = self.drop_canvas.winfo_width() or self.WINDOW_WIDTH - 100
        height = self.DROP_ZONE_HEIGHT

        # Draw icon (folder with arrow)
        center_x = width // 2
        center_y = height // 2 - 20

        # Simple folder icon using lines
        self.drop_canvas.create_rectangle(
            center_x - 30, center_y - 10,
            center_x + 30, center_y + 20,
            outline="#666666", width=2, fill="#ffffff"
        )
        self.drop_canvas.create_polygon(
            center_x - 30, center_y - 10,
            center_x - 30, center_y - 20,
            center_x - 10, center_y - 20,
            center_x - 5, center_y - 10,
            outline="#666666", width=2, fill="#ffffff"
        )
        # Arrow pointing down
        self.drop_canvas.create_line(
            center_x, center_y - 35,
            center_x, center_y - 15,
            arrow=tk.LAST, width=3, fill="#1976d2"
        )

        # Text
        if DND_AVAILABLE:
            main_text = "Drag & Drop EPUB file here"
            sub_text = "or click to browse"
        else:
            main_text = "Click to select EPUB file"
            sub_text = "(Drag & drop not available - install tkinterdnd2)"

        self.drop_canvas.create_text(
            center_x, center_y + 45,
            text=main_text,
            font=("Segoe UI", 12, "bold"),
            fill="#333333"
        )
        self.drop_canvas.create_text(
            center_x, center_y + 70,
            text=sub_text,
            font=("Segoe UI", 9),
            fill="#666666"
        )

    def _create_file_info(self, parent: ttk.Frame):
        """Create file information display."""
        info_frame = ttk.LabelFrame(parent, text="Selected File", padding="10")
        info_frame.pack(fill=tk.X, pady=(0, 10))

        self.file_label = ttk.Label(
            info_frame,
            text="No file selected",
            font=("Segoe UI", 9)
        )
        self.file_label.pack(anchor=tk.W)

        self.file_size_label = ttk.Label(
            info_frame,
            text="",
            font=("Segoe UI", 8),
            foreground="#666666"
        )
        self.file_size_label.pack(anchor=tk.W)

    def _create_options(self, parent: ttk.Frame):
        """Create conversion options section."""
        options_frame = ttk.LabelFrame(parent, text="Options", padding="10")
        options_frame.pack(fill=tk.X, pady=(0, 10))

        # Method selection
        method_frame = ttk.Frame(options_frame)
        method_frame.pack(fill=tk.X)

        ttk.Label(method_frame, text="Conversion Method:").pack(side=tk.LEFT)

        methods = [
            ("Auto (Recommended)", "auto"),
            ("Prince", "prince"),
            ("Vivliostyle", "vivliostyle"),
        ]

        for text, value in methods:
            rb = ttk.Radiobutton(
                method_frame,
                text=text,
                value=value,
                variable=self.selected_method
            )
            rb.pack(side=tk.LEFT, padx=(10, 0))

    def _create_progress_section(self, parent: ttk.Frame):
        """Create progress display section."""
        progress_frame = ttk.Frame(parent)
        progress_frame.pack(fill=tk.X, pady=(0, 10))

        self.progress_bar = ttk.Progressbar(
            progress_frame,
            mode="indeterminate",
            length=300
        )
        self.progress_bar.pack(fill=tk.X)

        self.progress_label = ttk.Label(
            progress_frame,
            text="",
            font=("Segoe UI", 9)
        )
        self.progress_label.pack(anchor=tk.W, pady=(5, 0))

    def _create_log_viewer(self, parent: ttk.Frame):
        """Create log viewer section."""
        log_frame = ttk.LabelFrame(parent, text="Conversion Log", padding="5")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Text widget with scrollbar for log display
        log_container = ttk.Frame(log_frame)
        log_container.pack(fill=tk.BOTH, expand=True)

        self.log_text = tk.Text(
            log_container,
            height=8,
            font=("Consolas", 9),
            wrap=tk.WORD,
            state=tk.DISABLED,
            bg="#1e1e1e",
            fg="#d4d4d4"
        )
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        log_scrollbar = ttk.Scrollbar(
            log_container,
            orient=tk.VERTICAL,
            command=self.log_text.yview
        )
        log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.configure(yscrollcommand=log_scrollbar.set)

        # Log file path display and open button
        log_path_frame = ttk.Frame(log_frame)
        log_path_frame.pack(fill=tk.X, pady=(5, 0))

        log_file = get_log_file_path()
        ttk.Label(
            log_path_frame,
            text=f"Log file: {log_file}",
            font=("Segoe UI", 8),
            foreground="#666666"
        ).pack(side=tk.LEFT)

        self.open_log_button = ttk.Button(
            log_path_frame,
            text="Open Log File",
            command=self._open_log_file
        )
        self.open_log_button.pack(side=tk.RIGHT)

    def _append_log(self, message: str):
        """Append a message to the log viewer."""
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.configure(state=tk.DISABLED)

    def _clear_log(self):
        """Clear the log viewer."""
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.configure(state=tk.DISABLED)

    def _open_log_file(self):
        """Open the log file in the default text editor."""
        import subprocess
        import platform

        log_file = get_log_file_path()
        if log_file.exists():
            if platform.system() == "Windows":
                subprocess.run(["notepad", str(log_file)])
            elif platform.system() == "Darwin":
                subprocess.run(["open", str(log_file)])
            else:
                subprocess.run(["xdg-open", str(log_file)])
        else:
            messagebox.showinfo("Log File", f"Log file not found:\n{log_file}")

    def _create_buttons(self, parent: ttk.Frame):
        """Create action buttons."""
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X, pady=(0, 10))

        self.convert_button = ttk.Button(
            button_frame,
            text="Convert to PDF",
            style="Convert.TButton",
            command=self._start_conversion,
            state=tk.DISABLED
        )
        self.convert_button.pack(side=tk.LEFT, padx=(0, 10))

        self.open_folder_button = ttk.Button(
            button_frame,
            text="Open Output Folder",
            command=self._open_output_folder,
            state=tk.DISABLED
        )
        self.open_folder_button.pack(side=tk.LEFT)

    def _create_status_bar(self, parent: ttk.Frame):
        """Create status bar at bottom."""
        status_frame = ttk.Frame(parent)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)

        ttk.Separator(status_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=(0, 5))

        self.status_label = ttk.Label(
            status_frame,
            text="Ready",
            style="Status.TLabel"
        )
        self.status_label.pack(side=tk.LEFT)

        self.methods_label = ttk.Label(
            status_frame,
            text="",
            style="Status.TLabel"
        )
        self.methods_label.pack(side=tk.RIGHT)

    def _check_available_methods(self):
        """Check and display available conversion methods."""
        available = get_available_methods()

        if available:
            method_names = [m.value for m in available]
            self.methods_label.configure(
                text=f"Available: {', '.join(method_names)}"
            )
        else:
            self.methods_label.configure(
                text="No conversion tools found!",
                foreground="red"
            )
            messagebox.showwarning(
                "Missing Dependencies",
                "No EPUB conversion tools found.\n\n"
                "Please install one of the following:\n\n"
                "- PyMuPDF: pip install pymupdf\n"
                "- MuPDF: https://mupdf.com/releases/\n"
                "- Calibre: https://calibre-ebook.com/download"
            )

    def _on_drop(self, event):
        """Handle file drop event."""
        # Parse dropped file path
        file_path = event.data

        # Handle Windows path format (may have braces)
        if file_path.startswith("{") and file_path.endswith("}"):
            file_path = file_path[1:-1]

        # Handle multiple files (take first)
        if " " in file_path and not Path(file_path).exists():
            # Try to parse as multiple files
            files = file_path.split()
            file_path = files[0]

        self._load_file(Path(file_path))

    def _on_drag_enter(self, event):
        """Handle drag enter event."""
        self._draw_drop_zone_content(highlight=True)

    def _on_drag_leave(self, event):
        """Handle drag leave event."""
        self._draw_drop_zone_content(highlight=False)

    def _browse_file(self):
        """Open file browser dialog."""
        file_path = filedialog.askopenfilename(
            title="Select EPUB File",
            filetypes=[
                ("EPUB files", "*.epub"),
                ("All files", "*.*")
            ]
        )

        if file_path:
            self._load_file(Path(file_path))

    def _load_file(self, file_path: Path):
        """Load and validate an EPUB file."""
        if not file_path.exists():
            messagebox.showerror("Error", f"File not found:\n{file_path}")
            return

        if file_path.suffix.lower() != ".epub":
            messagebox.showerror(
                "Invalid File",
                f"Please select an EPUB file.\n\nSelected: {file_path.suffix}"
            )
            return

        self.current_file = file_path

        # Update UI
        self.file_label.configure(text=str(file_path))

        # Show file size
        size_bytes = file_path.stat().st_size
        if size_bytes < 1024:
            size_str = f"{size_bytes} bytes"
        elif size_bytes < 1024 * 1024:
            size_str = f"{size_bytes / 1024:.1f} KB"
        else:
            size_str = f"{size_bytes / (1024 * 1024):.1f} MB"

        self.file_size_label.configure(text=f"Size: {size_str}")

        # Enable convert button
        self.convert_button.configure(state=tk.NORMAL)
        self._draw_drop_zone_content()

        self.status_label.configure(text=f"File loaded: {file_path.name}")

    def _start_conversion(self):
        """Start the conversion process in a background thread."""
        if self.current_file is None or self.is_converting:
            return

        # Ask for output location
        output_path = filedialog.asksaveasfilename(
            title="Save PDF As",
            defaultextension=".pdf",
            initialdir=self.current_file.parent,
            initialfile=self.current_file.stem + ".pdf",
            filetypes=[
                ("PDF files", "*.pdf"),
                ("All files", "*.*")
            ]
        )

        if not output_path:
            return

        self.output_path = Path(output_path)
        self.is_converting = True

        # Clear and update log
        self._clear_log()
        self._append_log(f"Input: {self.current_file}")
        self._append_log(f"Output: {self.output_path}")

        # Update UI for conversion
        self.convert_button.configure(state=tk.DISABLED)
        self.progress_bar.start(10)
        self.progress_label.configure(text="Starting conversion...")

        # Get selected method
        method_str = self.selected_method.get()
        method = {
            "auto": ConversionMethod.AUTO,
            "vivliostyle": ConversionMethod.VIVLIOSTYLE,
            "calibre": ConversionMethod.CALIBRE,
        }.get(method_str, ConversionMethod.AUTO)

        self._append_log(f"Method: {method.value}")
        self._append_log("=" * 40)

        # Run conversion in background thread
        thread = threading.Thread(
            target=self._convert_thread,
            args=(self.current_file, self.output_path, method),
            daemon=True
        )
        thread.start()

    def _convert_thread(
        self,
        epub_path: Path,
        pdf_path: Path,
        method: ConversionMethod
    ):
        """Background thread for conversion."""
        try:
            convert_epub_to_pdf(
                epub_path,
                pdf_path,
                method=method,
                progress_callback=self._update_progress
            )

            # Schedule UI update on main thread
            self.root.after(0, lambda: self._conversion_complete(True))

        except ConversionError as e:
            self.root.after(0, lambda: self._conversion_complete(False, str(e)))
        except Exception as e:
            self.root.after(0, lambda: self._conversion_complete(False, str(e)))

    def _update_progress(self, message: str):
        """Update progress label and log (called from background thread)."""
        self.root.after(0, lambda: self.progress_label.configure(text=message))
        self.root.after(0, lambda: self._append_log(message))

    def _conversion_complete(self, success: bool, error: Optional[str] = None):
        """Handle conversion completion."""
        self.is_converting = False
        self.progress_bar.stop()
        self.convert_button.configure(state=tk.NORMAL)

        if success:
            self._append_log("=" * 40)
            self._append_log("Conversion completed successfully!")
            self._append_log(f"Output: {self.output_path}")
            self.progress_label.configure(text="Conversion complete!")
            self.status_label.configure(text=f"PDF saved: {self.output_path.name}")
            self.open_folder_button.configure(state=tk.NORMAL)

            messagebox.showinfo(
                "Success",
                f"PDF created successfully!\n\n{self.output_path}"
            )
        else:
            self._append_log("=" * 40)
            self._append_log("CONVERSION FAILED!")
            self._append_log(f"Error: {error}")
            self.progress_label.configure(text="Conversion failed")
            self.status_label.configure(text="Error during conversion")

            messagebox.showerror(
                "Conversion Failed",
                f"Failed to convert EPUB to PDF:\n\n{error}"
            )

    def _open_output_folder(self):
        """Open the folder containing the output PDF."""
        if hasattr(self, "output_path") and self.output_path.exists():
            import subprocess
            import platform

            if platform.system() == "Windows":
                subprocess.run(["explorer", "/select,", str(self.output_path)])
            elif platform.system() == "Darwin":
                subprocess.run(["open", "-R", str(self.output_path)])
            else:
                subprocess.run(["xdg-open", str(self.output_path.parent)])

    def run(self):
        """Run the application main loop."""
        self.root.mainloop()


def main():
    """Application entry point."""
    app = EPUBToPDFApp()
    app.run()


if __name__ == "__main__":
    main()
