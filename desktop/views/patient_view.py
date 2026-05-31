from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QStackedWidget, QFrame, QSplitter, QDialog, QFormLayout,
    QTextEdit, QComboBox, QDateEdit, QTimeEdit, QDialogButtonBox,
    QHeaderView, QGraphicsDropShadowEffect
)
from PyQt5.QtCore import Qt, QDate, QTime
from datetime import date

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from views.components import (
    STYLE_BASE, C_BG, C_WHITE, C_PRIMARY, C_PRIMARY_DARK, C_PRIMARY_LIGHT,
    C_SUCCESS, C_DANGER, C_WARNING, C_TEXT, C_TEXT_SEC, C_TEXT_LIGHT, C_BORDER,
    C_SUCCESS_LIGHT, C_WARNING_LIGHT, make_btn, page_title, section_title,
    CardWidget, StatCard, Sidebar, TableWithEmpty, ToastNotification
)
from models.patient_model import PatientModel
from algorithms import search_medical_history, PatientHashTable, AVLTree


class PatientView(QMainWindow):
    def __init__(self, patient, user, controller):
        super().__init__()
        self.patient = patient
        self.user = user
        self._controller = controller
        self.setWindowTitle(f"Carnet Medical - {patient['prenom']} {patient['nom']}")
        self.setMinimumSize(1200, 750)
        self.setStyleSheet(STYLE_BASE)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Sidebar
        profile = QFrame()
        profile.setStyleSheet(f"background: {C_PRIMARY_DARK}; padding: 20px;")
        pl = QVBoxLayout(profile)
        pl.setContentsMargins(16, 20, 16, 20)
        pl.setSpacing(4)
        avatar = QLabel("\U0001F468\u200D\U0001F393")
        avatar.setStyleSheet("font-size: 40px;")
        pl.addWidget(avatar)
        self.sb_name = QLabel(f"{patient['prenom']} {patient['nom']}")
        self.sb_name.setStyleSheet("font-size: 16px; font-weight: 700; color: white;")
        pl.addWidget(self.sb_name)
        self.sb_dos = QLabel(f"Dossier: {patient.get('numero_dossier','')}")
        self.sb_dos.setStyleSheet(f"font-size: 11px; color: #93C5FD;")
        pl.addWidget(self.sb_dos)

        nav_items = [
            ("tableau_bord", "\U0001F4CA  Tableau de bord"),
            ("carnet", "\U0001F4D6  Mon Carnet"),
            ("medecins", "\U0001FA7A  Mes Medecins"),
            ("rendezvous", "\U0001F4C5  Rendez-vous"),
            ("prescriptions", "\U0001F48A  Prescriptions"),
            ("allergies", "\u26A0\uFE0F  Allergies"),
            ("examens", "\U0001F52C  Examens"),
        ]
        self.sidebar = Sidebar(nav_items, profile)
        self.sidebar.logout_btn.clicked.connect(self._on_logout)
        for key, btn in self.sidebar.nav_buttons.items():
            btn.clicked.connect(lambda checked, k=key: self._show_page(k))
        layout.addWidget(self.sidebar)

        # Main content
        self.content_stack = QStackedWidget()
        self.pages = {}
        creators = [
            ("tableau_bord", self._build_dashboard),
            ("carnet", self._build_carnet),
            ("medecins", self._build_medecins),
            ("rendezvous", self._build_rendezvous),
            ("prescriptions", self._build_prescriptions),
            ("allergies", self._build_allergies),
            ("examens", self._build_examens),
        ]
        for key, creator in creators:
            page = creator()
            self.pages[key] = page
            self.content_stack.addWidget(page)
        layout.addWidget(self.content_stack, 1)
        self._show_page("tableau_bord")

    def _show_page(self, key):
        self.sidebar.set_active(key)
        if key in self.pages:
            self.content_stack.setCurrentWidget(self.pages[key])
            refreshers = {
                "tableau_bord": self._refresh_dashboard,
                "carnet": self._refresh_carnet,
                "medecins": self._refresh_medecins,
                "rendezvous": self._refresh_rdv,
                "prescriptions": self._refresh_prescriptions,
                "allergies": self._refresh_allergies,
                "examens": self._refresh_examens,
            }
            if key in refreshers:
                refreshers[key]()

    def _on_logout(self):
        self._controller.logout(self.user['id'], "patient")

    def show_toast(self, message, type="success"):
        toast = ToastNotification(self.content_stack, message, type)
        toast.show()
        pw = self.content_stack.width()
        toast.setGeometry(pw - 370, 16, 350, 52)

    # ===== DASHBOARD =====
    def _build_dashboard(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(28, 28, 28, 28)

        header = QWidget()
        hl = QHBoxLayout(header)
        hl.setContentsMargins(0, 0, 0, 0)
        self.dash_welcome = QLabel()
        self.dash_welcome.setStyleSheet(f"font-size: 22px; font-weight: 700; color: {C_TEXT};")
        hl.addWidget(self.dash_welcome)
        self.dash_badge = QLabel()
        self.dash_badge.setStyleSheet(f"background: {C_SUCCESS_LIGHT}; color: #065F46; padding: 6px 16px; border-radius: 20px; font-size: 13px; font-weight: 600;")
        hl.addWidget(self.dash_badge)
        hl.addStretch()
        layout.addWidget(header)

        self.dash_stats = QWidget()
        self.dash_stats.setLayout(QHBoxLayout())
        layout.addWidget(self.dash_stats)

        row2 = QSplitter(Qt.Horizontal)
        info_card = CardWidget(" Informations personnelles")
        self.dash_info = QWidget()
        self.dash_info.setLayout(QFormLayout())
        info_card.layout.addWidget(self.dash_info)
        row2.addWidget(info_card)

        quick_card = CardWidget(" Actions rapides")
        self.dash_quick_layout = QVBoxLayout()
        quick_card.layout.addLayout(self.dash_quick_layout)
        row2.addWidget(quick_card)
        row2.setSizes([400, 400])
        layout.addWidget(row2, 1)
        return page

    def _refresh_dashboard(self):
        p = self.patient
        self.dash_welcome.setText(f"Bonjour, {p['prenom']} {p['nom']}")
        patient_id = p['id']
        consults = PatientModel.get_consultations(patient_id)
        prescs = PatientModel.get_prescriptions(patient_id)
        rdvs = PatientModel.get_rendezvous(patient_id)
        allergies = PatientModel.get_allergies(patient_id)
        links = PatientModel.get_links(patient_id)
        today_rdvs = [r for r in rdvs if r.get('date_rdv') == date.today().isoformat()]

        badge = ""
        if today_rdvs:
            badge = f"\U0001F514 {len(today_rdvs)} RDV aujourd'hui"
        elif rdvs:
            badge = f"\U0001F4C5 Prochain: {rdvs[0].get('date_rdv','')}"
        self.dash_badge.setText(badge)
        self.dash_badge.setVisible(bool(badge))

        old = self.dash_stats.layout()
        while old.count():
            w = old.takeAt(0).widget()
            if w: w.deleteLater()
        stats_w = QWidget()
        sl = QHBoxLayout(stats_w)
        sl.setSpacing(16)
        for lbl, val, col, ic in [
            ("Consultations", len(consults), C_PRIMARY, "\U0001F4CB"),
            ("Prescriptions", len(prescs), C_SUCCESS, "\U0001F48A"),
            ("Rendez-vous", len(rdvs), C_WARNING, "\U0001F4C5"),
            ("Allergies", len(allergies), C_DANGER, "\u26A0\uFE0F"),
            ("Medecins", len(links), "#8B5CF6", "\U0001FA7A"),
        ]:
            sl.addWidget(StatCard(lbl, val, col, ic))
        old.addWidget(stats_w)

        info_layout = self.dash_info.layout()
        while info_layout.count():
            info_layout.removeRow(info_layout.rowCount() - 1)
        for label, val in [
            ("Dossier", p.get("numero_dossier","")),
            ("Date naissance", p.get("date_naissance","")),
            ("Sexe", "Masculin" if p.get("sexe")=="M" else "Feminin"),
            ("Groupe", p.get("groupe_sanguin","N/A")),
            ("Taille", f'{p.get("taille_cm","")} cm' if p.get("taille_cm") else "N/A"),
            ("Poids", f'{p.get("poids_kg","")} kg' if p.get("poids_kg") else "N/A"),
            ("Telephone", p.get("telephone","N/A")),
        ]:
            l = QLabel(f"<b>{label}:</b>"); l.setStyleSheet(f"color: {C_TEXT_SEC};")
            v = QLabel(str(val)); v.setStyleSheet(f"color: {C_TEXT}; font-weight: 500;")
            info_layout.addRow(l, v)

        while self.dash_quick_layout.count():
            w = self.dash_quick_layout.takeAt(0).widget()
            if w: w.deleteLater()
        for txt, cb in [
            ("\U0001F4D6  Consulter mon carnet", lambda: self._show_page("carnet")),
            ("\U0001F4C5  Mes rendez-vous", lambda: self._show_page("rendezvous")),
            ("\U0001FA7A  Gerer mes medecins", lambda: self._show_page("medecins")),
        ]:
            btn = QPushButton(txt)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet(f"""
                QPushButton {{ text-align: left; padding: 14px 18px; font-size: 14px;
                    background: {C_WHITE}; border: 2px solid {C_BORDER}; border-radius: 16px;
                    color: {C_TEXT}; font-weight: 500; }}
                QPushButton:hover {{ background: {C_PRIMARY_LIGHT}; color: {C_PRIMARY}; border-color: {C_PRIMARY}; }}
            """)
            btn.clicked.connect(cb)
            self.dash_quick_layout.addWidget(btn)

    # ===== CARNET =====
    def _build_carnet(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.addWidget(page_title("\U0001F4D6  Mon Carnet Medical"))

        search_bar = QWidget()
        sl = QHBoxLayout(search_bar)
        sl.setContentsMargins(0, 0, 0, 12)
        self.kmp_input = QLineEdit()
        self.kmp_input.setPlaceholderText("Rechercher dans l'historique medical...")
        self.kmp_input.returnPressed.connect(self._kmp_search)
        btn_search = make_btn("Rechercher", "primary", "\U0001F50D")
        btn_search.clicked.connect(self._kmp_search)
        sl.addWidget(self.kmp_input, 1); sl.addWidget(btn_search)
        layout.addWidget(search_bar)

        self.carnet_status = QLabel("Entrez un mot-cle pour trouver rapidement une consultation.")
        self.carnet_status.setStyleSheet(f"color: {C_TEXT_SEC}; font-size: 13px; margin-bottom: 10px;")
        layout.addWidget(self.carnet_status)

        self.carnet_table = TableWithEmpty(["Date", "Heure", "Medecin", "Motif", "Diagnostic", "Observations", "Traitement"], "carnet")
        layout.addWidget(self.carnet_table, 1)
        return page

    def _refresh_carnet(self):
        self._load_consultations()

    def _load_consultations(self, search_query=""):
        consults = PatientModel.get_consultations(self.patient['id'])
        if search_query:
            consults = search_medical_history(consults, search_query)
            self.carnet_status.setText(f"{len(consults)} resultat(s) trouve(s)")
        else:
            self.carnet_status.setText("Entrez un mot-cle pour trouver rapidement une consultation.")
        data = []
        for c in consults:
            data.append([
                c.get('date_consultation',''), c.get('heure_consultation',''),
                f"{c.get('medecin_prenom','')} {c.get('medecin_nom','')}",
                c.get('motif',''), c.get('diagnostic',''),
                c.get('observations',''), c.get('traitement','')
            ])
        self.carnet_table.set_data(data)

    def _kmp_search(self):
        query = self.kmp_input.text().strip()
        self._load_consultations(query)

    # ===== MEDECINS =====
    def _build_medecins(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.addWidget(page_title("\U0001FA7A  Mes Medecins"))

        assoc = QWidget()
        al = QHBoxLayout(assoc)
        al.setContentsMargins(0, 0, 0, 12)
        self.assoc_code = QLineEdit()
        self.assoc_code.setPlaceholderText("Entrez le code d'association fourni par votre medecin")
        btn_assoc = make_btn("Valider l'association", "success", "\U00002714")
        btn_assoc.clicked.connect(self._validate_association)
        al.addWidget(self.assoc_code, 1); al.addWidget(btn_assoc)
        layout.addWidget(assoc)

        self.medecins_table = TableWithEmpty(["Medecin", "Specialite", "Etablissement", "Statut", "Telephone", "Action"], "medecins")
        layout.addWidget(self.medecins_table, 1)
        return page

    def _refresh_medecins(self):
        links = PatientModel.get_links(self.patient['id'])
        data = []
        for l in links:
            data.append([f"Dr. {l.get('prenom','')} {l.get('nom','')}", l.get('specialite',''),
                         l.get('etablissement',''), l.get('statut',''), l.get('telephone',''), ""])
        self.medecins_table.set_data(data)
        for r, l in enumerate(links):
            if l.get('statut') == 'actif':
                btn = make_btn("Revoguer", "danger", "\u274C")
                btn.clicked.connect(lambda checked, lid=l['id']: self._revoke_medecin(lid))
                self.medecins_table.table.setCellWidget(r, 5, btn)
            elif l.get('statut') == 'en_attente':
                lbl = QLabel("  \u23F3 En attente de validation")
                lbl.setStyleSheet(f"color: {C_WARNING}; font-weight: 600; padding: 4px;")
                self.medecins_table.table.setCellWidget(r, 5, lbl)

    def _validate_association(self):
        code = self.assoc_code.text().strip()
        if not code:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Erreur", "Entrez un code d'association.")
            return
        if PatientModel.validate_link(code, self.patient['id']):
            self._controller.log_action(self.user['id'], "patient", "VALIDATE_ASSOCIATION", "patient_medecin_links", details=f"code={code}")
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.information(self, "Succes", "Association validee avec succes!")
            self.assoc_code.clear()
            self._refresh_medecins()
        else:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Erreur", "Code invalide ou deja utilise.")

    def _revoke_medecin(self, link_id):
        from PyQt5.QtWidgets import QMessageBox
        if QMessageBox.question(self, "Confirmation", "Revoguer l'acces de ce medecin a votre dossier?",
                                QMessageBox.Yes|QMessageBox.No) == QMessageBox.Yes:
            PatientModel.revoke_link(link_id)
            self._controller.log_action(self.user['id'], "patient", "REVOKE_MEDECIN", "patient_medecin_links", link_id)
            self._refresh_medecins()

    # ===== RENDEZ-VOUS =====
    def _build_rendezvous(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.addWidget(page_title("\U0001F4C5  Mes Rendez-vous"))
        self.rdv_table = TableWithEmpty(["Date", "Heure", "Motif", "Type", "Statut"], "rdv")
        layout.addWidget(self.rdv_table, 1)
        return page

    def _refresh_rdv(self):
        rdvs = PatientModel.get_rendezvous(self.patient['id'])
        data = []
        for r in rdvs:
            data.append([r.get('date_rdv',''), f"{r.get('heure_debut','')} - {r.get('heure_fin','')}",
                         r.get('motif',''), r.get('type',''), r.get('statut','')])
        self.rdv_table.set_data(data)

    # ===== PRESCRIPTIONS =====
    def _build_prescriptions(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.addWidget(page_title("\U0001F48A  Mes Prescriptions"))
        self.presc_table = TableWithEmpty(["Titre", "Contenu", "Medecin", "Date debut", "Date fin", "Statut"], "prescriptions")
        layout.addWidget(self.presc_table, 1)
        return page

    def _refresh_prescriptions(self):
        prescs = PatientModel.get_prescriptions(self.patient['id'])
        data = []
        for p in prescs:
            data.append([p.get('titre',''), p.get('contenu',''),
                         f"Dr. {p.get('medecin_prenom','')} {p.get('medecin_nom','')}",
                         p.get('date_debut',''), p.get('date_fin',''), p.get('statut','')])
        self.presc_table.set_data(data)

    # ===== ALLERGIES =====
    def _build_allergies(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(28, 28, 28, 28)

        title_row = QWidget()
        trl = QHBoxLayout(title_row)
        trl.setContentsMargins(0, 0, 0, 8)
        t = QLabel("\u26A0\uFE0F  Allergies")
        t.setStyleSheet(f"font-size: 24px; font-weight: 800; color: {C_TEXT};")
        trl.addWidget(t); trl.addStretch()
        btn_add = make_btn("Ajouter une allergie", "warning", "\u2795")
        btn_add.clicked.connect(self._add_allergie)
        trl.addWidget(btn_add)
        layout.addWidget(title_row)

        self.allergies_table = TableWithEmpty(["Allergene", "Reaction", "Description", "Date", "Action"], "allergies")
        layout.addWidget(self.allergies_table, 1)
        return page

    def _refresh_allergies(self):
        allergies = PatientModel.get_allergies(self.patient['id'])
        data = []
        for a in allergies:
            data.append([a.get('allergene',''), a.get('type_reaction',''), a.get('description',''),
                         a.get('date_diagnostic','') or a.get('created_at',''), ""])
        self.allergies_table.set_data(data)
        for r, a in enumerate(allergies):
            btn = make_btn("Supprimer", "danger", "\u274C")
            btn.clicked.connect(lambda checked, aid=a['id']: self._delete_allergie(aid))
            self.allergies_table.table.setCellWidget(r, 4, btn)

    def _add_allergie(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Ajouter une allergie")
        dialog.setMinimumWidth(450)
        dialog.setStyleSheet(f"QDialog {{ background: {C_WHITE}; }}")
        layout = QFormLayout(dialog)
        layout.setSpacing(12); layout.setContentsMargins(24, 20, 24, 20)
        allergene = QLineEdit(); allergene.setPlaceholderText("Ex: Penicilline")
        reaction = QComboBox(); reaction.addItems(["legere", "moderee", "severe", "anaphylaxie"])
        description = QTextEdit(); description.setPlaceholderText("Description des symptomes..."); description.setMaximumHeight(80)
        date_diag = QDateEdit(); date_diag.setCalendarPopup(True); date_diag.setDate(QDate.currentDate())
        layout.addRow("Allergene:", allergene); layout.addRow("Reaction:", reaction)
        layout.addRow("Description:", description); layout.addRow("Date diagnostic:", date_diag)
        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btn_box.accepted.connect(dialog.accept); btn_box.rejected.connect(dialog.reject)
        layout.addRow(btn_box)
        if dialog.exec() == QDialog.Accepted and allergene.text().strip():
            PatientModel.create_allergie(self.patient['id'], allergene.text().strip(),
                                         reaction.currentText(), description.toPlainText().strip() or None,
                                         date_diag.date().toString("yyyy-MM-dd"))
            self._controller.log_action(self.user['id'], "patient", "ADD_ALLERGIE", "allergies", details=f"allergene={allergene.text()}")
            self._refresh_allergies()
            self.show_toast("Allergie ajoutee avec succes", "success")

    def _delete_allergie(self, allergy_id):
        from PyQt5.QtWidgets import QMessageBox
        if QMessageBox.question(self, "Confirmation", "Supprimer cette allergie?",
                                QMessageBox.Yes|QMessageBox.No) == QMessageBox.Yes:
            PatientModel.delete_allergie(allergy_id)
            self._controller.log_action(self.user['id'], "patient", "DELETE_ALLERGIE", "allergies", allergy_id)
            self._refresh_allergies()
            self.show_toast("Allergie supprimee", "success")

    # ===== EXAMENS =====
    def _build_examens(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(28, 28, 28, 28)

        title_row = QWidget()
        trl = QHBoxLayout(title_row)
        trl.setContentsMargins(0, 0, 0, 8)
        t = QLabel("\U0001F52C  Examens")
        t.setStyleSheet(f"font-size: 24px; font-weight: 800; color: {C_TEXT};")
        trl.addWidget(t); trl.addStretch()
        btn_add = make_btn("Ajouter un examen", "primary", "\u2795")
        btn_add.clicked.connect(self._add_examen)
        trl.addWidget(btn_add)
        layout.addWidget(title_row)

        self.examens_table = TableWithEmpty(["Type", "Date", "Resultats", "Valeurs"], "examens")
        layout.addWidget(self.examens_table, 1)
        return page

    def _refresh_examens(self):
        examens = PatientModel.get_examens(self.patient['id'])
        data = []
        for e in examens:
            data.append([e.get('type_examen',''), e.get('date_examen',''),
                         e.get('resultats',''), e.get('valeurs','')])
        self.examens_table.set_data(data)

    def _add_examen(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Ajouter un examen")
        dialog.setMinimumWidth(450)
        dialog.setStyleSheet(f"QDialog {{ background: {C_WHITE}; }}")
        layout = QFormLayout(dialog)
        layout.setSpacing(12); layout.setContentsMargins(24, 20, 24, 20)
        type_exam = QLineEdit(); type_exam.setPlaceholderText("IRM, prise de sang, radio...")
        date_exam = QDateEdit(); date_exam.setCalendarPopup(True); date_exam.setDate(QDate.currentDate())
        resultats = QTextEdit(); resultats.setPlaceholderText("Resultats de l'examen..."); resultats.setMaximumHeight(100)
        layout.addRow("Type:", type_exam); layout.addRow("Date:", date_exam)
        layout.addRow("Resultats:", resultats)
        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btn_box.accepted.connect(dialog.accept); btn_box.rejected.connect(dialog.reject)
        layout.addRow(btn_box)
        if dialog.exec() == QDialog.Accepted and type_exam.text().strip():
            PatientModel.create_examen(self.patient['id'], type_exam.text().strip(),
                                       resultats.toPlainText().strip() or None,
                                       date_exam.date().toString("yyyy-MM-dd"))
            self._controller.log_action(self.user['id'], "patient", "ADD_EXAMEN", "examens", details=f"type={type_exam.text()}")
            self._refresh_examens()
            self.show_toast("Examen ajoute avec succes", "success")
