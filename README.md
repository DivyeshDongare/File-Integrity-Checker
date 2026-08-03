# 🛡️ File Integrity Checker

A **File Integrity Checker** is a cybersecurity project that monitors files and detects unauthorized modifications by comparing their cryptographic hash values. Each file is assigned a unique hash (digital fingerprint) using the **SHA-256** algorithm. If the file is modified, even by a single character, its hash changes, allowing the application to identify potential tampering.

This project is useful for monitoring sensitive files, verifying data integrity, and learning the fundamentals of cryptography and cybersecurity.

---

# 🎯 Project Objectives

The main objectives of this project are:

* Generate a SHA-256 hash for each monitored file.
* Store hash values securely for future comparison.
* Scan files and directories efficiently.
* Detect modified, deleted, or newly added files.
* Log integrity check results.
* Provide a simple command-line interface for users.

---

# ✨ Features

* Generate SHA-256 hashes for files.
* Monitor individual files or complete directories.
* Store hash values in a local database.
* Detect:

  * Modified files
  * Deleted files
  * Newly added files
* Generate detailed logs of all integrity checks.
* Simple and user-friendly CLI.
* Configurable project settings using a JSON configuration file.

---

# 🛠️ Technologies Used

| Category      | Technology       |
| ------------- | ---------------- |
| Language      | Python 3         |
| Hashing       | hashlib          |
| File Handling | os, pathlib      |
| Database      | SQLite (sqlite3) |
| Configuration | JSON             |
| Logging       | logging          |
| CLI           | argparse         |

---

# 📚 Python Libraries

### Built-in Libraries

* `hashlib` – Generate SHA-256 hashes.
* `os` – File and directory operations.
* `pathlib` – Cross-platform file path handling.
* `sqlite3` – Store file hash information.
* `json` – Read configuration settings.
* `logging` – Record integrity check activities.
* `argparse` – Command-line argument parsing.

### Optional Libraries

* `rich` – Colored terminal output.
* `schedule` – Automatic periodic scanning.
* `colorama` – Cross-platform colored console output.
* `PyQt5` or `Tkinter` – GUI implementation.

---

# 📂 Project Structure

```text
file_integrity_checker/
│
├── scanner.py          # Scans directories and files
├── hasher.py           # Generates SHA-256 hashes
├── database.py         # Stores and retrieves file hashes
├── checker.py          # Compares stored and current hashes
├── logger.py           # Logging configuration
├── config.json         # Project configuration
├── cli.py              # Command-line interface
├── gui.py              # GUI implementation (optional)
├── main.py             # Application entry point
│
├── logs/               # Log files
│
└── database/
    └── integrity.db    # SQLite database
```

---

# ⚙️ How It Works

1. Select a file or directory to monitor.
2. Generate a SHA-256 hash for every file.
3. Store the generated hashes in the SQLite database.
4. During future scans, generate new hashes.
5. Compare the new hashes with the stored values.
6. If a mismatch is found, report the file as modified.
7. Log all scan results for future reference.

---

# 🔒 Hashing Algorithm

This project uses the **SHA-256** cryptographic hashing algorithm.

Why SHA-256?

* Produces a unique 256-bit hash value.
* Collision resistant.
* Widely used in cybersecurity.
* Secure and reliable for integrity verification.

---

# 📝 Logging

The application maintains log files containing:

* Scan date and time
* Files scanned
* Modified files
* Deleted files
* Newly added files
* Errors (if any)

---

# 🧪 Testing

To test the application:

1. Create a folder containing sample files.
2. Run the application to generate and store hashes.
3. Modify one of the files.
4. Run the integrity check again.
5. Verify that the modified file is detected.
6. Delete or add files and confirm they are reported correctly.

---

# 🚀 Future Enhancements

* Real-time file monitoring.
* Email notifications for file changes.
* GUI using Tkinter or PyQt5.
* Automatic scheduled scans.
* Support for multiple hashing algorithms.
* Export scan reports to PDF or CSV.
* Cloud database integration.
* Multi-user authentication.

---

# 🎓 Learning Outcomes

By completing this project, you will gain practical experience with:

* Cryptographic hashing (SHA-256)
* File system operations
* SQLite database management
* Logging and error handling
* Command-line application development
* Cybersecurity fundamentals
* Python project organization

---

# 📌 Conclusion

The **File Integrity Checker** is a practical cybersecurity project that demonstrates how cryptographic hashing can be used to verify file integrity and detect unauthorized modifications. It provides hands-on experience with Python, file handling, databases, and security concepts while serving as a strong portfolio project for students and aspiring cybersecurity professionals.
