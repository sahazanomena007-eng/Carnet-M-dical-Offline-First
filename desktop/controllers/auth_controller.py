import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import db

from PyQt5.QtWidgets import QMessageBox, QDialog, QVBoxLayout, QLabel, QPushButton
from PyQt5.QtCore import Qt


class AuthController:
    def __init__(self, app_manager):
        self.app = app_manager

    def show_create_account_dialog(self, parent):
        dialog = QDialog(parent)
        dialog.setWindowTitle("Creer un compte")
        dialog.setFixedSize(400, 260)
        dialog.setStyleSheet("QDialog { background: #ffffff; border-radius: 16px; }")
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)

        title = QLabel("Choisissez le type de compte"); title.setStyleSheet("font-size: 17px; font-weight: 700; color: #1F2937;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        desc = QLabel("Je suis un..."); desc.setStyleSheet("font-size: 13px; color: #6B7280;")
        desc.setAlignment(Qt.AlignCenter)
        layout.addWidget(desc)

        from views.components import C_SUCCESS, C_PRIMARY

        btn_patient = QPushButton("\U0001F468\u200D\U0001F3EB  Patient - Acceder a mon carnet")
        btn_patient.setStyleSheet(f"background: {C_SUCCESS}; color: white; border: none; padding: 14px; border-radius: 16px; font-weight: 600; font-size: 14px; text-align: left;")
        btn_patient.clicked.connect(lambda: self._choose("patient", dialog, parent))
        layout.addWidget(btn_patient)

        btn_medecin = QPushButton("\U0001FA7A  Medecin - Gerer mes patients")
        btn_medecin.setStyleSheet(f"background: {C_PRIMARY}; color: white; border: none; padding: 14px; border-radius: 16px; font-weight: 600; font-size: 14px; text-align: left;")
        btn_medecin.clicked.connect(lambda: self._choose("medecin", dialog, parent))
        layout.addWidget(btn_medecin)

        btn_close = QPushButton("Annuler")
        btn_close.setStyleSheet(f"background: white; color: {C_PRIMARY}; border: 2px solid #E5E7EB; padding: 10px 24px; border-radius: 12px; font-weight: 600; font-size: 13px;")
        btn_close.clicked.connect(dialog.reject)
        layout.addWidget(btn_close)
        dialog.exec()

    def _choose(self, role, dialog, login_view):
        dialog.accept()
        login_view.stack.setCurrentIndex(1 if role == "patient" else 2)

    def do_login(self, email, password, login_view):
        user = db.authenticate_user(email, password)
        if not user:
            login_view.login_failed()
            QMessageBox.critical(login_view, "Erreur", "Email ou mot de passe incorrect.")
            db.log_action(0, "anonymous", "LOGIN_FAILED", "users", details=f"email={email}")
            return
        db.log_action(user['id'], user['role'], "LOGIN", "users", user['id'])
        self.app.on_login_success(user, login_view)

    def do_register_patient(self, email, password, nom, prenom, date_naiss, sexe, tel, adresse, gs, login_view):
        if len(password) < 8:
            QMessageBox.warning(login_view, "Erreur", "Le mot de passe doit contenir au moins 8 caracteres.")
            return
        if not email or not nom or not prenom:
            QMessageBox.warning(login_view, "Erreur", "Veuillez remplir tous les champs obligatoires.")
            return
        try:
            user_id = db.create_user(email, password, "patient", nom, prenom, tel)
            db.create_patient(user_id, nom, prenom, date_naiss, sexe, adresse=adresse, groupe_sanguin=gs)
            db.log_action(user_id, "patient", "REGISTER", "users", user_id)
            QMessageBox.information(login_view, "Succes", "Compte cree avec succes! Vous pouvez maintenant vous connecter.")
            login_view.reset_register_fields()
            login_view.show_login()
        except Exception as e:
            QMessageBox.critical(login_view, "Erreur", str(e))

    def do_register_medecin(self, email, password, nom, prenom, num_ordre, specialite, etablissement, tel, login_view):
        if len(password) < 8:
            QMessageBox.warning(login_view, "Erreur", "Le mot de passe doit contenir au moins 8 caracteres.")
            return
        if not email or not nom or not prenom or not num_ordre or not specialite or not tel:
            QMessageBox.warning(login_view, "Erreur", "Veuillez remplir tous les champs obligatoires.")
            return
        try:
            user_id = db.create_user(email, password, "medecin", nom, prenom, tel)
            db.create_medecin(user_id, num_ordre, nom, prenom, specialite, etablissement, tel, email)
            db.log_action(user_id, "medecin", "REGISTER", "medecins", user_id)
            QMessageBox.information(login_view, "Succes", "Compte cree! En attente de verification par l'administrateur.")
            login_view.reset_register_fields()
            login_view.show_login()
        except Exception as e:
            QMessageBox.critical(login_view, "Erreur", str(e))

    @staticmethod
    def log_action(user_id, role, action, entite, entite_id=None, details=None):
        db.log_action(user_id, role, action, entite, entite_id, details)
