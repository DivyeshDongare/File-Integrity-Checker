"""
GUI frontend using standard Tkinter (no CustomTkinter required).
"""

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
import json
from pathlib import Path
import sys

# Import project modules
try:
    from scanner import DirectoryScanner
    from hasher import FileHasher
    from database import HashDatabase
    from checker import IntegrityChecker
    from logger import setup_logger, get_audit_logger
except ImportError as e:
    print(f"Error importing modules: {e}")
    sys.exit(1)


class FileIntegrityGUI:
    """Main GUI application class using standard Tkinter."""
    
    def __init__(self):
        """Initialize the GUI application."""
        # Create main window
        self.root = tk.Tk()
        self.root.title("File Integrity Checker")
        self.root.geometry("1100x700")
        self.root.minsize(900, 600)
        
        # Load configuration
        self.config = self.load_config()
        
        # Initialize components
        self.database = HashDatabase(self.config.get('database_path', 'file_hashes.db'))
        self.logger = setup_logger(
            log_dir=self.config.get('log_directory', 'logs'),
            log_level=self.config.get('log_level', 'INFO')
        )
        self.audit_logger = get_audit_logger(self.config.get('log_directory', 'logs'))
        
        # Variables
        self.selected_path = tk.StringVar()
        self.status_text = tk.StringVar(value="Ready")
        self.progress_var = tk.DoubleVar(value=0)
        
        # Style configuration
        self.style = ttk.Style()
        self.style.theme_use('clam')  # Modern theme
        
        # Build UI
        self.create_widgets()
        
        # Update statistics on startup
        self.update_statistics()
    
    def load_config(self) -> dict:
        """Load configuration from config.json."""
        try:
            with open('config.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            messagebox.showwarning("Config Not Found", 
                                  "config.json not found. Using defaults.")
            return self.get_default_config()
        except json.JSONDecodeError:
            messagebox.showerror("Config Error", 
                                "Invalid config.json. Using defaults.")
            return self.get_default_config()
    
    @staticmethod
    def get_default_config() -> dict:
        """Return default configuration."""
        return {
            'hash_algorithm': 'sha256',
            'recursive_scan': True,
            'exclude_patterns': ['*.log', '__pycache__', '*.pyc', '.git'],
            'database_path': 'file_hashes.db',
            'log_directory': 'logs',
            'log_level': 'INFO'
        }
    
    def create_widgets(self):
        """Create all GUI widgets."""
        # Main container with padding
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill="both", expand=True)
        
        # Title
        title_label = tk.Label(
            main_frame,
            text="File Integrity Checker",
            font=("Arial", 24, "bold"),
            bg="#f0f0f0"
        )
        title_label.pack(pady=20)
        
        # Path selection frame
        self.create_path_selection(main_frame)
        
        # Action buttons frame
        self.create_action_buttons(main_frame)
        
        # Notebook (tabbed interface)
        self.create_notebook(main_frame)
        
        # Status bar at bottom
        self.create_status_bar(main_frame)
    
    def create_path_selection(self, parent):
        """Create path selection section."""
        path_frame = ttk.LabelFrame(parent, text="Directory Selection", padding="10")
        path_frame.pack(fill="x", padx=10, pady=10)
        
        ttk.Label(path_frame, text="Path:").pack(side="left", padx=5)
        
        path_entry = ttk.Entry(path_frame, textvariable=self.selected_path, width=60)
        path_entry.pack(side="left", padx=5, fill="x", expand=True)
        
        browse_btn = ttk.Button(path_frame, text="Browse", command=self.browse_directory)
        browse_btn.pack(side="left", padx=5)
    
    def create_action_buttons(self, parent):
        """Create action buttons section."""
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill="x", padx=10, pady=10)
        
        # Create buttons with styling
        ttk.Button(
            button_frame,
            text="Create Baseline",
            command=self.create_baseline_thread
        ).pack(side="left", padx=5, pady=5)
        
        ttk.Button(
            button_frame,
            text="Verify Integrity",
            command=self.verify_integrity_thread
        ).pack(side="left", padx=5, pady=5)
        
        ttk.Button(
            button_frame,
            text="Update Baseline",
            command=self.update_baseline_thread
        ).pack(side="left", padx=5, pady=5)
        
        ttk.Button(
            button_frame,
            text="Clear Baseline",
            command=self.clear_baseline
        ).pack(side="left", padx=5, pady=5)
    
    def create_notebook(self, parent):
        """Create notebook (tabbed interface)."""
        self.notebook = ttk.Notebook(parent)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Create tabs
        self.results_tab = ttk.Frame(self.notebook)
        self.stats_tab = ttk.Frame(self.notebook)
        self.settings_tab = ttk.Frame(self.notebook)
        self.logs_tab = ttk.Frame(self.notebook)
        
        self.notebook.add(self.results_tab, text="Results")
        self.notebook.add(self.stats_tab, text="Statistics")
        self.notebook.add(self.settings_tab, text="Settings")
        self.notebook.add(self.logs_tab, text="Logs")
        
        # Populate tabs
        self.create_results_tab()
        self.create_statistics_tab()
        self.create_settings_tab()
        self.create_logs_tab()
    
    def create_results_tab(self):
        """Create results display tab."""
        # Results text widget with scrollbar
        text_frame = ttk.Frame(self.results_tab)
        text_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        scrollbar = ttk.Scrollbar(text_frame)
        scrollbar.pack(side="right", fill="y")
        
        self.results_text = tk.Text(
            text_frame,
            wrap="word",
            yscrollcommand=scrollbar.set,
            font=("Courier", 10)
        )
        self.results_text.pack(fill="both", expand=True)
        scrollbar.config(command=self.results_text.yview)
    
    def create_statistics_tab(self):
        """Create statistics display tab."""
        stats_frame = ttk.Frame(self.stats_tab, padding="20")
        stats_frame.pack(fill="both", expand=True)
        
        # Statistics labels
        self.stats_labels = {}
        
        stats_items = [
            ("Total Files:", "total_files"),
            ("Total Size:", "total_size"),
            ("Hash Algorithm:", "algorithm"),
            ("Last Update:", "last_update")
        ]
        
        for idx, (label_text, key) in enumerate(stats_items):
            ttk.Label(
                stats_frame,
                text=label_text,
                font=("Arial", 12, "bold")
            ).grid(row=idx, column=0, padx=10, pady=10, sticky="w")
            
            value_label = ttk.Label(stats_frame, text="N/A", font=("Arial", 12))
            value_label.grid(row=idx, column=1, padx=10, pady=10, sticky="w")
            self.stats_labels[key] = value_label
        
        # Refresh button
        ttk.Button(
            stats_frame,
            text="Refresh Statistics",
            command=self.update_statistics
        ).grid(row=len(stats_items), column=0, columnspan=2, pady=20)
    
    def create_settings_tab(self):
        """Create settings configuration tab."""
        settings_frame = ttk.Frame(self.settings_tab, padding="20")
        settings_frame.pack(fill="both", expand=True)
        
        # Hash algorithm
        ttk.Label(settings_frame, text="Hash Algorithm:", font=("Arial", 11)).grid(
            row=0, column=0, padx=10, pady=10, sticky="w"
        )
        
        self.algo_var = tk.StringVar(value=self.config.get('hash_algorithm', 'sha256'))
        algo_combo = ttk.Combobox(
            settings_frame,
            textvariable=self.algo_var,
            values=["md5", "sha1", "sha256", "sha384", "sha512", "blake2b"],
            state="readonly"
        )
        algo_combo.grid(row=0, column=1, padx=10, pady=10, sticky="w")
        
        # Recursive scan
        self.recursive_var = tk.BooleanVar(value=self.config.get('recursive_scan', True))
        ttk.Checkbutton(
            settings_frame,
            text="Recursive Scan",
            variable=self.recursive_var
        ).grid(row=1, column=0, padx=10, pady=10, sticky="w")
        
        # Log level
        ttk.Label(settings_frame, text="Log Level:", font=("Arial", 11)).grid(
            row=2, column=0, padx=10, pady=10, sticky="w"
        )
        
        self.log_level_var = tk.StringVar(value=self.config.get('log_level', 'INFO'))
        log_combo = ttk.Combobox(
            settings_frame,
            textvariable=self.log_level_var,
            values=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
            state="readonly"
        )
        log_combo.grid(row=2, column=1, padx=10, pady=10, sticky="w")
        
        # Save button
        ttk.Button(
            settings_frame,
            text="Save Settings",
            command=self.save_settings
        ).grid(row=3, column=0, columnspan=2, pady=20)
    
    def create_logs_tab(self):
        """Create logs display tab."""
        logs_frame = ttk.Frame(self.logs_tab)
        logs_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Logs text widget with scrollbar
        scrollbar = ttk.Scrollbar(logs_frame)
        scrollbar.pack(side="right", fill="y")
        
        self.logs_text = tk.Text(
            logs_frame,
            wrap="word",
            yscrollcommand=scrollbar.set,
            font=("Courier", 9)
        )
        self.logs_text.pack(fill="both", expand=True)
        scrollbar.config(command=self.logs_text.yview)
        
        # Refresh button
        ttk.Button(
            self.logs_tab,
            text="Refresh Logs",
            command=self.load_logs
        ).pack(pady=5)
    
    def create_status_bar(self, parent):
        """Create status bar at bottom."""
        status_frame = ttk.Frame(parent)
        status_frame.pack(fill="x", padx=10, pady=5)
        
        # Status label
        ttk.Label(
            status_frame,
            textvariable=self.status_text,
            relief="sunken",
            anchor="w"
        ).pack(side="left", fill="x", expand=True, padx=5)
        
        # Progress bar
        self.progress_bar = ttk.Progressbar(
            status_frame,
            mode="determinate",
            variable=self.progress_var,
            maximum=1.0,
            length=300
        )
        self.progress_bar.pack(side="right", padx=5)
    
    def browse_directory(self):
        """Open directory browser dialog."""
        directory = filedialog.askdirectory(title="Select Directory to Monitor")
        if directory:
            self.selected_path.set(directory)
    
    # Rest of the methods remain the same as CustomTkinter version
    # (create_baseline_thread, create_baseline, verify_integrity_thread, etc.)
    # Just copy them from the original code
    
    def create_baseline_thread(self):
        """Create baseline in separate thread."""
        if not self.selected_path.get():
            messagebox.showwarning("No Path", "Please select a directory first.")
            return
        thread = threading.Thread(target=self.create_baseline, daemon=True)
        thread.start()
    
    def create_baseline(self):
        """Create file integrity baseline."""
        try:
            path = self.selected_path.get()
            self.status_text.set("Creating baseline...")
            self.progress_var.set(0.3)
            
            scanner = DirectoryScanner(path, exclude_patterns=self.config.get('exclude_patterns', []))
            files = scanner.scan_directory(recursive=self.recursive_var.get())
            
            self.progress_var.set(0.5)
            
            hasher = FileHasher(algorithm=self.algo_var.get())
            processed = 0
            for file_info in files:
                try:
                    file_hash = hasher.hash_file(file_info.path)
                    self.database.store_hash(
                        file_path=file_info.relative_path,
                        file_hash=file_hash,
                        file_size=file_info.size,
                        modified_time=file_info.modified_time,
                        algorithm=self.algo_var.get()
                    )
                    processed += 1
                except Exception as e:
                    self.logger.error(f"Error processing {file_info.path}: {e}")
            
            self.progress_var.set(1.0)
            self.status_text.set(f"Baseline created: {processed} files")
            self.display_results(f"✓ Baseline created successfully\nTotal files: {processed}\nPath: {path}")
            self.audit_logger.log_baseline_created(path, processed)
            self.update_statistics()
            messagebox.showinfo("Success", f"Baseline created with {processed} files")
        except Exception as e:
            self.status_text.set("Error creating baseline")
            messagebox.showerror("Error", f"Failed to create baseline: {e}")
        finally:
            self.progress_var.set(0)
    
    def verify_integrity_thread(self):
        """Verify integrity in separate thread."""
        if not self.selected_path.get():
            messagebox.showwarning("No Path", "Please select a directory first.")
            return
        thread = threading.Thread(target=self.verify_integrity, daemon=True)
        thread.start()
    
    def verify_integrity(self):
        """Verify file integrity."""
        # Implementation same as CustomTkinter version
        pass
    
    def update_baseline_thread(self):
        """Update baseline in separate thread."""
        if messagebox.askyesno("Confirm", "Replace current baseline?"):
            thread = threading.Thread(target=self.update_baseline, daemon=True)
            thread.start()
    
    def update_baseline(self):
        """Update baseline."""
        self.database.clear_baseline()
        self.create_baseline()
    
    def clear_baseline(self):
        """Clear baseline."""
        if messagebox.askyesno("Confirm", "Delete all baseline data?"):
            self.database.clear_baseline()
            self.status_text.set("Baseline cleared")
            self.update_statistics()
            messagebox.showinfo("Success", "Baseline cleared")
    
    def display_results(self, text: str):
        """Display results."""
        self.results_text.delete("1.0", "end")
        self.results_text.insert("1.0", text)
        self.notebook.select(self.results_tab)
    
    def update_statistics(self):
        """Update statistics."""
        stats = self.database.get_statistics()
        self.stats_labels['total_files'].config(text=str(stats.get('total_files', 0)))
        total_size = stats.get('total_size', 0)
        self.stats_labels['total_size'].config(text=f"{total_size / (1024*1024):.2f} MB")
        algorithms = stats.get('algorithms', {})
        self.stats_labels['algorithm'].config(text=", ".join([f"{k}: {v}" for k, v in algorithms.items()]) or "N/A")
        self.stats_labels['last_update'].config(text=str(stats.get('latest_update', 'N/A')))
    
    def save_settings(self):
        """Save settings."""
        self.config['hash_algorithm'] = self.algo_var.get()
        self.config['recursive_scan'] = self.recursive_var.get()
        self.config['log_level'] = self.log_level_var.get()
        with open('config.json', 'w') as f:
            json.dump(self.config, f, indent=4)
        messagebox.showinfo("Success", "Settings saved")
    
    def load_logs(self):
        """Load logs."""
        logs = self.database.get_audit_log(limit=50)
        self.logs_text.delete("1.0", "end")
        for log in logs:
            log_line = f"[{log['timestamp']}] {log['operation']}"
            if log['file_path']:
                log_line += f" - {log['file_path']}"
            self.logs_text.insert("end", log_line + "\n")
    
    def run(self):
        """Start GUI."""
        self.root.mainloop()


def launch_gui():
    """Launch GUI."""
    app = FileIntegrityGUI()
    app.run()


if __name__ == "__main__":
    launch_gui()
