from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTabWidget, QGridLayout, QFrame, QMessageBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from views.components import (
    STYLE_BASE, C_BG, C_WHITE, C_PRIMARY, C_PRIMARY_DARK, C_PRIMARY_LIGHT,
    C_SUCCESS, C_DANGER, C_WARNING, C_TEXT, C_TEXT_SEC, C_TEXT_LIGHT, C_BORDER,
    C_SUCCESS_LIGHT, C_DANGER_LIGHT, C_WARNING_LIGHT, C_INFO_LIGHT, C_PURPLE,
    make_btn, StatCard, TableWithEmpty, ToastNotification, page_title
)
from models.medecin_model import MedecinModel


class AdminView(QMainWindow):
    def __init__(self, user, controller):
        super().__init__()
        self.user = user
        self._controller = controller
        self.setWindowTitle("Administration — Carnet Médical")
        self.setMinimumSize(1260, 780)
        self.setStyleSheet(STYLE_BASE)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(16)

        header = QWidget()
        hl = QHBoxLayout(header)
        hl.setContentsMargins(0, 0, 0, 0)

        title = QLabel("🛡️  Administration")
        title.setStyleSheet(f"font-size: 26px; font-weight: 800; color: {C_TEXT};")
        hl.addWidget(title)
        hl.addStretch()

        admin_badge = QLabel(f"Admin: {user.get('email', '')}")
        admin_badge.setStyleSheet(f"""
            background: {C_PURPLE}; color: white; padding: 7px 18px;
            border-radius: 20px; font-size: 12px; font-weight: 600;
        """)
        hl.addWidget(admin_badge)

        btn_logout = make_btn("Déconnexion", "danger")
        btn_logout.clicked.connect(self._on_logout)
        hl.addWidget(btn_logout)
        layout.addWidget(header)

        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{ border: 1px solid {C_BORDER}; border-radius: 14px;
                background: {C_WHITE}; padding: 8px; }}
            QTabBar::tab {{ padding: 12px 28px; font-size: 13px; font-weight: 500;
                color: {C_TEXT_SEC}; }}
            QTabBar::tab:selected {{ background: {C_PRIMARY}; color: white;
                border-radius: 8px 8px 0 0; font-weight: 700; }}
            QTabBar::tab:hover:!selected {{ background: {C_PRIMARY_LIGHT}; color: {C_PRIMARY}; }}
        """)

        self.tabs.addTab(self._build_medecins_tab(), "👨‍⚕️  Médecins")
        self.tabs.addTab(self._build_users_tab(), "👥  Utilisateurs")
        self.tabs.addTab(self._build_audit_tab(), "📋  Journal d'Audit")
        self.tabs.addTab(self._build_stats_tab(), "📊  Statistiques")
        layout.addWidget(self.tabs, 1)

    def _on_logout(self):
        self._controller.logout(self.user['id'], "admin")

    def show_toast(self, message, type="success"):
        t = ToastNotification(self.tabs, message, type)
        t.show()
        t.setGeometry(self.tabs.width() - 370, 8, 350, 52)

    # ======================== MÉDECINS ========================
    def _build_medecins_tab(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        header = QWidget()
        hl = QHBoxLayout(header)
        hl.setContentsMargins(0, 0, 0, 0)
        hl.addWidget(QLabel("Gestion des médecins — validation, suspension, rejet"))
        hl.addStretch()
        btn_refresh = make_btn("🔄  Actualiser", "outline", "sm")
        btn_refresh.clicked.connect(self._load_medecins)
        hl.addWidget(btn_refresh)
        layout.addWidget(header)

        self.medecins_table = TableWithEmpty(
            ["ID", "Nom", "Prénom", "Spécialité", "N° Ordre", "Email", "Téléphone", "Statut", "Action"],
            "default"
        )
        layout.addWidget(self.medecins_table, 1)
        self._load_medecins()
        return page

    def _load_medecins(self):
        medecins = MedecinModel.get_all_medecins()
        data = [[
            str(m.get('id', '')), m.get('nom', ''), m.get('prenom', ''),
            m.get('specialite', ''), m.get('numero_ordre', ''),
            m.get('email', '') or '', m.get('telephone', ''),
            m.get('statut', ''), ""
        ] for m in medecins]
        self.medecins_table.set_data(data)
        for r, m in enumerate(medecins):
            statut = m.get('statut', '')
            if statut == "en_attente":
                w = QWidget()
                bl = QHBoxLayout(w)
                bl.setContentsMargins(2, 2, 2, 2)
                bl.setSpacing(6)
                val = make_btn("✅  Valider", "success", "sm")
                val.clicked.connect(lambda checked, mid=m['id']: self._verify_medecin(mid, "verifie"))
                rej = make_btn("❌  Rejeter", "danger", "sm")
                rej.clicked.connect(lambda checked, mid=m['id']: self._verify_medecin(mid, "rejete"))
                bl.addWidget(val); bl.addWidget(rej)
                self.medecins_table.table.setCellWidget(r, 8, w)
            elif statut == "verifie":
                btn = make_btn("⛔  Suspendre", "warning", "sm")
                btn.clicked.connect(lambda checked, mid=m['id']: self._verify_medecin(mid, "suspendu"))
                self.medecins_table.table.setCellWidget(r, 8, btn)
            elif statut == "suspendu":
                btn = make_btn("🔄  Réactiver", "success", "sm")
                btn.clicked.connect(lambda checked, mid=m['id']: self._verify_medecin(mid, "verifie"))
                self.medecins_table.table.setCellWidget(r, 8, btn)
            elif statut == "rejete":
                btn = make_btn("🗑️", "danger", "sm")
                self.medecins_table.table.setCellWidget(r, 8, btn)

    def _verify_medecin(self, medecin_id, statut):
        MedecinModel.update_medecin_status(medecin_id, statut, self.user['id'])
        self._controller.log_action(self.user['id'], "admin", f"MEDECIN_{statut.upper()}", "medecins", medecin_id)
        self._load_medecins()
        labels = {"verifie": "validé", "rejete": "rejeté", "suspendu": "suspendu"}
        self.show_toast(f"Médecin {labels.get(statut, statut)} avec succès",
                        "success" if statut != "rejete" else "warning")

    # ======================== UTILISATEURS ========================
    def _build_users_tab(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        header = QWidget()
        hl = QHBoxLayout(header)
        hl.setContentsMargins(0, 0, 0, 0)
        hl.addWidget(QLabel("Gestion des comptes utilisateurs — suspension, suppression"))
        hl.addStretch()
        btn_refresh = make_btn("🔄  Actualiser", "outline", "sm")
        btn_refresh.clicked.connect(self._load_users)
        hl.addWidget(btn_refresh)
        layout.addWidget(header)

        self.users_table = TableWithEmpty(
            ["ID", "Email", "Rôle", "Nom", "Prénom", "Actif", "Actions"],
            "default"
        )
        layout.addWidget(self.users_table, 1)
        self._load_users()
        return page

    def _load_users(self):
        users = MedecinModel.get_all_users()
        data = [[
            str(u.get('id', '')), u.get('email', ''), u.get('role', ''),
            u.get('nom', ''), u.get('prenom', ''),
            "✅ Actif" if u.get('est_actif', 1) else "⛔ Suspendu", ""
        ] for u in users]
        self.users_table.set_data(data)
        for r, u in enumerate(users):
            w = QWidget()
            bl = QHBoxLayout(w)
            bl.setContentsMargins(2, 2, 2, 2)
            bl.setSpacing(4)
            if u.get('est_actif', 1):
                btn = make_btn("⛔  Suspendre", "warning", "sm")
            else:
                btn = make_btn("🔄  Réactiver", "success", "sm")
            btn.clicked.connect(lambda checked, uid=u['id'], actif=u.get('est_actif', 1):
                                self._toggle_user_status(uid, not actif))
            bl.addWidget(btn)
            if u.get('role') != 'admin':
                btn_del = make_btn("🗑️", "danger", "sm")
                btn_del.clicked.connect(lambda checked, uid=u['id'], email=u.get('email', ''):
                                        self._delete_user(uid, email))
                bl.addWidget(btn_del)
            self.users_table.table.setCellWidget(r, 6, w)

    def _toggle_user_status(self, user_id, actif):
        MedecinModel.toggle_user_status(user_id, actif)
        self._controller.log_action(self.user['id'], "admin", "TOGGLE_USER_STATUS", "users", user_id,
                                    details=f"actif={actif}")
        self._load_users()

    def _delete_user(self, user_id, email):
        if QMessageBox.question(self, "Confirmation",
                                f"Supprimer l'utilisateur {email} (ID: {user_id}) ?\nCette action est irréversible.",
                                QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            MedecinModel.delete_user(user_id)
            self._controller.log_action(self.user['id'], "admin", "DELETE_USER", "users", user_id,
                                        details=f"email={email}")
            self._load_users()
            self.show_toast(f"Utilisateur {email} supprimé", "success")

    # ======================== AUDIT ========================
    def _build_audit_tab(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        header = QWidget()
        hl = QHBoxLayout(header)
        hl.setContentsMargins(0, 0, 0, 0)
        hl.addWidget(QLabel("Journal des actions — traçabilité complète"))
        hl.addStretch()
        btn_refresh = make_btn("🔄  Actualiser", "outline", "sm")
        btn_refresh.clicked.connect(self._load_audit)
        hl.addWidget(btn_refresh)
        layout.addWidget(header)

        self.audit_table = TableWithEmpty(
            ["Date", "Utilisateur", "Rôle", "Action", "Entité", "Détails", "Statut"],
            "default"
        )
        layout.addWidget(self.audit_table, 1)
        self._load_audit()
        return page

    def _load_audit(self):
        logs = MedecinModel.get_audit_logs()
        data = [[
            log.get('created_at', ''), str(log.get('user_id', '')),
            log.get('user_role', ''), log.get('action', ''),
            f"{log.get('entite', '')} #{log.get('entite_id', '')}",
            log.get('details', ''), log.get('statut', '')
        ] for log in logs]
        self.audit_table.set_data(data)
        for r, log in enumerate(logs):
            if log.get('statut', '') == 'echec':
                item = self.audit_table.table.item(r, 6)
                if item:
                    item.setForeground(QColor(C_DANGER))

    # ======================== STATISTIQUES ========================
    def _build_stats_tab(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        title = QLabel("📊  Aperçu des statistiques système")
        title.setStyleSheet(f"font-size: 18px; font-weight: 700; color: {C_TEXT};")
        layout.addWidget(title)

        stats_data = MedecinModel.get_stats()
        cards = QWidget()
        gl = QGridLayout(cards)
        gl.setSpacing(14)

        items = [
            ("👥  Utilisateurs", stats_data.get('utilisateurs', 0), C_PRIMARY),
            ("🧑  Patients", stats_data.get('patients', 0), C_SUCCESS),
            ("👨‍⚕️  Médecins", stats_data.get('medecins', 0), "#8B5CF6"),
            ("⏳  En attente", stats_data.get('en_attente', 0), C_WARNING),
            ("🩺  Consultations", stats_data.get('consultations', 0), C_DANGER),
            ("💊  Prescriptions", stats_data.get('prescriptions', 0), "#EC4899"),
            ("📅  Rendez-vous", stats_data.get('rendez_vous', 0), "#14B8A6"),
            ("⚠️  Allergies", stats_data.get('allergies', 0), "#F97316"),
            ("🔬  Examens", stats_data.get('examens', 0), "#6366F1"),
            ("📝  Actions", stats_data.get('audit_log', 0), "#84CC16"),
        ]
        for i, (label, count, color) in enumerate(items):
            gl.addWidget(StatCard(label, count, color), i // 2, i % 2)

        layout.addWidget(cards)
        layout.addStretch()
        return page
