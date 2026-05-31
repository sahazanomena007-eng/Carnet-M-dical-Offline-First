from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QStackedWidget, QFrame, QDialog, QDateEdit, QComboBox,
    QProgressBar
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QGraphicsDropShadowEffect

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from views.components import (
    STYLE_BASE, C_BG, C_WHITE, C_PRIMARY, C_PRIMARY_DARK, C_PRIMARY_LIGHT,
    C_SUCCESS, C_DANGER, C_BORDER, C_TEXT, C_TEXT_SEC, C_TEXT_LIGHT,
    C_SUCCESS_LIGHT, C_WARNING_LIGHT, make_btn, section_title, add_shadow
)


class LoginView(QMainWindow):
    def __init__(self, controller):
        super().__init__()
        self._controller = controller
        self.setWindowTitle("MediCare Santé - Connexion")
        self.setMinimumSize(520, 700)
        self.setStyleSheet(STYLE_BASE)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setAlignment(Qt.AlignCenter)
        layout.setContentsMargins(40, 40, 40, 40)

        card = QWidget()
        card.setStyleSheet(f"""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 {C_WHITE}, stop:1 #F8FAFC);
            border-radius: 20px; padding: 36px;
            max-width: 460px; margin: 0 auto;
        """)
        cl = QVBoxLayout(card)
        cl.setSpacing(8)
        cl.setAlignment(Qt.AlignCenter)
        add_shadow(card, blur=40, offset=4, color=QColor(15, 108, 189, 50))

        icon_lbl = QLabel("\U0001F3E5")
        icon_lbl.setStyleSheet("font-size: 56px;")
        icon_lbl.setAlignment(Qt.AlignCenter)
        cl.addWidget(icon_lbl)

        titre = QLabel("MediCare Santé")
        titre.setStyleSheet(f"font-size: 26px; font-weight: 700; color: {C_PRIMARY}; text-align: center; letter-spacing: -0.3px;")
        titre.setAlignment(Qt.AlignCenter)
        cl.addWidget(titre)

        sous_titre = QLabel("Plateforme Medicale Professionnelle")
        sous_titre.setStyleSheet(f"font-size: 13px; color: {C_TEXT_SEC}; text-align: center; margin-bottom: 12px;")
        sous_titre.setAlignment(Qt.AlignCenter)
        cl.addWidget(sous_titre)

        deco = QFrame()
        deco.setFixedHeight(3)
        deco.setFixedWidth(60)
        deco.setStyleSheet(f"background: {C_PRIMARY}; border-radius: 2px; margin: 4px 0 12px 0;")
        cl.addWidget(deco)

        layout.addWidget(card)

        self.stack = QStackedWidget()
        layout.addWidget(self.stack)

        self.stack.addWidget(self._build_login_panel())
        self.stack.addWidget(self._build_register_patient())
        self.stack.addWidget(self._build_register_medecin())

    def _card(self, title=""):
        w = QWidget()
        w.setStyleSheet(f"background: {C_WHITE}; border-radius: 12px; max-width: 440px;")
        lo = QVBoxLayout(w)
        lo.setContentsMargins(28, 24, 28, 24)
        lo.setSpacing(14)
        if title:
            t = QLabel(title)
            t.setStyleSheet(f"font-size: 18px; font-weight: 700; color: {C_TEXT}; margin-bottom: 4px;")
            lo.addWidget(t)
        return w, lo

    def _build_login_panel(self):
        panel, lo = self._card("Connexion")
        self.login_email = QLineEdit()
        self.login_email.setPlaceholderText("Entrez votre email")
        lo.addWidget(QLabel("\U0001F4E7  Email"))
        lo.addWidget(self.login_email)

        pwd_row = QWidget()
        prl = QHBoxLayout(pwd_row)
        prl.setContentsMargins(0, 0, 0, 0)
        self.login_password = QLineEdit()
        self.login_password.setPlaceholderText("Mot de passe")
        self.login_password.setEchoMode(QLineEdit.Password)
        prl.addWidget(self.login_password, 1)
        self.toggle_pwd_btn = QPushButton("\U0001F441")
        self.toggle_pwd_btn.setFixedWidth(40)
        self.toggle_pwd_btn.setStyleSheet(f"background: {C_BORDER}; color: {C_TEXT_SEC}; border: none; border-radius: 6px; padding: 8px;")
        self.toggle_pwd_btn.setToolTip("Afficher/Masquer le mot de passe")
        self.toggle_pwd_btn.clicked.connect(self._toggle_password)
        prl.addWidget(self.toggle_pwd_btn)
        lo.addWidget(QLabel("\U0001F512  Mot de passe"))
        lo.addWidget(pwd_row)

        self.login_loading = QProgressBar()
        self.login_loading.setRange(0, 0)
        self.login_loading.hide()
        lo.addWidget(self.login_loading)

        btn_login = make_btn("Se connecter", "primary")
        btn_login.clicked.connect(self._on_login)
        lo.addWidget(btn_login)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f"color: {C_BORDER}; margin: 4px 0;")
        lo.addWidget(sep)

        btn_create = make_btn("Creer un compte", "success", "\U0001F464")
        btn_create.clicked.connect(self._show_create_dialog)
        lo.addWidget(btn_create)
        return panel

    def _toggle_password(self):
        if self.login_password.echoMode() == QLineEdit.Password:
            self.login_password.setEchoMode(QLineEdit.Normal)
        else:
            self.login_password.setEchoMode(QLineEdit.Password)

    def _show_create_dialog(self):
        self._controller.show_create_account_dialog(self)

    def _build_register_patient(self):
        panel, lo = self._card("Inscription Patient")
        self.reg_p_email = QLineEdit(); self.reg_p_email.setPlaceholderText("Email")
        self.reg_p_password = QLineEdit(); self.reg_p_password.setPlaceholderText("Mot de passe (min 8 car.)")
        self.reg_p_password.setEchoMode(QLineEdit.Password)
        self.reg_p_nom = QLineEdit(); self.reg_p_nom.setPlaceholderText("Nom")
        self.reg_p_prenom = QLineEdit(); self.reg_p_prenom.setPlaceholderText("Prenom")
        self.reg_p_date_naiss = QDateEdit(); self.reg_p_date_naiss.setCalendarPopup(True)
        self.reg_p_date_naiss.setDate(QDate(1990, 1, 1))
        self.reg_p_sexe = QComboBox(); self.reg_p_sexe.addItems(["Masculin", "Feminin"])
        self.reg_p_tel = QLineEdit(); self.reg_p_tel.setPlaceholderText("Telephone (optionnel)")
        self.reg_p_adresse = QLineEdit(); self.reg_p_adresse.setPlaceholderText("Adresse (optionnel)")
        self.reg_p_gs = QComboBox(); self.reg_p_gs.addItems(["", "A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"])

        for w in [self.reg_p_email, self.reg_p_password, self.reg_p_nom, self.reg_p_prenom]:
            lo.addWidget(section_title(w.placeholderText().split("(")[0].strip()))
            lo.addWidget(w)
        lo.addWidget(section_title("Date naissance")); lo.addWidget(self.reg_p_date_naiss)
        lo.addWidget(section_title("Sexe")); lo.addWidget(self.reg_p_sexe)
        lo.addWidget(section_title("Telephone")); lo.addWidget(self.reg_p_tel)
        lo.addWidget(section_title("Adresse")); lo.addWidget(self.reg_p_adresse)
        lo.addWidget(section_title("Groupe sanguin")); lo.addWidget(self.reg_p_gs)

        btn = make_btn("Creer mon compte patient", "success", "\U00002714")
        btn.clicked.connect(self._on_register_patient)
        lo.addWidget(btn)

        btn_back = QPushButton("\u2190  Retour")
        btn_back.setObjectName("btnOutline")
        btn_back.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        lo.addWidget(btn_back)
        return panel

    def _build_register_medecin(self):
        panel, lo = self._card("Inscription Medecin")
        self.reg_m_email = QLineEdit(); self.reg_m_email.setPlaceholderText("Email professionnel")
        self.reg_m_password = QLineEdit(); self.reg_m_password.setPlaceholderText("Mot de passe (min 8 car.)")
        self.reg_m_password.setEchoMode(QLineEdit.Password)
        self.reg_m_nom = QLineEdit(); self.reg_m_nom.setPlaceholderText("Nom")
        self.reg_m_prenom = QLineEdit(); self.reg_m_prenom.setPlaceholderText("Prenom")
        self.reg_m_num_ordre = QLineEdit(); self.reg_m_num_ordre.setPlaceholderText("Numero d'ordre")
        self.reg_m_specialite = QLineEdit(); self.reg_m_specialite.setPlaceholderText("Specialite")
        self.reg_m_etablissement = QLineEdit(); self.reg_m_etablissement.setPlaceholderText("Etablissement (optionnel)")
        self.reg_m_tel = QLineEdit(); self.reg_m_tel.setPlaceholderText("Telephone")

        for w in [self.reg_m_email, self.reg_m_password, self.reg_m_nom, self.reg_m_prenom,
                  self.reg_m_num_ordre, self.reg_m_specialite]:
            lo.addWidget(section_title(w.placeholderText()))
            lo.addWidget(w)
        lo.addWidget(section_title("Etablissement")); lo.addWidget(self.reg_m_etablissement)
        lo.addWidget(section_title("Telephone")); lo.addWidget(self.reg_m_tel)

        note = QLabel("\u2139  Votre compte sera soumis a verification par l'administrateur.")
        note.setStyleSheet(f"font-size: 12px; color: #D97706; background: {C_WARNING_LIGHT}; padding: 10px 14px; border-radius: 12px; font-weight: 500;")
        lo.addWidget(note)

        btn = make_btn("Creer mon compte medecin", "primary", "\U00002714")
        btn.clicked.connect(self._on_register_medecin)
        lo.addWidget(btn)

        btn_back = QPushButton("\u2190  Retour")
        btn_back.setObjectName("btnOutline")
        btn_back.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        lo.addWidget(btn_back)
        return panel

    def _on_login(self):
        email = self.login_email.text().strip()
        password = self.login_password.text()
        if not email or not password:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Erreur", "Veuillez remplir tous les champs.")
            return
        self.login_loading.show()
        from PyQt5.QtWidgets import QApplication
        QApplication.processEvents()
        self._controller.do_login(email, password, self)

    def _on_register_patient(self):
        self._controller.do_register_patient(
            self.reg_p_email.text().strip(),
            self.reg_p_password.text(),
            self.reg_p_nom.text().strip(),
            self.reg_p_prenom.text().strip(),
            self.reg_p_date_naiss.date().toString("yyyy-MM-dd"),
            "M" if self.reg_p_sexe.currentText() == "Masculin" else "F",
            self.reg_p_tel.text().strip() or None,
            self.reg_p_adresse.text().strip() or None,
            self.reg_p_gs.currentText() or None,
            self
        )

    def _on_register_medecin(self):
        self._controller.do_register_medecin(
            self.reg_m_email.text().strip(),
            self.reg_m_password.text(),
            self.reg_m_nom.text().strip(),
            self.reg_m_prenom.text().strip(),
            self.reg_m_num_ordre.text().strip(),
            self.reg_m_specialite.text().strip(),
            self.reg_m_etablissement.text().strip() or None,
            self.reg_m_tel.text().strip(),
            self
        )

    def show_login(self):
        self.stack.setCurrentIndex(0)
        self.show()

    def login_failed(self):
        self.login_loading.hide()

    def reset_register_fields(self):
        for w in [self.reg_p_email, self.reg_p_password, self.reg_p_nom, self.reg_p_prenom,
                  self.reg_p_tel, self.reg_p_adresse,
                  self.reg_m_email, self.reg_m_password, self.reg_m_nom, self.reg_m_prenom,
                  self.reg_m_num_ordre, self.reg_m_specialite, self.reg_m_etablissement, self.reg_m_tel]:
            w.clear()
