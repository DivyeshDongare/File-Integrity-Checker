# 🔒 File Integrity Checker

A Python-based **File Integrity Checker** that helps monitor files for unauthorized modifications by generating and comparing cryptographic hash values. The application verifies file integrity using the **SHA-256** hashing algorithm and alerts users if a file has been modified, deleted, or newly added. This project is useful for cybersecurity, digital forensics, and data integrity verification.

---

## 🎯 Project Objectives

The primary objectives of this project are:

- Generate SHA-256 hashes for files.
- Store hash values securely for future verification.
- Detect unauthorized file modifications.
- Identify newly added and deleted files.
- Provide an easy-to-use graphical interface.
- Maintain logs of integrity checks.

---

## ✨ Features

- Verify file integrity using the SHA-256 hashing algorithm.
- Detect modified or corrupted files.
- Detect newly added files.
- Detect deleted files.
- User-friendly graphical interface.
- Fast and reliable integrity checking.
- Store file hash values for future comparison.
- Lightweight and easy to use.
- Cross-platform Python application.
- Generate logs of integrity check results.

---

## 🛠️ Technologies Used

| Category | Technology |
|----------|------------|
| Language | Python 3.x |
| GUI | Tkinter |
| Hashing | hashlib |
| File Handling | os, pathlib |
| Database | SQLite (sqlite3) |
| Configuration | JSON |
| Logging | logging |

---

## 📚 Python Libraries

### Built-in Libraries

- `hashlib` – Generate SHA-256 hashes.
- `os` – File and directory operations.
- `pathlib` – Cross-platform path handling.
- `sqlite3` – Store and retrieve file hash values.
- `json` – Manage configuration settings.
- `logging` – Record application activities.
- `tkinter` – Build the graphical user interface.

### Optional Libraries

- `rich` – Colored terminal output.
- `colorama` – Colored console output.
- `schedule` – Automatic integrity scans.

---

## 📁 Project Structure

```text
File-Integrity-Checker/
│
├── main.py                # Application entry point
├── gui.py                 # Graphical User Interface
├── scanner.py             # Scans directories and files
├── hasher.py              # Generates SHA-256 hashes
├── checker.py             # Compares stored and current hashes
├── database.py            # Database operations
├── logger.py              # Logging configuration
├── config.json            # Project configuration
├── requirements.txt       # Project dependencies
├── README.md
├── LICENSE
├── .gitignore
│
├── assets/                # Images and icons
├── logs/                  # Generated log files
└── database/
    └── integrity.db       # SQLite database
```

> **Note:** The `logs/`, `database/`, `venv/`, and `__pycache__/` directories are generated locally and should not be committed to GitHub.

---

## ⚙️ Installation

### 1. Clone the repository

```bash
git clone https://github.com/your-username/File-Integrity-Checker.git
```

### 2. Move into the project directory

```bash
cd File-Integrity-Checker
```

### 3. (Optional) Create a virtual environment

#### Windows

```bash
python -m venv venv
venv\Scripts\activate
```

#### Linux / macOS

```bash
python3 -m venv venv
source venv/bin/activate
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

---

## ▶️ Running the Application

Run the application using:

```bash
python main.py
```

If your project starts from the GUI file instead:

```bash
python gui.py
```

---

## ⚙️ How It Works

1. Select a file or folder to monitor.
2. Generate SHA-256 hashes for all selected files.
3. Store the generated hashes in the SQLite database.
4. Run an integrity scan whenever required.
5. Generate new hashes for the current files.
6. Compare current hashes with the stored hashes.
7. Display whether each file is:
   - ✅ Unchanged
   - ✏️ Modified
   - ➕ Newly Added
   - ❌ Deleted
8. Save the scan results in the log file.

---

## 🔐 Hashing Algorithm

This project uses the **SHA-256** cryptographic hashing algorithm.

### Why SHA-256?

- Produces a unique 256-bit fingerprint.
- Highly secure and collision-resistant.
- Detects even the smallest file modification.
- Commonly used in cybersecurity and digital forensics.

---

## 📋 Workflow

```text
Clone Repository
       │
       ▼
Install Dependencies
       │
       ▼
Run Application
       │
       ▼
Select File or Folder
       │
       ▼
Generate SHA-256 Hashes
       │
       ▼
Store Hashes
       │
       ▼
Run Integrity Check
       │
       ▼
Compare Hash Values
       │
       ▼
Display Results
       │
       ▼
Generate Logs
```

---

## 📝 Logging

Every integrity check is recorded in a log file, including:

- Scan date and time
- Files scanned
- Modified files
- Newly added files
- Deleted files
- Error messages (if any)

---

## 🧪 Testing

To verify that the application works correctly:

1. Create a folder containing sample files.
2. Generate and save the initial hash values.
3. Modify one of the files.
4. Run another integrity check.
5. Confirm that the modified file is detected.
6. Delete a file and verify it is reported.
7. Add a new file and ensure it is recognized.

---

## 📋 Requirements

- Python 3.10 or later
- Windows, Linux, or macOS

---

## 🚀 Future Enhancements

- Real-time file monitoring.
- Scheduled automatic scans.
- Email notifications for detected changes.
- Export reports as PDF or CSV.
- Support for additional hashing algorithms.
- Password-protected database.
- Multi-user support.
- Dark mode interface.
- Cloud synchronization.

---

## 🎓 Learning Outcomes

This project demonstrates practical knowledge of:

- Cryptographic hashing (SHA-256)
- File system operations
- Python GUI development with Tkinter
- SQLite database management
- Logging and error handling
- Cybersecurity fundamentals
- File integrity verification techniques

---

## 🤝 Contributing

Contributions are welcome! If you have suggestions, bug fixes, or new features, feel free to:

1. Fork the repository.
2. Create a feature branch.
3. Commit your changes.
4. Push the branch.
5. Open a Pull Request.

---
