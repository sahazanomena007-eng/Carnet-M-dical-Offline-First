from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QFrame, QStackedWidget, QDialog, QScrollArea, QDateEdit, QApplication, QStyle
)
from PyQt5.QtCore import Qt, QTimer, QPoint
from .components import (
    C_PRIMARY, C_PRIMARY_DARK, C_PRIMARY_LIGHT, C_WHITE, C_TEXT, C_TEXT_SEC,
    C_TEXT_LIGHT, C_BORDER, C_BG, C_SUCCESS, C_DANGER, C_DANGER_LIGHT
)


def _input_field(placeholder="", password=False):
    edit = QLineEdit()
    edit.setPlaceholderText(placeholder)
    edit.setMinimumHeight(46)
    edit.setStyleSheet(f"""
        QLineEdit {{
            background: {C_WHITE}; border: 1.5px solid {C_BORDER};
            border-radius: 10px; padding: 0 16px; font-size: 14px;
            color: {C_TEXT};
        }}
        QLineEdit:focus {{ border-color: {C_PRIMARY}; }}
        QLineEdit::placeholder {{ color: {C_TEXT_LIGHT}; }}
    """)
    if password:
        edit.setEchoMode(QLineEdit.Password)
    return edit


def _feature_icon(icon_type):
    icon_map = {
        "storage": QStyle.SP_DriveHDIcon,
        "record": QStyle.SP_FileIcon,
        "consultation": QStyle.SP_DialogOpenButton,
        "prescription": QStyle.SP_DialogApplyButton,
    }
    style = QApplication.instance().style() if QApplication.instance() else QApplication.style()
    icon = style.standardIcon(icon_map.get(icon_type, QStyle.SP_FileIcon)) if style else None
    label = QLabel()
    label.setFixedSize(32, 32)
    label.setAlignment(Qt.AlignCenter)
    label.setStyleSheet("background: rgba(255,255,255,0.18); border-radius: 16px;")
    if icon:
        label.setPixmap(icon.pixmap(20, 20))
    return label


class LoginView(QDialog):
    login_clicked = None
    inscription_clicked = None
    login_success = None

    def __init__(self, controller=None):
        super().__init__(None)
        self._controller = controller
        self.login_clicked = None
        self.inscription_clicked = None
        self.login_success = None
        self._drag_pos = QPoint()
        self.setWindowTitle("Carnet Médical - Connexion")
        self.setFixedSize(920, 620)
        self.setStyleSheet(f"background: {C_BG};")

        # Remove default title bar
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground, False)

        main = QHBoxLayout(self)
        main.setContentsMargins(0, 0, 0, 0)
        main.setSpacing(0)

        # --- Left Panel (Branding) ---
        left = QFrame()
        left.setFixedWidth(400)
        left.setStyleSheet(f"""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 {C_PRIMARY}, stop:1 #1D4ED8);
        """)
        left_l = QVBoxLayout(left)
        left_l.setContentsMargins(40, 50, 40, 50)
        left_l.setSpacing(16)

        logo = QLabel("CM")
        logo.setFixedSize(92, 92)
        logo.setAlignment(Qt.AlignCenter)
        logo.setStyleSheet(
            "color: white; background: rgba(255,255,255,0.18);"
            "font-size: 32px; font-weight: 800; border-radius: 46px;"
        )
        left_l.addWidget(logo, 0, Qt.AlignHCenter)

        brand = QLabel("Carnet Médical")
        brand.setStyleSheet(f"font-size: 30px; font-weight: 800; color: white; letter-spacing: -0.5px;")
        brand.setAlignment(Qt.AlignCenter)
        left_l.addWidget(brand)

        tagline = QLabel("Application de gestion de dossiers\nmédicaux sécurisée")
        tagline.setStyleSheet("font-size: 14px; color: rgba(255,255,255,0.8);")
        tagline.setAlignment(Qt.AlignCenter)
        tagline.setWordWrap(True)
        left_l.addWidget(tagline)

        left_l.addStretch()

        features = [
            ("storage", "Stockage local sécurisé"),
            ("record", "Carnet de santé numérique"),
            ("consultation", "Gestion des consultations"),
            ("prescription", "Prescriptions et suivi"),
        ]
        for icon_key, txt in features:
            row = QHBoxLayout()
            row.setSpacing(12)
            ic = _feature_icon(icon_key)
            row.addWidget(ic)
            lbl = QLabel(txt)
            lbl.setStyleSheet("font-size: 13px; color: rgba(255,255,255,0.85);")
            row.addWidget(lbl)
            row.addStretch()
            left_l.addLayout(row)

        left_l.addStretch()

        version = QLabel("v1.0 • Offline-First")
        version.setStyleSheet("font-size: 11px; color: rgba(255,255,255,0.5);")
        version.setAlignment(Qt.AlignCenter)
        left_l.addWidget(version)

        main.addWidget(left)

        # --- Right Panel (Forms) ---
        right = QFrame()
        right.setStyleSheet(f"background: {C_WHITE};")
        right_l = QVBoxLayout(right)
        right_l.setContentsMargins(48, 0, 48, 40)
        right_l.setSpacing(0)

        # Custom title bar with close button
        title_bar = QFrame()
        title_bar.setFixedHeight(40)
        title_bar.setStyleSheet("background: transparent;")
        title_bar.mousePressEvent = lambda e: self._drag_start(e)
        title_bar.mouseMoveEvent = lambda e: self._drag_move(e)
        tbl = QHBoxLayout(title_bar)
        tbl.setContentsMargins(0, 8, 0, 0)
        tbl.addStretch()
        btn_close = QPushButton("✕")
        btn_close.setFixedSize(28, 28)
        btn_close.setCursor(Qt.PointingHandCursor)
        btn_close.setStyleSheet(f"""
            QPushButton {{ background: transparent; color: {C_TEXT_LIGHT}; border: none;
                border-radius: 6px; font-size: 14px; font-weight: 600; }}
            QPushButton:hover {{ background: {C_DANGER_LIGHT}; color: {C_DANGER}; }}
        """)
        btn_close.clicked.connect(self.close)
        tbl.addWidget(btn_close)
        right_l.addWidget(title_bar)

        self._build_tabs(right_l)

        self.stack = QStackedWidget()
        right_l.addWidget(self.stack, 1)

        self._build_login_page()
        self._build_register_page()

        self.stack.setCurrentIndex(0)
        main.addWidget(right, 1)

        # Loader overlay
        self.loader = QLabel("Connexion en cours...")
        self.loader.setStyleSheet(f"""
            background: rgba(255,255,255,0.95); border-radius: 14px;
            padding: 30px; font-size: 15px; font-weight: 600; color: {C_PRIMARY};
        """)
        self.loader.setAlignment(Qt.AlignCenter)
        self.loader.hide()
        self.loader.setMinimumSize(280, 120)

    def _build_tabs(self, parent_layout):
        tab_bar = QFrame()
        tab_bar.setFixedHeight(44)
        tab_l = QHBoxLayout(tab_bar)
        tab_l.setContentsMargins(0, 10, 0, 16)
        tab_l.setSpacing(4)

        self.tab_login = QPushButton("Connexion")
        self.tab_register = QPushButton("Inscription")
        for btn in (self.tab_login, self.tab_register):
            btn.setCursor(Qt.PointingHandCursor)
            btn.setFixedHeight(36)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: transparent; color: {C_TEXT_LIGHT}; border: none;
                    font-size: 14px; font-weight: 500; padding: 0 14px;
                    border-radius: 8px;
                }}
                QPushButton:hover {{ background: {C_PRIMARY_LIGHT}; color: {C_PRIMARY}; }}
            """)

        self.tab_login.setStyleSheet(f"""
            QPushButton {{
                background: {C_PRIMARY_LIGHT}; color: {C_PRIMARY}; border: none;
                font-size: 14px; font-weight: 700; padding: 0 14px;
                border-radius: 8px;
            }}
        """)
        self.tab_login.clicked.connect(lambda: self._switch_tab(0))
        self.tab_register.clicked.connect(lambda: self._switch_tab(1))
        tab_l.addWidget(self.tab_login)
        tab_l.addWidget(self.tab_register)
        tab_l.addStretch()

        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background: {C_BORDER};")
        parent_layout.addWidget(tab_bar)
        parent_layout.addWidget(sep)

    def _switch_tab(self, idx):
        self.stack.setCurrentIndex(idx)
        active = [self.tab_login, self.tab_register][idx]
        inactive = [self.tab_login, self.tab_register][1 - idx]
        active.setStyleSheet(f"""
            QPushButton {{
                background: {C_PRIMARY_LIGHT}; color: {C_PRIMARY}; border: none;
                font-size: 14px; font-weight: 700; padding: 0 14px;
                border-radius: 8px;
            }}
        """)
        inactive.setStyleSheet(f"""
            QPushButton {{
                background: transparent; color: {C_TEXT_LIGHT}; border: none;
                font-size: 14px; font-weight: 500; padding: 0 14px;
                border-radius: 8px;
            }}
            QPushButton:hover {{ background: {C_PRIMARY_LIGHT}; color: {C_PRIMARY}; }}
        """)

    def _build_login_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 28, 0, 0)
        layout.setSpacing(20)

        title = QLabel("Bienvenue")
        title.setStyleSheet(f"font-size: 26px; font-weight: 800; color: {C_TEXT};")
        layout.addWidget(title)
        subtitle = QLabel("Connectez-vous pour accéder à votre dossier médical")
        subtitle.setStyleSheet(f"font-size: 13px; color: {C_TEXT_SEC};")
        layout.addWidget(subtitle)

        layout.addSpacing(12)

        self.login_username = _input_field("Email")
        layout.addWidget(self.login_username)

        self.login_password = _input_field("Mot de passe", password=True)
        layout.addWidget(self.login_password)

        self.login_error = QLabel("")
        self.login_error.setStyleSheet(f"color: {C_DANGER}; font-size: 12px; font-weight: 500;")
        self.login_error.hide()
        layout.addWidget(self.login_error)

        layout.addSpacing(8)

        self.login_btn = QPushButton("Se connecter")
        self.login_btn.setCursor(Qt.PointingHandCursor)
        self.login_btn.setMinimumHeight(46)
        self.login_btn.setStyleSheet(f"""
            QPushButton {{
                background: {C_PRIMARY}; color: white; border: none;
                border-radius: 10px; font-size: 15px; font-weight: 700;
            }}
            QPushButton:hover {{ background: {C_PRIMARY_DARK}; }}
            QPushButton:pressed {{ background: #062E5F; }}
        """)
        if self.login_clicked:
            self.login_btn.clicked.connect(self.login_clicked)
        else:
            self.login_btn.clicked.connect(self._on_login)
        layout.addWidget(self.login_btn)

        layout.addStretch()

        self.stack.addWidget(page)

    def _build_register_page(self):
        page = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("background: transparent; border: none;")

        form = QWidget()
        layout = QVBoxLayout(form)
        layout.setContentsMargins(0, 20, 0, 0)
        layout.setSpacing(14)

        title = QLabel("Créer un compte")
        title.setStyleSheet(f"font-size: 24px; font-weight: 800; color: {C_TEXT};")
        layout.addWidget(title)
        subtitle = QLabel("Remplissez les informations ci-dessous")
        subtitle.setStyleSheet(f"font-size: 13px; color: {C_TEXT_SEC}; margin-bottom: 4px;")
        layout.addWidget(subtitle)

        self.reg_nom = _input_field("Nom")
        layout.addWidget(self.reg_nom)
        self.reg_prenom = _input_field("Prénom")
        layout.addWidget(self.reg_prenom)

        dob = QHBoxLayout()
        dob.setSpacing(8)
        self.reg_date_naissance = QDateEdit()
        self.reg_date_naissance.setDisplayFormat("yyyy-MM-dd")
        self.reg_date_naissance.setDate(self.reg_date_naissance.date().addYears(-18))
        self.reg_date_naissance.setMinimumHeight(46)
        self.reg_date_naissance.setStyleSheet(f"""
            QDateEdit {{
                background: {C_WHITE}; border: 1.5px solid {C_BORDER};
                border-radius: 10px; padding: 0 14px; font-size: 14px;
                color: {C_TEXT};
            }}
            QDateEdit:focus {{ border-color: {C_PRIMARY}; }}
        """)
        dob.addWidget(QLabel("Date naissance:"))
        dob.addWidget(self.reg_date_naissance, 1)
        layout.addLayout(dob)

        self.reg_adresse = _input_field("Adresse")
        layout.addWidget(self.reg_adresse)
        self.reg_telephone = _input_field("Téléphone")
        layout.addWidget(self.reg_telephone)

        sep2 = QFrame()
        sep2.setFixedHeight(1)
        sep2.setStyleSheet(f"background: {C_BORDER}; margin: 6px 0;")
        layout.addWidget(sep2)

        self.reg_username = _input_field("Nom d'utilisateur")
        layout.addWidget(self.reg_username)
        self.reg_password = _input_field("Mot de passe", password=True)
        layout.addWidget(self.reg_password)
        self.reg_confirm = _input_field("Confirmer le mot de passe", password=True)
        layout.addWidget(self.reg_confirm)

        self.reg_error = QLabel("")
        self.reg_error.setStyleSheet(f"color: {C_DANGER}; font-size: 12px; font-weight: 500;")
        self.reg_error.hide()
        layout.addWidget(self.reg_error)

        self.reg_btn = QPushButton("Créer mon compte")
        self.reg_btn.setCursor(Qt.PointingHandCursor)
        self.reg_btn.setMinimumHeight(46)
        self.reg_btn.setStyleSheet(f"""
            QPushButton {{
                background: {C_SUCCESS}; color: white; border: none;
                border-radius: 10px; font-size: 15px; font-weight: 700;
            }}
            QPushButton:hover {{ background: #047857; }}
            QPushButton:pressed {{ background: #065F46; }}
        """)
        if self.inscription_clicked:
            self.reg_btn.clicked.connect(self.inscription_clicked)
        else:
            self.reg_btn.clicked.connect(self._on_register)
        layout.addWidget(self.reg_btn)

        layout.addStretch()

        scroll.setWidget(form)
        page_l = QVBoxLayout(page)
        page_l.setContentsMargins(0, 0, 0, 0)
        page_l.addWidget(scroll)
        self.stack.addWidget(page)

    def _on_login(self):
        if self.login_clicked:
            self.login_clicked()
        elif self._controller and hasattr(self._controller, 'do_login'):
            email, password = self.get_login_data()
            if not email or not password:
                self.show_login_error("Veuillez remplir tous les champs.")
                return
            self.show_loading(True)
            self._controller.do_login(email, password, self)

    def _on_register(self):
        if self.inscription_clicked:
            self.inscription_clicked()
        elif self._controller and hasattr(self._controller, 'do_register_patient'):
            nom, prenom, date_naissance, adresse, telephone, username, password, confirm = self.get_register_data()
            if password != confirm:
                self.show_register_error("Les mots de passe ne correspondent pas")
                return
            if not (nom and prenom and username and password):
                self.show_register_error("Veuillez remplir tous les champs obligatoires.")
                return
            self.show_loading(True)
            self._controller.do_register_patient(
                username,
                password,
                nom,
                prenom,
                date_naissance,
                "M",
                telephone or None,
                adresse or None,
                None,
                self,
            )

    def login_failed(self):
        self.show_loading(False)
        self.show_login_error("Email ou mot de passe incorrect.")

    def show_login(self):
        self.reset()
        self._switch_tab(0)
        self.show()

    def get_login_data(self):
        return self.login_username.text(), self.login_password.text()

    def get_register_data(self):
        return (
            self.reg_nom.text(), self.reg_prenom.text(),
            self.reg_date_naissance.date().toString("yyyy-MM-dd"),
            self.reg_adresse.text(), self.reg_telephone.text(),
            self.reg_username.text(), self.reg_password.text(),
            self.reg_confirm.text()
        )

    def show_login_error(self, msg):
        self.login_error.setText(msg)
        self.login_error.show()

    def show_register_error(self, msg):
        self.reg_error.setText(msg)
        self.reg_error.show()

    def _drag_start(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()

    def _drag_move(self, event):
        if event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self._drag_pos)

    def show_loading(self, show=True):
        if show:
            self.loader.show()
            QTimer.singleShot(2500, lambda: self.loader.hide())
        else:
            self.loader.hide()

    def reset(self):
        self.login_username.clear()
        self.login_password.clear()
        self.reg_nom.clear()
        self.reg_prenom.clear()
        self.reg_adresse.clear()
        self.reg_telephone.clear()
        self.reg_username.clear()
        self.reg_password.clear()
        self.reg_confirm.clear()
        self.login_error.hide()
        self.reg_error.hide()
        self.stack.setCurrentIndex(0)
        self._switch_tab(0)



