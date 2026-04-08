# Historical Display Generator

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

Desktop application for generating historical event posters for 4-sided LED displays.

## Features

- Automatic event loading from Wikipedia API
- Real-time event preview
- Editable event text
- Automatic image loading from Wikipedia
- 2080x1872 pixel poster generation (4 sides)
- Gradient background and customizable styles
- Logging system for all operations
- Backup and restore functionality

## Installation

### Requirements

- Python 3.8+
- tkinter (included in Python standard library)
- Pillow: `pip install Pillow`
- requests: `pip install requests`

### Quick Start

```bash
# Clone the repository
git clone https://github.com/yourusername/historical-display.git
cd historical-display

# Install dependencies
pip install Pillow requests

# Run the application
python historical_display_gui.py
```

Or use the pre-built executable:
```
dist/HistoricalDisplay.exe
```

## Project Structure

```
historical-display/
├── historical_display_gui.py  # Main application file
├── logging_config.py          # Logging configuration
├── backup.py                  # Backup/restore script
├── LICENSE                    # MIT License
├── README.md                  # This file
├── requirements.txt           # Python dependencies
├── Маскот/                   # Mascot images
│   ├── tsvet_21.png
│   ├── tsvet_23.png
│   ├── tsvet_25.png
│   └── tsvet_27.png
└── dist/                     # Compiled executables
```

## Usage

### 1. Select Date

1. Enter day and month
2. Click "Загрузить" (Load)
3. System will load up to 100 events from Wikipedia

### 2. Select Events

For each of 4 sides:
1. Select event from dropdown
2. Edit text if needed in input field
3. Click "Загр" to load images

### 3. Generate Poster

1. Click "Сохранить изображение" (Save Image)
2. Choose save folder
3. File will be saved as `история_DD_MM.png`

## Backup Commands

```bash
# Create backup
python backup.py create

# List backups
python backup.py list

# Restore from backup
python backup.py restore historical_display_backup_YYYYMMDD_HHMMSS.zip
```

## Generated Poster Structure

```
┌─────────┬─────────┬─────────┬─────────┐
│         │         │         │         │
│  Date   │  Date   │  Date   │  Date   │
│  This   │  This   │  This   │  This   │
│  day    │  day    │  day    │  day    │
│in history│in history│in history│in history│
├─────────┼─────────┼─────────┼─────────┤
│         │         │         │         │
│  Year   │  Year   │  Year   │  Year   │
│         │         │         │         │
├─────────┼─────────┼─────────┼─────────┤
│         │         │         │         │
│  Event  │  Event  │  Event  │  Event  │
│  Text   │  Text   │  Text   │  Text   │
│         │         │         │         │
├─────────┼─────────┼─────────┼─────────┤
│         │         │         │         │
│  Image  │  Image  │  Image  │  Image  │
│         │         │         │         │
│[Mascot]│[Mascot]│[Mascot]│[Mascot]│
└─────────┴─────────┴─────────┴─────────┘
```

## Settings

### Color Scheme

- Start background: `#23363d`
- End background: `#20B2AA`
- Text color: white

### Block Sizes

- Side: 520x1872 pixels
- Header block: ~520 pixels
- Year block: ~200 pixels
- Text block: ~340 pixels
- Image block: ~800 pixels
- Line thickness: 4 pixels

## Building Executable

```bash
# Install PyInstaller
pip install pyinstaller

# Build executable
pyinstaller --onefile --windowed --name "HistoricalDisplay" historical_display_gui.py
```

## Notes

- Wikipedia API provides events from 1500 CE
- For events BCE, manual input is required
- Images are loaded from Russian and English Wikipedia
- Application uses threads for async image loading

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
