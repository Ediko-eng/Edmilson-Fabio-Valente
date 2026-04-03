# FINITE AUTOMATA & MORPHOLOGY ANALYSIS SYSTEM FOR TETUM and English LANGUAGE

*A rule-based linguistic analyzer for Tetum and English, powered by DFA/NFA engines and a modern PyQt6 interface.*

---

## 📖 Description
This system is an advanced linguistic tool developed to perform morphology analysis and vocabulary extraction. By integrating **Deterministic Finite Automata (DFA)** and **Nondeterministic Finite Automata (NFA)**, the application recognizes complex text patterns. 

A primary goal of this project is to address the **"over-stemming"** challenge in the Tetum language—ensuring that root words (like *hatan*) are preserved and not incorrectly truncated during linguistic processing.

![App Screenshot](screenshot.png) 
*Note: Replace screenshot.png with an actual image of your app.*

## 🚀 Features
* **Morphology Analysis:** Extracts prefixes, roots, and suffixes for Tetum and English.
* **Automata Engines:** Specialized DFA/NFA classes for pattern recognition.
* **Multi-Format Support:** Seamlessly processes **PDF, DOCX, and TXT** files.
* **Over-stemming Protection:** Implements rule-based logic to maintain high accuracy for Tetum stems.
* **Export Capabilities:** Save analysis results to **CSV** for Excel or Database use.

## 🛠 Tech Stack
* **Language:** Python 3.11+
* **GUI Framework:** PyQt6
* **Data Handling:** Pandas
* **Document Processing:** PyPDF2, python-docx

## 📁 Project Structure
* `main_app.py`: Entry point for the application.
* `main_window.py`: Responsive UI and thread management.
* `morphology_logic.py`: Core Tetum/English stemming engine.
* `fa_logic.py`: DFA and NFA engine implementation.
* `file_reader.py`: Utility for reading PDF, Word, and Text.

## ⚙️ Installation & Usage

### 1. Clone the repository
```bash
git clone [https://github.com/your-username/your-repo-name.git](https://github.com/your-username/your-repo-name.git)
cd your-repo-name
