# gui/styles.py
# 定义GUI的样式表和视觉主题

def get_stylesheet():
    """
    返回应用程序的全局样式表。
    """
    return '''
    /* Global styles */
    QWidget {
        background-color: #2b2b2b;
        color: #f0f0f0;
        font-family: "Microsoft YaHei", "Segoe UI", "Arial", sans-serif;
        font-size: 10pt;
    }

    /* Main window */
    QMainWindow {
        background-color: #3c3c3c;
    }

    /* Labels */
    QLabel {
        color: #f0f0f0;
    }

    /* Buttons */
    QPushButton {
        background-color: #555555;
        color: #f0f0f0;
        border: 1px solid #666666;
        padding: 5px 10px;
        border-radius: 4px;
    }

    QPushButton:hover {
        background-color: #666666;
        border: 1px solid #777777;
    }

    QPushButton:pressed {
        background-color: #444444;
        border: 1px solid #555555;
    }
    
    QPushButton:disabled {
        background-color: #404040;
        color: #808080;
        border: 1px solid #505050;
    }

    /* Line edits */
    QLineEdit {
        background-color: #3c3c3c;
        color: #f0f0f0;
        border: 1px solid #555555;
        border-radius: 4px;
        padding: 4px;
    }

    QLineEdit:focus {
        border: 1px solid #0078d7;
    }
    
    QLineEdit:read-only {
        background-color: #333333;
    }

    /* Text edits */
    QTextEdit {
        background-color: #3c3c3c;
        color: #f0f0f0;
        border: 1px solid #555555;
        border-radius: 4px;
        padding: 4px;
    }
    
    QTextEdit:focus {
        border: 1px solid #0078d7;
    }

    /* Combo box */
    QComboBox {
        background-color: #555555;
        border: 1px solid #666666;
        border-radius: 4px;
        padding: 1px 18px 1px 3px;
        min-width: 6em;
    }

    QComboBox:editable {
        background: #3c3c3c;
    }

    QComboBox:!editable, QComboBox::drop-down:editable {
         background: #555555;
    }

    QComboBox:!editable:on, QComboBox::drop-down:editable:on {
        background: #666666;
    }

    QComboBox::drop-down {
        subcontrol-origin: padding;
        subcontrol-position: top right;
        width: 15px;
        border-left-width: 1px;
        border-left-color: #666666;
        border-left-style: solid;
        border-top-right-radius: 3px;
        border-bottom-right-radius: 3px;
    }

    QComboBox::down-arrow {
        image: url(./gui/resources/down_arrow.png); /* Needs an icon */
    }
    
    QComboBox QAbstractItemView {
        border: 1px solid #666666;
        background-color: #3c3c3c;
        selection-background-color: #0078d7;
    }

    /* Scroll bars */
    QScrollBar:vertical {
        border: 1px solid #444444;
        background: #3c3c3c;
        width: 12px;
        margin: 16px 0 16px 0;
    }

    QScrollBar::handle:vertical {
        background: #555555;
        min-height: 20px;
        border-radius: 6px;
    }
    
    QScrollBar::handle:vertical:hover {
        background: #666666;
    }

    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
        height: 0px;
    }

    QScrollBar:horizontal {
        border: 1px solid #444444;
        background: #3c3c3c;
        height: 12px;
        margin: 0 16px 0 16px;
    }

    QScrollBar::handle:horizontal {
        background: #555555;
        min-width: 20px;
        border-radius: 6px;
    }
    
    QScrollBar::handle:horizontal:hover {
        background: #666666;
    }

    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
        width: 0px;
    }

    /* Checkbox */
    QCheckBox {
        spacing: 5px;
    }

    QCheckBox::indicator {
        width: 13px;
        height: 13px;
        border: 1px solid #555555;
        border-radius: 3px;
    }

    QCheckBox::indicator:unchecked {
        background-color: #3c3c3c;
    }
    
    QCheckBox::indicator:unchecked:hover {
        border: 1px solid #0078d7;
    }

    QCheckBox::indicator:checked {
        background-color: #0078d7;
        border: 1px solid #0078d7;
        image: url(./gui/resources/check.png); /* Needs an icon */
    }

    /* Radio button */
    QRadioButton {
        spacing: 5px;
    }

    QRadioButton::indicator {
        width: 13px;
        height: 13px;
        border: 1px solid #555555;
        border-radius: 7px;
    }

    QRadioButton::indicator:unchecked {
        background-color: #3c3c3c;
    }
    
    QRadioButton::indicator:unchecked:hover {
        border: 1px solid #0078d7;
    }

    QRadioButton::indicator:checked {
        background-color: #0078d7;
        border: 1px solid #0078d7;
    }
    
    /* Tab widget */
    QTabWidget::pane {
        border-top: 2px solid #3c3c3c;
    }

    QTabBar::tab {
        background: #444444;
        border: 1px solid #555555;
        border-bottom-color: #3c3c3c; /* same as pane color */
        border-top-left-radius: 4px;
        border-top-right-radius: 4px;
        min-width: 8ex;
        padding: 5px;
    }

    QTabBar::tab:selected, QTabBar::tab:hover {
        background: #555555;
    }

    QTabBar::tab:selected {
        border-color: #666666;
        border-bottom-color: #555555; /* same as tab color */
    }

    QTabBar::tab:!selected {
        margin-top: 2px; /* make non-selected tabs look smaller */
    }
    
    /* Group box */
    QGroupBox {
        background-color: #3c3c3c;
        border: 1px solid #555555;
        border-radius: 5px;
        margin-top: 1ex; /* leave space at the top for the title */
    }

    QGroupBox::title {
        subcontrol-origin: margin;
        subcontrol-position: top center; /* position at the top center */
        padding: 0 3px;
        background-color: #3c3c3c;
    }
    
    /* Progress bar */
    QProgressBar {
        border: 1px solid #555555;
        border-radius: 5px;
        text-align: center;
        background-color: #3c3c3c;
    }

    QProgressBar::chunk {
        background-color: #0078d7;
        width: 20px;
    }
    
    /* Tooltip */
    QToolTip {
        color: #f0f0f0;
        background-color: #2b2b2b;
        border: 1px solid #3c3c3c;
        border-radius: 4px;
    }
    
    /* Menu */
    QMenuBar {
        background-color: #3c3c3c;
    }

    QMenuBar::item {
        background: transparent;
        padding: 4px 8px;
    }

    QMenuBar::item:selected {
        background: #555555;
    }

    QMenu {
        background-color: #3c3c3c;
        border: 1px solid #555555;
    }

    QMenu::item {
        padding: 4px 20px 4px 20px;
    }

    QMenu::item:selected {
        background-color: #0078d7;
    }
    
    /* Status bar */
    QStatusBar {
        background-color: #3c3c3c;
    }
    
    QStatusBar::item {
        border: none;
    }
    '''
