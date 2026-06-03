import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame, QFormLayout,
    QScrollArea, QSizePolicy
)
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve, QPoint, QTimer
from PyQt5.QtGui import QColor, QFont, QIcon, QPixmap

# === PROFESSIONAL MEDICAL THEME ===
C_BG = "#F0F4F8"
C_WHITE = "#FFFFFF"
C_PRIMARY = "#0B6BCB"
C_PRIMARY_DARK = "#084A8A"
C_PRIMARY_LIGHT = "#E8F1FB"
C_SECONDARY = "#6366F1"
C_SUCCESS = "#059669"
C_SUCCESS_LIGHT = "#D1FAE5"
C_DANGER = "#DC2626"
C_DANGER_LIGHT = "#FEE2E2"
C_WARNING = "#D97706"
C_WARNING_LIGHT = "#FEF3C7"
C_INFO = "#0284C7"
C_INFO_LIGHT = "#E0F2FE"
C_PURPLE = "#7C3AED"
C_PURPLE_LIGHT = "#EDE9FE"
C_TEXT = "#0F172A"
C_TEXT_SEC = "#475569"
C_TEXT_LIGHT = "#94A3B8"
C_BORDER = "#E2E8F0"
C_SIDEBAR_BG = "#0F172A"
C_SIDEBAR_HOVER = "#1E293B"
C_SIDEBAR_ACTIVE = "#1D4ED8"
C_CARD_SHADOW = "rgba(15, 23, 42, 0.06)"

STYLE_BASE = f"""
QMainWindow {{ background-color: {C_BG}; }}
QWidget {{ font-family: 'Segoe UI', -apple-system, Arial, sans-serif; font-size: 13px; color: {C_TEXT}; }}
QLineEdit, QTextEdit, QComboBox, QSpinBox, QDoubleSpinBox, QDateEdit, QTimeEdit {{
    padding: 10px 14px; border: 1.5px solid {C_BORDER}; border-radius: 10px;
    background: {C_WHITE}; font-size: 13px; min-height: 18px;
    color: {C_TEXT};
}}
QLineEdit:focus, QTextEdit:focus, QComboBox:focus,
QSpinBox:focus, QDoubleSpinBox:focus, QDateEdit:focus, QTimeEdit:focus {{
    border-color: {C_PRIMARY}; background: {C_WHITE};
}}
QLineEdit:disabled {{ background: #F8FAFC; color: {C_TEXT_LIGHT}; }}
QComboBox {{ min-width: 130px; }}
QComboBox::drop-down {{ border: none; width: 30px; }}
QComboBox::down-arrow {{ image: none; border-left: 5px solid transparent; border-right: 5px solid transparent; border-top: 6px solid {C_TEXT_SEC}; margin-right: 8px; }}
QTableWidget {{
    border: 1px solid {C_BORDER}; border-radius: 12px; background: {C_WHITE};
    gridline-color: #F1F5F9; selection-background-color: {C_PRIMARY_LIGHT};
}}
QTableWidget::item {{ padding: 10px 12px; min-height: 32px; border-bottom: 1px solid #F8FAFC; }}
QTableWidget::item:hover {{ background: #F8FAFC; }}
QTableWidget::item:selected {{ background: {C_PRIMARY_LIGHT}; color: {C_TEXT}; }}
QHeaderView::section {{
    background: {C_PRIMARY}; color: white; padding: 12px 12px;
    border: none; font-weight: 700; font-size: 12px; text-transform: uppercase;
    letter-spacing: 0.5px;
}}
QTabWidget::pane {{ border: 1px solid {C_BORDER}; border-radius: 12px; background: {C_WHITE}; }}
QTabBar::tab {{ padding: 12px 24px; margin-right: 2px; font-size: 13px; font-weight: 500; color: {C_TEXT_SEC}; }}
QTabBar::tab:selected {{ background: {C_PRIMARY}; color: white; border-radius: 8px 8px 0 0; font-weight: 700; }}
QTabBar::tab:hover:!selected {{ background: {C_PRIMARY_LIGHT}; color: {C_PRIMARY}; }}
QGroupBox {{ font-weight: 600; border: 1px solid {C_BORDER}; border-radius: 12px; margin-top: 8px; padding-top: 18px; }}
QGroupBox::title {{ subcontrol-origin: margin; left: 14px; padding: 0 8px; }}
QProgressBar {{ border: none; border-radius: 6px; background: {C_BORDER}; height: 8px; text-align: center; }}
QProgressBar::chunk {{ background: {C_PRIMARY}; border-radius: 6px; }}
QScrollBar:vertical {{ width: 6px; background: transparent; border-radius: 3px; }}
QScrollBar::handle:vertical {{ background: #CBD5E1; border-radius: 3px; min-height: 30px; }}
QScrollBar::handle:vertical:hover {{ background: {C_TEXT_LIGHT}; }}
QScrollBar:horizontal {{ height: 6px; background: transparent; border-radius: 3px; }}
QScrollBar::handle:horizontal {{ background: #CBD5E1; border-radius: 3px; min-width: 30px; }}
QScrollBar::handle:horizontal:hover {{ background: {C_TEXT_LIGHT}; }}
QDialog {{ background: {C_WHITE}; }}
QTextEdit {{ padding: 10px 14px; }}
QDateEdit::drop-down, QTimeEdit::drop-down {{ border: none; width: 28px; }}
"""

CARD_STYLE = f"background: {C_WHITE}; border: 1px solid {C_BORDER}; border-radius: 16px;"
STAT_CARD = f"background: {C_WHITE}; border-radius: 14px; padding: 18px;"
PAGE_MARGINS = "28px 32px"


def add_shadow(widget, blur=20, offset=2, color=QColor(15, 23, 42, 30)):
    shadow = QGraphicsDropShadowEffect()
    shadow.setBlurRadius(blur)
    shadow.setOffset(offset, offset)
    shadow.setColor(color)
    widget.setGraphicsEffect(shadow)


def make_btn(text, style="primary", size="md"):
    btn = QPushButton(text)
    btn.setCursor(Qt.PointingHandCursor)
    pads = {"sm": "7px 16px", "md": "11px 24px", "lg": "14px 32px"}
    fs = {"sm": "12px", "md": "13px", "lg": "15px"}
    p = pads.get(size, pads["md"])
    f = fs.get(size, fs["md"])

    base = f"""
        QPushButton {{ padding: {p}; border-radius: 10px; font-weight: 600; font-size: {f}; }}
        QPushButton:disabled {{ background: #E2E8F0 !important; color: #94A3B8 !important; border-color: #E2E8F0 !important; }}
    """
    styles = {
        "primary": f"""
            QPushButton {{ background: {C_PRIMARY}; color: white; border: none; }}
            QPushButton:hover {{ background: {C_PRIMARY_DARK}; }}
            QPushButton:pressed {{ background: #062E5F; }}
        """ + base,
        "danger": f"""
            QPushButton {{ background: {C_DANGER}; color: white; border: none; }}
            QPushButton:hover {{ background: #B91C1C; }}
            QPushButton:pressed {{ background: #991B1B; }}
        """ + base,
        "success": f"""
            QPushButton {{ background: {C_SUCCESS}; color: white; border: none; }}
            QPushButton:hover {{ background: #047857; }}
            QPushButton:pressed {{ background: #065F46; }}
        """ + base,
        "outline": f"""
            QPushButton {{ background: {C_WHITE}; color: {C_PRIMARY};
                border: 1.5px solid {C_BORDER}; }}
            QPushButton:hover {{ background: {C_PRIMARY_LIGHT}; border-color: {C_PRIMARY}; }}
            QPushButton:pressed {{ background: #D9EAFB; }}
        """ + base,
        "ghost": f"""
            QPushButton {{ background: transparent; color: {C_TEXT_SEC}; border: none; }}
            QPushButton:hover {{ background: {C_PRIMARY_LIGHT}; color: {C_PRIMARY}; }}
        """ + base,
        "warning": f"""
            QPushButton {{ background: {C_WARNING}; color: white; border: none; }}
            QPushButton:hover {{ background: #B45309; }}
        """ + base,
    }
    btn.setStyleSheet(styles.get(style, styles["primary"]))
    return btn


def section_title(text):
    lbl = QLabel(text)
    lbl.setStyleSheet(f"font-size: 12px; font-weight: 600; color: {C_TEXT_SEC}; text-transform: uppercase; letter-spacing: 0.5px; padding: 2px 0;")
    return lbl


def page_title(text):
    lbl = QLabel(text)
    lbl.setStyleSheet(f"font-size: 22px; font-weight: 800; color: {C_TEXT}; letter-spacing: -0.3px;")
    return lbl


class StatusBadge(QLabel):
    def __init__(self, text, status_type="info", parent=None):
        super().__init__(text, parent)
        colors = {
            "success": (C_SUCCESS_LIGHT, "#065F46", C_SUCCESS),
            "warning": (C_WARNING_LIGHT, "#92400E", C_WARNING),
            "danger": (C_DANGER_LIGHT, "#991B1B", C_DANGER),
            "info": (C_PRIMARY_LIGHT, C_PRIMARY_DARK, C_PRIMARY),
            "neutral": ("#F1F5F9", "#475569", "#CBD5E1"),
        }
        bg, fg, border = colors.get(status_type, colors["neutral"])
        self.setStyleSheet(f"""
            background: {bg}; color: {fg}; border: none;
            border-radius: 20px; padding: 4px 14px; font-size: 11px;
            font-weight: 700; letter-spacing: 0.3px;
        """)


class ToastNotification(QFrame):
    def __init__(self, parent, message, type="success", duration=3500):
        super().__init__(parent)
        self.setFixedHeight(54)
        self.setMinimumWidth(340)
        colors = {
            "success": (C_SUCCESS, C_SUCCESS_LIGHT),
            "error": (C_DANGER, C_DANGER_LIGHT),
            "info": (C_PRIMARY, C_PRIMARY_LIGHT),
            "warning": (C_WARNING, C_WARNING_LIGHT),
        }
        border_c, bg_c = colors.get(type, (C_PRIMARY, C_PRIMARY_LIGHT))
        self.setStyleSheet(f"""
            background: {bg_c}; border-left: 4px solid {border_c};
            border-radius: 12px;
        """)
        add_shadow(self, blur=24, offset=3, color=QColor(15, 23, 42, 50))
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 0, 12, 0)
        icon_lbl = QLabel()
        icons = {"success": "✓", "error": "✗", "info": "ℹ", "warning": "⚠"}
        icon_lbl.setText(icons.get(type, "ℹ"))
        icon_lbl.setStyleSheet(f"font-size: 20px; font-weight: 800; color: {border_c};")
        layout.addWidget(icon_lbl)
        lbl_msg = QLabel(message)
        lbl_msg.setStyleSheet(f"font-size: 13px; font-weight: 600; color: {C_TEXT};")
        lbl_msg.setWordWrap(True)
        layout.addWidget(lbl_msg, 1)
        btn_close = QPushButton("✕")
        btn_close.setFixedSize(22, 22)
        btn_close.setStyleSheet(f"background: transparent; color: {C_TEXT_LIGHT}; border: none; font-size: 13px; font-weight: 600; padding: 0;")
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
        add_shadow(self, blur=12, offset=2, color=QColor(15, 23, 42, 25))
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(20, 18, 20, 18)
        self.layout.setSpacing(12)
        if title:
            title_lbl = QLabel(title)
            title_lbl.setStyleSheet(f"font-size: 15px; font-weight: 700; color: {C_TEXT};")
            self.layout.addWidget(title_lbl)


class StatCard(QFrame):
    def __init__(self, label, value, color=C_PRIMARY, icon="", parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"{STAT_CARD}; border-left: 4px solid {color};")
        add_shadow(self, blur=10, offset=1, color=QColor(15, 23, 42, 18))
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(4)
        lbl_val = QLabel(str(value))
        lbl_val.setStyleSheet(f"font-size: 30px; font-weight: 800; color: {color}; letter-spacing: -1px;")
        lbl_label = QLabel(label)
        lbl_label.setStyleSheet(f"font-size: 12px; color: {C_TEXT_SEC}; font-weight: 500;")
        layout.addWidget(lbl_val)
        layout.addWidget(lbl_label)


EMPTY_MESSAGES = {
    "carnet": ("📋", "Aucune consultation", "Les consultations apparaitront ici"),
    "medecins": ("👨‍⚕️", "Aucun médecin lié", "Un médecin peut envoyer une demande depuis son compte"),
    "rdv": ("📅", "Aucun rendez-vous", "Prenez rendez-vous avec votre médecin"),
    "prescriptions": ("💊", "Aucune prescription", "Vos prescriptions apparaitront ici"),
    "allergies": ("⚠️", "Aucune allergie", "Ajoutez vos allergies"),
    "examens": ("🔬", "Aucun examen", "Vos résultats d'examens apparaitront ici"),
    "patients": ("👤", "Aucun patient lié", "Utilisez l'ID ou le n° dossier"),
    "consultations": ("🩺", "Aucune consultation", "Les consultations apparaitront ici"),
    "patients_list": ("👥", "Aucun patient", ""),
    "default": ("📄", "Aucune donnée", ""),
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
        self.table.verticalHeader().setVisible(False)
        layout.addWidget(self.table, 1)

        icon, title, desc = EMPTY_MESSAGES.get(context, EMPTY_MESSAGES["default"])
        empty_w = QWidget()
        empty_w.setStyleSheet(f"background: {C_WHITE}; border: 2px dashed {C_BORDER}; border-radius: 14px;")
        empty_l = QVBoxLayout(empty_w)
        empty_l.setAlignment(Qt.AlignCenter)
        empty_l.setSpacing(8)
        ic = QLabel(icon)
        ic.setStyleSheet("font-size: 42px;")
        ic.setAlignment(Qt.AlignCenter)
        empty_l.addWidget(ic)
        self.empty_title = QLabel(title)
        self.empty_title.setStyleSheet(f"font-size: 15px; font-weight: 700; color: {C_TEXT_SEC};")
        self.empty_title.setAlignment(Qt.AlignCenter)
        empty_l.addWidget(self.empty_title)
        self.empty_desc = QLabel(desc)
        self.empty_desc.setStyleSheet(f"font-size: 12px; color: {C_TEXT_LIGHT};")
        self.empty_desc.setAlignment(Qt.AlignCenter)
        empty_l.addWidget(self.empty_desc)
        empty_l.addSpacing(8)
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

    def clear_table(self):
        self.table.setRowCount(0)
        self.update_empty("Aucune donnée", "")


class Sidebar(QFrame):
    def __init__(self, items, profile_widget, parent=None):
        super().__init__(parent)
        self.setFixedWidth(250)
        self.setStyleSheet(f"background: {C_SIDEBAR_BG};")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        layout.addWidget(profile_widget)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setStyleSheet("background: transparent; border: none;")

        nav_widget = QWidget()
        nav_layout = QVBoxLayout(nav_widget)
        nav_layout.setContentsMargins(8, 12, 8, 12)
        nav_layout.setSpacing(2)

        self.nav_buttons = {}
        for key, label, icon in items:
            btn = QPushButton(f"  {label}")
            btn.setCursor(Qt.PointingHandCursor)
            btn.setMinimumHeight(44)
            btn.setStyleSheet(f"""
                QPushButton {{ background: transparent; color: #CBD5E1; border: none;
                    border-radius: 10px; padding: 10px 14px; text-align: left;
                    font-size: 13px; font-weight: 500; }}
                QPushButton:hover {{ background: {C_SIDEBAR_HOVER}; color: white; }}
                QPushButton:checked {{ background: {C_SIDEBAR_ACTIVE}; color: white;
                    font-weight: 700; }}
            """)
            btn.setCheckable(True)
            nav_layout.addWidget(btn)
            self.nav_buttons[key] = btn

        nav_layout.addStretch()
        scroll.setWidget(nav_widget)
        layout.addWidget(scroll, 1)

        self.logout_btn = QPushButton("  Déconnexion")
        self.logout_btn.setCursor(Qt.PointingHandCursor)
        self.logout_btn.setStyleSheet(f"""
            QPushButton {{ background: transparent; color: #FCA5A5; border: none;
                border-top: 1px solid rgba(255,255,255,0.08);
                padding: 16px 22px; text-align: left; font-size: 13px; font-weight: 500; }}
            QPushButton:hover {{ background: {C_DANGER}; color: white; }}
        """)
        layout.addWidget(self.logout_btn)

    def set_active(self, key):
        for k, btn in self.nav_buttons.items():
            btn.setChecked(k == key)


# Re-export for backward compatibility
from PyQt5.QtWidgets import QGraphicsDropShadowEffect
