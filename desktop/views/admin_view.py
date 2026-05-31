from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTabWidget, QGridLayout, QFrame
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from views.components import (
    STYLE_BASE, C_BG, C_WHITE, C_PRIMARY, C_PRIMARY_DARK, C_PRIMARY_LIGHT,
    C_SUCCESS, C_DANGER, C_WARNING, C_TEXT, C_TEXT_SEC, C_TEXT_LIGHT, C_BORDER,
    make_btn, StatCard, TableWithEmpty, ToastNotification
)
from models.medecin_model import MedecinModel


class AdminView(QMainWindow):
    def __init__(self, user, controller):
        super().__init__()
        self.user = user
        self._controller = controller
        self.setWindowTitle("Administration - MediCare Santé")
        self.setMinimumSize(1200, 750)
        self.setStyleSheet(STYLE_BASE)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(28, 28, 28, 28)

        header = QWidget()
        hl = QHBoxLayout(header)
        hl.setContentsMargins(0, 0, 0, 16)
        titre = QLabel("\U0001F6E1\uFE0F  Administration")
        titre.setStyleSheet(f"font-size: 22px; font-weight: 700; color: {C_TEXT};")
        hl.addWidget(titre); hl.addStretch()
        btn_logout = make_btn("Deconnexion", "danger", "\U0001F6AA")
        btn_logout.clicked.connect(self._on_logout)
        hl.addWidget(btn_logout)
        layout.addWidget(header)

        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(f"""
            QTabBar::tab {{ padding: 12px 24px; font-size: 13px; font-weight: 500; }}
            QTabBar::tab:selected {{ background: {C_PRIMARY}; color: white; border-radius: 6px 6px 0 0; font-weight: 700; }}
            QTabBar::tab:hover:!selected {{ background: {C_PRIMARY_LIGHT}; }}
        """)
        self.tabs.addTab(self._build_medecins_tab(), "Valider Medecins")
        self.tabs.addTab(self._build_users_tab(), "Utilisateurs")
        self.tabs.addTab(self._build_audit_tab(), "Journal d'Audit")
        self.tabs.addTab(self._build_stats_tab(), "Statistiques")
        layout.addWidget(self.tabs, 1)

    def _on_logout(self):
        self._controller.logout(self.user['id'], "admin")

    def show_toast(self, message, type="success"):
        toast = ToastNotification(self.tabs, message, type)
        toast.show()
        tw = self.tabs.width()
        toast.setGeometry(tw - 370, 8, 350, 52)

    def _build_medecins_tab(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 20, 20, 20)
        self.medecins_table = TableWithEmpty(["ID", "Nom", "Prenom", "Specialite", "N Ordre", "Email", "Telephone", "Statut", "Action"], "default")
        layout.addWidget(self.medecins_table, 1)
        btn_refresh = make_btn("Actualiser", "outline", "\U0001F504")
        btn_refresh.clicked.connect(self._load_medecins)
        layout.addWidget(btn_refresh)
        self._load_medecins()
        return page

    def _load_medecins(self):
        medecins = MedecinModel.get_all_medecins()
        data = []
        for m in medecins:
            data.append([str(m.get('id','')), m.get('nom',''), m.get('prenom',''), m.get('specialite',''),
                         m.get('numero_ordre',''), m.get('telephone',''), m.get('email','') or '',
                         m.get('statut',''), ""])
        self.medecins_table.set_data(data)
        for r, m in enumerate(medecins):
            if m.get('statut') == 'en_attente':
                actions = QWidget(); al = QHBoxLayout(actions); al.setContentsMargins(2, 2, 2, 2); al.setSpacing(6)
                btn_val = make_btn("Valider", "success", "\u2705")
                btn_val.clicked.connect(lambda checked, mid=m['id']: self._verify_medecin(mid, "verifie"))
                btn_rej = make_btn("Rejeter", "danger", "\u274C")
                btn_rej.clicked.connect(lambda checked, mid=m['id']: self._verify_medecin(mid, "rejete"))
                al.addWidget(btn_val); al.addWidget(btn_rej)
                self.medecins_table.table.setCellWidget(r, 8, actions)
            elif m.get('statut') == 'verifie':
                btn_sus = make_btn("Suspendre", "warning", "\u26D4")
                btn_sus.clicked.connect(lambda checked, mid=m['id']: self._verify_medecin(mid, "suspendu"))
                self.medecins_table.table.setCellWidget(r, 8, btn_sus)
            elif m.get('statut') == 'suspendu':
                btn_react = make_btn("Reactivier", "success", "\u267B")
                btn_react.clicked.connect(lambda checked, mid=m['id']: self._verify_medecin(mid, "verifie"))
                self.medecins_table.table.setCellWidget(r, 8, btn_react)

    def _verify_medecin(self, medecin_id, statut):
        MedecinModel.update_medecin_status(medecin_id, statut, self.user['id'])
        self._controller.log_action(self.user['id'], "admin", f"MEDECIN_{statut.upper()}", "medecins", medecin_id)
        self._load_medecins()
        status_map = {"verifie": "valide", "rejete": "rejete", "suspendu": "suspendu"}
        self.show_toast(f"Medecin {status_map.get(statut, statut)} avec succes",
                       "success" if statut != "rejete" else "warning")

    def _build_users_tab(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 20, 20, 20)
        self.users_table = TableWithEmpty(["ID", "Email", "Role", "Nom", "Prenom", "Actif", "Actions"], "default")
        layout.addWidget(self.users_table, 1)
        btn_refresh = make_btn("Actualiser", "outline", "\U0001F504")
        btn_refresh.clicked.connect(self._load_users)
        layout.addWidget(btn_refresh)
        self._load_users()
        return page

    def _load_users(self):
        users = MedecinModel.get_all_users()
        data = []
        for u in users:
            data.append([str(u.get('id','')), u.get('email',''), u.get('role',''),
                         u.get('nom',''), u.get('prenom',''), "Oui" if u.get('est_actif', 1) else "Non", ""])
        self.users_table.set_data(data)
        for r, u in enumerate(users):
            actions = QWidget(); al = QHBoxLayout(actions); al.setContentsMargins(2, 2, 2, 2); al.setSpacing(4)
            if u.get('est_actif', 1):
                btn_sus = make_btn("Suspendre", "warning", "\u26D4")
            else:
                btn_sus = make_btn("Reactivier", "success", "\u267B")
            btn_sus.clicked.connect(lambda checked, uid=u['id'], actif=u.get('est_actif', 1):
                self._toggle_user_status(uid, not actif))
            btn_del = make_btn("Suppr.", "danger", "\u274C")
            btn_del.clicked.connect(lambda checked, uid=u['id'], email=u.get('email',''):
                self._delete_user(uid, email))
            al.addWidget(btn_sus)
            if u.get('role') != 'admin':
                al.addWidget(btn_del)
            self.users_table.table.setCellWidget(r, 6, actions)

    def _toggle_user_status(self, user_id, actif):
        MedecinModel.toggle_user_status(user_id, actif)
        self._controller.log_action(self.user['id'], "admin", "TOGGLE_USER_STATUS", "users", user_id, details=f"actif={actif}")
        self._load_users()

    def _delete_user(self, user_id, email):
        from PyQt5.QtWidgets import QMessageBox
        if QMessageBox.question(self, "Confirmation",
                f"Supprimer l'utilisateur {email} (ID: {user_id}) ?\nCette action est irreversible.",
                QMessageBox.Yes|QMessageBox.No) == QMessageBox.Yes:
            MedecinModel.delete_user(user_id)
            self._controller.log_action(self.user['id'], "admin", "DELETE_USER", "users", user_id, details=f"email={email}")
            self._load_users()
            self.show_toast(f"Utilisateur {email} supprime", "success")

    def _build_audit_tab(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 20, 20, 20)
        self.audit_table = TableWithEmpty(["Date", "Utilisateur", "Role", "Action", "Entite", "Details", "Statut"], "default")
        layout.addWidget(self.audit_table, 1)
        btn_refresh = make_btn("Actualiser", "outline", "\U0001F504")
        btn_refresh.clicked.connect(self._load_audit)
        layout.addWidget(btn_refresh)
        self._load_audit()
        return page

    def _load_audit(self):
        logs = MedecinModel.get_audit_logs()
        data = []
        for log in logs:
            data.append([log.get('created_at',''), str(log.get('user_id','')),
                         log.get('user_role',''), log.get('action',''),
                         f"{log.get('entite','')} #{log.get('entite_id','')}", log.get('details',''), log.get('statut','')])
        self.audit_table.set_data(data)
        for r, log in enumerate(logs):
            if log.get('statut','') == 'echec':
                item = self.audit_table.table.item(r, 6)
                if item:
                    item.setForeground(QColor(C_DANGER))

    def _build_stats_tab(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 20, 20, 20)
        stats = QWidget()
        sl = QGridLayout(stats)
        sl.setSpacing(16)
        stats_data = MedecinModel.get_stats()
        labels = [
            ("Patients Utilisateurs", stats_data.get('utilisateurs', 0), C_PRIMARY),
            ("\U0001F468 Patients", stats_data.get('patients', 0), C_SUCCESS),
            ("[M] Medecins", stats_data.get('medecins', 0), "#8B5CF6"),
            ("\u23F3 En attente", stats_data.get('en_attente', 0), C_WARNING),
            ("Records Consultations", stats_data.get('consultations', 0), C_DANGER),
            ("Rx Prescriptions", stats_data.get('prescriptions', 0), "#EC4899"),
            ("Schedule Rendez-vous", stats_data.get('rendez_vous', 0), "#14B8A6"),
            ("\u26A0 Allergies", stats_data.get('allergies', 0), "#F97316"),
            ("Labs Examens", stats_data.get('examens', 0), "#6366F1"),
            ("\U0001F4DD Actions", stats_data.get('audit_log', 0), "#84CC16"),
        ]
        for i, (label, count, color) in enumerate(labels):
            sl.addWidget(StatCard(label, count, color), i // 2, i % 2)
        layout.addWidget(stats)
        layout.addStretch()
        return page
