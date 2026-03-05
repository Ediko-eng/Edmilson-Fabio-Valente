"""
Main Window - Responsive UI for Laptop Screens
"""

import sys
import os
import re
import pandas as pd
from collections import Counter
import PyPDF2
import docx
from PyPDF2.errors import PdfReadError
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QComboBox, QTableWidget, QTableWidgetItem, QLabel, QPushButton,
    QHeaderView, QMessageBox, QFileDialog, QProgressBar, QGroupBox,
    QSplitter, QTextEdit, QListWidget, QListWidgetItem, QTabWidget,
    QRadioButton, QButtonGroup, QStackedWidget, QSpinBox, QCheckBox,
    QFormLayout, QFrame, QSizePolicy, QScrollArea
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QSize
from PyQt6.QtGui import QFont, QColor, QPalette

# Import our modular components
from morphology_logic import LinguisticEngine
from fa_logic import EnhancedDFAAnalyzer, NFAVocabularyAnalyzer
from file_reader import FileReader


# ============================================================================
# PROCESSING THREADS
# ============================================================================

class FAProcessingThread(QThread):
    """Thread for Finite Automata processing with language support"""
    progress_updated = pyqtSignal(int)
    result_ready = pyqtSignal(list, dict)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, file_path, fa_type, params):
        super().__init__()
        self.file_path = file_path
        self.fa_type = fa_type  # 'dfa' or 'nfa'
        self.params = params
    
    def run(self):
        try:
            # Read file using FileReader
            text = FileReader.read_file(self.file_path)
            self.progress_updated.emit(50)
            
            # Process based on FA type
            if self.fa_type == 'dfa':
                # ===== USE ENHANCED DFA WITH LANGUAGE =====
                from fa_logic import EnhancedDFAAnalyzer
                
                # Get language from parameters (if provided) or use default
                language = self.params.get('language', 'English')
                
                # Check if language parameter was passed from UI
                if 'language' in self.params:
                    dfa = EnhancedDFAAnalyzer(language=self.params['language'])
                else:
                    dfa = EnhancedDFAAnalyzer(language='English')
                
                min_len = self.params.get('min_length', 3)
                max_len = self.params.get('max_length', 15)
                filter_stop = self.params.get('filter_stop_words', True)
                
                words = dfa.process_text_with_language(
                    text, 
                    min_length=min_len, 
                    max_length=max_len,
                    filter_stop_words=filter_stop
                )
                # ==========================================
                
                # Get language-specific stats
                stats = dfa.get_language_stats(words)
                
            elif self.fa_type == 'nfa':
                nfa = NFAVocabularyAnalyzer()
                pattern_name = self.params.get('pattern', 'English Words')
                words = nfa.process_with_pattern(text, pattern_name)
                words.sort()
                
                # Statistics for NFA
                if words:
                    lengths = [len(w) for w in words]
                    stats = {
                        'total_words': len(words),
                        'min_length': min(lengths),
                        'max_length': max(lengths),
                        'avg_length': round(sum(lengths) / len(words), 2),
                        'fa_type': self.fa_type.upper(),
                        'pattern': self.params.get('pattern', 'N/A')
                    }
                else:
                    stats = {
                        'total_words': 0,
                        'min_length': 0,
                        'max_length': 0,
                        'avg_length': 0,
                        'fa_type': self.fa_type.upper(),
                        'pattern': self.params.get('pattern', 'N/A')
                    }
            
            # Prepare results
            result = [(i+1, word) for i, word in enumerate(words)]
            
            self.progress_updated.emit(100)
            self.result_ready.emit(result, stats)
            
        except Exception as e:
            self.error_occurred.emit(str(e))

class MorphologyProcessingThread(QThread):
    """Thread for morphology analysis"""
    progress_updated = pyqtSignal(int)
    result_ready = pyqtSignal(list, dict)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, file_path, language):
        super().__init__()
        self.file_path = file_path
        self.language = language
    
    def run(self):
        try:
            # Read file using FileReader
            text = FileReader.read_file(self.file_path)
            self.progress_updated.emit(30)
            
            # Extract words
            words = re.findall(r'\b[a-z]{3,}\b', text.lower())
            unique_words = sorted(list(set(words)))
            
            # Filter by language
            filtered_words = []
            for i, word in enumerate(unique_words):
                if len(word) >= 3 and word not in LinguisticEngine.LANGUAGE_PATTERNS.get(self.language, {}).get("stop_words", {}):
                    filtered_words.append(word)
                
                # Update progress
                if i % 100 == 0:
                    progress = 30 + int((i + 1) / len(unique_words) * 30)
                    self.progress_updated.emit(progress)
            
            # Analyze morphology with improved analysis
            results = []
            for i, word in enumerate(filtered_words):
                prefix, suffix, root, confidence, analysis_type = LinguisticEngine.identify_morphology(word, self.language)
                results.append([i+1, word, prefix, suffix, root, f"{confidence:.1%}", analysis_type])
                
                # Update progress
                if i % 50 == 0:
                    progress = 60 + int((i + 1) / len(filtered_words) * 40)
                    self.progress_updated.emit(progress)
            
            # Statistics
            stats = {
                'total_words': len(words),
                'filtered_words': len(filtered_words),
                'language': self.language,
                'unique_words': len(unique_words),
                'analysis_type': 'Improved Morphology with Over-stemming Prevention'
            }
            
            self.progress_updated.emit(100)
            self.result_ready.emit(results, stats)
            
        except Exception as e:
            self.error_occurred.emit(str(e))


# ============================================================================
# MAIN APPLICATION WINDOW (RESPONSIVE FOR LAPTOPS)
# ============================================================================

class UltimateFAAnalyzer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("UNTL - Finite Automata & Morphology Analysis System")
        
        # Set reasonable initial size for laptops
        self.resize(1200, 700)
        self.setMinimumSize(1024, 600)  # Minimum for 13-14" laptops
        
        # Initialize
        self.folder_path = "dataset"
        self.current_results = []
        self.current_stats = {}
        self.processing_thread = None
        self.current_mode = "morphology"
        self.screen_width = QApplication.primaryScreen().availableGeometry().width()
        
        # Setup
        self.setup_styles()
        self.init_ui()
        
        # Timer to adjust layout after showing
        QTimer.singleShot(100, self.adjust_for_screen)
    
    def adjust_for_screen(self):
        """Adjust UI based on screen size"""
        screen_width = self.screen_width
        
        if screen_width < 1366:  # Small laptop screens (13-14")
            # Make left panel narrower
            self.left_panel.setMaximumWidth(320)
            # Adjust font sizes
            font = self.font()
            font.setPointSize(9)
            self.setFont(font)
        elif screen_width < 1600:  # Medium laptop screens (15-16")
            self.left_panel.setMaximumWidth(380)
        else:  # Large screens
            self.left_panel.setMaximumWidth(420)
    
    def setup_styles(self):
        """Modern dark theme styling with responsive adjustments"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #0f172a;
            }
            QLabel {
                color: #f8fafc;
                font-family: 'Segoe UI', 'Inter', sans-serif;
            }
            QLabel#TitleLabel {
                font-size: 22px;
                font-weight: bold;
                color: #38bdf8;
                padding: 8px;
                letter-spacing: 0.3px;
            }
            QGroupBox {
                color: #38bdf8;
                font-weight: bold;
                border: 1px solid #334155;
                border-radius: 8px;
                margin-top: 8px;
                padding-top: 16px;
                background-color: rgba(30, 41, 59, 0.7);
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 10px;
                font-size: 14px;
            }
            QComboBox, QSpinBox {
                background-color: #1e293b;
                color: #cbd5e1;
                border: 1px solid #334155;
                border-radius: 6px;
                padding: 8px 12px;
                min-height: 22px;
                font-size: 13px;
            }
            QComboBox:hover, QSpinBox:hover {
                border-color: #38bdf8;
                background-color: #1e293b;
            }
            QPushButton {
                border-radius: 8px;
                padding: 10px 18px;
                font-weight: 600;
                border: 1px solid transparent;
                font-size: 13px;
                transition: all 0.2s;
            }
            QPushButton#ProcessBtn {
                background-color: #3b82f6;
                color: white;
                border-color: #2563eb;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton#ProcessBtn:hover {
                background-color: #2563eb;
                transform: translateY(-1px);
                box-shadow: 0 3px 8px rgba(37, 99, 235, 0.3);
            }
            QPushButton#ProcessBtn:pressed {
                background-color: #1d4ed8;
                transform: translateY(0);
            }
            QPushButton#ExportBtn {
                background-color: #10b981;
                color: white;
                border-color: #059669;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton#ExportBtn:hover {
                background-color: #059669;
                transform: translateY(-1px);
                box-shadow: 0 3px 8px rgba(5, 150, 105, 0.3);
            }
            QPushButton#ExportBtn:pressed {
                background-color: #047857;
                transform: translateY(0);
            }
            QPushButton:disabled {
                background-color: #374151;
                color: #9ca3af;
                border-color: #4b5563;
            }
            QTableWidget {
                background-color: #1e293b;
                color: #e2e8f0;
                gridline-color: #334155;
                border: 1px solid #334155;
                border-radius: 8px;
                font-size: 12px;
                selection-background-color: #38bdf8;
                selection-color: #0f172a;
            }
            QHeaderView::section {
                background-color: #334155;
                color: #38bdf8;
                font-weight: bold;
                border: none;
                height: 35px;
                padding-left: 12px;
                font-size: 12px;
            }
            QProgressBar {
                border: 1px solid #334155;
                border-radius: 6px;
                text-align: center;
                color: #f8fafc;
                font-weight: bold;
                font-size: 11px;
                height: 20px;
            }
            QProgressBar::chunk {
                background-color: #38bdf8;
                border-radius: 4px;
            }
            QRadioButton {
                color: #cbd5e1;
                spacing: 10px;
                font-size: 13px;
                font-weight: 500;
                padding: 6px 0;
            }
            QRadioButton::indicator {
                width: 18px;
                height: 18px;
                border-radius: 9px;
                border: 1px solid #475569;
            }
            QRadioButton::indicator:checked {
                background-color: #38bdf8;
                border-color: #38bdf8;
            }
            QTextEdit {
                background-color: #1e293b;
                color: #cbd5e1;
                border: 1px solid #334155;
                border-radius: 6px;
                padding: 8px;
                font-size: 11px;
            }
            QCheckBox {
                color: #cbd5e1;
                font-size: 12px;
            }
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                border: none;
                background-color: #1e293b;
                width: 10px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background-color: #475569;
                border-radius: 5px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #64748b;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
    
    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main horizontal layout
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)
        
        # ========= LEFT PANEL (Controls) =========
        self.left_panel = QWidget()
        self.left_panel.setMaximumWidth(380)  # Will be adjusted based on screen
        left_layout = QVBoxLayout(self.left_panel)
        left_layout.setSpacing(15)
        
        # Title Section
        title_section = QWidget()
        title_layout = QVBoxLayout(title_section)
        title_layout.setSpacing(5)
        
        title = QLabel("UNIVERSIDADE NACIONAL TIMOR LOROSA'E")
        title.setObjectName("TitleLabel")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setWordWrap(True)
        title.setMaximumHeight(60)
        
        subtitle = QLabel("Finite Automata & Morphology Analysis System")
        subtitle.setStyleSheet("color: #94a3b8; font-size: 13px; text-align: center; padding: 3px;")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setWordWrap(True)
        
        title_layout.addWidget(title)
        title_layout.addWidget(subtitle)
        left_layout.addWidget(title_section)
        
        # Mode Selection
        mode_group = QGroupBox("Select Analysis Mode")
        mode_layout = QVBoxLayout(mode_group)
        mode_layout.setSpacing(8)
        
        self.morphology_radio = QRadioButton("🧬 Morphology Analyzer")
        self.morphology_radio.setChecked(True)
        self.morphology_radio.toggled.connect(self.on_mode_changed)
        
        self.dfa_radio = QRadioButton("🔢 DFA Engine (Lowercase Words)")
        self.dfa_radio.toggled.connect(self.on_mode_changed)
        
        self.nfa_radio = QRadioButton("🔍 NFA Engine (Pattern Search)")
        self.nfa_radio.toggled.connect(self.on_mode_changed)
        
        mode_layout.addWidget(self.morphology_radio)
        mode_layout.addWidget(self.dfa_radio)
        mode_layout.addWidget(self.nfa_radio)
        mode_layout.addStretch()
        
        left_layout.addWidget(mode_group)
        
        # Stacked Widget for different modes
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        left_layout.addWidget(self.stacked_widget)
        
        # Create widgets for each mode
        morphology_widget = self.create_morphology_widget()
        self.stacked_widget.addWidget(morphology_widget)
        
        dfa_widget = self.create_dfa_widget()
        self.stacked_widget.addWidget(dfa_widget)
        
        nfa_widget = self.create_nfa_widget()
        self.stacked_widget.addWidget(nfa_widget)
        
        # Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        left_layout.addWidget(self.progress_bar)
        
        # Action Buttons
        button_layout = QVBoxLayout()
        button_layout.setSpacing(12)
        
        self.btn_process = QPushButton("🚀 START ANALYSIS")
        self.btn_process.setObjectName("ProcessBtn")
        self.btn_process.clicked.connect(self.start_analysis)
        self.btn_process.setMinimumHeight(40)
        
        self.btn_export = QPushButton("📊 EXPORT RESULTS")
        self.btn_export.setObjectName("ExportBtn")
        self.btn_export.setEnabled(False)
        self.btn_export.clicked.connect(self.export_results)
        self.btn_export.setMinimumHeight(40)
        
        button_layout.addWidget(self.btn_process)
        button_layout.addWidget(self.btn_export)
        
        left_layout.addLayout(button_layout)
        left_layout.addStretch()
        
        # Add left panel to main layout
        main_layout.addWidget(self.left_panel)
        
        # ========= RIGHT PANEL (Results) =========
        # Create scroll area for right panel
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        right_panel_container = QWidget()
        right_layout = QVBoxLayout(right_panel_container)
        right_layout.setSpacing(15)
        
        # Results Area
        results_group = QGroupBox("Analysis Results")
        results_layout = QVBoxLayout(results_group)
        results_layout.setSpacing(12)
        
        # Statistics
        stats_layout = QHBoxLayout()
        
        self.stats_label = QLabel("Ready for analysis...")
        self.stats_label.setStyleSheet("""
            color: #94a3b8; 
            font-size: 12px; 
            padding: 8px;
            background-color: rgba(30, 41, 59, 0.5);
            border-radius: 6px;
            border: 1px solid #334155;
        """)
        self.stats_label.setWordWrap(True)
        self.stats_label.setMinimumHeight(60)
        
        self.details_label = QLabel("🧬 Morphology Mode")
        self.details_label.setStyleSheet("""
            color: #38bdf8; 
            font-weight: bold; 
            font-size: 13px;
            padding: 8px 12px;
            background-color: rgba(30, 41, 59, 0.7);
            border-radius: 6px;
            border: 1px solid #334155;
        """)
        self.details_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.details_label.setMinimumWidth(120)
        
        stats_layout.addWidget(self.stats_label, 3)
        stats_layout.addWidget(self.details_label, 1)
        
        results_layout.addLayout(stats_layout)
        
        # Results Table with scroll
        table_container = QWidget()
        table_layout = QVBoxLayout(table_container)
        table_layout.setContentsMargins(0, 0, 0, 0)
        
        self.results_table = QTableWidget()
        self.results_table.setAlternatingRowColors(True)
        self.results_table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        # Enable horizontal scrolling for table
        self.results_table.setHorizontalScrollMode(QTableWidget.ScrollMode.ScrollPerPixel)
        
        table_layout.addWidget(self.results_table)
        results_layout.addWidget(table_container, 1)
        
        right_layout.addWidget(results_group, 1)
        
        # Status Label
        self.status_label = QLabel("System ready. Select a mode and file to begin analysis.")
        self.status_label.setStyleSheet("""
            color: #94a3b8; 
            font-size: 11px; 
            font-style: italic;
            padding: 6px;
            border-top: 1px solid #334155;
            background-color: rgba(30, 41, 59, 0.3);
        """)
        self.status_label.setWordWrap(True)
        right_layout.addWidget(self.status_label)
        
        # Set the scroll area widget
        scroll_area.setWidget(right_panel_container)
        
        # Add scroll area to main layout
        main_layout.addWidget(scroll_area, 1)
        
        # Initial setup
        QApplication.processEvents()
        self.refresh_file_list()
        
        # Set initial column sizes
        QTimer.singleShot(100, self.setup_table_columns)
    
    def setup_table_columns(self):
        """Setup table column widths based on current window size"""
        if self.current_mode == "morphology":
            # Calculate column widths based on available space
            table_width = self.results_table.width() - 40  # Account for scrollbar
            
            if table_width > 600:
                # Enough space for all columns
                self.results_table.setColumnWidth(0, 50)   # #
                self.results_table.setColumnWidth(1, 100)  # Word
                self.results_table.setColumnWidth(2, 90)   # Prefix
                self.results_table.setColumnWidth(3, 90)   # Suffix
                self.results_table.setColumnWidth(4, 100)  # Root
                self.results_table.setColumnWidth(5, 80)   # Confidence
                self.results_table.setColumnWidth(6, 120)  # Type
            else:
                # Limited space, make columns smaller
                self.results_table.setColumnWidth(0, 40)   # #
                self.results_table.setColumnWidth(1, 80)   # Word
                self.results_table.setColumnWidth(2, 70)   # Prefix
                self.results_table.setColumnWidth(3, 70)   # Suffix
                self.results_table.setColumnWidth(4, 80)   # Root
                self.results_table.setColumnWidth(5, 70)   # Confidence
                self.results_table.setColumnWidth(6, 100)  # Type
        else:
            # DFA/NFA mode
            table_width = self.results_table.width() - 40
            
            if table_width > 500:
                self.results_table.setColumnWidth(0, 60)   # #
                self.results_table.setColumnWidth(1, 180)  # Word
                self.results_table.setColumnWidth(2, 80)   # Length
                self.results_table.setColumnWidth(3, 120)  # Type
            else:
                self.results_table.setColumnWidth(0, 50)   # #
                self.results_table.setColumnWidth(1, 150)  # Word
                self.results_table.setColumnWidth(2, 70)   # Length
                self.results_table.setColumnWidth(3, 100)  # Type
    
    def create_morphology_widget(self):
        """Create morphology analysis widget"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(12)
        
        # File selection
        file_group = QGroupBox("File Selection (PDF, DOCX, TXT)")
        file_layout = QVBoxLayout(file_group)
        
        file_combo_layout = QHBoxLayout()
        self.file_combo = QComboBox()
        self.file_combo.setMinimumHeight(30)
        
        btn_refresh = QPushButton("⟳")
        btn_refresh.setMaximumWidth(40)
        btn_refresh.setToolTip("Refresh file list")
        btn_refresh.clicked.connect(self.refresh_file_list)
        
        btn_browse = QPushButton("📁")
        btn_browse.setMaximumWidth(40)
        btn_browse.setToolTip("Browse for files")
        btn_browse.clicked.connect(self.browse_file)
        
        file_combo_layout.addWidget(self.file_combo, 1)
        file_combo_layout.addWidget(btn_refresh)
        file_combo_layout.addWidget(btn_browse)
        
        file_layout.addLayout(file_combo_layout)
        layout.addWidget(file_group)
        
        # Language selection
        lang_group = QGroupBox("Language Selection")
        lang_layout = QVBoxLayout(lang_group)
        
        self.lang_combo = QComboBox()
        self.lang_combo.addItems(["English", "Indonesia", "Tetum"])
        self.lang_combo.setMinimumHeight(30)
        
        lang_layout.addWidget(self.lang_combo)
        layout.addWidget(lang_group)
        
        # Info label
        info_label = QLabel("""
        <div style='color: #94a3b8; font-size: 11px;'>
        <b>Improved Morphology Analysis:</b><br>
        • True prefixes/suffixes only<br>
        • Over-stemming prevention<br>
        • Common root validation<br>
        • Analysis type identification
        </div>
        """)
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        layout.addStretch()
        return widget
    
    def create_dfa_widget(self):
        """Create DFA analysis widget"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(12)
        
        # File selection
        file_group = QGroupBox("File Selection (PDF, DOCX, TXT)")
        file_layout = QVBoxLayout(file_group)
        
        file_combo_layout = QHBoxLayout()
        self.dfa_file_combo = QComboBox()
        self.dfa_file_combo.setMinimumHeight(30)
        
        btn_refresh = QPushButton("⟳")
        btn_refresh.setMaximumWidth(40)
        btn_refresh.setToolTip("Refresh file list")
        btn_refresh.clicked.connect(self.refresh_file_list)
        
        btn_browse = QPushButton("📁")
        btn_browse.setMaximumWidth(40)
        btn_browse.setToolTip("Browse for files")
        btn_browse.clicked.connect(self.browse_file)
        
        file_combo_layout.addWidget(self.dfa_file_combo, 1)
        file_combo_layout.addWidget(btn_refresh)
        file_combo_layout.addWidget(btn_browse)
        
        file_layout.addLayout(file_combo_layout)
        layout.addWidget(file_group)
        
        # Language Selection for DFA
        lang_group = QGroupBox("Language Selection for DFA")
        lang_layout = QVBoxLayout(lang_group)
        
        self.dfa_lang_combo = QComboBox()
        self.dfa_lang_combo.addItems(["English", "Indonesia", "Tetum"])
        self.dfa_lang_combo.setMinimumHeight(30)
        
        lang_layout.addWidget(self.dfa_lang_combo)
        layout.addWidget(lang_group)
        
        # DFA Parameters
        params_group = QGroupBox("DFA Parameters")
        params_layout = QVBoxLayout(params_group)
        params_layout.setSpacing(8)
        
        # Word length
        length_layout = QHBoxLayout()
        length_layout.addWidget(QLabel("Min:"))
        self.dfa_min_spin = QSpinBox()
        self.dfa_min_spin.setRange(1, 20)
        self.dfa_min_spin.setValue(3)
        self.dfa_min_spin.setMinimumWidth(60)
        self.dfa_min_spin.setMinimumHeight(30)
        
        length_layout.addWidget(self.dfa_min_spin)
        length_layout.addSpacing(10)
        length_layout.addWidget(QLabel("Max:"))
        self.dfa_max_spin = QSpinBox()
        self.dfa_max_spin.setRange(2, 50)
        self.dfa_max_spin.setValue(12)
        self.dfa_max_spin.setMinimumWidth(60)
        self.dfa_max_spin.setMinimumHeight(30)
        
        length_layout.addWidget(self.dfa_max_spin)
        length_layout.addStretch()
        
        params_layout.addLayout(length_layout)
        
        # Filter option
        self.dfa_filter_check = QCheckBox("Filter language-specific stop words")
        self.dfa_filter_check.setChecked(True)
        params_layout.addWidget(self.dfa_filter_check)
        
        # DFA Info
        info_label = QLabel("""
        <div style='color: #94a3b8; font-size: 11px;'>
        <b>Enhanced DFA with Language Support:</b><br>
        • Language-specific character validation<br>
        • Language-specific stop word filtering<br>
        • Tetum/Indonesian diacritic support<br>
        • Language-specific word validation
        </div>
        """)
        info_label.setWordWrap(True)
        params_layout.addWidget(info_label)
        
        layout.addWidget(params_group)
        layout.addStretch()
        return widget
    
    def create_nfa_widget(self):
        """Create NFA analysis widget"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(12)
        
        # File selection
        file_group = QGroupBox("File Selection (PDF, DOCX, TXT)")
        file_layout = QVBoxLayout(file_group)
        
        file_combo_layout = QHBoxLayout()
        self.nfa_file_combo = QComboBox()
        self.nfa_file_combo.setMinimumHeight(30)
        
        btn_refresh = QPushButton("⟳")
        btn_refresh.setMaximumWidth(40)
        btn_refresh.setToolTip("Refresh file list")
        btn_refresh.clicked.connect(self.refresh_file_list)
        
        btn_browse = QPushButton("📁")
        btn_browse.setMaximumWidth(40)
        btn_browse.setToolTip("Browse for files")
        btn_browse.clicked.connect(self.browse_file)
        
        file_combo_layout.addWidget(self.nfa_file_combo, 1)
        file_combo_layout.addWidget(btn_refresh)
        file_combo_layout.addWidget(btn_browse)
        
        file_layout.addLayout(file_combo_layout)
        layout.addWidget(file_group)
        
        # NFA Pattern Selection
        pattern_group = QGroupBox("NFA Pattern Selection")
        pattern_layout = QVBoxLayout(pattern_group)
        pattern_layout.setSpacing(8)
        
        self.nfa_pattern_combo = QComboBox()
        self.nfa_pattern_combo.setMinimumHeight(30)
        nfa_engine = NFAVocabularyAnalyzer()
        self.nfa_pattern_combo.addItems(nfa_engine.get_patterns())
        self.nfa_pattern_combo.currentTextChanged.connect(self.on_nfa_pattern_changed)
        
        pattern_layout.addWidget(self.nfa_pattern_combo)
        
        # Pattern explanation
        self.nfa_explain_label = QTextEdit()
        self.nfa_explain_label.setMaximumHeight(100)
        self.nfa_explain_label.setReadOnly(True)
        pattern_layout.addWidget(self.nfa_explain_label)
        
        layout.addWidget(pattern_group)
        layout.addStretch()
        
        # Set initial explanation
        self.on_nfa_pattern_changed(self.nfa_pattern_combo.currentText())
        
        return widget
    
    def refresh_file_list(self):
        """Refresh file list for all combos"""
        files = []
        
        os.makedirs(self.folder_path, exist_ok=True)
        
        if os.path.exists(self.folder_path):
            try:
                # Support multiple file formats
                supported_formats = FileReader.get_supported_formats()
                files = [f for f in os.listdir(self.folder_path) 
                        if f.lower().endswith(tuple(supported_formats))]
                files.sort()
            except:
                files = []
        
        # Update all combos
        for combo_name in ['file_combo', 'dfa_file_combo', 'nfa_file_combo']:
            combo = getattr(self, combo_name, None)
            if combo is not None:
                current_text = combo.currentText()
                combo.clear()
                if files:
                    combo.addItems(files)
                    # Try to restore previous selection
                    if current_text in files:
                        combo.setCurrentText(current_text)
        
        if files:
            self.status_label.setText(f"Found {len(files)} files in dataset folder (PDF, DOCX, TXT)")
        else:
            self.status_label.setText("No supported files found in dataset folder")
    
    def on_mode_changed(self):
        """Handle mode change"""
        if self.morphology_radio.isChecked():
            self.current_mode = "morphology"
            self.stacked_widget.setCurrentIndex(0)
            self.details_label.setText("🧬 Morphology Mode")
            self.status_label.setText("Morphology mode: Analyzes word prefixes, suffixes, and roots with over-stemming prevention")
        elif self.dfa_radio.isChecked():
            self.current_mode = "dfa"
            self.stacked_widget.setCurrentIndex(1)
            self.details_label.setText("🔢 DFA Mode")
            self.status_label.setText("DFA mode: Finds lowercase words within specified length range")
        elif self.nfa_radio.isChecked():
            self.current_mode = "nfa"
            self.stacked_widget.setCurrentIndex(2)
            self.details_label.setText("🔍 NFA Mode")
            self.status_label.setText("NFA mode: Searches for specific word patterns")
        
        # Reset table
        self.results_table.clear()
        self.results_table.setRowCount(0)
        self.stats_label.setText("Ready for analysis. Select a file and click START ANALYSIS.")
        self.btn_export.setEnabled(False)
        
        # Adjust table columns for new mode
        self.setup_table_columns()
    
    def on_nfa_pattern_changed(self, pattern_name):
        """Update NFA pattern explanation"""
        try:
            nfa_engine = NFAVocabularyAnalyzer()
            explanation = nfa_engine.explain_pattern(pattern_name)
            self.nfa_explain_label.setText(f"<b>Pattern:</b> {pattern_name}<br><br>{explanation}")
        except Exception as e:
            self.nfa_explain_label.setText(f"<b>Pattern:</b> {pattern_name}<br><br>Error: {str(e)}")
    
    def browse_file(self):
        """Browse and add file"""
        file_filter = "Supported Files (*.pdf *.docx *.doc *.txt *.text);;PDF Files (*.pdf);;Word Documents (*.docx *.doc);;Text Files (*.txt *.text);;All Files (*.*)"
        
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select File", "", file_filter
        )
        
        if file_path:
            try:
                filename = os.path.basename(file_path)
                dest = os.path.join(self.folder_path, filename)
                
                os.makedirs(self.folder_path, exist_ok=True)
                
                import shutil
                
                if os.path.exists(dest):
                    reply = QMessageBox.question(
                        self, "File Exists", 
                        f"File '{filename}' already exists in dataset. Replace it?",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                    )
                    if reply == QMessageBox.StandardButton.No:
                        return
                
                shutil.copy(file_path, dest)
                self.refresh_file_list()
                
                # Update appropriate combo box
                if self.current_mode == "morphology":
                    self.file_combo.setCurrentText(filename)
                elif self.current_mode == "dfa":
                    self.dfa_file_combo.setCurrentText(filename)
                elif self.current_mode == "nfa":
                    self.nfa_file_combo.setCurrentText(filename)
                
                # Check file type
                ext = os.path.splitext(filename)[1].lower()
                file_type = {
                    '.pdf': 'PDF',
                    '.docx': 'Word Document',
                    '.doc': 'Word Document (older format)',
                    '.txt': 'Text File',
                    '.text': 'Text File'
                }.get(ext, 'Unknown')
                
                self.status_label.setText(f"Added {file_type}: '{filename}' to dataset")
                
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to add file: {str(e)}")
                self.status_label.setText("Failed to add file")
    
    def start_analysis(self):
        """Start analysis based on selected mode"""
        # Get file based on mode
        if self.current_mode == "morphology":
            filename = self.file_combo.currentText()
            language = self.lang_combo.currentText()
        elif self.current_mode == "dfa":
            filename = self.dfa_file_combo.currentText()
            # Get language from DFA language combo box
            language = self.dfa_lang_combo.currentText() if hasattr(self, 'dfa_lang_combo') else "English"
        elif self.current_mode == "nfa":
            filename = self.nfa_file_combo.currentText()
        else:
            return
        
        if not filename:
            QMessageBox.warning(self, "Warning", "Please select a file")
            return
        
        file_path = os.path.join(self.folder_path, filename)
        if not os.path.exists(file_path):
            QMessageBox.critical(self, "Error", f"File not found: {filename}")
            return
        
        # Reset UI
        self.results_table.clear()
        self.results_table.setRowCount(0)
        self.stats_label.setText("Processing... Please wait")
        
        # Setup table based on mode
        if self.current_mode == "morphology":
            self.results_table.setColumnCount(7)
            self.results_table.setHorizontalHeaderLabels(["#", "Word", "Prefix", "Suffix", "Root", "Confidence", "Type"])
            # Column widths will be set by setup_table_columns
        else:
            self.results_table.setColumnCount(4)
            self.results_table.setHorizontalHeaderLabels(["#", "Word", "Length", "Type"])
        
        # Adjust table columns for current window size
        self.setup_table_columns()
        
        # Show progress
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        # Disable buttons
        self.btn_process.setEnabled(False)
        self.btn_export.setEnabled(False)
        
        # Start appropriate thread
        if self.current_mode == "morphology":
            self.processing_thread = MorphologyProcessingThread(file_path, language)
            self.status_label.setText(f"Analyzing morphology in {language} (with over-stemming prevention)...")
        else:
            # Prepare parameters
            params = {}
            if self.current_mode == "dfa":
                params = {
                    'min_length': self.dfa_min_spin.value(),
                    'max_length': self.dfa_max_spin.value(),
                    'filter_stop_words': self.dfa_filter_check.isChecked(),
                    'language': language  # ADD LANGUAGE HERE
                }
                self.status_label.setText(f"Running DFA analysis in {language} (length: {params['min_length']}-{params['max_length']})...")
            elif self.current_mode == "nfa":
                pattern = self.nfa_pattern_combo.currentText()
                params = {'pattern': pattern}
                self.status_label.setText(f"Running NFA pattern: {pattern}...")
            
            self.processing_thread = FAProcessingThread(file_path, self.current_mode, params)
        
        # Connect signals
        self.processing_thread.progress_updated.connect(self.update_progress)
        self.processing_thread.result_ready.connect(self.on_analysis_complete)
        self.processing_thread.error_occurred.connect(self.on_analysis_error)
        self.processing_thread.start()
    
    def update_progress(self, value):
        self.progress_bar.setValue(value)
    
    def on_analysis_complete(self, results, stats):
        """Handle analysis completion"""
        self.current_results = results
        self.current_stats = stats
        
        # Update table
        self.results_table.setRowCount(len(results))
        
        if self.current_mode == "morphology":
            # Add morphology data
            for i, row in enumerate(results):
                for j, value in enumerate(row):
                    item = QTableWidgetItem(str(value))
                    
                    # Formatting
                    if j == 0:  # Number
                        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                        item.setForeground(QColor("#94a3b8"))
                    elif j == 1:  # Word
                        item.setForeground(QColor("#38bdf8"))
                        font = item.font()
                        font.setBold(True)
                        font.setPointSize(11)
                        item.setFont(font)
                    elif j in [2, 3]:  # Prefix/Suffix
                        if str(value).lower() != "none" and str(value).lower() != "root word":
                            item.setForeground(QColor("#10b981"))
                    elif j == 4:  # Root
                        item.setForeground(QColor("#f59e0b"))
                    elif j == 5:  # Confidence
                        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                        try:
                            conf_value = float(value.strip('%')) / 100
                            if conf_value >= 0.8:
                                item.setForeground(QColor("#10b981"))  # Green
                            elif conf_value >= 0.5:
                                item.setForeground(QColor("#f59e0b"))  # Yellow
                            else:
                                item.setForeground(QColor("#ef4444"))  # Red
                        except:
                            item.setForeground(QColor("#94a3b8"))
                    elif j == 6:  # Type
                        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                        if "Overstemming" in str(value):
                            item.setForeground(QColor("#ef4444"))
                        elif "Common" in str(value):
                            item.setForeground(QColor("#10b981"))
                        else:
                            item.setForeground(QColor("#8b5cf6"))
                    
                    self.results_table.setItem(i, j, item)
        else:
            # Add DFA/NFA data
            for i, (num, word) in enumerate(results):
                # Number
                num_item = QTableWidgetItem(str(num))
                num_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                num_item.setForeground(QColor("#94a3b8"))
                self.results_table.setItem(i, 0, num_item)
                
                # Word
                word_item = QTableWidgetItem(word)
                word_item.setForeground(QColor("#38bdf8"))
                font = word_item.font()
                font.setBold(True)
                font.setPointSize(11)
                word_item.setFont(font)
                self.results_table.setItem(i, 1, word_item)
                
                # Length
                length_item = QTableWidgetItem(str(len(word)))
                length_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                
                # Color code length
                length = len(word)
                if length <= 4:
                    length_item.setForeground(QColor("#10b981"))
                elif length <= 8:
                    length_item.setForeground(QColor("#f59e0b"))
                else:
                    length_item.setForeground(QColor("#ef4444"))
                
                self.results_table.setItem(i, 2, length_item)
                
                # Type (DFA or NFA)
                type_item = QTableWidgetItem(self.current_mode.upper())
                type_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if self.current_mode == "dfa":
                    type_item.setForeground(QColor("#8b5cf6"))
                else:
                    type_item.setForeground(QColor("#ec4899"))
                self.results_table.setItem(i, 3, type_item)
        
        # Update statistics
        if self.current_mode == "morphology":
            stats_text = f"""
Morphology Analysis ({stats.get('language', 'Unknown')}):
• Total words in text: {stats.get('total_words', 0):,}
• Language-specific words: {stats.get('filtered_words', 0):,}
• Unique vocabulary: {stats.get('unique_words', 0):,}
• Analysis: {stats.get('analysis_type', 'Standard')}
            """.strip()
        else:
            fa_type = stats.get('fa_type', 'FA')
            pattern = stats.get('pattern', '')
            pattern_text = f"\n• Pattern: {pattern}" if pattern else ""
            
            if stats.get('total_words', 0) > 0:
                stats_text = f"""
{fa_type} Analysis:
• Words found: {stats.get('total_words', 0):,}
• Min length: {stats.get('min_length', 0)} chars
• Max length: {stats.get('max_length', 0)} chars
• Average length: {stats.get('avg_length', 0)} chars{pattern_text}
                """.strip()
            else:
                stats_text = f"{fa_type} Analysis: No words found matching criteria"
        
        self.stats_label.setText(stats_text)
        
        # Reset UI
        self.progress_bar.setVisible(False)
        self.btn_process.setEnabled(True)
        self.btn_export.setEnabled(True)
        
        if len(results) == 0:
            self.status_label.setText(f"Analysis complete: No words found matching criteria")
        else:
            self.status_label.setText(f"Analysis complete: {len(results)} words found")
    
    def on_analysis_error(self, error_message):
        self.progress_bar.setVisible(False)
        self.btn_process.setEnabled(True)
        
        QMessageBox.critical(self, "Error", error_message)
        self.status_label.setText("Analysis failed")
    
    def export_results(self):
        """Export results based on current mode"""
        if not self.current_results:
            QMessageBox.warning(self, "Warning", "No results to export")
            return
        
        base_name = f"untl_analysis_{self.current_mode}"
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Results", f"{base_name}.csv", "CSV Files (*.csv)"
        )
        
        if not file_path:
            return
        
        try:
            if self.current_mode == "morphology":
                # Morphology data export
                data = []
                for row in self.current_results:
                    data.append({
                        "Number": row[0],
                        "Word": row[1],
                        "Prefix": row[2],
                        "Suffix": row[3],
                        "Root": row[4],
                        "Confidence": row[5],
                        "Analysis Type": row[6]
                    })
                columns = ["Number", "Word", "Prefix", "Suffix", "Root", "Confidence", "Analysis Type"]
            else:
                # DFA/NFA data export
                data = []
                for num, word in self.current_results:
                    data.append({
                        "Number": num,
                        "Word": word,
                        "Length": len(word),
                        "Type": self.current_mode.upper(),
                        "Accepted": "YES"
                    })
                columns = ["Number", "Word", "Length", "Type", "Accepted"]
            
            df = pd.DataFrame(data, columns=columns)
            df.to_csv(file_path, index=False, encoding='utf-8-sig')
            
            QMessageBox.information(self, "Success", 
                                  f"Results exported to:\n{os.path.basename(file_path)}")
            self.status_label.setText(f"Exported successfully to {os.path.basename(file_path)}")
            
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to export: {str(e)}")
            self.status_label.setText("Export failed")
    
    def resizeEvent(self, event):
        """Handle window resize events"""
        super().resizeEvent(event)
        # Adjust UI elements when window is resized
        self.setup_table_columns()