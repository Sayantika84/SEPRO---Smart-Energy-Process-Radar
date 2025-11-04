from PyQt6.QtWidgets import QMessageBox

class AlertPopup(QMessageBox):
    """
    A custom dialog that blocks and asks the user for
    an action on a detected anomaly.
    """
    def __init__(self, parent, process_name):
        super().__init__(parent)
        self.process_name = process_name
        
        # --- Configure the Alert ---
        self.setIcon(QMessageBox.Icon.Warning)
        self.setWindowTitle("⚠️ Anomaly Detected")
        self.setText(f"Suspicious activity detected in '{process_name}'.")
        self.setInformativeText(
            "This process is showing abnormal behavior based on its learned behavior.\n\n"
            "Do you want to terminate this process?"
        )
        
        
        # Add Buttons 
        # We create button objects to check which one was clicked
        self.kill_button = self.addButton("Kill Process", QMessageBox.ButtonRole.DestructiveRole)
        self.ignore_button = self.addButton("Ignore", QMessageBox.ButtonRole.RejectRole)
        
        # Make "Ignore" the default (e.g., if user hits Enter)
        self.setDefaultButton(self.ignore_button)

    def show_alert(self):
        """
        Shows the modal alert and returns True if 'Kill' was clicked,
        False otherwise.
        """
        # exec() blocks the app until the user clicks a button
        self.exec()
        
        # Check which button was clicked
        if self.clickedButton() == self.kill_button:
            return True
        else:
            return False