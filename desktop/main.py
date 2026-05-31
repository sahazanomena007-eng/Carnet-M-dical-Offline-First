#!/usr/bin/env python3
"""
Carnet Medical Numerique - Application Desktop (PyQt5)
Architecture MVC : Models, Views, Controllers
Theme : Mode Sante professionnel
"""

import sys, os

sys.path.insert(0, os.path.dirname(__file__))

import db
from PyQt5.QtWidgets import QApplication, QMessageBox
from views.components import STYLE_BASE


class AppManager:
    """Orchestre les vues : login, patient, medecin, admin"""

    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setStyleSheet(STYLE_BASE)
        self.login_view = None
        self.auth_controller = None

    def start(self):
        db.init_db()
        self._seed_if_empty()
        from controllers.auth_controller import AuthController
        self.auth_controller = AuthController(self)
        self.show_login(self.auth_controller)
        sys.exit(self.app.exec_())

    def _seed_if_empty(self):
        """Insere les donnees de demonstration si la base est vide"""
        count = db._execute("SELECT COUNT(*) as c FROM users", (), fetchone=True)
        if count and count.get('c', 0) > 0:
            return
        print("Seed: Ajout des donnees de demonstration...")
        admin_id = db.create_user("admin@carnetmed.mg", "admin123", "admin", "Admin", "Systeme")
        db.log_action(admin_id, "admin", "SEED", "system", details="Seed automatique")
        pat_user_id = db.create_user("patient@exemple.mg", "patient123", "patient", "Rakoto", "Jean", "0341234567")
        db.create_patient(pat_user_id, "Rakoto", "Jean", "1990-05-15", "M",
                         adresse="Antananarivo", groupe_sanguin="O+", taille_cm=175, poids_kg="70")
        med_user_id = db.create_user("medecin@exemple.mg", "medecin123", "medecin", "Rasoa", "Marie", "0347654321")
        db.create_medecin(med_user_id, "MG-2024-001", "Rasoa", "Marie", "Cardiologie",
                         "CHU Antananarivo", "0347654321", "medecin@exemple.mg",
                         statut="verifie", verifie_par=admin_id)
        pat = db._execute("SELECT id FROM patients WHERE user_id=?", (pat_user_id,), fetchone=True)
        med = db._execute("SELECT id FROM medecins WHERE user_id=?", (med_user_id,), fetchone=True)
        pat_id = pat['id'] if pat else None
        med_id = med['id'] if med else None
        if pat_id and med_id:
            db.create_link(pat_id, med_id, "LINK-2024-001")
            db.validate_link("LINK-2024-001", pat_id)
            db.create_consultation(pat_id, med_id, "2024-06-15", "09:30", "Consultation de routine",
                                  "Toux seche, fievre legere", "Rhinite allergique",
                                  "Prescrire antihistaminique", "Cetirizine 10mg/jour")
            db.create_prescription(1, pat_id, med_id, "Antihistaminique", "Cetirizine 10mg",
                                  date_debut="2024-06-15", date_fin="2024-07-15")
            db.create_rendezvous(pat_id, med_id, "2024-07-15", "10:00", "10:30",
                                "Suivi mensuel", "suivi", 2)
            db.create_allergie(pat_id, "Penicilline", "severe",
                              "Reaction cutanee severe, necessite hospitalisation", "2018-03-10")
            db.create_examen(pat_id, 1, med_id, "Prise de sang",
                            "Globules blancs: 7500/mm3\nHemoglobine: 14g/dL", date_examen="2024-06-15")
        db.log_action(admin_id, "admin", "SEED_COMPLETE", "system", details="Donnees de demo inserees")
        print("Seed: Donnees de demonstration ajoutees avec succes.")

    def show_login(self, auth_controller=None):
        from views.login_view import LoginView
        if auth_controller:
            self.auth_controller = auth_controller
        self.login_view = LoginView(self.auth_controller)
        self.login_view.show()

    def on_login_success(self, user, login_view):
        if user['role'] == 'patient':
            from controllers.patient_controller import PatientController
            rows = db.get_patient(user_id=user['id'])
            if not rows:
                QMessageBox.critical(login_view, "Erreur", "Profil patient introuvable.")
                return
            ctrl = PatientController(self)
            ctrl.open_patient_window(rows[0], user, login_view)
        elif user['role'] == 'medecin':
            from controllers.medecin_controller import MedecinController
            rows = db.get_medecin(user_id=user['id'])
            if not rows:
                QMessageBox.critical(login_view, "Erreur", "Profil medecin introuvable.")
                return
            m = rows[0]
            if m.get('statut') != 'verifie':
                QMessageBox.information(login_view, "En attente",
                    "Votre compte est en cours de verification par l'administrateur.")
                return
            ctrl = MedecinController(self)
            ctrl.open_medecin_window(m, user, login_view)
        elif user['role'] == 'admin':
            from controllers.admin_controller import AdminController
            ctrl = AdminController(self)
            ctrl.open_admin_window(user, login_view)


if __name__ == "__main__":
    AppManager().start()
