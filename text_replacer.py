import tkinter as tk
from tkinter import filedialog, messagebox, ttk, simpledialog
import os
import re
import json
import concurrent.futures
from datetime import datetime

class ReplacementTask:
    def __init__(self, parent_frame, app, index):
        self.app = app
        self.index = index
        self.replacements = []
        
        # Create a frame for this replacement task with custom styling
        self.frame = ttk.LabelFrame(parent_frame, text=f"Replacement Task {index + 1}")
        self.frame.pack(fill="x", padx=10, pady=5, anchor="n")
        
        # Top options frame
        options_frame = ttk.Frame(self.frame)
        options_frame.pack(fill="x", padx=5, pady=5)
        
        # Search text with label
        search_frame = ttk.Frame(options_frame)
        search_frame.pack(fill="x", padx=5, pady=5)
        ttk.Label(search_frame, text="Search for:").pack(side="left", padx=5)
        self.search_text = tk.StringVar()
        ttk.Entry(search_frame, textvariable=self.search_text, width=30).pack(side="left", padx=5, expand=True, fill="x")
        
        # Options sub-frame for regex and case sensitivity
        sub_options = ttk.Frame(options_frame)
        sub_options.pack(fill="x", padx=5)
        
        # Regex option
        self.use_regex = tk.BooleanVar(value=False)
        ttk.Checkbutton(sub_options, text="Use Regular Expression", variable=self.use_regex).pack(side="left", padx=5)
        
        # Case sensitivity option
        self.case_sensitive = tk.BooleanVar(value=True)
        ttk.Checkbutton(sub_options, text="Case Sensitive", variable=self.case_sensitive).pack(side="left", padx=20)
        
        # Frame for replacement percentages
        self.replacements_frame = ttk.Frame(self.frame)
        self.replacements_frame.pack(fill="x", padx=5, pady=5)
        
        # Add first replacement
        self.add_replacement()
        
        # Buttons frame
        buttons_frame = ttk.Frame(self.frame)
        buttons_frame.pack(fill="x", padx=5, pady=5)
        
        # Add replacement button
        ttk.Button(buttons_frame, text="Add Replacement", command=self.add_replacement).pack(side="left", padx=5)
        
        # Remove task button
        ttk.Button(buttons_frame, text="Remove Task", command=lambda: self.app.remove_task(self.index)).pack(side="right", padx=5)

    def add_replacement(self):
        replacement_idx = len(self.replacements)
        replacement_frame = ttk.Frame(self.replacements_frame)
        replacement_frame.pack(fill="x", pady=2)
        
        # Replace with text
        ttk.Label(replacement_frame, text="Replace with:").pack(side="left", padx=5)
        replace_text = tk.StringVar()
        ttk.Entry(replacement_frame, textvariable=replace_text, width=30).pack(side="left", padx=5)
        
        # Percentage
        ttk.Label(replacement_frame, text="Percentage:").pack(side="left", padx=5)
        percentage = tk.StringVar(value="100")
        percentage_entry = ttk.Spinbox(replacement_frame, from_=0, to=100, textvariable=percentage, width=5)
        percentage_entry.pack(side="left", padx=5)
        ttk.Label(replacement_frame, text="%").pack(side="left")
        
        # Remove replacement button (create a simple function reference instead of lambda)
        remove_btn = ttk.Button(replacement_frame, text="✕", width=2)
        remove_btn.pack(side="right", padx=5)
        
        # Store the replacement data
        replacement_data = {
            "frame": replacement_frame,
            "replace_text": replace_text,
            "percentage": percentage,
            "remove_btn": remove_btn,
            "idx": replacement_idx
        }
        self.replacements.append(replacement_data)
        
        # Set command after adding to list for proper reference
        remove_btn.config(command=lambda r=replacement_data: self.remove_replacement(r["idx"]))
    
    def remove_replacement(self, idx):
        if len(self.replacements) <= 1:
            messagebox.showinfo("Info", "You need at least one replacement option.")
            return
            
        # Find the replacement with the matching idx
        to_remove = None
        for i, repl in enumerate(self.replacements):
            if repl["idx"] == idx:
                to_remove = i
                break
                
        if to_remove is not None:
            # Remove the frame
            self.replacements[to_remove]["frame"].destroy()
            # Remove from the list
            self.replacements.pop(to_remove)
    
    def get_data(self):
        search_term = self.search_text.get().strip()
        if not search_term:
            return None
        
        replacement_data = []
        total_percentage = 0
        
        for replacement in self.replacements:
            replace_with = replacement["replace_text"].get()
            try:
                percentage_str = replacement["percentage"].get().strip()
                if not percentage_str:  # Empty percentage field
                    messagebox.showerror("Error", "Please fill in all percentage fields")
                    return None
                    
                percentage = float(percentage_str)
                if percentage <= 0:
                    raise ValueError("Percentage must be positive")
                total_percentage += percentage
                replacement_data.append({
                    "replace_with": replace_with,
                    "percentage": percentage
                })
            except ValueError as e:
                messagebox.showerror("Error", f"Invalid percentage for replacement: {replacement['replace_text'].get()}\n{str(e)}")
                return None
            
        return {
            "search_term": search_term,
            "replacements": replacement_data,
            "use_regex": self.use_regex.get(),
            "case_sensitive": self.case_sensitive.get()
        }

    def set_data(self, data):
        if not data:
            return
            
        self.search_text.set(data.get("search_term", ""))
        self.use_regex.set(data.get("use_regex", False))
        self.case_sensitive.set(data.get("case_sensitive", True))
        
        # Clear existing replacements
        for repl in self.replacements:
            repl["frame"].destroy()
        self.replacements = []
        
        # Add replacements from data
        for repl_data in data.get("replacements", []):
            self.add_replacement()
            last_idx = len(self.replacements) - 1
            self.replacements[last_idx]["replace_text"].set(repl_data.get("replace_with", ""))
            self.replacements[last_idx]["percentage"].set(str(repl_data.get("percentage", 100)))


class TextReplacerApp:
    def __init__(self, root):
        self.root = root
        root.title("Percentage-based Text Replacer")
        root.geometry("800x700")
        
        # Apply simpler styling without using ttkthemes
        self.style = ttk.Style()
        
        # Configure basic styles
        if os.name == 'nt':  # Windows
            self.style.theme_use('vista')
        else:
            try:
                self.style.theme_use('clam')  # A decent cross-platform theme
            except:
                pass  # Fallback to default
        
        # Main container
        main_container = ttk.Frame(root)
        main_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Title and header
        header_frame = ttk.Frame(main_container)
        header_frame.pack(fill="x", pady=(0, 10))
        
        # Create a simpler header
        header_label = ttk.Label(header_frame, text="Text Replacer", font=("TkDefaultFont", 11, "bold"))
        header_label.pack(side="left")
        
        # Stats frame
        self.stats_frame = ttk.LabelFrame(main_container, text="Statistics")
        self.stats_frame.pack(fill="x", padx=5, pady=5)
        
        stats_inner = ttk.Frame(self.stats_frame)
        stats_inner.pack(fill="x", padx=5, pady=5)
        
        # Stats labels
        ttk.Label(stats_inner, text="Original:").grid(row=0, column=0, sticky="w", padx=5)
        self.original_chars = tk.StringVar(value="0 characters, 0 words")
        ttk.Label(stats_inner, textvariable=self.original_chars).grid(row=0, column=1, sticky="w", padx=5)
        
        ttk.Label(stats_inner, text="After replacements:").grid(row=1, column=0, sticky="w", padx=5)
        self.replaced_chars = tk.StringVar(value="0 characters, 0 words")
        ttk.Label(stats_inner, textvariable=self.replaced_chars).grid(row=1, column=1, sticky="w", padx=5)
        
        # File selection section
        file_frame = ttk.LabelFrame(main_container, text="File Selection")
        file_frame.pack(fill="x", padx=5, pady=5)
        
        file_inner = ttk.Frame(file_frame)
        file_inner.pack(fill="x", padx=5, pady=5)
        
        ttk.Label(file_inner, text="Input File(s):").pack(side="left", padx=5)
        self.file_path = tk.StringVar()
        ttk.Entry(file_inner, textvariable=self.file_path, width=50).pack(side="left", padx=5, expand=True, fill="x")
        ttk.Button(file_inner, text="Browse", command=self.browse_files).pack(side="right", padx=5)
        
        # Output naming options
        output_frame = ttk.Frame(file_frame)
        output_frame.pack(fill="x", padx=5, pady=5)
        
        ttk.Label(output_frame, text="Output Prefix:").pack(side="left", padx=5)
        self.output_prefix = tk.StringVar(value="Imp_")
        ttk.Entry(output_frame, textvariable=self.output_prefix, width=15).pack(side="left", padx=5)
        
        ttk.Label(output_frame, text="Output Suffix:").pack(side="left", padx=5)
        self.output_suffix = tk.StringVar(value="")
        ttk.Entry(output_frame, textvariable=self.output_suffix, width=15).pack(side="left", padx=5)
        
        ttk.Label(output_frame, text="Output Directory:").pack(side="left", padx=5)
        self.output_dir = tk.StringVar(value="")
        ttk.Entry(output_frame, textvariable=self.output_dir, width=20).pack(side="left", padx=5)
        ttk.Button(output_frame, text="Browse", command=self.browse_output_dir).pack(side="right", padx=5)
        
        # Create scrollable frame for tasks - using optimized approach
        tasks_outer_frame = ttk.LabelFrame(main_container, text="Replacement Tasks")
        tasks_outer_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Create optimized scrolled frame
        self.scrolled_frame = ScrolledFrame(tasks_outer_frame)
        self.scrolled_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Tasks frame inside scrolled area
        self.tasks_frame = ttk.Frame(self.scrolled_frame.interior)
        self.tasks_frame.pack(fill="both", expand=True)
        
        # List to keep track of replacement tasks
        self.tasks = []
        
        # Buttons frame
        buttons_frame = ttk.Frame(main_container)
        buttons_frame.pack(fill="x", pady=5)
        
        # Add task and configuration buttons
        ttk.Button(buttons_frame, text="Add Replacement Task", command=self.add_task).pack(side="left", padx=5)
        ttk.Button(buttons_frame, text="Save Configuration", command=self.save_config).pack(side="left", padx=5)
        ttk.Button(buttons_frame, text="Load Configuration", command=self.load_config).pack(side="left", padx=5)
        
        # Replace button with standard styling
        replace_btn = ttk.Button(main_container, text="Replace All", command=self.perform_replacements)
        replace_btn.pack(pady=10)
        
        # Add first task by default
        self.add_task()
        
        # Files to process
        self.files_to_process = []
        
        # Optimize event handling
        self.root.update_idletasks()
        self.root.after(100, self.optimize_tasks)
    
    def optimize_tasks(self):
        """Perform optimizations after initial rendering"""
        # Update the scrollregion after initial tasks are loaded
        self.scrolled_frame.update_scrollregion()
        
    def browse_files(self):
        file_paths = filedialog.askopenfilenames(filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if file_paths:
            self.files_to_process = file_paths
            # Update the display text
            if len(file_paths) == 1:
                self.file_path.set(file_paths[0])
            else:
                self.file_path.set(f"Selected {len(file_paths)} files")
    
    def browse_output_dir(self):
        dir_path = filedialog.askdirectory()
        if dir_path:
            self.output_dir.set(dir_path)
    
    def add_task(self):
        # Use update_idletasks to prevent UI freezing
        self.root.update_idletasks()
        task = ReplacementTask(self.tasks_frame, self, len(self.tasks))
        self.tasks.append(task)
        # Update scrollregion after adding a task
        self.scrolled_frame.update_scrollregion()
    
    def remove_task(self, idx):
        if len(self.tasks) <= 1:
            messagebox.showinfo("Info", "You need at least one replacement task.")
            return
            
        # Remove the frame
        self.tasks[idx].frame.destroy()
        # Remove from the list
        self.tasks.pop(idx)
        
        # Renumber the remaining tasks
        for i, task in enumerate(self.tasks):
            task.index = i
            task.frame.config(text=f"Replacement Task {i + 1}")
            
        # Update scrollregion after removing a task
        self.scrolled_frame.update_scrollregion()
    
    def save_config(self):
        # Get a file name to save to
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Save Configuration"
        )
        
        if not file_path:
            return
            
        config = {
            "output_prefix": self.output_prefix.get(),
            "output_suffix": self.output_suffix.get(),
            "output_dir": self.output_dir.get(),
            "tasks": []
        }
        
        # Save task data
        for task in self.tasks:
            task_data = task.get_data()
            if task_data:
                config["tasks"].append(task_data)
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)
            messagebox.showinfo("Success", "Configuration saved successfully")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save configuration: {str(e)}")
    
    def load_config(self):
        # Get a file name to load from
        file_path = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Load Configuration"
        )
        
        if not file_path:
            return
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                
            # Set output options
            self.output_prefix.set(config.get("output_prefix", "Imp_"))
            self.output_suffix.set(config.get("output_suffix", ""))
            self.output_dir.set(config.get("output_dir", ""))
            
            # Clear existing tasks
            for task in self.tasks:
                task.frame.destroy()
            self.tasks = []
            
            # Create new tasks from config
            if "tasks" in config and config["tasks"]:
                for task_data in config["tasks"]:
                    self.add_task()
                    self.tasks[-1].set_data(task_data)
            else:
                # Add at least one task
                self.add_task()
                
            messagebox.showinfo("Success", "Configuration loaded successfully")
            
            # Update scrollregion after loading tasks
            self.scrolled_frame.update_scrollregion()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load configuration: {str(e)}")
            # Add a default task if none exist
            if not self.tasks:
                self.add_task()
    
    def count_words_chars(self, text):
        """Count words and characters in text"""
        # Count characters (excluding whitespace)
        char_count = sum(1 for c in text if not c.isspace())
        # Count words
        word_count = len(text.split())
        return char_count, word_count
    
    def perform_replacements(self):
        import threading
        # Get files to process
        files_to_process = self.files_to_process
        if not files_to_process:
            messagebox.showerror("Error", "Please select at least one input file.")
            return
        # Check if all files exist
        for file_path in files_to_process:
            if not os.path.isfile(file_path):
                messagebox.showerror("Error", f"File does not exist: {file_path}")
                return
        # Gather replacement task data
        task_data = []
        for task in self.tasks:
            data = task.get_data()
            if data is None:  # Validation failed
                return
            task_data.append(data)
        # Get output directory
        output_dir = self.output_dir.get().strip()
        if output_dir and not os.path.isdir(output_dir):
            try:
                os.makedirs(output_dir)
            except Exception as e:
                messagebox.showerror("Error", f"Could not create output directory: {str(e)}")
                return
        # Show progress dialog
        progress_dialog = tk.Toplevel(self.root)
        progress_dialog.title("Processing Files")
        progress_dialog.transient(self.root)
        progress_dialog.grab_set()
        progress_dialog.geometry("300x100")
        progress_dialog.resizable(False, False)
        # Center the dialog
        progress_dialog.geometry("+%d+%d" % (
            self.root.winfo_rootx() + self.root.winfo_width() // 2 - 150,
            self.root.winfo_rooty() + self.root.winfo_height() // 2 - 50
        ))
        progress_label = ttk.Label(progress_dialog, text="Processing files...")
        progress_label.pack(pady=10)
        progress_var = tk.DoubleVar()
        progress_bar = ttk.Progressbar(progress_dialog, variable=progress_var, maximum=len(files_to_process))
        progress_bar.pack(fill="x", padx=20, pady=10)

        # Worker function for each file
        def process_file(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                original_chars, original_words = self.count_words_chars(content)
                modified_content = content
                for task in task_data:
                    modified_content = self.process_replacement_task(modified_content, task)
                replaced_chars, replaced_words = self.count_words_chars(modified_content)
                dir_name, file_name = os.path.split(file_path)
                base_name, ext = os.path.splitext(file_name)
                output_path = output_dir if output_dir else dir_name
                prefix = self.output_prefix.get()
                suffix = self.output_suffix.get()
                output_file = os.path.join(output_path, f"{prefix}{base_name}{suffix}{ext}")
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(modified_content)
                return {
                    "output_file": output_file,
                    "original_chars": original_chars,
                    "original_words": original_words,
                    "replaced_chars": replaced_chars,
                    "replaced_words": replaced_words,
                }
            except Exception as e:
                return {"error": str(e), "file": file_path}

        # Run in thread to avoid blocking UI
        def run_parallel():
            total_original_chars = 0
            total_original_words = 0
            total_replaced_chars = 0
            total_replaced_words = 0
            processed_files = []
            errors = []
            max_workers = min(8, os.cpu_count() or 4)  # Use up to 8 threads
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_file = {executor.submit(process_file, file_path): file_path for file_path in files_to_process}
                completed = 0
                for future in concurrent.futures.as_completed(future_to_file):
                    result = future.result()
                    completed += 1
                    def update_progress():
                        progress_label.config(text=f"Processing file {completed} of {len(files_to_process)}")
                        progress_var.set(completed)
                    self.root.after(0, update_progress)
                    if result.get("error"):
                        errors.append(result)
                    else:
                        processed_files.append(result["output_file"])
                        total_original_chars += result["original_chars"]
                        total_original_words += result["original_words"]
                        total_replaced_chars += result["replaced_chars"]
                        total_replaced_words += result["replaced_words"]
            def finish():
                progress_dialog.destroy()
                self.original_chars.set(f"{total_original_chars} characters, {total_original_words} words")
                self.replaced_chars.set(f"{total_replaced_chars} characters, {total_replaced_words} words")
                if errors:
                    msg = "\n".join([f"{e['file']}: {e['error']}" for e in errors])
                    messagebox.showerror("Error", f"Some files failed to process:\n{msg}")
                elif len(processed_files) == 1:
                    messagebox.showinfo("Success", f"Replacement completed. Output saved to:\n{processed_files[0]}")
                else:
                    messagebox.showinfo("Success", f"Replacement completed for {len(processed_files)} files.\nFiles saved to output location.")
            self.root.after(0, finish)

        threading.Thread(target=run_parallel, daemon=True).start()
    
    def process_replacement_task(self, content, task):
        """Process a single replacement task on content"""
        search_term = task["search_term"]
        use_regex = task["use_regex"]
        case_sensitive = task["case_sensitive"]
        
        # Find all occurrences
        if use_regex:
            try:
                if case_sensitive:
                    pattern = re.compile(search_term)
                else:
                    pattern = re.compile(search_term, re.IGNORECASE)
                matches = list(pattern.finditer(content))
            except re.error as e:
                messagebox.showerror("Regex Error", f"Invalid regular expression: {str(e)}")
                return content
        else:
            if case_sensitive:
                matches = list(re.finditer(re.escape(search_term), content))
            else:
                matches = list(re.finditer(re.escape(search_term), content, re.IGNORECASE))
        
        total_occurrences = len(matches)
        
        if total_occurrences == 0:
            return content  # No matches, return unchanged
        
        # Calculate how many occurrences to replace for each replacement
        replacements = []
        start_idx = 0
        
        # Only replace the percentage specified by the user, leave the rest as original
        for replacement in task["replacements"]:
            # Calculate the number of occurrences to replace for this percentage
            count = int(round(total_occurrences * replacement["percentage"] / 100.0))
            end_idx = min(start_idx + count, total_occurrences)
            
            if end_idx > start_idx:  # Only add if there's something to replace
                replacements.append({
                    "replace_with": replacement["replace_with"],
                    "start_idx": start_idx,
                    "end_idx": end_idx
                })
            
            start_idx = end_idx
        
        # Create a list of tuples (position, replacement text)
        to_replace = []
        
        for repl in replacements:
            for i in range(repl["start_idx"], repl["end_idx"]):
                if i < len(matches):
                    match = matches[i]
                    to_replace.append((match.start(), match.end(), repl["replace_with"]))
        
        # Sort replacements by position (descending)
        to_replace.sort(key=lambda x: x[0], reverse=True)
        
        # Apply replacements
        content_list = list(content)
        for start, end, repl in to_replace:
            content_list[start:end] = repl
        
        return ''.join(content_list)


class ScrolledFrame(ttk.Frame):
    """An optimized scrollable frame widget"""
    def __init__(self, parent, *args, **kwargs):
        ttk.Frame.__init__(self, parent, *args, **kwargs)
        
        # Create a canvas for scrolling
        self.canvas = tk.Canvas(self, borderwidth=0, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        # Layout the widgets
        self.scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        
        # Create the interior frame that will hold widgets
        self.interior = ttk.Frame(self.canvas)
        self.interior_id = self.canvas.create_window((0, 0), window=self.interior, anchor="nw")
        
        # Configure the canvas to resize with the frame
        self.interior.bind("<Configure>", self._on_interior_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        
        # Bind mouse wheel for scrolling (platform specific)
        if os.name == 'nt':  # Windows
            self.canvas.bind_all("<MouseWheel>", self._on_mousewheel_windows)
        else:  # Unix systems
            self.canvas.bind_all("<Button-4>", self._on_mousewheel_unix_up)
            self.canvas.bind_all("<Button-5>", self._on_mousewheel_unix_down)
        
        # Initial update
        self.update_scrollregion()
    
    def _on_interior_configure(self, event):
        """Update the scrollbar when the interior frame changes size"""
        self.update_scrollregion()
    
    def _on_canvas_configure(self, event):
        """Resize the interior frame when the canvas changes size"""
        # Update the width of the interior frame to match the canvas
        self.canvas.itemconfig(self.interior_id, width=event.width)
    
    def update_scrollregion(self):
        """Update the canvas scroll region to match the interior's size"""
        self.canvas.update_idletasks()
        self.canvas.config(scrollregion=self.canvas.bbox("all"))
    
    def _on_mousewheel_windows(self, event):
        """Handle Windows mousewheel events"""
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
    
    def _on_mousewheel_unix_up(self, event):
        """Handle Unix mousewheel up events"""
        self.canvas.yview_scroll(-1, "units")
    
    def _on_mousewheel_unix_down(self, event):
        """Handle Unix mousewheel down events"""
        self.canvas.yview_scroll(1, "units")
    
    def __del__(self):
        """Clean up event bindings when widget is destroyed"""
        # Unbind all mousewheel events to prevent memory leaks
        try:
            self.canvas.unbind_all("<MouseWheel>")
            self.canvas.unbind_all("<Button-4>")
            self.canvas.unbind_all("<Button-5>")
        except:
            pass


if __name__ == "__main__":
    root = tk.Tk()
    # Set icon and theme
    try:
        root.iconbitmap("icon.ico")
    except Exception as e:
        print(f"Could not load custom .ico: {e!r}")
    root.option_add('*Font', 'TkDefaultFont 9')
    app = TextReplacerApp(root)
    root.mainloop()
