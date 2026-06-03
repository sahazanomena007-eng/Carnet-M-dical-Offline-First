from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QStackedWidget, QFrame, QDialog, QFormLayout,
    QTextEdit, QComboBox, QDateEdit, QTimeEdit, QDialogButtonBox,
    QScrollArea, QDoubleSpinBox, QSpinBox, QMessageBox
)
from PyQt5.QtCore import Qt, QDate, QTime
from datetime import date

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from views.components import (
    STYLE_BASE, C_BG, C_WHITE, C_PRIMARY, C_PRIMARY_DARK, C_PRIMARY_LIGHT,
    C_SUCCESS, C_DANGER, C_WARNING, C_TEXT, C_TEXT_SEC, C_TEXT_LIGHT, C_BORDER,
    C_SUCCESS_LIGHT, C_DANGER_LIGHT, C_WARNING_LIGHT, C_INFO_LIGHT, C_PURPLE,
    CARD_STYLE, add_shadow, QColor,
    make_btn, page_title, section_title, CardWidget, StatCard, Sidebar,
    TableWithEmpty, ToastNotification, StatusBadge
)
from models.medecin_model import MedecinModel
from models.patient_model import PatientModel
from algorithms import (
    search_medical_history, PatientHashTable, Appointment,
    greedy_schedule_optimization, Medicament, optimize_prescriptions_dp,
    levenshtein_distance, fuzzy_search, BinarySearchTree,
)
import db


class MedecinView(QMainWindow):
    def __init__(self, medecin, user, controller):
        super().__init__()
        self.medecin = medecin
        self.user = user
        self._controller = controller
        self.setWindowTitle(f"Carnet Médical - Dr. {medecin['prenom']} {medecin['nom']} (Médecin)")
        self.setMinimumSize(1260, 780)
        self.setStyleSheet(STYLE_BASE)

        self.patient_cache = PatientHashTable()
        self._init_cache()

        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        profile = self._make_profile()
        nav_items = [
            ("tableau_bord", "Tableau de bord", "📊"),
            ("patients", "Mes Patients", "👥"),
            ("consultations", "Consultations", "🩺"),
            ("rendezvous", "Rendez-vous", "📅"),
            ("prescriptions", "Prescriptions", "💊"),
            ("recherche", "Recherche", "🔍"),
        ]
        self.sidebar = Sidebar(nav_items, profile)
        self.sidebar.logout_btn.clicked.connect(self._on_logout)
        for key, btn in self.sidebar.nav_buttons.items():
            btn.clicked.connect(lambda checked, k=key: self._show_page(k))
        layout.addWidget(self.sidebar)

        self.content_stack = QStackedWidget()
        builders = [
            ("tableau_bord", self._build_dashboard),
            ("patients", self._build_patients),
            ("consultations", self._build_consultations),
            ("rendezvous", self._build_rendezvous),
            ("prescriptions", self._build_prescriptions),
            ("recherche", self._build_recherche),
        ]
        self.pages = {}
        for key, builder in builders:
            p = builder()
            self.pages[key] = p
            self.content_stack.addWidget(p)
        layout.addWidget(self.content_stack, 1)
        self._show_page("tableau_bord")

    def _make_profile(self):
        m = self.medecin
        w = QFrame()
        w.setStyleSheet(f"background: linear-gradient(180deg, {C_PRIMARY_DARK}, #0B4B8A);")
        l = QVBoxLayout(w)
        l.setContentsMargins(16, 24, 16, 20)
        l.setSpacing(4)

        avatar = QFrame()
        avatar.setFixedSize(56, 56)
        avatar.setStyleSheet("background: rgba(255,255,255,0.15); border-radius: 14px; border: 2px solid rgba(255,255,255,0.3);")
        av_l = QVBoxLayout(avatar)
        av_l.setAlignment(Qt.AlignCenter)
        av_t = QLabel("👨‍⚕️")
        av_t.setStyleSheet("font-size: 24px;")
        av_l.addWidget(av_t)
        l.addWidget(avatar, alignment=Qt.AlignCenter)

        self.sb_name = QLabel(f"Dr. {m['prenom']} {m['nom']}")
        self.sb_name.setStyleSheet("font-size: 15px; font-weight: 700; color: white;")
        self.sb_name.setAlignment(Qt.AlignCenter)
        l.addWidget(self.sb_name)

        self.sb_spc = QLabel(m.get('specialite', ''))
        self.sb_spc.setStyleSheet("font-size: 11px; color: rgba(255,255,255,0.6);")
        self.sb_spc.setAlignment(Qt.AlignCenter)
        l.addWidget(self.sb_spc)

        return w

    def _init_cache(self):
        patients = MedecinModel.get_all_patients()
        for p in patients:
            self.patient_cache.insert(p.get('numero_dossier', ''), p)
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
        t = ToastNotification(self.content_stack, message, type)
        t.show()
        t.setGeometry(self.content_stack.width() - 370, 16, 350, 52)

    def _page_container(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(28, 28, 28, 28)
        l.setSpacing(16)
        return w, l

    # ======================== DASHBOARD ========================
    def _build_dashboard(self):
        page, layout = self._page_container()

        header = QWidget()
        hl = QHBoxLayout(header)
        hl.setContentsMargins(0, 0, 0, 8)
        self.dash_welcome = QLabel()
        self.dash_welcome.setStyleSheet(f"font-size: 26px; font-weight: 800; color: {C_TEXT};")
        hl.addWidget(self.dash_welcome)
        hl.addStretch()
        self.dash_badge = QLabel()
        hl.addWidget(self.dash_badge)
        layout.addWidget(header)

        self.dash_stats_container = QWidget()
        self.dash_stats_container.setLayout(QHBoxLayout())
        layout.addWidget(self.dash_stats_container)

        gre = QWidget()
        gl = QHBoxLayout(gre)
        gl.setContentsMargins(0, 0, 0, 0)
        gl.setSpacing(16)

        quick_card = CardWidget("Actions rapides")
        self.dash_quick_layout = QVBoxLayout()
        quick_card.layout.addLayout(self.dash_quick_layout)
        gl.addWidget(quick_card, 1)

        info_card = CardWidget("Informations")
        self.dash_info_layout = QFormLayout()
        info_card.layout.addLayout(self.dash_info_layout)
        gl.addWidget(info_card, 1)

        layout.addWidget(gre, 1)
        return page

    def _refresh_dashboard(self):
        m = self.medecin
        self.dash_welcome.setText(f"Dr. {m['prenom']} {m['nom']} 👨‍⚕️")
        mid = m['id']
        patients = MedecinModel.get_patients(mid)
        consults = MedecinModel.get_consultations(mid)
        rdvs = MedecinModel.get_rendezvous(mid)
        prescs = MedecinModel.get_prescriptions(mid)
        today_rdvs = [r for r in rdvs if r.get('date_rdv') == date.today().isoformat()]

        badge = ""
        if today_rdvs:
            badge = f"🔔 {len(today_rdvs)} RDV aujourd'hui"
        self.dash_badge.setText(badge)
        self.dash_badge.setStyleSheet(f"""
            background: {C_INFO_LIGHT}; color: #0369A1; padding: 7px 18px;
            border-radius: 20px; font-size: 13px; font-weight: 600;
        """ if badge else "")
        self.dash_badge.setVisible(bool(badge))

        old = self.dash_stats_container.layout()
        while old.count():
            w = old.takeAt(0).widget()
            if w: w.deleteLater()
        stats_w = QWidget()
        sl = QHBoxLayout(stats_w)
        sl.setSpacing(14)
        for lbl, val, col in [
            ("Patients", len(patients), C_PRIMARY),
            ("Consultations", len(consults), C_SUCCESS),
            ("Rendez-vous", len(rdvs), C_WARNING),
            ("Prescriptions", len(prescs), "#8B5CF6"),
        ]:
            sl.addWidget(StatCard(lbl, val, col))
        old.addWidget(stats_w)

        while self.dash_quick_layout.count():
            w = self.dash_quick_layout.takeAt(0).widget()
            if w: w.deleteLater()
        for txt, cb in [
            ("👥  Voir mes patients", lambda: self._show_page("patients")),
            ("🩺  Nouvelle consultation", lambda: self._show_page("consultations")),
            ("📅  Gérer les rendez-vous", lambda: self._show_page("rendezvous")),
        ]:
            btn = make_btn(txt, "outline")
            btn.setMinimumHeight(48)
            btn.clicked.connect(cb)
            self.dash_quick_layout.addWidget(btn)

        info_l = self.dash_info_layout
        while info_l.count():
            info_l.removeRow(0)
        for l, v in [
            ("Spécialité", m.get("specialite", "")),
            ("Établissement", m.get("etablissement", "N/A")),
            ("N° Ordre", m.get("numero_ordre", "")),
            ("Statut", m.get("statut", "")),
            ("Patients actifs", str(len(patients))),
            ("Consultations", str(len(consults))),
        ]:
            lbl = QLabel(l)
            lbl.setStyleSheet(f"font-weight: 600; color: {C_TEXT_SEC}; font-size: 13px;")
            val = QLabel(str(v))
            val.setStyleSheet(f"font-weight: 500; color: {C_TEXT}; font-size: 13px;")
            info_l.addRow(lbl, val)

    # ======================== PATIENTS ========================
    def _build_patients(self):
        page, layout = self._page_container()

        header = QWidget()
        hl = QHBoxLayout(header)
        hl.setContentsMargins(0, 0, 0, 0)
        hl.addWidget(page_title("Mes Patients"))
        hl.addStretch()
        layout.addWidget(header)

        assoc = QWidget()
        al = QHBoxLayout(assoc)
        al.setContentsMargins(0, 0, 0, 0)
        self.assoc_patient_input = QLineEdit()
        self.assoc_patient_input.setPlaceholderText("🔗  ID ou N° dossier du patient")
        btn_assoc = make_btn("Demander association", "primary")
        btn_assoc.clicked.connect(self._request_association)
        al.addWidget(self.assoc_patient_input, 1)
        al.addSpacing(8)
        al.addWidget(btn_assoc)
        layout.addWidget(assoc)

        fuzzy = QWidget()
        fl = QHBoxLayout(fuzzy)
        fl.setContentsMargins(0, 0, 0, 0)
        fl.addWidget(QLabel("🔍  Recherche floue (Levenshtein):"))
        self.fuzzy_search_input = QLineEdit()
        self.fuzzy_search_input.setPlaceholderText("Nom du patient...")
        self.fuzzy_search_input.textChanged.connect(self._filter_fuzzy)
        fl.addWidget(self.fuzzy_search_input, 1)
        self.fuzzy_threshold = QComboBox()
        self.fuzzy_threshold.addItems(["1", "2", "3", "4"])
        self.fuzzy_threshold.setCurrentIndex(2)
        self.fuzzy_threshold.currentIndexChanged.connect(self._filter_fuzzy)
        fl.addWidget(QLabel("Seuil:"))
        fl.addWidget(self.fuzzy_threshold)
        layout.addWidget(fuzzy)

        self.patients_table = TableWithEmpty(
            ["Patient", "Dossier", "Naissance", "Téléphone", "Statut", "Action"],
            "patients"
        )
        layout.addWidget(self.patients_table, 1)
        return page

    def _filter_fuzzy(self):
        query = self.fuzzy_search_input.text().strip()
        threshold = int(self.fuzzy_threshold.currentText())
        all_patients = MedecinModel.get_patients(self.medecin['id'])
        if not query:
            self._display_patients(all_patients)
            return
        texts = [f"{p.get('prenom', '')} {p.get('nom', '')}".lower() for p in all_patients]
        indices = fuzzy_search(query, texts, threshold)
        self._display_patients([all_patients[i] for i in indices])

    def _display_patients(self, patients):
        data = [[
            f"{p.get('prenom', '')} {p.get('nom', '')}",
            p.get('numero_dossier', ''),
            p.get('date_naissance', ''),
            p.get('telephone', ''),
            p.get('statut', ''),
            ""
        ] for p in patients]
        self.patients_table.set_data(data)
        for r, p in enumerate(patients):
            btn = make_btn("Voir dossier", "primary", "sm")
            btn.clicked.connect(lambda checked, pid=p['id']: self._show_patient_dossier(pid))
            self.patients_table.table.setCellWidget(r, 5, btn)

    def _refresh_patients(self):
        self._display_patients(MedecinModel.get_patients(self.medecin['id']))

    def _request_association(self):
        pid = self.assoc_patient_input.text().strip()
        if not pid:
            QMessageBox.warning(self, "Erreur", "Entrez l'ID ou le numéro de dossier du patient.")
            return
        patient = self.patient_cache.get(pid)
        if not patient:
            QMessageBox.critical(self, "Erreur", "Patient introuvable. Vérifiez l'ID ou le N° dossier.")
            return
        try:
            link_id, _ = MedecinModel.request_association(patient['id'], self.medecin['id'])
            self._controller.log_action(self.user['id'], "medecin", "REQUEST_ASSOCIATION",
                                        "patient_medecin_links", link_id)
            self.assoc_patient_input.clear()
            QMessageBox.information(self, "Association",
                                    "Demande envoyée au patient — il doit l'accepter depuis son compte.")
        except Exception as e:
            QMessageBox.critical(self, "Erreur", str(e))

    def _show_patient_dossier(self, patient_id):
        patient = PatientModel.get_patient(patient_id=patient_id)
        if not patient:
            QMessageBox.critical(self, "Erreur", "Patient introuvable.")
            return
        age = db.calcul_age(patient.get('date_naissance', ''))
        consults = PatientModel.get_consultations(patient_id)
        prescs = PatientModel.get_prescriptions(patient_id)
        allergies = PatientModel.get_allergies(patient_id)
        vaccins = PatientModel.get_vaccins(patient_id)
        rdvs = PatientModel.get_rendezvous(patient_id)

        d = QDialog(self)
        d.setWindowTitle(f"Dossier - {patient.get('prenom', '')} {patient.get('nom', '')}")
        d.setMinimumSize(760, 540)
        d.setStyleSheet(f"QDialog {{ background: {C_WHITE}; }}")
        l = QVBoxLayout(d)
        l.setContentsMargins(24, 24, 24, 24)
        l.setSpacing(12)

        title = QLabel(f"Dossier de {patient.get('prenom', '')} {patient.get('nom', '')}")
        title.setStyleSheet(f"font-size: 22px; font-weight: 800; color: {C_TEXT};")
        l.addWidget(title)

        info = QWidget()
        infol = QHBoxLayout(info)
        infol.setSpacing(20)
        for lbl, v in [
            ("N° Dossier", patient.get('numero_dossier', '')),
            ("Âge", f"{age} ans"),
            ("Groupe", patient.get('groupe_sanguin', 'N/A')),
            ("Vaccins", str(len(vaccins))),
        ]:
            lb = QLabel(f"<b>{lbl}:</b> {v}")
            lb.setStyleSheet(f"color: {C_TEXT}; font-size: 13px;")
            infol.addWidget(lb)
        l.addWidget(info)

        if patient.get('antecedents_personnels'):
            mal = QLabel(f"⚠️  {patient['antecedents_personnels']}")
            mal.setStyleSheet(f"background: {C_WARNING_LIGHT}; color: #92400E; border-radius: 8px; padding: 10px 14px; font-size: 13px; font-weight: 500;")
            l.addWidget(mal)

        tabs = QWidget()
        tabs_layout = QVBoxLayout(tabs)
        tabs_layout.setSpacing(6)

        cons_label = QLabel(f"🩺  Consultations ({len(consults)}):")
        cons_label.setStyleSheet(f"font-size: 14px; font-weight: 700; color: {C_PRIMARY};")
        tabs_layout.addWidget(cons_label)
        for c in consults[:5]:
            lb = QLabel(f"  • {c.get('date_consultation', '')} {c.get('heure_consultation', '')} | {c.get('motif', '')}")
            lb.setStyleSheet(f"color: {C_TEXT_SEC}; font-size: 12px;")
            tabs_layout.addWidget(lb)
        if len(consults) > 5:
            more = QLabel(f"  ... et {len(consults) - 5} autre(s)")
            more.setStyleSheet(f"color: {C_TEXT_LIGHT}; font-size: 11px; font-style: italic;")
            tabs_layout.addWidget(more)

        all_label = QLabel(f"⚠️  Allergies ({len(allergies)}):")
        all_label.setStyleSheet(f"font-size: 14px; font-weight: 700; color: {C_DANGER}; margin-top: 6px;")
        tabs_layout.addWidget(all_label)
        for a in allergies:
            lb = QLabel(f"  • {a.get('allergene', '')} ({a.get('type_reaction', '')})")
            lb.setStyleSheet(f"color: {C_TEXT_SEC}; font-size: 12px;")
            tabs_layout.addWidget(lb)

        vac_label = QLabel(f"💉  Vaccins ({len(vaccins)}):")
        vac_label.setStyleSheet(f"font-size: 14px; font-weight: 700; color: #10B981; margin-top: 6px;")
        tabs_layout.addWidget(vac_label)
        for v in vaccins:
            lb = QLabel(f"  • {v.get('type_examen', '')} ({v.get('date_examen', '')})")
            lb.setStyleSheet(f"color: {C_TEXT_SEC}; font-size: 12px;")
            tabs_layout.addWidget(lb)

        scroll = QScrollArea()
        scroll.setWidget(tabs)
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none;")
        l.addWidget(scroll, 1)

        btn_row = QWidget()
        brl = QHBoxLayout(btn_row)
        brl.setContentsMargins(0, 0, 0, 0)
        for txt, cb in [
            ("📄  Ordonnance PDF", lambda: self._export_ordo_pdf(patient, prescs)),
            ("📄  Certificat PDF", lambda: self._export_certificat_pdf(patient, consults)),
            ("📄  Carnet Vaccinal PDF", lambda: self._export_carnet_vaccinal_pdf(patient, vaccins)),
        ]:
            btn = make_btn(txt, "primary", "sm")
            btn.clicked.connect(cb)
            brl.addWidget(btn)
        brl.addStretch()
        btn_close = QPushButton("Fermer")
        btn_close.clicked.connect(d.accept)
        btn_close.setStyleSheet(f"""
            QPushButton {{ background: {C_WHITE}; color: {C_TEXT_SEC};
                border: 1.5px solid {C_BORDER}; border-radius: 10px;
                padding: 9px 20px; font-weight: 600; font-size: 13px; }}
            QPushButton:hover {{ background: {C_PRIMARY_LIGHT}; color: {C_PRIMARY}; }}
        """)
        brl.addWidget(btn_close)
        l.addWidget(btn_row)
        d.exec()

    # ======================== CONSULTATIONS ========================
    def _build_consultations(self):
        page, layout = self._page_container()

        header = QWidget()
        hl = QHBoxLayout(header)
        hl.setContentsMargins(0, 0, 0, 0)
        hl.addWidget(page_title("Consultations"))
        hl.addStretch()
        btn_new = make_btn("+ Nouvelle consultation", "success")
        btn_new.clicked.connect(self._new_consultation)
        hl.addWidget(btn_new)
        layout.addWidget(header)

        filter_row = QWidget()
        fl = QHBoxLayout(filter_row)
        fl.setContentsMargins(0, 0, 0, 0)
        fl.addWidget(QLabel("Filtrer (BST):"))
        self.filter_date_debut = QDateEdit()
        self.filter_date_debut.setCalendarPopup(True)
        self.filter_date_debut.setDate(QDate(2024, 1, 1))
        fl.addWidget(self.filter_date_debut)
        fl.addWidget(QLabel("→"))
        self.filter_date_fin = QDateEdit()
        self.filter_date_fin.setCalendarPopup(True)
        self.filter_date_fin.setDate(QDate.currentDate())
        fl.addWidget(self.filter_date_fin)
        btn_filter = make_btn("Appliquer", "primary", "sm")
        btn_filter.clicked.connect(self._refresh_consultations)
        fl.addWidget(btn_filter)
        btn_pdf = make_btn("📄 Export PDF", "outline", "sm")
        btn_pdf.clicked.connect(self._export_consultations_pdf)
        fl.addWidget(btn_pdf)
        self.filter_count_label = QLabel("")
        self.filter_count_label.setStyleSheet(f"color: {C_TEXT_SEC}; font-size: 12px;")
        fl.addWidget(self.filter_count_label)
        fl.addStretch()
        layout.addWidget(filter_row)

        self.consults_table = TableWithEmpty(
            ["Patient", "Date", "Heure", "Motif", "Diagnostic", "Statut"],
            "consultations"
        )
        layout.addWidget(self.consults_table, 1)
        return page

    def _refresh_consultations(self):
        consults = MedecinModel.get_consultations(self.medecin['id'])
        debut = self.filter_date_debut.date().toString("yyyy-MM-dd")
        fin = self.filter_date_fin.date().toString("yyyy-MM-dd")
        bst = BinarySearchTree()
        for c in consults:
            bst.insert(c.get('date_consultation', '1900-01-01'), c)
        filtered = bst.range_search(debut, fin)
        data = [[
            f"{c.get('patient_prenom', '')} {c.get('patient_nom', '')}",
            c.get('date_consultation', ''), c.get('heure_consultation', ''),
            c.get('motif', ''), c.get('diagnostic', ''), c.get('statut', '')
        ] for c in filtered]
        self.consults_table.set_data(data)
        self.filter_count_label.setText(f"{len(filtered)}/{len(consults)} consultations")

    def _export_consultations_pdf(self):
        try:
            from fpdf import FPDF
            consults = MedecinModel.get_consultations(self.medecin['id'])
            debut = self.filter_date_debut.date().toString("yyyy-MM-dd")
            fin = self.filter_date_fin.date().toString("yyyy-MM-dd")
            bst = BinarySearchTree()
            for c in consults:
                bst.insert(c.get('date_consultation', '1900-01-01'), c)
            filtered = bst.range_search(debut, fin)
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Helvetica", "B", 16)
            pdf.cell(0, 10, "Liste des Consultations", new_x="LMARGIN", new_y="NEXT", align="C")
            pdf.set_font("Helvetica", "", 10)
            pdf.cell(0, 8, f"Filtre: {debut} → {fin}", new_x="LMARGIN", new_y="NEXT")
            pdf.ln(4)
            col_w = [40, 25, 50, 50]
            pdf.set_font("Helvetica", "B", 10)
            for i, h in enumerate(["Date", "Patient", "Motif", "Diagnostic"]):
                pdf.cell(col_w[i], 8, h, border=1)
            pdf.ln()
            pdf.set_font("Helvetica", "", 9)
            for c in filtered:
                pdf.cell(col_w[0], 7, str(c.get('date_consultation', ''))[:10], border=1)
                pdf.cell(col_w[1], 7, f"{c.get('patient_prenom', '')} {c.get('patient_nom', '')}"[:15], border=1)
                pdf.cell(col_w[2], 7, (c.get('motif', '') or '')[:25], border=1)
                pdf.cell(col_w[3], 7, (c.get('diagnostic', '') or '')[:25], border=1)
                pdf.ln()
            pdf.output(f"consultations_{debut}_{fin}.pdf")
            self.show_toast(f"PDF exporté: {len(filtered)} consultations", "success")
        except Exception as e:
            QMessageBox.critical(self, "Erreur PDF", str(e))

    def _new_consultation(self):
        d = QDialog(self)
        d.setWindowTitle("Nouvelle consultation")
        d.setMinimumWidth(560)
        d.setStyleSheet(f"QDialog {{ background: {C_WHITE}; }}")
        l = QFormLayout(d)
        l.setSpacing(10); l.setContentsMargins(24, 20, 24, 20)

        patients_list = MedecinModel.get_patients(self.medecin['id'])
        patient_combo = QComboBox()
        patient_combo.addItem("-- Sélectionner un patient --", None)
        for p in patients_list:
            patient_combo.addItem(f"{p.get('prenom', '')} {p.get('nom', '')} (N°{p.get('numero_dossier', '')})", p.get('id'))
        date_c = QDateEdit(); date_c.setCalendarPopup(True); date_c.setDate(QDate.currentDate())
        heure_c = QTimeEdit(); heure_c.setTime(QTime.currentTime())
        motif = QTextEdit(); motif.setMaximumHeight(60)
        symptomes = QTextEdit(); symptomes.setMaximumHeight(60)
        diagnostic = QTextEdit(); diagnostic.setMaximumHeight(60)
        observations = QTextEdit(); observations.setMaximumHeight(60)
        traitement = QTextEdit(); traitement.setMaximumHeight(60)

        l.addRow("Patient:", patient_combo); l.addRow("Date:", date_c); l.addRow("Heure:", heure_c)
        l.addRow("Motif:", motif); l.addRow("Symptômes:", symptomes)
        l.addRow("Diagnostic:", diagnostic); l.addRow("Observations:", observations)
        l.addRow("Traitement:", traitement)

        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(d.accept); btns.rejected.connect(d.reject)
        l.addRow(btns)

        if d.exec() == QDialog.Accepted:
            patient_id = patient_combo.currentData()
            if not patient_id or not motif.toPlainText().strip():
                QMessageBox.warning(self, "Erreur", "Sélectionnez un patient et un motif.")
                return
            MedecinModel.create_consultation(
                patient_id, self.medecin['id'],
                date_c.date().toString("yyyy-MM-dd"), heure_c.time().toString("HH:mm"),
                motif.toPlainText().strip(), symptomes.toPlainText().strip() or None,
                diagnostic.toPlainText().strip() or None, observations.toPlainText().strip() or None,
                traitement.toPlainText().strip() or None
            )
            db.create_notification(patient_id, "consultation_ajoutee", "Nouvelle consultation",
                                   f"Consultation ajoutée le {date_c.date().toString('yyyy-MM-dd')}")
            self._controller.log_action(self.user['id'], "medecin", "CREATE_CONSULTATION",
                                        "consultations", details=f"patient_id={patient_id}")
            self._refresh_consultations()
            self.show_toast("Consultation créée avec succès (notification envoyée)", "success")

    # ======================== RENDEZ-VOUS ========================
    def _build_rendezvous(self):
        page, layout = self._page_container()

        header = QWidget()
        hl = QHBoxLayout(header)
        hl.setContentsMargins(0, 0, 0, 0)
        hl.addWidget(page_title("Rendez-vous"))
        hl.addStretch()
        btn_new = make_btn("+ Nouveau RDV", "primary")
        btn_new.clicked.connect(self._new_rdv)
        btn_opt = make_btn("⚡ Optimiser (Glouton)", "success")
        btn_opt.clicked.connect(self._optimize_rdv)
        hl.addWidget(btn_new)
        hl.addWidget(btn_opt)
        self.optimize_result = QLabel("")
        self.optimize_result.setStyleSheet(f"color: {C_SUCCESS}; font-weight: 600; font-size: 13px;")
        hl.addWidget(self.optimize_result)
        layout.addWidget(header)

        self.rdv_table = TableWithEmpty(
            ["Patient", "Date", "Horaire", "Motif", "Type", "Priorité", "Statut"],
            "rdv"
        )
        layout.addWidget(self.rdv_table, 1)
        return page

    def _refresh_rdv(self):
        rdvs = MedecinModel.get_rendezvous(self.medecin['id'])
        data = []
        for r in rdvs:
            pat = self.patient_cache.get(str(r.get('patient_id', '')))
            nom = f"{pat.get('prenom', '')} {pat.get('nom', '')}" if pat else f"Patient #{r.get('patient_id', '')}"
            data.append([
                nom, r.get('date_rdv', ''),
                f"{r.get('heure_debut', '')} - {r.get('heure_fin', '')}",
                r.get('motif', ''), r.get('type', ''),
                str(r.get('priorite', '')), r.get('statut', '')
            ])
        self.rdv_table.set_data(data)

    def _new_rdv(self):
        d = QDialog(self)
        d.setWindowTitle("Nouveau rendez-vous")
        d.setMinimumWidth(540)
        d.setStyleSheet(f"QDialog {{ background: {C_WHITE}; }}")
        l = QFormLayout(d)
        l.setSpacing(10); l.setContentsMargins(24, 20, 24, 20)

        patients_list = MedecinModel.get_patients(self.medecin['id'])
        patient_combo = QComboBox()
        patient_combo.addItem("-- Sélectionner un patient --", None)
        for p in patients_list:
            patient_combo.addItem(f"{p.get('prenom', '')} {p.get('nom', '')} (N°{p.get('numero_dossier', '')})", p.get('id'))
        date_rdv = QDateEdit(); date_rdv.setCalendarPopup(True); date_rdv.setDate(QDate.currentDate())
        heure_deb = QTimeEdit(); heure_deb.setTime(QTime(9, 0))
        heure_fin = QTimeEdit(); heure_fin.setTime(QTime(9, 30))
        motif = QTextEdit(); motif.setMaximumHeight(60)
        type_rdv = QComboBox(); type_rdv.addItems(["consultation", "suivi", "urgence", "examen", "vaccination"])
        priorite = QComboBox(); priorite.addItems(["1 - Normal", "2 - Urgent", "3 - Critique"])

        l.addRow("Patient:", patient_combo); l.addRow("Date:", date_rdv)
        l.addRow("Début:", heure_deb); l.addRow("Fin:", heure_fin)
        l.addRow("Motif:", motif); l.addRow("Type:", type_rdv); l.addRow("Priorité:", priorite)

        actions = QWidget()
        actions_layout = QHBoxLayout(actions)
        actions_layout.setContentsMargins(0, 0, 0, 0)
        actions_layout.setSpacing(10)

        btn_save = QPushButton("Enregistrer")
        btn_save.setCursor(Qt.PointingHandCursor)
        btn_save.setStyleSheet(f"background: {C_PRIMARY}; color: white; border: none; padding: 10px 18px; border-radius: 10px; font-weight: 700;")
        btn_cancel = QPushButton("Annuler")
        btn_cancel.setCursor(Qt.PointingHandCursor)
        btn_cancel.setStyleSheet(f"background: #F3F4F6; color: {C_TEXT}; border: none; padding: 10px 18px; border-radius: 10px; font-weight: 600;")
        actions_layout.addWidget(btn_save)
        actions_layout.addWidget(btn_cancel)
        l.addRow(actions)

        def save_rdv():
            patient_id = patient_combo.currentData()
            if not patient_id or not motif.toPlainText().strip():
                QMessageBox.warning(d, "Erreur", "Sélectionnez un patient et un motif.")
                return
            prio = int(priorite.currentText().split(" ")[0])
            MedecinModel.create_rendezvous(
                patient_id, self.medecin['id'],
                date_rdv.date().toString("yyyy-MM-dd"),
                heure_deb.time().toString("HH:mm"), heure_fin.time().toString("HH:mm"),
                motif.toPlainText().strip(), type_rdv.currentText(), prio
            )
            db.create_notification(patient_id, "rdv_confirm", "Nouveau rendez-vous",
                                   f"Rendez-vous le {date_rdv.date().toString('yyyy-MM-dd')} à {heure_deb.time().toString('HH:mm')}")
            self._controller.log_action(self.user['id'], "medecin", "CREATE_RDV",
                                        "rendez_vous", details=f"patient_id={patient_id}")
            self._refresh_rdv()
            self.show_toast("Rendez-vous créé avec succès (notification envoyée)", "success")
            d.accept()

        btn_save.clicked.connect(save_rdv)
        btn_cancel.clicked.connect(d.reject)

        d.exec()

    def _optimize_rdv(self):
        rdvs = MedecinModel.get_rendezvous(self.medecin['id'])
        rdvs_today = [r for r in rdvs if r.get('date_rdv') == date.today().isoformat()]
        if not rdvs_today:
            QMessageBox.information(self, "Optimisation", "Aucun rendez-vous aujourd'hui.")
            return
        appointments = []
        for r in rdvs_today:
            pat = self.patient_cache.get(str(r.get('patient_id', '')))
            nom = f"{pat.get('prenom', '')} {pat.get('nom', '')}" if pat else ""
            appointments.append(Appointment(
                id=r['id'], heure_debut=r.get('heure_debut', ''),
                heure_fin=r.get('heure_fin', ''), priorite=r.get('priorite', 1),
                motif=r.get('motif', ''), patient_nom=nom
            ))
        selected, conflicts = greedy_schedule_optimization(appointments)
        total = len(rdvs_today)
        opt = len(selected)
        msg = f"⚡ Optimisation: {opt}/{total} planifiables"
        if conflicts:
            msg += f" | {len(conflicts)} conflit(s)"
        self.optimize_result.setText(msg)
        QMessageBox.information(self, "Optimisation gloutonne",
                                f"Rendez-vous aujourd'hui: {total}\nPlanifiables: {opt}\nConflits: {len(conflicts)}")

    # ======================== PRESCRIPTIONS ========================
    def _build_prescriptions(self):
        page, layout = self._page_container()

        header = QWidget()
        hl = QHBoxLayout(header)
        hl.setContentsMargins(0, 0, 0, 0)
        hl.addWidget(page_title("Prescriptions"))
        hl.addStretch()
        btn_new = make_btn("+ Nouvelle prescription", "success")
        btn_new.clicked.connect(self._new_prescription)
        btn_opt = make_btn("🧮 Optimiser (DP)", "primary")
        btn_opt.clicked.connect(self._optimize_presc)
        hl.addWidget(btn_new); hl.addWidget(btn_opt)
        layout.addWidget(header)

        self.presc_table = TableWithEmpty(
            ["Patient", "Titre", "Contenu", "Date début", "Date fin", "Statut"],
            "prescriptions"
        )
        layout.addWidget(self.presc_table, 1)
        return page

    def _refresh_prescriptions(self):
        prescs = MedecinModel.get_prescriptions(self.medecin['id'])
        data = [[
            f"{p.get('patient_prenom', '')} {p.get('patient_nom', '')}",
            p.get('titre', ''), p.get('contenu', ''),
            p.get('date_debut', ''), p.get('date_fin', ''), p.get('statut', '')
        ] for p in prescs]
        self.presc_table.set_data(data)

    def _new_prescription(self):
        d = QDialog(self)
        d.setWindowTitle("Nouvelle prescription")
        d.setMinimumWidth(560)
        d.setStyleSheet(f"QDialog {{ background: {C_WHITE}; }}")
        l = QFormLayout(d)
        l.setSpacing(10); l.setContentsMargins(24, 20, 24, 20)

        pid_input = QLineEdit(); pid_input.setPlaceholderText("ID ou N° dossier du patient")
        titre = QLineEdit(); titre.setPlaceholderText("Titre de la prescription")
        contenu = QTextEdit(); contenu.setMaximumHeight(80)
        instructions = QTextEdit(); instructions.setMaximumHeight(60)
        date_deb = QDateEdit(); date_deb.setCalendarPopup(True); date_deb.setDate(QDate.currentDate())
        date_fin = QDateEdit(); date_fin.setCalendarPopup(True)
        date_fin.setDate(QDate.currentDate().addDays(30))

        l.addRow("Patient ID:", pid_input); l.addRow("Titre:", titre)
        l.addRow("Contenu:", contenu); l.addRow("Instructions:", instructions)
        l.addRow("Début:", date_deb); l.addRow("Fin:", date_fin)

        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(d.accept); btns.rejected.connect(d.reject)
        l.addRow(btns)

        if d.exec() == QDialog.Accepted:
            pid = pid_input.text().strip()
            if not pid or not titre.text().strip() or not contenu.toPlainText().strip():
                QMessageBox.warning(self, "Erreur", "Champs obligatoires manquants.")
                return
            patient = self.patient_cache.get(pid)
            if not patient:
                QMessageBox.critical(self, "Erreur", "Patient introuvable.")
                return
            MedecinModel.create_prescription(
                patient['id'], self.medecin['id'],
                titre.text().strip(), contenu.toPlainText().strip(),
                instructions=instructions.toPlainText().strip() or None,
                date_debut=date_deb.date().toString("yyyy-MM-dd"),
                date_fin=date_fin.date().toString("yyyy-MM-dd")
            )
            self._controller.log_action(self.user['id'], "medecin", "CREATE_PRESCRIPTION",
                                        "prescriptions", details=f"patient_id={patient['id']}, titre={titre.text()}")
            self._refresh_prescriptions()
            self.show_toast("Prescription créée avec succès", "success")

    def _optimize_presc(self):
        d = QDialog(self)
        d.setWindowTitle("Optimisation DP des prescriptions")
        d.setMinimumWidth(580)
        d.setStyleSheet(f"QDialog {{ background: {C_WHITE}; }}")
        l = QVBoxLayout(d)
        l.setContentsMargins(24, 20, 24, 20)
        l.setSpacing(12)

        l.addWidget(QLabel("🧮  Programmation dynamique — Sac à dos 0/1"))
        l.addWidget(QLabel("Ajoutez des médicaments avec leur coût et efficacité :"))

        med_list = QWidget()
        med_layout = QVBoxLayout(med_list)
        med_layout.setSpacing(6)
        med_entries = []

        def add_med(nom="", cout=0, eff=0, duree=30):
            row = QWidget()
            rl = QHBoxLayout(row)
            rl.setContentsMargins(0, 2, 0, 2)
            e_nom = QLineEdit(nom)
            e_nom.setPlaceholderText("Médicament")
            e_cout = QDoubleSpinBox()
            e_cout.setRange(0, 10000); e_cout.setValue(cout); e_cout.setPrefix("Ar ")
            e_eff = QSpinBox(); e_eff.setRange(0, 100); e_eff.setValue(eff)
            e_dur = QSpinBox(); e_dur.setRange(1, 365); e_dur.setValue(duree)
            rl.addWidget(e_nom, 2)
            rl.addWidget(QLabel("Coût:")); rl.addWidget(e_cout)
            rl.addWidget(QLabel("Eff:")); rl.addWidget(e_eff)
            rl.addWidget(QLabel("Jrs:")); rl.addWidget(e_dur)
            med_layout.addWidget(row)
            med_entries.append((e_nom, e_cout, e_eff, e_dur))

        add_med("Paracétamol", 5, 7, 30)
        add_med("Ibuprofène", 8, 9, 15)
        add_med("Amoxicilline", 15, 10, 7)
        add_med("Vitamine C", 3, 4, 30)
        add_med("Oméprazole", 12, 8, 30)

        scroll = QScrollArea()
        scroll.setWidget(med_list)
        scroll.setWidgetResizable(True)
        scroll.setMaximumHeight(220)
        scroll.setStyleSheet("border: none;")
        l.addWidget(scroll)

        budget_w = QWidget()
        bl = QHBoxLayout(budget_w)
        bl.setContentsMargins(0, 0, 0, 0)
        budget_spin = QDoubleSpinBox()
        budget_spin.setRange(1, 100000); budget_spin.setValue(30); budget_spin.setPrefix("Ar ")
        bl.addWidget(QLabel("Budget max:")); bl.addWidget(budget_spin); bl.addStretch()
        l.addWidget(budget_w)

        result_area = QTextEdit()
        result_area.setReadOnly(True)
        result_area.setMaximumHeight(150)
        result_area.setStyleSheet(f"background: {C_PRIMARY_LIGHT}; border: 2px solid {C_PRIMARY}; border-radius: 12px; padding: 10px; font-size: 12px;")
        l.addWidget(result_area)

        btn_calc = make_btn("🧮  Optimiser (DP Sac à dos)", "primary")
        btn_calc.clicked.connect(lambda: self._run_dp(med_entries, budget_spin, result_area))
        l.addWidget(btn_calc)

        btn_close = QPushButton("Fermer")
        btn_close.setStyleSheet(f"""
            QPushButton {{ background: {C_WHITE}; color: {C_TEXT_SEC};
                border: 1.5px solid {C_BORDER}; border-radius: 10px;
                padding: 9px 20px; font-weight: 600; }}
            QPushButton:hover {{ background: {C_PRIMARY_LIGHT}; color: {C_PRIMARY}; }}
        """)
        btn_close.clicked.connect(d.accept)
        l.addWidget(btn_close)
        d.exec()

    def _run_dp(self, entries, budget_spin, result_area):
        medicaments = []
        for e_nom, e_cout, e_eff, e_dur in entries:
            nom = e_nom.text().strip()
            if nom:
                medicaments.append(Medicament(nom, e_cout.value(), e_eff.value(), e_dur.value()))
        if not medicaments:
            QMessageBox.warning(self, "Erreur", "Ajoutez au moins un médicament.")
            return
        result = optimize_prescriptions_dp(medicaments, budget_spin.value())
        selected = result['selected']
        if not selected:
            result_area.setText("Aucun médicament sélectionné dans le budget.")
            return
        lines = [
            "═══ Résultat DP (Sac à dos 0/1) ═══",
            f"Budget: Ar {budget_spin.value():.0f}",
            f"Médicaments retenus ({len(selected)}):",
        ]
        for m in selected:
            lines.append(f"  • {m.nom}: Ar {m.cout:.0f} (eff: {m.efficacite}, {m.duree_jours}j)")
        lines.append(f"Coût total: Ar {result['total_cost']:.0f}")
        lines.append(f"Efficacité totale: {result['total_efficacy']}")
        lines.append(f"Budget utilisé: {result['budget_used']:.0f}%")
        result_area.setText("\n".join(lines))

    # ======================== PDF EXPORTS ========================
    def _export_ordo_pdf(self, patient, prescs):
        try:
            from fpdf import FPDF
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Helvetica", "B", 16)
            pdf.cell(0, 10, "ORDONNANCE MÉDICALE", new_x="LMARGIN", new_y="NEXT", align="C")
            pdf.set_font("Helvetica", "", 10)
            pdf.cell(0, 7, f"Dr. {self.medecin['prenom']} {self.medecin['nom']}", new_x="LMARGIN", new_y="NEXT")
            pdf.cell(0, 7, f"Patient: {patient.get('prenom', '')} {patient.get('nom', '')} — N°{patient.get('numero_dossier', '')}", new_x="LMARGIN", new_y="NEXT")
            pdf.cell(0, 7, f"Date: {date.today().isoformat()}", new_x="LMARGIN", new_y="NEXT")
            pdf.ln(4)
            pdf.set_font("Helvetica", "B", 12)
            for i, pr in enumerate(prescs, 1):
                pdf.cell(0, 7, f"{i}. {pr.get('titre', '')}", new_x="LMARGIN", new_y="NEXT")
                pdf.set_font("Helvetica", "", 10)
                contenu = pr.get('contenu', '') or ''
                for line in contenu.split('\n')[:3]:
                    pdf.cell(0, 6, line, new_x="LMARGIN", new_y="NEXT")
                pdf.cell(0, 6, f"Durée: {pr.get('date_debut', '')} → {pr.get('date_fin', '')}", new_x="LMARGIN", new_y="NEXT")
                pdf.set_font("Helvetica", "B", 12)
            pdf.ln(10)
            pdf.cell(0, 10, "Signature du médecin:", new_x="LMARGIN", new_y="NEXT")
            pdf.output(f"ordonnance_{patient.get('nom', '')}_{patient.get('prenom', '')}.pdf")
            self.show_toast("Ordonnance PDF exportée", "success")
        except Exception as e:
            QMessageBox.critical(self, "Erreur PDF", str(e))

    def _export_certificat_pdf(self, patient, consults):
        try:
            from fpdf import FPDF
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Helvetica", "B", 16)
            pdf.cell(0, 10, "CERTIFICAT MÉDICAL", new_x="LMARGIN", new_y="NEXT", align="C")
            pdf.set_font("Helvetica", "", 11)
            pdf.cell(0, 8, "Je soussigné, médecin traitant, certifie avoir examiné le patient :", new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("Helvetica", "B", 12)
            pdf.cell(0, 8, f"{patient.get('prenom', '')} {patient.get('nom', '')} — Né(e) le {patient.get('date_naissance', '')}", new_x="LMARGIN", new_y="NEXT")
            pdf.ln(4)
            pdf.set_font("Helvetica", "", 11)
            pdf.cell(0, 7, "Motifs de consultation récents :", new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("Helvetica", "", 9)
            for c in consults[:5]:
                pdf.cell(0, 6, f"  • {c.get('date_consultation', '')[:10]}: {c.get('motif', '')}", new_x="LMARGIN", new_y="NEXT")
                if c.get('diagnostic'):
                    pdf.cell(0, 5, f"    Diag: {c.get('diagnostic', '')}", new_x="LMARGIN", new_y="NEXT")
            pdf.ln(8)
            pdf.set_font("Helvetica", "", 11)
            pdf.cell(0, 7, "Ce certificat est délivré pour faire valoir ce que de droit.", new_x="LMARGIN", new_y="NEXT")
            pdf.cell(0, 7, f"Fait à Antananarivo, le {date.today().isoformat()}", new_x="LMARGIN", new_y="NEXT")
            pdf.ln(10)
            pdf.cell(0, 10, "Signature et cachet du médecin :", new_x="LMARGIN", new_y="NEXT")
            pdf.output(f"certificat_{patient.get('nom', '')}_{patient.get('prenom', '')}.pdf")
            self.show_toast("Certificat PDF exporté", "success")
        except Exception as e:
            QMessageBox.critical(self, "Erreur PDF", str(e))

    def _export_carnet_vaccinal_pdf(self, patient, vaccins):
        try:
            from fpdf import FPDF
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Helvetica", "B", 16)
            pdf.cell(0, 10, "CARNET DE VACCINATION", new_x="LMARGIN", new_y="NEXT", align="C")
            pdf.set_font("Helvetica", "", 11)
            pdf.cell(0, 7, f"Patient: {patient.get('prenom', '')} {patient.get('nom', '')}", new_x="LMARGIN", new_y="NEXT")
            pdf.cell(0, 7, f"N° Dossier: {patient.get('numero_dossier', '')}", new_x="LMARGIN", new_y="NEXT")
            pdf.cell(0, 7, f"Date naissance: {patient.get('date_naissance', '')}", new_x="LMARGIN", new_y="NEXT")
            pdf.ln(4)
            if vaccins:
                col_w = [60, 40, 60]
                pdf.set_font("Helvetica", "B", 10)
                for i, h in enumerate(["Vaccin", "Date", "Résultat"]):
                    pdf.cell(col_w[i], 8, h, border=1)
                pdf.ln()
                pdf.set_font("Helvetica", "", 9)
                for v in vaccins:
                    pdf.cell(col_w[0], 7, str(v.get('type_examen', ''))[:25], border=1)
                    pdf.cell(col_w[1], 7, str(v.get('date_examen', '') or '')[:10], border=1)
                    pdf.cell(col_w[2], 7, (v.get('resultat', '') or 'N/R')[:25], border=1)
                    pdf.ln()
            else:
                pdf.cell(0, 7, "Aucun vaccin enregistré.", new_x="LMARGIN", new_y="NEXT")
            pdf.output(f"carnet_vaccinal_{patient.get('nom', '')}_{patient.get('prenom', '')}.pdf")
            self.show_toast("Carnet vaccinal PDF exporté", "success")
        except Exception as e:
            QMessageBox.critical(self, "Erreur PDF", str(e))

    # ======================== RECHERCHE ========================
    def _build_recherche(self):
        page, layout = self._page_container()
        layout.addWidget(page_title("Recherche Médicale"))

        subtitle = QLabel("Trouvez rapidement une consultation dans l'historique de vos patients.")
        subtitle.setStyleSheet(f"color: {C_TEXT_SEC}; font-size: 13px;")
        layout.addWidget(subtitle)

        search_bar = QWidget()
        sl = QHBoxLayout(search_bar)
        sl.setContentsMargins(0, 8, 0, 0)
        self.kmp_search_input = QLineEdit()
        self.kmp_search_input.setPlaceholderText("🔍  Motif, diagnostic, symptômes...")
        self.kmp_search_input.returnPressed.connect(self._kmp_search)
        btn_search = make_btn("Rechercher", "primary")
        btn_search.clicked.connect(self._kmp_search)
        sl.addWidget(self.kmp_search_input, 1)
        sl.addSpacing(8)
        sl.addWidget(btn_search)
        layout.addWidget(search_bar)

        self.kmp_result_label = QLabel("Entrez un terme de recherche.")
        self.kmp_result_label.setStyleSheet(f"color: {C_TEXT_SEC}; font-size: 13px;")
        layout.addWidget(self.kmp_result_label)

        self.kmp_table = TableWithEmpty(
            ["Patient", "Date", "Heure", "Motif", "Diagnostic", "Observations", "Traitement"],
            "default"
        )
        layout.addWidget(self.kmp_table, 1)
        return page

    def _kmp_search(self):
        query = self.kmp_search_input.text().strip()
        if not query:
            QMessageBox.warning(self, "Recherche", "Entrez un terme de recherche.")
            return
        patients = MedecinModel.get_patients(self.medecin['id'])
        all_results = []
        for pat in patients:
            consults = PatientModel.get_consultations(pat['id'])
            results = search_medical_history(consults, query)
            for r in results:
                r['_patient_name'] = f"{pat.get('prenom', '')} {pat.get('nom', '')}"
                all_results.append(r)
        data = [[
            c.get('_patient_name', ''), c.get('date_consultation', ''),
            c.get('heure_consultation', ''), c.get('motif', ''),
            c.get('diagnostic', ''), c.get('observations', ''), c.get('traitement', '')
        ] for c in all_results]
        self.kmp_table.set_data(data)
        self.kmp_result_label.setText(f"{len(all_results)} résultat(s) trouvé(s)")
