from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTableWidget, QPushButton, QFrame, QCheckBox, 
    QTextEdit, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QTableWidgetItem
from PyQt6.QtGui import QColor

from PyQt6.QtCore import QTimer
from core.process_scanner import ProcessScanner
import core.power_model as pm

from ui.graph_widget import ProcessGraph
from ui.alert_popup import AlertPopup
from ui.toast import Toast

import psutil, datetime, os
import time

# AppData Path Setup 
APP_NAME = "SEPRO"
APP_DIR = os.path.join(os.getenv('LOCALAPPDATA'), APP_NAME)
LOGS_DIR = os.path.join(APP_DIR, "logs")

if not os.path.exists(LOGS_DIR):
    os.makedirs(LOGS_DIR)
ANOMALY_LOG_FILE = os.path.join(LOGS_DIR, "anomalies.log")
# End Path Setup 

class MainWindow(QMainWindow):
    
    COOLDOWN_PERIOD = 3 * 60  # 3-min alert snooze
    APP_START_GRACE_PERIOD = 30 # startup grace period in seconds

    def __init__(self):
        super().__init__()

        self.setWindowTitle("SEPRO - Smart Energy Process Radar")
        self.setMinimumSize(1200, 700)

        self.scanner = ProcessScanner()
        self.detector = pm.AnomalyDetector()
        self.current_process = None
        self.snooze_timestamps = {}
        self.app_start_time = time.time()

        container = QWidget()
        layout = QVBoxLayout(container)

        title = QLabel("SEPRO — Real-Time Power & Anomaly Monitor")
        title.setStyleSheet("font-size:18px; font-weight:bold; color:#00C3FF;")
        layout.addWidget(title)

        content_layout = QHBoxLayout()

        # --- Table has 6 columns ---
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(
            ["Process", "CPU %", "Memory MB", "Disk MB/s", "Power Score", "Action"]
        )
        self.table.cellClicked.connect(self.select_process)
        
        # --- Resize the last column ---
        self.table.setColumnWidth(5, 70) # 70 pixels for the "Kill" button
        
        content_layout.addWidget(self.table, stretch=3)

        # Right Panel
        right_panel = QVBoxLayout()
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        self.log_display.setText("Anomaly Log (This Session):\n")
        self.log_display.setStyleSheet(
            "border:2px solid #00C3FF; padding:10px; color:#FFFFFF;"
        )
        right_panel.addWidget(self.log_display, stretch=1)
        
        self.clear_log_button = QPushButton("Clear Log")
        self.clear_log_button.clicked.connect(self.clear_anomaly_log)
        right_panel.addWidget(self.clear_log_button, stretch=0)

        self.graph = ProcessGraph()
        right_panel.addWidget(self.graph, stretch=2)
        content_layout.addLayout(right_panel, stretch=2)
        layout.addLayout(content_layout)

        # Bottom Bar
        bottom_bar = QHBoxLayout()
        self.freeze_checkbox = QCheckBox("❄️ Freeze Table (Stop Sorting)")
        bottom_bar.addWidget(self.freeze_checkbox)

        self.top_consumers_button = QPushButton("Show Top Power Consumers")
        self.top_consumers_button.clicked.connect(self.show_top_consumers)
        bottom_bar.addWidget(self.top_consumers_button)

        self.status = QLabel("Status: Idle")
        self.status.setStyleSheet("color:#4FD3FF; padding:4px")
        bottom_bar.addWidget(self.status, 1, Qt.AlignmentFlag.AlignRight) 
        layout.addLayout(bottom_bar)

        self.setCentralWidget(container)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_process_table)
        self.timer.start(2000)
    def show_top_consumers(self):
        """
        Reads the baseline_store.json file, finds the top 5 processes
        based on their long-term AVERAGE (mean) power score, and displays them.
        """
        try:
            # Load the baseline data from baseline_store.json
            baseline_data = pm.load_baseline()

            if not baseline_data:
                QMessageBox.information(self, "No Data", "No baseline data has been learned yet. Use the app for a few minutes.")
                return

            # Create a list of (name, mean_score) tuples
            all_processes = []
            for name, data in baseline_data.items():
                # We are interested in the 'mean' (average score)
                mean_score = data.get("mean", 0)
                all_processes.append((name, mean_score))

            # Sort the list by score (the 2nd item in the tuple) in descending order
            sorted_consumers = sorted(all_processes, key=lambda item: item[1], reverse=True)

            # Get the top 5
            top_5 = sorted_consumers[:5]

            if not top_5:
                QMessageBox.information(self, "No Data", "No processes have been recorded.")
                return

            message_body = "Based on long-term average 'Power Score':\n"
            details = []
            for i, (name, score) in enumerate(top_5):
                details.append(f"{i+1}. {name} (Average Score: {score:.3f})")

            message_body += "\n".join(details)

            # Use a dynamic title
            title = f"Top {len(top_5)} All-Time Consumers"
            QMessageBox.information(self, title, message_body)

        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not parse baseline file: {e}")

    def clear_anomaly_log(self):
        self.log_display.setText("Anomaly Log (This Session):\n")

    def update_process_table(self):
        is_frozen = self.freeze_checkbox.isChecked()

        if is_frozen:
            processes = self.scanner.get_app_processes()
            self.table.setSortingEnabled(False)
        else:
            processes = sorted(
                self.scanner.get_app_processes(),
                # --- This is the corrected lambda function ---
                key=lambda p: p["score"] if "score" in p else pm.PowerModel.compute_score(p.get("cpu", 0), p.get("mem", 0), p.get("disk", 0)),
                reverse=True
            )
            self.table.setSortingEnabled(True)
            self.table.sortByColumn(4, Qt.SortOrder.DescendingOrder)

        self.table.setRowCount(len(processes))
        process_alive = False
        
        current_names = {p['name'] for p in processes}
        self.snooze_timestamps = {
            name: timestamp for name, timestamp
            in self.snooze_timestamps.items()
            if name in current_names
        }
        
        current_time = time.time() 
        in_startup_grace_period = (current_time - self.app_start_time) < self.APP_START_GRACE_PERIOD

        for row, p in enumerate(processes):
            name, cpu, mem, disk = p["name"], p["cpu"], p["mem"], p["disk"]
            score = pm.PowerModel.compute_score(cpu, mem, disk)
            p["score"] = score

            if in_startup_grace_period:
                self.detector.check(name, score) # Learn, but don't flag
                is_suspicious = False
            else:
                is_suspicious, rules = self.detector.check(name, score)

            if is_suspicious:
                self.log_anomaly(name, rules, score)
                
                last_alert_time = self.snooze_timestamps.get(name, 0)
                if (current_time - last_alert_time) > self.COOLDOWN_PERIOD:
                    
                    self.snooze_timestamps[name] = current_time
                    
                    if self.isMinimized():
                        self.activateWindow()
                    
                    alert = AlertPopup(self, name)
                    
                    if alert.show_alert():
                        self.kill_process(name)
                    
                    timestamp = datetime.datetime.now().strftime("%I:%M:%S %p")
                    self.log_display.append(
                        f"⚠️ {timestamp}: '{name}' flagged"
                    )
                
            if self.current_process == name:
                process_alive = True
                self.graph.update(cpu, score)

            values = [name, cpu, mem, disk, round(score, 3)]
            for col, val in enumerate(values):
                item = QTableWidgetItem(str(val))
                if is_suspicious:
                    item.setForeground(Qt.GlobalColor.red)
                self.table.setItem(row, col, item)
            
            # --- This section re-creates the button every time ---
            kill_button = QPushButton("Kill")
            kill_button.setStyleSheet("background-color: #550000; color: white; padding: 4px;")
            kill_button.clicked.connect(lambda checked, n=name: self.kill_process(n))
            self.table.setCellWidget(row, 5, kill_button)
            # --- END ---

        if self.current_process and not process_alive:
            self.graph.freeze()

        self.detector.save()
        
        if in_startup_grace_period:
            remaining = (self.app_start_time + self.APP_START_GRACE_PERIOD) - current_time
            self.status.setStyleSheet("color: #FFAA00; padding: 4px;") # Yellow
            self.status.setText(f"Status: Learning... (Grace period: {remaining:.0f}s left)")
        else:
            self.status.setStyleSheet("color: #4FD3FF; padding: 4px;") # Cyan
            self.status.setText(f"Status: Monitoring… {len(processes)} processes")
        
        if self.current_process:
            self.highlight_selected_row(self.current_process)

    def highlight_selected_row(self, proc_name):
        highlight_color = QColor(40, 80, 120) 
        
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if not item:
                continue
            
            is_selected_row = (item.text() == proc_name)
            
            for col in range(self.table.columnCount() - 1): # -1 to skip button col
                cell = self.table.item(row, col)
                if not cell:
                    continue
                
                if is_selected_row:
                    cell.setBackground(highlight_color)
                else:
                    cell.setBackground(QColor(Qt.GlobalColor.transparent))

    def select_process(self, row, col):
        if col == 5: # Column 5 is the "Action" column
            return
        
        try:
            proc = self.table.item(row, 0).text()
            self.current_process = proc
            self.graph.cpu_history.clear()
            self.graph.score_history.clear()
            self.graph.set_tracking_process(proc)
            self.highlight_selected_row(proc)
            
            Toast(self, f"Tracking {proc}")
        except Exception as e:
            print(f"Error in select_process: {e}")

    def kill_process(self, process_name):
        killed_count = 0
        error_count = 0
        process_found = False
        
        for proc in psutil.process_iter(['name']):
            if proc.info['name'] == process_name:
                process_found = True 
                try:
                    proc.kill()
                    killed_count += 1
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    error_count += 1
                except:
                    error_count += 1

        # toast call
        try:
            if killed_count > 0:
                Toast(self, f"Killed {killed_count} instance(s) of {process_name}")
            elif error_count > 0:
                Toast(self, f"Could not kill {process_name}. May require Admin rights.")
            elif not process_found:
                 Toast(self, f"Process '{process_name}' not found. (May have already closed)")
        except Exception as e:
            print(f"Toast notification failed: {e}")
            if killed_count > 0:
                print(f"Killed {killed_count} instance(s) of {process_name}")


    def log_anomaly(self, name, rules, score):
        with open(ANOMALY_LOG_FILE, "a") as f:
            f.write(f"{datetime.datetime.now()} | {name} | rules={rules} | score={score}\n")