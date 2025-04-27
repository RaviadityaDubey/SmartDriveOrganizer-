# SmartDrive Organizer 🧠💾

SmartDrive Organizer is a Windows desktop application that helps you organize messy folders intelligently using file types, modification dates, and even an AI-based fallback classifier.

## 🚀 Features

- 🗂️ Sort by categories (Documents, Images, Videos, etc.)
- 🧠 AI fallback for unknown file types
- 📆 Option to sort by modification date (Year/Month)
- 🧪 Preview sort results before applying
- 🔄 Undo last sort
- 📋 Action logs viewer
- 🖱️ Drag & Drop folder selection
- 🧳 Portable `.exe` – no installation required

## 🖥️ Requirements

- Windows 10/11
- Python 3.8+ (only if using source code)
- Packages: `tkinter`, `scikit-learn`, `joblib`, `sqlite3`

## 📦 Installation (Executable)

1. Download the latest `SmartDriveOrganizer.exe` from [Releases](https://github.com/yourusername/smartdrive/releases)
2. Run the `.exe` (no install needed)
3. Select a folder → choose categories → click `Run Sort`

## 💻 Developer Setup

```bash
git clone https://github.com/yourusername/smartdrive-organizer
cd smartdrive-organizer
pip install -r requirements.txt
python main.py
