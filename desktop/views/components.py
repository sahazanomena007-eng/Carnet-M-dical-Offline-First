import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame, QFormLayout
)
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve, QPoint, QTimer
from PyQt5.QtGui import QColor, QFont
from PyQt5.QtWidgets import QGraphicsDropShadowEffect

# === THEME ===
C_BG = "#F3F7FB"
C_WHITE = "#ffffff"
C_PRIMARY = "#0F6CBD"
C_PRIMARY_DARK = "#0B5DA8"
C_PRIMARY_LIGHT = "#EBF4FF"
C_SUCCESS = "#10B981"
C_SUCCESS_LIGHT = "#D1FAE5"
C_DANGER = "#EF4444"
C_DANGER_LIGHT = "#FEE2E2"
C_WARNING = "#F59E0B"
C_WARNING_LIGHT = "#FEF3C7"
C_TEXT = "#1F2937"
C_TEXT_SEC = "#6B7280"
C_TEXT_LIGHT = "#9CA3AF"
C_BORDER = "#E5E7EB"

STYLE_BASE = f"""
QMainWindow {{ background-color: {C_BG}; }}
QWidget {{ font-family: 'Segoe UI', -apple-system, Arial, sans-serif; font-size: 13px; color: {C_TEXT}; }}
QPushButton {{
    background-color: {C_PRIMARY}; color: white; border: none;
    padding: 10px 24px; border-radius: 12px; font-weight: 600; font-size: 13px;
    min-height: 20px;
}}
QPushButton:hover {{ background-color: {C_PRIMARY_DARK}; }}
QPushButton:pressed {{ background-color: {C_PRIMARY_DARK}; }}
QPushButton:disabled {{ background-color: {C_BORDER}; color: {C_TEXT_LIGHT}; }}
QPushButton#btnDanger {{ background-color: {C_DANGER}; }}
QPushButton#btnDanger:hover {{ background-color: #DC2626; }}
QPushButton#btnOutline {{
    background-color: {C_WHITE}; color: {C_PRIMARY};
    border: 2px solid {C_BORDER};
}}
QPushButton#btnOutline:hover {{
    background-color: {C_PRIMARY_LIGHT}; border-color: {C_PRIMARY};
}}
QPushButton#btnSuccess {{ background-color: {C_SUCCESS}; }}
QPushButton#btnSuccess:hover {{ background-color: #059669; }}
QPushButton#btnWarning {{ background-color: {C_WARNING}; color: white; }}
QPushButton#btnWarning:hover {{ background-color: #D97706; }}
QLineEdit, QTextEdit, QComboBox, QSpinBox, QDoubleSpinBox, QDateEdit, QTimeEdit {{
    padding: 10px 14px; border: 2px solid {C_BORDER}; border-radius: 12px;
    background: {C_WHITE}; font-size: 13px; min-height: 18px;
}}
QLineEdit:focus, QTextEdit:focus, QComboBox:focus,
QSpinBox:focus, QDoubleSpinBox:focus, QDateEdit:focus, QTimeEdit:focus {{
    border-color: {C_PRIMARY};
}}
QTableWidget {{
    border: 1px solid {C_BORDER}; border-radius: 16px; background: {C_WHITE};
    gridline-color: #F3F4F6; selection-background-color: {C_PRIMARY_LIGHT};
}}
QTableWidget::item {{ padding: 10px 8px; min-height: 28px; }}
QTableWidget::item:hover {{ background: #F9FAFB; }}
QHeaderView::section {{
    background: {C_PRIMARY}; color: white; padding: 12px 8px;
    border: none; font-weight: 700; font-size: 12px;
}}
QTabWidget::pane {{ border: 1px solid {C_BORDER}; border-radius: 16px; background: {C_WHITE}; }}
QTabBar::tab {{ padding: 12px 24px; margin-right: 2px; font-size: 13px; font-weight: 500; }}
QTabBar::tab:selected {{ background: {C_PRIMARY}; color: white; border-radius: 6px 6px 0 0; font-weight: 700; }}
QTabBar::tab:hover:!selected {{ background: {C_PRIMARY_LIGHT}; }}
QGroupBox {{ font-weight: 600; border: 1px solid {C_BORDER}; border-radius: 16px; margin-top: 8px; padding-top: 18px; }}
QGroupBox::title {{ subcontrol-origin: margin; left: 14px; padding: 0 8px; }}
QComboBox {{ min-width: 130px; }}
QProgressBar {{ border: none; border-radius: 6px; background: {C_BORDER}; height: 10px; text-align: center; }}
QProgressBar::chunk {{ background: {C_PRIMARY}; border-radius: 6px; }}
QScrollBar:vertical {{ width: 8px; background: transparent; border-radius: 4px; }}
QScrollBar::handle:vertical {{ background: #D1D5DB; border-radius: 4px; min-height: 30px; }}
QScrollBar::handle:vertical:hover {{ background: {C_TEXT_LIGHT}; }}
QScrollBar:horizontal {{ height: 8px; background: transparent; border-radius: 4px; }}
QScrollBar::handle:horizontal {{ background: #D1D5DB; border-radius: 4px; min-width: 30px; }}
QScrollBar::handle:horizontal:hover {{ background: {C_TEXT_LIGHT}; }}
QDialog {{ background: {C_WHITE}; }}
"""

CARD_STYLE = f"background: {C_WHITE}; border: 1px solid {C_BORDER}; border-radius: 18px; padding: 22px;"
STAT_CARD = f"background: {C_WHITE}; border-radius: 16px; padding: 16px; border-left: 5px solid {C_PRIMARY};"

def add_shadow(widget, blur=20, offset=2, color=QColor(0, 0, 0, 40)):
    shadow = QGraphicsDropShadowEffect()
    shadow.setBlurRadius(blur)
    shadow.setOffset(offset, offset)
    shadow.setColor(color)
    widget.setGraphicsEffect(shadow)

def make_btn(text, style="primary", icon=""):
    btn = QPushButton(f"{icon} {text}" if icon else text)
    btn.setCursor(Qt.PointingHandCursor)
    styles = {
        "primary": f"""
            QPushButton {{ background: {C_PRIMARY}; color: white; border: none;
                padding: 10px 24px; border-radius: 12px; font-weight: 600; font-size: 13px; }}
            QPushButton:hover {{ background: {C_PRIMARY_DARK}; }}
            QPushButton:pressed {{ background: #094D8A; }}
        """,
        "danger": f"""
            QPushButton {{ background: {C_DANGER}; color: white; border: none;
                padding: 10px 24px; border-radius: 12px; font-weight: 600; font-size: 13px; }}
            QPushButton:hover {{ background: #DC2626; }}
        """,
        "success": f"""
            QPushButton {{ background: {C_SUCCESS}; color: white; border: none;
                padding: 10px 24px; border-radius: 12px; font-weight: 600; font-size: 13px; }}
            QPushButton:hover {{ background: #059669; }}
        """,
        "outline": f"""
            QPushButton {{ background: {C_WHITE}; color: {C_PRIMARY};
                border: 2px solid {C_BORDER}; padding: 10px 24px;
                border-radius: 12px; font-weight: 600; font-size: 13px; }}
            QPushButton:hover {{ background: {C_PRIMARY_LIGHT}; border-color: {C_PRIMARY}; }}
        """,
    }
    btn.setStyleSheet(styles.get(style, styles["primary"]))
    return btn

def section_title(text):
    lbl = QLabel(text)
    lbl.setStyleSheet(f"font-size: 14px; font-weight: 700; color: {C_TEXT}; padding: 4px 0;")
    return lbl

def page_title(text):
    lbl = QLabel(text)
    lbl.setStyleSheet(f"font-size: 24px; font-weight: 800; color: {C_TEXT}; margin-bottom: 8px;")
    return lbl


class StatusBadge(QLabel):
    def __init__(self, text, status_type="info", parent=None):
        super().__init__(text, parent)
        colors = {
            "success": (C_SUCCESS_LIGHT, "#065F46", C_SUCCESS),
            "warning": (C_WARNING_LIGHT, "#92400E", C_WARNING),
            "danger": (C_DANGER_LIGHT, "#991B1B", C_DANGER),
            "info": (C_PRIMARY_LIGHT, C_PRIMARY_DARK, C_PRIMARY),
            "neutral": ("#F3F4F6", "#4B5563", "#9CA3AF"),
        }
        bg, fg, border = colors.get(status_type, colors["neutral"])
        self.setStyleSheet(f"""
            background: {bg}; color: {fg}; border: 1px solid {border};
            border-radius: 12px; padding: 4px 12px; font-size: 11px;
            font-weight: 700;
        """)


class ToastNotification(QFrame):
    def __init__(self, parent, message, type="success", duration=3500):
        super().__init__(parent)
        self.setFixedHeight(56)
        self.setMinimumWidth(320)
        colors = {
            "success": (C_SUCCESS, C_SUCCESS_LIGHT, "\u2713"),
            "error": (C_DANGER, C_DANGER_LIGHT, "\u2717"),
            "info": (C_PRIMARY, C_PRIMARY_LIGHT, "\u2139"),
            "warning": (C_WARNING, C_WARNING_LIGHT, "\u26A0"),
        }
        border_c, bg_c, icon = colors.get(type, (C_PRIMARY, C_PRIMARY_LIGHT, "\u2139"))
        self.setStyleSheet(f"""
            background: {bg_c}; border-left: 5px solid {border_c};
            border-radius: 16px; padding: 12px 18px;
        """)
        add_shadow(self, blur=24, offset=3, color=QColor(0, 0, 0, 60))
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 0, 16, 0)
        lbl_icon = QLabel(icon)
        lbl_icon.setStyleSheet(f"font-size: 24px; font-weight: 800; color: {border_c};")
        layout.addWidget(lbl_icon)
        lbl_msg = QLabel(message)
        lbl_msg.setStyleSheet(f"font-size: 13px; font-weight: 600; color: {C_TEXT};")
        lbl_msg.setWordWrap(True)
        layout.addWidget(lbl_msg, 1)
        btn_close = QPushButton("\u2716")
        btn_close.setFixedSize(24, 24)
        btn_close.setStyleSheet(f"background: transparent; color: {C_TEXT_SEC}; border: none; font-size: 14px; padding: 0;")
        btn_close.clicked.connect(self.deleteLater)
        layout.addWidget(btn_close)
        self._start_animation()
        QTimer.singleShot(duration, self._fade_out)

    def _start_animation(self):
        self.anim = QPropertyAnimation(self, b"pos")
        self.anim.setDuration(300)
        self.anim.setEasingCurve(QEasingCurve.OutCubic)

    def _fade_out(self):
        self.anim = QPropertyAnimation(self, b"pos")
        self.anim.setDuration(250)
        self.anim.setEasingCurve(QEasingCurve.InCubic)
        parent = self.parent()
        if parent:
            start = self.pos()
            end = QPoint(parent.width(), self.pos().y())
            self.anim.setStartValue(start)
            self.anim.setEndValue(end)
            self.anim.finished.connect(self.deleteLater)
            self.anim.start()


class CardWidget(QFrame):
    def __init__(self, title="", parent=None):
        super().__init__(parent)
        self.setStyleSheet(CARD_STYLE)
        add_shadow(self, blur=16, offset=2, color=QColor(0, 0, 0, 25))
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(20, 16, 20, 16)
        if title:
            title_lbl = QLabel(title)
            title_lbl.setStyleSheet(f"font-size: 16px; font-weight: 700; color: {C_TEXT}; padding-bottom: 8px;")
            self.layout.addWidget(title_lbl)


class StatCard(QFrame):
    def __init__(self, label, value, color=C_PRIMARY, icon="", parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"{STAT_CARD}; border-left-color: {color};")
        add_shadow(self, blur=12, offset=1, color=QColor(0, 0, 0, 20))
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        if icon:
            hdr = QWidget()
            hl = QHBoxLayout(hdr)
            hl.setContentsMargins(0, 0, 0, 0)
            ic = QLabel(icon)
            ic.setStyleSheet(f"font-size: 22px;")
            hl.addWidget(ic)
            hl.addStretch()
            layout.addWidget(hdr)
        lbl_val = QLabel(str(value))
        lbl_val.setStyleSheet(f"font-size: 32px; font-weight: 800; color: {color}; letter-spacing: -0.5px;")
        lbl_label = QLabel(label)
        lbl_label.setStyleSheet(f"font-size: 13px; color: {C_TEXT_SEC}; font-weight: 500;")
        layout.addWidget(lbl_val)
        layout.addWidget(lbl_label)


EMPTY_MESSAGES = {
    "carnet": ("\U0001F4D6", "Aucune consultation", "Vos consultations apparaitront ici"),
    "medecins": ("\U0001FA7A", "Aucun medecin lie", "Utilisez le code d'association"),
    "rdv": ("\U0001F4C5", "Aucun rendez-vous", "Prenez rendez-vous avec votre medecin"),
    "prescriptions": ("\U0001F48A", "Aucune prescription", "Vos prescriptions apparaitront ici"),
    "allergies": ("\u26A0\uFE0F", "Aucune allergie", "Ajoutez vos allergies"),
    "examens": ("\U0001F52C", "Aucun examen", "Vos resultats d'examens apparaitront ici"),
    "patients": ("\U0001F465", "Aucun patient lie", "Utilisez l'ID ou le N dossier"),
    "consultations": ("\U0001F4CB", "Aucune consultation", "Les consultations apparaitront ici"),
    "default": ("\U0001F4AD", "Aucune donnee", ""),
}


class TableWithEmpty(QWidget):
    def __init__(self, headers, context="default", parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        self.table = QTableWidget()
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table, 1)
        icon, title, desc = EMPTY_MESSAGES.get(context, EMPTY_MESSAGES["default"])
        empty_w = QWidget()
        empty_w.setStyleSheet(f"background: {C_WHITE}; border: 2px dashed {C_BORDER}; border-radius: 14px;")
        empty_l = QVBoxLayout(empty_w)
        empty_l.setAlignment(Qt.AlignCenter)
        empty_l.setSpacing(8)
        ic = QLabel(icon)
        ic.setStyleSheet(f"font-size: 48px;")
        ic.setAlignment(Qt.AlignCenter)
        empty_l.addWidget(ic)
        self.empty_title = QLabel(title)
        self.empty_title.setStyleSheet(f"font-size: 16px; font-weight: 700; color: {C_TEXT_SEC};")
        self.empty_title.setAlignment(Qt.AlignCenter)
        empty_l.addWidget(self.empty_title)
        self.empty_desc = QLabel(desc)
        self.empty_desc.setStyleSheet(f"font-size: 13px; color: {C_TEXT_LIGHT};")
        self.empty_desc.setAlignment(Qt.AlignCenter)
        empty_l.addWidget(self.empty_desc)
        empty_l.addSpacing(12)
        layout.addWidget(empty_w)
        self.empty_widget = empty_w

    def set_data(self, data):
        self.table.setRowCount(0)
        if not data:
            self.table.hide()
            self.empty_widget.show()
            return
        self.empty_widget.hide()
        self.table.show()
        self.table.setRowCount(len(data))
        for r, row in enumerate(data):
            for c, val in enumerate(row):
                item = QTableWidgetItem(str(val) if val else "")
                item.setFont(QFont("Segoe UI", 12))
                self.table.setItem(r, c, item)

    def update_empty(self, title, desc=""):
        self.empty_title.setText(title)
        self.empty_desc.setText(desc)


class Sidebar(QFrame):
    def __init__(self, items, profile_widget, parent=None):
        super().__init__(parent)
        self.setFixedWidth(240)
        self.setStyleSheet(f"background: {C_PRIMARY};")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(profile_widget)
        self.nav_buttons = {}
        for key, label in items:
            btn = QPushButton(label)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setMinimumHeight(46)
            btn.setStyleSheet("""
                QPushButton { background: transparent; color: #DBEAFE; border: none; border-radius: 12px;
                    padding: 12px 18px; text-align: left; font-size: 14px; font-weight: 500; margin: 4px 8px; }
                QPushButton:hover { background: rgba(255,255,255,0.14); color: white; }
                QPushButton:checked { background: rgba(255,255,255,0.22); color: white;
                    font-weight: 700; border-left: 4px solid white; }
            """)
            btn.setCheckable(True)
            layout.addWidget(btn)
            self.nav_buttons[key] = btn
        layout.addStretch()
        self.logout_btn = QPushButton("  Deconnexion")
        self.logout_btn.setCursor(Qt.PointingHandCursor)
        self.logout_btn.setStyleSheet(f"""
            QPushButton {{ background: transparent; color: #FECACA; border: none;
                border-top: 1px solid rgba(255,255,255,0.15);
                padding: 16px 20px; text-align: left; font-size: 13px; font-weight: 500; }}
            QPushButton:hover {{ background: {C_DANGER}; color: white; }}
        """)
        layout.addWidget(self.logout_btn)

    def set_active(self, key):
        for k, btn in self.nav_buttons.items():
            btn.setChecked(k == key)
