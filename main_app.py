# ============================================================================
# MAIN APPLICATION ENTRY POINT
# ============================================================================

import sys
from PyQt6.QtWidgets import QApplication
from main_window import UltimateFAAnalyzer

def main():
    # Create application instance
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    app.setApplicationName("UNTL FA Analyzer")
    app.setOrganizationName("UNTL")
    
    # Create and show main window
    window = UltimateFAAnalyzer()
    window.show()
    
    # Execute application
    sys.exit(app.exec())

if __name__ == "__main__":
    main()