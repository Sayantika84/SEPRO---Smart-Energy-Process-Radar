# SEPRO — Smart Energy Process Radar

A real-time Windows desktop application to monitor, analyze, and detect anomalies in process-level power consumption.

---

## How to Run the Project

### **1. Requirements**

* **OS:** Windows 10 or 11
* **Python:** Version 3.8 or above
* **Libraries:**

  ```bash
  pip install pyqt6 psutil pyqtgraph
  ```

### **2. Run the Application**

If running from source:

```bash
python main.py
```

The main window will open displaying:

* Real-time process table with CPU, memory, disk, and power score.
* Live graph (CPU% vs Power Score).
* Alerts for suspicious processes.

### **3. Optional — Build Executable (.exe)**

To package the app as a standalone executable:

```bash
pyinstaller --onefile --windowed main.py
```

The generated `.exe` can be found inside the **dist/** folder.

---

## Project Structure

```
SOURCE_CODE_SEPRO/
│
├── build/                    # PyInstaller build directory (ignored in Git)
│
├── core/                     # Core logic modules
│   ├── process_scanner.py     # Scans and aggregates process metrics
│   ├── power_model.py         # Power Score calculation and anomaly detection
│
├── dist/                     # Generated executable output
│   └── main.exe
│
├── logs/                     # Runtime anomaly and event logs
│
├── ui/                       # User interface components
│   ├── __init__.py
│   ├── alert_popup.py         # Alert popup for anomaly detection
│   ├── graph_widget.py        # Real-time CPU vs Power Score visualization
│   ├── main_window.py         # Main application window controller
│   ├── toast.py               # Non-blocking notification system
│
├── venv/                     # Virtual environment (excluded from Git)
│
├── main.py                   # Entry point of the application
├── main.spec                 # PyInstaller spec file (optional)
├── README.md                 # Project documentation
├── requirement.txt            # List of required Python libraries
└── .gitignore                # Git ignore configuration
```

---

## Data Files

The app automatically creates and maintains the following files in:

```
%LOCALAPPDATA%\SEPRO\
├── baseline_store.json   # Stores learned baseline data
└── anomalies.log         # Logs all detected anomalies
```

---

## Description

* Computes a **Power Score** for each process based on CPU, memory, and disk usage.
* Learns baseline behavior using an exponential moving average.
* Flags anomalies when multiple statistical deviation rules are triggered.
* Allows users to terminate or ignore suspicious processes via alert popups.

---

## Credits

Developed as part of the Coursework of **Software Engineering (CA725)**
**Department of Computer Applications, NIT Trichy**

**Contributors:**

* Arjun Singh Panwar 
* Sayantika Mondal 
