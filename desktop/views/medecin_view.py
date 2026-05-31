from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QStackedWidget, QFrame, QSplitter, QDialog, QFormLayout,
    QTextEdit, QComboBox, QDateEdit, QTimeEdit, QDialogButtonBox,
    QScrollArea, QDoubleSpinBox, QSpinBox
)
from PyQt5.QtCore import Qt, QDate, QTime
from datetime import date

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from views.components import (
    STYLE_BASE, C_BG, C_WHITE, C_PRIMARY, C_PRIMARY_DARK, C_PRIMARY_LIGHT,
    C_SUCCESS, C_DANGER, C_WARNING, C_TEXT, C_TEXT_SEC, C_TEXT_LIGHT, C_BORDER,
    make_btn, page_title, CardWidget, StatCard, Sidebar, TableWithEmpty, ToastNotification
)
from models.medecin_model import MedecinModel
from models.patient_model import PatientModel
from algorithms import (
    search_medical_history, PatientHashTable, Appointment,
    greedy_schedule_optimization, Medicament, optimize_prescriptions_dp
)


class MedecinView(QMainWindow):
    def __init__(self, medecin, user, controller):
        super().__init__()
        self.medecin = medecin
        self.user = user
        self._controller = controller
        self.setWindowTitle(f"Carnet Medical - Dr. {medecin['prenom']} {medecin['nom']}")
        self.setMinimumSize(1200, 750)
        self.setStyleSheet(STYLE_BASE)

        self.patient_cache = PatientHashTable()
        self._init_cache()

        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        profile = QFrame()
        profile.setStyleSheet(f"background: {C_PRIMARY_DARK}; padding: 20px;")
        pl = QVBoxLayout(profile)
        pl.setContentsMargins(16, 20, 16, 20)
        pl.setSpacing(4)
        avatar = QLabel("\U0001FA7A")
        avatar.setStyleSheet("font-size: 40px;")
        pl.addWidget(avatar)
        self.sb_name = QLabel(f"Dr. {medecin['prenom']} {medecin['nom']}")
        self.sb_name.setStyleSheet("font-size: 16px; font-weight: 700; color: white;")
        pl.addWidget(self.sb_name)
        self.sb_spc = QLabel(f"{medecin.get('specialite','')}")
        self.sb_spc.setStyleSheet(f"font-size: 12px; color: #93C5FD;")
        pl.addWidget(self.sb_spc)

        nav_items = [
            ("tableau_bord", "\U0001F4CA  Tableau de bord"),
            ("patients", "\U0001F465  Mes Patients"),
            ("consultations", "\U0001F4CB  Consultations"),
            ("rendezvous", "\U0001F4C5  Rendez-vous"),
            ("prescriptions", "\U0001F48A  Prescriptions"),
            ("recherche", "\U0001F50D  Recherche"),
        ]
        self.sidebar = Sidebar(nav_items, profile)
        self.sidebar.logout_btn.clicked.connect(self._on_logout)
        for key, btn in self.sidebar.nav_buttons.items():
            btn.clicked.connect(lambda checked, k=key: self._show_page(k))
        layout.addWidget(self.sidebar)

        self.content_stack = QStackedWidget()
        self.pages = {}
        creators = [
            ("tableau_bord", self._build_dashboard),
            ("patients", self._build_patients),
            ("consultations", self._build_consultations),
            ("rendezvous", self._build_rendezvous),
            ("prescriptions", self._build_prescriptions),
            ("recherche", self._build_recherche),
        ]
        for key, creator in creators:
            page = creator()
            self.pages[key] = page
            self.content_stack.addWidget(page)
        layout.addWidget(self.content_stack, 1)
        self._show_page("tableau_bord")

    def _init_cache(self):
        patients = MedecinModel.get_all_patients()
        for p in patients:
            self.patient_cache.insert(p.get('numero_dossier',''), p)
            self.patient_cache.insert(str(p['id']), p)

    def _show_page(self, key):
        self.sidebar.set_active(key)
        if key in self.pages:
            self.content_stack.setCurrentWidget(self.pages[key])
            refreshers = {
                "tableau_bord": self._refresh_dashboard,
                "patients": self._refresh_patients,
                "consultations": self._refresh_consultations,
                "rendezvous": self._refresh_rdv,
                "prescriptions": self._refresh_prescriptions,
            }
            if key in refreshers:
                refreshers[key]()

    def _on_logout(self):
        self._controller.logout(self.user['id'], "medecin")

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
        self.dash_badge.setStyleSheet(f"background: {C_PRIMARY_LIGHT}; color: {C_PRIMARY_DARK}; padding: 6px 16px; border-radius: 20px; font-size: 13px; font-weight: 600;")
        hl.addWidget(self.dash_badge); hl.addStretch()
        layout.addWidget(header)
        self.dash_stats = QWidget()
        self.dash_stats.setLayout(QHBoxLayout())
        layout.addWidget(self.dash_stats)
        row2 = QSplitter(Qt.Horizontal)
        quick_card = CardWidget(" Actions rapides")
        self.dash_quick_layout = QVBoxLayout()
        quick_card.layout.addLayout(self.dash_quick_layout)
        row2.addWidget(quick_card)
        info_card = CardWidget(" Informations")
        self.dash_info_layout = QFormLayout()
        info_card.layout.addLayout(self.dash_info_layout)
        row2.addWidget(info_card)
        row2.setSizes([400, 400])
        layout.addWidget(row2, 1)
        return page

    def _refresh_dashboard(self):
        m = self.medecin
        self.dash_welcome.setText(f"Dr. {m['prenom']} {m['nom']} - {m.get('specialite','')}")
        patients = MedecinModel.get_patients(m['id'])
        consults = MedecinModel.get_consultations(m['id'])
        rdvs = MedecinModel.get_rendezvous(m['id'])
        prescs = MedecinModel.get_prescriptions(m['id'])
        today_rdvs = [r for r in rdvs if r.get('date_rdv') == date.today().isoformat()]
        badge = ""
        if today_rdvs:
            badge = f"\U0001F514 {len(today_rdvs)} RDV aujourd'hui"
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
            ("Patients", len(patients), C_PRIMARY, "\U0001F465"),
            ("Consultations", len(consults), C_SUCCESS, "\U0001F4CB"),
            ("Rendez-vous", len(rdvs), C_WARNING, "\U0001F4C5"),
            ("Prescriptions", len(prescs), "#8B5CF6", "\U0001F48A"),
        ]:
            sl.addWidget(StatCard(lbl, val, col, ic))
        old.addWidget(stats_w)
        while self.dash_quick_layout.count():
            w = self.dash_quick_layout.takeAt(0).widget()
            if w: w.deleteLater()
        for txt, cb in [
            ("\U0001F465  Voir mes patients", lambda: self._show_page("patients")),
            ("\U0001F4CB  Nouvelle consultation", lambda: self._show_page("consultations")),
            ("\U0001F4C5  Gerer rendez-vous", lambda: self._show_page("rendezvous")),
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
        info_layout = self.dash_info_layout
        while info_layout.count():
            info_layout.removeRow(info_layout.rowCount() - 1)
        for l, v in [
            ("Specialite", m.get("specialite","")), ("Etablissement", m.get("etablissement","N/A")),
            ("N Ordre", m.get("numero_ordre","")), ("Statut", m.get("statut","")),
            ("Patients actifs", str(len(patients))), ("Consultations", str(len(consults))),
        ]:
            lbl = QLabel(f"<b>{l}:</b>"); lbl.setStyleSheet(f"color: {C_TEXT_SEC};")
            val = QLabel(str(v)); val.setStyleSheet(f"color: {C_TEXT}; font-weight: 500;")
            info_layout.addRow(lbl, val)

    # ===== PATIENTS =====
    def _build_patients(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(28, 28, 28, 28)
        title_row = QWidget()
        trl = QHBoxLayout(title_row)
        trl.setContentsMargins(0, 0, 0, 8)
        t = page_title("\U0001F465  Mes Patients")
        trl.addWidget(t); trl.addStretch()
        layout.addWidget(title_row)

        assoc = QWidget()
        al = QHBoxLayout(assoc)
        al.setContentsMargins(0, 0, 0, 12)
        self.assoc_patient_input = QLineEdit()
        self.assoc_patient_input.setPlaceholderText("ID ou N dossier du patient")
        btn_assoc = make_btn("Demander association", "primary", "\U0001F517")
        btn_assoc.clicked.connect(self._request_association)
        al.addWidget(self.assoc_patient_input, 1); al.addWidget(btn_assoc)
        self.assoc_code_label = QLabel("")
        self.assoc_code_label.setStyleSheet(f"color: {C_SUCCESS}; font-weight: 600; padding: 0 8px;")
        al.addWidget(self.assoc_code_label)
        layout.addWidget(assoc)

        self.patients_table = TableWithEmpty(["Patient", "Dossier", "Naissance", "Telephone", "Statut"], "patients")
        layout.addWidget(self.patients_table, 1)
        return page

    def _refresh_patients(self):
        patients = MedecinModel.get_patients(self.medecin['id'])
        data = []
        for p in patients:
            data.append([f"{p.get('prenom','')} {p.get('nom','')}", p.get('numero_dossier',''),
                         p.get('date_naissance',''), p.get('telephone',''), p.get('statut','')])
        self.patients_table.set_data(data)

    def _request_association(self):
        pid = self.assoc_patient_input.text().strip()
        if not pid:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Erreur", "Entrez l'ID ou le numero de dossier du patient.")
            return
        patient = self.patient_cache.get(pid)
        if not patient:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Erreur", "Patient introuvable. Verifiez l'ID ou le N dossier.")
            return
        try:
            link_id, code = MedecinModel.request_association(patient['id'], self.medecin['id'])
            self._controller.log_action(self.user['id'], "medecin", "REQUEST_ASSOCIATION", "patient_medecin_links", link_id)
            self.assoc_code_label.setText(f"Code: {code}")
            self.assoc_patient_input.clear()
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.information(self, "Association", f"Code d'association genere: {code}\nDonnez ce code au patient.")
        except Exception as e:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Erreur", str(e))

    # ===== CONSULTATIONS =====
    def _build_consultations(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(28, 28, 28, 28)
        title_row = QWidget()
        trl = QHBoxLayout(title_row)
        trl.setContentsMargins(0, 0, 0, 8)
        t = page_title("\U0001F4CB  Consultations")
        trl.addWidget(t); trl.addStretch()
        btn_new = make_btn("Nouvelle consultation", "success", "\u2795")
        btn_new.clicked.connect(self._new_consultation)
        trl.addWidget(btn_new)
        layout.addWidget(title_row)
        self.consults_table = TableWithEmpty(["Patient", "Date", "Heure", "Motif", "Diagnostic", "Statut"], "consultations")
        layout.addWidget(self.consults_table, 1)
        return page

    def _refresh_consultations(self):
        consults = MedecinModel.get_consultations(self.medecin['id'])
        data = []
        for c in consults:
            data.append([f"{c.get('patient_prenom','')} {c.get('patient_nom','')}",
                         c.get('date_consultation',''), c.get('heure_consultation',''),
                         c.get('motif',''), c.get('diagnostic',''), c.get('statut','')])
        self.consults_table.set_data(data)

    def _new_consultation(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Nouvelle consultation")
        dialog.setMinimumWidth(550)
        dialog.setStyleSheet(f"QDialog {{ background: {C_WHITE}; }}")
        layout = QFormLayout(dialog); layout.setSpacing(12); layout.setContentsMargins(24, 20, 24, 20)
        pid_input = QLineEdit(); pid_input.setPlaceholderText("ID du patient")
        date_c = QDateEdit(); date_c.setCalendarPopup(True); date_c.setDate(QDate.currentDate())
        heure_c = QTimeEdit(); heure_c.setTime(QTime.currentTime())
        motif = QTextEdit(); motif.setMaximumHeight(60)
        symptomes = QTextEdit(); symptomes.setMaximumHeight(60)
        diagnostic = QTextEdit(); diagnostic.setMaximumHeight(60)
        observations = QTextEdit(); observations.setMaximumHeight(60)
        traitement = QTextEdit(); traitement.setMaximumHeight(60)
        layout.addRow("Patient ID:", pid_input); layout.addRow("Date:", date_c); layout.addRow("Heure:", heure_c)
        layout.addRow("Motif:", motif); layout.addRow("Symptomes:", symptomes)
        layout.addRow("Diagnostic:", diagnostic); layout.addRow("Observations:", observations)
        layout.addRow("Traitement:", traitement)
        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btn_box.accepted.connect(dialog.accept); btn_box.rejected.connect(dialog.reject)
        layout.addRow(btn_box)
        if dialog.exec() == QDialog.Accepted:
            pid = pid_input.text().strip()
            if not pid or not motif.toPlainText().strip():
                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.warning(self, "Erreur", "Patient ID et motif requis.")
                return
            patient = self.patient_cache.get(pid)
            if not patient:
                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.critical(self, "Erreur", "Patient introuvable.")
                return
            MedecinModel.create_consultation(patient['id'], self.medecin['id'],
                date_c.date().toString("yyyy-MM-dd"), heure_c.time().toString("HH:mm"),
                motif.toPlainText().strip(), symptomes.toPlainText().strip() or None,
                diagnostic.toPlainText().strip() or None, observations.toPlainText().strip() or None,
                traitement.toPlainText().strip() or None)
            self._controller.log_action(self.user['id'], "medecin", "CREATE_CONSULTATION", "consultations", details=f"patient_id={patient['id']}")
            self._refresh_consultations()
            self.show_toast("Consultation creee avec succes", "success")

    # ===== RENDEZ-VOUS =====
    def _build_rendezvous(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(28, 28, 28, 28)
        title_row = QWidget()
        trl = QHBoxLayout(title_row)
        trl.setContentsMargins(0, 0, 0, 8)
        t = page_title("\U0001F4C5  Rendez-vous")
        trl.addWidget(t); trl.addStretch()
        btn_new = make_btn("Nouveau RDV", "primary", "\u2795")
        btn_new.clicked.connect(self._new_rdv)
        btn_opt = make_btn("Optimiser (Glouton)", "success", "\U0001F4CA")
        btn_opt.clicked.connect(self._optimize_rdv)
        trl.addWidget(btn_new); trl.addWidget(btn_opt)
        self.optimize_result = QLabel("")
        self.optimize_result.setStyleSheet(f"color: {C_SUCCESS}; font-weight: 600;")
        trl.addWidget(self.optimize_result, 1)
        layout.addWidget(title_row)
        self.rdv_table = TableWithEmpty(["Patient", "Date", "Heure", "Motif", "Type", "Priorite", "Statut"], "rdv")
        layout.addWidget(self.rdv_table, 1)
        return page

    def _refresh_rdv(self):
        rdvs = MedecinModel.get_rendezvous(self.medecin['id'])
        data = []
        for r in rdvs:
            pat = self.patient_cache.get(str(r.get('patient_id','')))
            nom = f"{pat.get('prenom','')} {pat.get('nom','')}" if pat else f"Patient #{r.get('patient_id','')}"
            data.append([nom, r.get('date_rdv',''), f"{r.get('heure_debut','')} - {r.get('heure_fin','')}",
                         r.get('motif',''), r.get('type',''), str(r.get('priorite','')), r.get('statut','')])
        self.rdv_table.set_data(data)

    def _new_rdv(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Nouveau rendez-vous")
        dialog.setMinimumWidth(480)
        dialog.setStyleSheet(f"QDialog {{ background: {C_WHITE}; }}")
        layout = QFormLayout(dialog); layout.setSpacing(12); layout.setContentsMargins(24, 20, 24, 20)
        pid_input = QLineEdit(); pid_input.setPlaceholderText("ID du patient")
        date_rdv = QDateEdit(); date_rdv.setCalendarPopup(True); date_rdv.setDate(QDate.currentDate())
        heure_deb = QTimeEdit(); heure_deb.setTime(QTime(9, 0))
        heure_fin = QTimeEdit(); heure_fin.setTime(QTime(9, 30))
        motif = QTextEdit(); motif.setMaximumHeight(60)
        type_rdv = QComboBox(); type_rdv.addItems(["consultation", "suivi", "urgence", "examen", "vaccination"])
        priorite = QComboBox(); priorite.addItems(["1 - Normal", "2 - Urgent", "3 - Critique"])
        layout.addRow("Patient ID:", pid_input); layout.addRow("Date:", date_rdv)
        layout.addRow("Heure debut:", heure_deb); layout.addRow("Heure fin:", heure_fin)
        layout.addRow("Motif:", motif); layout.addRow("Type:", type_rdv); layout.addRow("Priorite:", priorite)
        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btn_box.accepted.connect(dialog.accept); btn_box.rejected.connect(dialog.reject)
        layout.addRow(btn_box)
        if dialog.exec() == QDialog.Accepted:
            pid = pid_input.text().strip()
            if not pid or not motif.toPlainText().strip():
                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.warning(self, "Erreur", "Patient ID et motif requis.")
                return
            patient = self.patient_cache.get(pid)
            if not patient:
                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.critical(self, "Erreur", "Patient introuvable.")
                return
            prio = int(priorite.currentText()[0])
            MedecinModel.create_rendezvous(patient['id'], self.medecin['id'],
                date_rdv.date().toString("yyyy-MM-dd"), heure_deb.time().toString("HH:mm"),
                heure_fin.time().toString("HH:mm"), motif.toPlainText().strip(),
                type_rdv.currentText(), prio)
            self._controller.log_action(self.user['id'], "medecin", "CREATE_RDV", "rendez_vous", details=f"patient_id={patient['id']}")
            self._refresh_rdv()
            self.show_toast("Rendez-vous cree avec succes", "success")

    def _optimize_rdv(self):
        rdvs = MedecinModel.get_rendezvous(self.medecin['id'])
        rdvs_today = [r for r in rdvs if r.get('date_rdv') == date.today().isoformat()]
        if not rdvs_today:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.information(self, "Optimisation", "Aucun rendez-vous aujourd'hui.")
            return
        appointments = []
        for r in rdvs_today:
            pat = self.patient_cache.get(str(r.get('patient_id','')))
            nom = f"{pat.get('prenom','')} {pat.get('nom','')}" if pat else ""
            appointments.append(Appointment(
                id=r['id'], heure_debut=r.get('heure_debut',''),
                heure_fin=r.get('heure_fin',''), priorite=r.get('priorite',1),
                motif=r.get('motif',''), patient_nom=nom
            ))
        selected, conflicts = greedy_schedule_optimization(appointments)
        total = len(rdvs_today); opt = len(selected); nb_conflicts = len(conflicts)
        msg = f"Optimisation: {opt}/{total} planifiables"
        if nb_conflicts > 0:
            msg += f" | {nb_conflicts} conflit(s)"
        self.optimize_result.setText(msg)
        from PyQt5.QtWidgets import QMessageBox
        QMessageBox.information(self, "Optimisation gloutonne",
            f"Rendez-vous aujourd'hui: {total}\nPlanifiables: {opt}\nConflits: {nb_conflicts}")

    # ===== PRESCRIPTIONS =====
    def _build_prescriptions(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(28, 28, 28, 28)
        title_row = QWidget()
        trl = QHBoxLayout(title_row)
        trl.setContentsMargins(0, 0, 0, 8)
        t = page_title("\U0001F48A  Prescriptions")
        trl.addWidget(t); trl.addStretch()
        btn_new = make_btn("Nouvelle prescription", "success", "\u2795")
        btn_new.clicked.connect(self._new_prescription)
        btn_opt = make_btn("Optimiser (DP)", "primary", "\U0001F4CA")
        btn_opt.clicked.connect(self._optimize_presc)
        trl.addWidget(btn_new); trl.addWidget(btn_opt)
        layout.addWidget(title_row)
        self.presc_table = TableWithEmpty(["Patient", "Titre", "Contenu", "Date debut", "Date fin", "Statut"], "prescriptions")
        layout.addWidget(self.presc_table, 1)
        return page

    def _refresh_prescriptions(self):
        prescs = MedecinModel.get_prescriptions(self.medecin['id'])
        data = []
        for p in prescs:
            data.append([f"{p.get('patient_prenom','')} {p.get('patient_nom','')}",
                         p.get('titre',''), p.get('contenu',''),
                         p.get('date_debut',''), p.get('date_fin',''), p.get('statut','')])
        self.presc_table.set_data(data)

    def _new_prescription(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Nouvelle prescription")
        dialog.setMinimumWidth(550)
        dialog.setStyleSheet(f"QDialog {{ background: {C_WHITE}; }}")
        layout = QFormLayout(dialog); layout.setSpacing(12); layout.setContentsMargins(24, 20, 24, 20)
        pid_input = QLineEdit(); pid_input.setPlaceholderText("ID du patient")
        titre = QLineEdit(); titre.setPlaceholderText("Titre de la prescription")
        contenu = QTextEdit(); contenu.setMaximumHeight(80)
        instructions = QTextEdit(); instructions.setMaximumHeight(60)
        date_deb = QDateEdit(); date_deb.setCalendarPopup(True); date_deb.setDate(QDate.currentDate())
        date_fin = QDateEdit(); date_fin.setCalendarPopup(True); date_fin.setDate(QDate.currentDate().addDays(30))
        layout.addRow("Patient ID:", pid_input); layout.addRow("Titre:", titre)
        layout.addRow("Contenu:", contenu); layout.addRow("Instructions:", instructions)
        layout.addRow("Date debut:", date_deb); layout.addRow("Date fin:", date_fin)
        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btn_box.accepted.connect(dialog.accept); btn_box.rejected.connect(dialog.reject)
        layout.addRow(btn_box)
        if dialog.exec() == QDialog.Accepted:
            pid = pid_input.text().strip()
            if not pid or not titre.text().strip() or not contenu.toPlainText().strip():
                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.warning(self, "Erreur", "Champs obligatoires manquants.")
                return
            patient = self.patient_cache.get(pid)
            if not patient:
                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.critical(self, "Erreur", "Patient introuvable.")
                return
            MedecinModel.create_prescription(patient['id'], self.medecin['id'],
                titre.text().strip(), contenu.toPlainText().strip(),
                instructions=instructions.toPlainText().strip() or None,
                date_debut=date_deb.date().toString("yyyy-MM-dd"),
                date_fin=date_fin.date().toString("yyyy-MM-dd"))
            self._controller.log_action(self.user['id'], "medecin", "CREATE_PRESCRIPTION", "prescriptions",
                                        details=f"patient_id={patient['id']}, titre={titre.text()}")
            self._refresh_prescriptions()
            self.show_toast("Prescription creee avec succes", "success")

    def _optimize_presc(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Optimisation DP des prescriptions")
        dialog.setMinimumWidth(550)
        dialog.setStyleSheet(f"QDialog {{ background: {C_WHITE}; }}")
        layout = QVBoxLayout(dialog); layout.setContentsMargins(24, 20, 24, 20); layout.setSpacing(12)
        layout.addWidget(QLabel("Programmation dynamique - Sac a dos 0/1"))
        layout.addWidget(QLabel("Ajoutez des medicaments avec leur cout et efficacite:"))
        med_list = QWidget()
        med_layout = QVBoxLayout(med_list)
        med_entries = []

        def add_med(nom="", cout=0, eff=0, duree=30):
            row = QWidget(); rl = QHBoxLayout(row); rl.setContentsMargins(0, 2, 0, 2)
            e_nom = QLineEdit(nom); e_nom.setPlaceholderText("Medicament")
            e_cout = QDoubleSpinBox(); e_cout.setRange(0, 10000); e_cout.setValue(cout); e_cout.setPrefix("Ar ")
            e_eff = QSpinBox(); e_eff.setRange(0, 100); e_eff.setValue(eff)
            e_dur = QSpinBox(); e_dur.setRange(1, 365); e_dur.setValue(duree)
            rl.addWidget(e_nom, 2); rl.addWidget(QLabel("Cout:")); rl.addWidget(e_cout)
            rl.addWidget(QLabel("Eff:")); rl.addWidget(e_eff); rl.addWidget(QLabel("Jrs:")); rl.addWidget(e_dur)
            med_layout.addWidget(row)
            med_entries.append((e_nom, e_cout, e_eff, e_dur))

        add_med("Paracetamol", 5, 7, 30); add_med("Ibuprofene", 8, 9, 15)
        add_med("Amoxicilline", 15, 10, 7); add_med("Vitamine C", 3, 4, 30); add_med("Omeprazole", 12, 8, 30)
        scroll = QScrollArea(); scroll.setWidget(med_list); scroll.setWidgetResizable(True); scroll.setMaximumHeight(250)
        layout.addWidget(scroll)
        budget_w = QWidget(); bl = QHBoxLayout(budget_w)
        budget_spin = QDoubleSpinBox(); budget_spin.setRange(1, 100000); budget_spin.setValue(30); budget_spin.setPrefix("Ar ")
        bl.addWidget(QLabel("Budget max:")); bl.addWidget(budget_spin); bl.addStretch()
        layout.addWidget(budget_w)
        result_area = QTextEdit(); result_area.setReadOnly(True); result_area.setMaximumHeight(140)
        result_area.setStyleSheet(f"background: {C_PRIMARY_LIGHT}; border: 2px solid {C_PRIMARY}; border-radius: 12px; padding: 8px;")
        layout.addWidget(result_area)
        btn_calc = make_btn("Optimiser (DP Sac a dos)", "primary", "\U0001F4CA")
        btn_calc.clicked.connect(lambda: self._run_dp(med_entries, budget_spin, result_area))
        layout.addWidget(btn_calc)
        btn_close = QPushButton("Fermer"); btn_close.setObjectName("btnOutline")
        btn_close.clicked.connect(dialog.accept)
        layout.addWidget(btn_close)
        dialog.exec()

    def _run_dp(self, entries, budget_spin, result_area):
        medicaments = []
        for e_nom, e_cout, e_eff, e_dur in entries:
            nom = e_nom.text().strip()
            if nom:
                medicaments.append(Medicament(nom, e_cout.value(), e_eff.value(), e_dur.value()))
        if not medicaments:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Erreur", "Ajoutez au moins un medicament.")
            return
        result = optimize_prescriptions_dp(medicaments, budget_spin.value())
        selected = result['selected']
        if not selected:
            result_area.setText("Aucun medicament selectionne dans le budget.")
            return
        lines = [f"=== Optimisation DP ===", f"Budget: Ar {budget_spin.value():.0f}", f"Medicaments ({len(selected)}):"]
        for m in selected:
            lines.append(f"  - {m.nom}: Ar {m.cout:.0f} (eff: {m.efficacite}, {m.duree_jours}j)")
        lines.append(f"Cout: Ar {result['total_cost']:.0f}")
        lines.append(f"Efficacite: {result['total_efficacy']}")
        lines.append(f"Budget utilise: {result['budget_used']:.0f}%")
        lines.append("Complexite: O(n x W)")
        result_area.setText("\n".join(lines))

    # ===== RECHERCHE =====
    def _build_recherche(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.addWidget(page_title("\U0001F50D  Recherche Medicale"))
        subtitle = QLabel("Trouvez rapidement une consultation dans l'historique de vos patients.")
        subtitle.setStyleSheet(f"color: {C_TEXT_SEC}; font-size: 13px; margin-bottom: 18px;")
        layout.addWidget(subtitle)
        search_bar = QWidget()
        sl = QHBoxLayout(search_bar)
        sl.setContentsMargins(0, 0, 0, 12)
        self.kmp_search_input = QLineEdit()
        self.kmp_search_input.setPlaceholderText("Motif, diagnostic, symptomes...")
        self.kmp_search_input.returnPressed.connect(self._kmp_search)
        btn_search = make_btn("Rechercher", "primary", "\U0001F50D")
        btn_search.clicked.connect(self._kmp_search)
        sl.addWidget(self.kmp_search_input, 1); sl.addWidget(btn_search)
        layout.addWidget(search_bar)
        self.kmp_result_label = QLabel("Entrez un terme de recherche.")
        self.kmp_result_label.setStyleSheet(f"color: {C_TEXT_SEC}; font-size: 13px; margin-bottom: 12px;")
        layout.addWidget(self.kmp_result_label)
        self.kmp_table = TableWithEmpty(["Patient", "Date", "Heure", "Motif", "Diagnostic", "Observations", "Traitement"], "default")
        layout.addWidget(self.kmp_table, 1)
        return page

    def _kmp_search(self):
        query = self.kmp_search_input.text().strip()
        if not query:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Recherche", "Entrez un terme de recherche.")
            return
        patients = MedecinModel.get_patients(self.medecin['id'])
        all_results = []
        for pat in patients:
            consults = PatientModel.get_consultations(pat['id'])
            results = search_medical_history(consults, query)
            for r in results:
                r['_patient_name'] = f"{pat.get('prenom','')} {pat.get('nom','')}"
                all_results.append(r)
        data = []
        for c in all_results:
            data.append([c.get('_patient_name',''), c.get('date_consultation',''),
                         c.get('heure_consultation',''), c.get('motif',''),
                         c.get('diagnostic',''), c.get('observations',''), c.get('traitement','')])
        self.kmp_table.set_data(data)
        self.kmp_result_label.setText(f"{len(all_results)} resultat(s) trouves")
