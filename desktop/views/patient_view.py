from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QStackedWidget, QFrame, QDialog, QFormLayout,
    QTextEdit, QComboBox, QDateEdit, QTimeEdit, QDialogButtonBox,
    QHeaderView, QMessageBox
)
from PyQt5.QtCore import Qt, QDate, QTime
from datetime import date

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from views.components import (
    STYLE_BASE, C_BG, C_WHITE, C_PRIMARY, C_PRIMARY_DARK, C_PRIMARY_LIGHT,
    C_SUCCESS, C_DANGER, C_WARNING, C_TEXT, C_TEXT_SEC, C_TEXT_LIGHT, C_BORDER,
    C_SUCCESS_LIGHT, C_DANGER_LIGHT, C_WARNING_LIGHT, C_INFO_LIGHT,
    CARD_STYLE, add_shadow, QColor,
    make_btn, page_title, section_title, CardWidget, StatCard, Sidebar,
    TableWithEmpty, ToastNotification, StatusBadge
)
from models.patient_model import PatientModel
from algorithms import search_medical_history
import db


class PatientView(QMainWindow):
    def __init__(self, patient, user, controller):
        super().__init__()
        self.patient = patient
        self.user = user
        self._controller = controller
        self.setWindowTitle(f"Carnet Médical - {patient['prenom']} {patient['nom']} (Patient)")
        self.setMinimumSize(1260, 780)
        self.setStyleSheet(STYLE_BASE)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        profile = self._make_profile()
        nav_items = [
            ("tableau_bord", "Tableau de bord", "📊"),
            ("carnet", "Mon Carnet", "📋"),
            ("medecins", "Mes Médecins", "👨‍⚕️"),
            ("rendezvous", "Rendez-vous", "📅"),
            ("prescriptions", "Prescriptions", "💊"),
            ("allergies", "Allergies", "⚠️"),
            ("examens", "Examens", "🔬"),
        ]
        self.sidebar = Sidebar(nav_items, profile)
        self.sidebar.logout_btn.clicked.connect(self._on_logout)
        for key, btn in self.sidebar.nav_buttons.items():
            btn.clicked.connect(lambda checked, k=key: self._show_page(k))
        layout.addWidget(self.sidebar)

        self.content_stack = QStackedWidget()
        builders = [
            ("tableau_bord", self._build_dashboard),
            ("carnet", self._build_carnet),
            ("medecins", self._build_medecins),
            ("rendezvous", self._build_rendezvous),
            ("prescriptions", self._build_prescriptions),
            ("allergies", self._build_allergies),
            ("examens", self._build_examens),
        ]
        self.pages = {}
        for key, builder in builders:
            p = builder()
            self.pages[key] = p
            self.content_stack.addWidget(p)
        layout.addWidget(self.content_stack, 1)
        self._show_page("tableau_bord")

    def _make_profile(self):
        p = self.patient
        w = QFrame()
        w.setStyleSheet(f"background: linear-gradient(180deg, {C_PRIMARY_DARK}, #0B4B8A);")
        l = QVBoxLayout(w)
        l.setContentsMargins(16, 24, 16, 20)
        l.setSpacing(4)

        avatar = QFrame()
        avatar.setFixedSize(56, 56)
        avatar.setStyleSheet(f"""
            background: rgba(255,255,255,0.15); border-radius: 14px;
            border: 2px solid rgba(255,255,255,0.3);
        """)
        av_l = QVBoxLayout(avatar)
        av_l.setAlignment(Qt.AlignCenter)
        av_t = QLabel("👤")
        av_t.setStyleSheet("font-size: 24px;")
        av_l.addWidget(av_t)
        l.addWidget(avatar, alignment=Qt.AlignCenter)

        self.sb_name = QLabel(f"{p['prenom']} {p['nom']}")
        self.sb_name.setStyleSheet("font-size: 15px; font-weight: 700; color: white;")
        self.sb_name.setAlignment(Qt.AlignCenter)
        l.addWidget(self.sb_name)

        self.sb_dos = QLabel(f"Dossier: {p.get('numero_dossier','N/A')}")
        self.sb_dos.setStyleSheet("font-size: 11px; color: rgba(255,255,255,0.6);")
        self.sb_dos.setAlignment(Qt.AlignCenter)
        l.addWidget(self.sb_dos)

        return w

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
        self.dash_welcome.setStyleSheet(f"font-size: 26px; font-weight: 800; color: {C_TEXT}; letter-spacing: -0.3px;")
        hl.addWidget(self.dash_welcome)
        hl.addStretch()
        self.dash_badge = QLabel()
        hl.addWidget(self.dash_badge)
        layout.addWidget(header)

        self.dash_stats_container = QWidget()
        self.dash_stats_container.setLayout(QHBoxLayout())
        layout.addWidget(self.dash_stats_container)

        info_card = CardWidget("Informations personnelles")
        self.dash_info_widget = QWidget()
        self.dash_info_widget.setLayout(QFormLayout())
        info_card.layout.addWidget(self.dash_info_widget)
        layout.addWidget(info_card)

        return page

    def _refresh_dashboard(self):
        p = self.patient
        self.dash_welcome.setText(f"Bonjour, {p['prenom']} 👋")
        pid = p['id']
        consults = PatientModel.get_consultations(pid)
        prescs = PatientModel.get_prescriptions(pid)
        rdvs = PatientModel.get_rendezvous(pid)
        allergies = PatientModel.get_allergies(pid)
        links = PatientModel.get_links(pid)
        vaccins = PatientModel.get_vaccins(pid)
        notifs = PatientModel.get_notifications(self.user['id'])
        age = PatientModel.calcul_age(p.get('date_naissance', ''))
        today_rdvs = [r for r in rdvs if r.get('date_rdv') == date.today().isoformat()]

        badge_parts = []
        if today_rdvs:
            badge_parts.append(f"🔔 {len(today_rdvs)} RDV aujourd'hui")
        elif rdvs:
            badge_parts.append(f"Prochain: {rdvs[0].get('date_rdv', '')}")
        unread = sum(1 for n in notifs if not n.get('lu'))
        if unread:
            badge_parts.append(f"📬 {unread} notification(s)")
        self.dash_badge.setText(" | ".join(badge_parts))
        self.dash_badge.setStyleSheet(f"""
            background: {C_INFO_LIGHT}; color: #0369A1; padding: 7px 18px;
            border-radius: 20px; font-size: 13px; font-weight: 600;
        """ if badge_parts else "")
        self.dash_badge.setVisible(bool(badge_parts))

        old = self.dash_stats_container.layout()
        while old.count():
            w = old.takeAt(0).widget()
            if w:
                w.deleteLater()
        stats_w = QWidget()
        sl = QHBoxLayout(stats_w)
        sl.setSpacing(14)
        for lbl, val, col in [
            ("Consultations", len(consults), C_PRIMARY),
            ("Prescriptions", len(prescs), C_SUCCESS),
            ("Rendez-vous", len(rdvs), C_WARNING),
            ("Allergies", len(allergies), C_DANGER),
            ("Médecins liés", len(links), "#8B5CF6"),
            ("Vaccins", len(vaccins), "#10B981"),
        ]:
            sl.addWidget(StatCard(lbl, val, col))
        old.addWidget(stats_w)

        info_l = self.dash_info_widget.layout()
        while info_l.rowCount():
            info_l.removeRow(0)

        age_str = f"{age} ans" if age else "N/A"
        rows = [
            ("ID Patient", f"#{p['id']}  ·  {p.get('numero_dossier', 'N/A')}"),
            ("Âge", age_str),
            ("Date naissance", p.get("date_naissance", "N/A")),
            ("Sexe", "Masculin" if p.get("sexe") == "M" else "Féminin"),
            ("Groupe sanguin", p.get("groupe_sanguin", "N/A")),
            ("Taille", f'{p.get("taille_cm", "")} cm' if p.get("taille_cm") else "N/A"),
            ("Poids", f'{p.get("poids_kg", "")} kg' if p.get("poids_kg") else "N/A"),
            ("Téléphone", p.get("telephone", "N/A")),
            ("Antécédents", p.get("antecedents_personnels", "Aucun")),
            ("Vaccins", f"{len(vaccins)} enregistré(s)"),
        ]
        for lbl, val in rows:
            l = QLabel(lbl)
            l.setStyleSheet(f"font-weight: 600; color: {C_TEXT_SEC}; font-size: 13px;")
            v = QLabel(str(val))
            v.setStyleSheet(f"font-weight: 500; color: {C_TEXT}; font-size: 13px;")
            info_l.addRow(l, v)

    # ======================== CARNET ========================
    def _build_carnet(self):
        page, layout = self._page_container()
        layout.addWidget(page_title("Mon Carnet Médical"))

        search_bar = QWidget()
        sl = QHBoxLayout(search_bar)
        sl.setContentsMargins(0, 0, 0, 0)
        self.kmp_input = QLineEdit()
        self.kmp_input.setPlaceholderText("🔍  Rechercher dans l'historique médical...")
        btn_search = make_btn("Rechercher", "primary")
        btn_search.clicked.connect(self._kmp_search)
        sl.addWidget(self.kmp_input, 1)
        sl.addSpacing(8)
        sl.addWidget(btn_search)
        layout.addWidget(search_bar)

        self.carnet_status = QLabel("Entrez un mot-clé pour retrouver rapidement une consultation.")
        self.carnet_status.setStyleSheet(f"color: {C_TEXT_SEC}; font-size: 13px;")
        layout.addWidget(self.carnet_status)

        self.carnet_table = TableWithEmpty(
            ["Date", "Heure", "Médecin", "Motif", "Diagnostic", "Observations", "Traitement"],
            "carnet"
        )
        layout.addWidget(self.carnet_table, 1)
        return page

    def _refresh_carnet(self):
        self._load_consultations()

    def _load_consultations(self, query=""):
        consults = PatientModel.get_consultations(self.patient['id'])
        if query:
            consults = search_medical_history(consults, query)
            self.carnet_status.setText(f"{len(consults)} résultat(s) trouvé(s)")
        else:
            self.carnet_status.setText("Entrez un mot-clé pour retrouver rapidement une consultation.")
        data = [[
            c.get('date_consultation', ''), c.get('heure_consultation', ''),
            f"{c.get('medecin_prenom', '')} {c.get('medecin_nom', '')}",
            c.get('motif', ''), c.get('diagnostic', ''),
            c.get('observations', ''), c.get('traitement', '')
        ] for c in consults]
        self.carnet_table.set_data(data)

    def _kmp_search(self):
        self._load_consultations(self.kmp_input.text().strip())

    # ======================== MEDECINS ========================
    def _build_medecins(self):
        page, layout = self._page_container()
        layout.addWidget(page_title("Mes Médecins"))
        self.medecins_table = TableWithEmpty(
            ["Médecin", "Spécialité", "Établissement", "Statut", "Téléphone", "Action"],
            "medecins"
        )
        layout.addWidget(self.medecins_table, 1)
        return page

    def _refresh_medecins(self):
        links = PatientModel.get_links(self.patient['id'])
        data = []
        for l in links:
            statut = l.get('statut', '')
            label_map = {"actif": "Actif", "en_attente": "En attente", "revoked": "Révoqué"}
            data.append([
                f"Dr. {l.get('prenom', '')} {l.get('nom', '')}",
                l.get('specialite', ''),
                l.get('etablissement', ''),
                label_map.get(statut, statut),
                l.get('telephone', ''),
                ""
            ])
        self.medecins_table.set_data(data)
        for r, l in enumerate(links):
            statut = l.get('statut', '')
            if statut == "en_attente":
                w = QWidget()
                bl = QHBoxLayout(w)
                bl.setContentsMargins(4, 4, 4, 4)
                bl.setSpacing(6)
                ok = make_btn("Accepter", "success", "sm")
                ok.clicked.connect(lambda checked, lid=l['id']: self._accept_medecin(lid))
                no = make_btn("Refuser", "danger", "sm")
                no.clicked.connect(lambda checked, lid=l['id']: self._refuse_medecin(lid))
                bl.addWidget(ok); bl.addWidget(no)
                self.medecins_table.table.setCellWidget(r, 5, w)
            elif statut == "actif":
                btn = make_btn("Révoquer", "danger", "sm")
                btn.clicked.connect(lambda checked, lid=l['id']: self._revoke_medecin(lid))
                self.medecins_table.table.setCellWidget(r, 5, btn)
            else:
                lbl = QLabel(l.get('statut', ''))
                lbl.setStyleSheet(f"color: {C_TEXT_LIGHT}; padding: 6px;")
                self.medecins_table.table.setCellWidget(r, 5, lbl)

    def _accept_medecin(self, lid):
        if PatientModel.accept_link(lid):
            self._controller.log_action(self.user['id'], "patient", "ACCEPT_ASSOCIATION", "patient_medecin_links", lid)
            QMessageBox.information(self, "Succès", "Vous êtes maintenant lié à ce médecin !")
            self._refresh_medecins()
        else:
            QMessageBox.warning(self, "Erreur", "Impossible d'accepter cette demande.")

    def _refuse_medecin(self, lid):
        if QMessageBox.question(self, "Confirmation", "Refuser cette demande d'association ?",
                                QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            PatientModel.refuse_link(lid)
            self._controller.log_action(self.user['id'], "patient", "REFUSE_ASSOCIATION", "patient_medecin_links", lid)
            self._refresh_medecins()

    def _revoke_medecin(self, lid):
        if QMessageBox.question(self, "Confirmation", "Révoquer l'accès de ce médecin à votre dossier ?",
                                QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            PatientModel.revoke_link(lid)
            self._controller.log_action(self.user['id'], "patient", "REVOKE_MEDECIN", "patient_medecin_links", lid)
            self._refresh_medecins()

    # ======================== RDV ========================
    def _build_rendezvous(self):
        page, layout = self._page_container()
        layout.addWidget(page_title("Mes Rendez-vous"))
        self.rdv_table = TableWithEmpty(
            ["Date", "Horaire", "Motif", "Type", "Statut"],
            "rdv"
        )
        layout.addWidget(self.rdv_table, 1)
        return page

    def _refresh_rdv(self):
        rdvs = PatientModel.get_rendezvous(self.patient['id'])
        data = [[
            r.get('date_rdv', ''),
            f"{r.get('heure_debut', '')} - {r.get('heure_fin', '')}",
            r.get('motif', ''), r.get('type', ''), r.get('statut', '')
        ] for r in rdvs]
        self.rdv_table.set_data(data)

    # ======================== PRESCRIPTIONS ========================
    def _build_prescriptions(self):
        page, layout = self._page_container()
        layout.addWidget(page_title("Mes Prescriptions"))
        self.presc_table = TableWithEmpty(
            ["Titre", "Contenu", "Médecin", "Date début", "Date fin", "Statut"],
            "prescriptions"
        )
        layout.addWidget(self.presc_table, 1)
        return page

    def _refresh_prescriptions(self):
        prescs = PatientModel.get_prescriptions(self.patient['id'])
        data = [[
            p.get('titre', ''), p.get('contenu', ''),
            f"Dr. {p.get('medecin_prenom', '')} {p.get('medecin_nom', '')}",
            p.get('date_debut', ''), p.get('date_fin', ''), p.get('statut', '')
        ] for p in prescs]
        self.presc_table.set_data(data)

    # ======================== ALLERGIES ========================
    def _build_allergies(self):
        page, layout = self._page_container()

        header = QWidget()
        hl = QHBoxLayout(header)
        hl.setContentsMargins(0, 0, 0, 0)
        hl.addWidget(page_title("Mes Allergies"))
        hl.addStretch()
        btn_add = make_btn("+ Ajouter une allergie", "warning")
        btn_add.clicked.connect(self._add_allergie)
        hl.addWidget(btn_add)
        layout.addWidget(header)

        self.allergies_table = TableWithEmpty(
            ["Allergène", "Réaction", "Description", "Date", "Action"],
            "allergies"
        )
        layout.addWidget(self.allergies_table, 1)
        return page

    def _refresh_allergies(self):
        allergies = PatientModel.get_allergies(self.patient['id'])
        data = [[
            a.get('allergene', ''), a.get('type_reaction', ''),
            a.get('description', ''),
            a.get('date_diagnostic', '') or a.get('created_at', ''),
            ""
        ] for a in allergies]
        self.allergies_table.set_data(data)
        for r, a in enumerate(allergies):
            btn = make_btn("Supprimer", "danger", "sm")
            btn.clicked.connect(lambda checked, aid=a['id']: self._delete_allergie(aid))
            self.allergies_table.table.setCellWidget(r, 4, btn)

    def _add_allergie(self):
        d = QDialog(self)
        d.setWindowTitle("Ajouter une allergie")
        d.setMinimumWidth(460)
        d.setStyleSheet(f"QDialog {{ background: {C_WHITE}; }}")
        l = QFormLayout(d)
        l.setSpacing(14); l.setContentsMargins(28, 24, 28, 24)

        allergene = QLineEdit(); allergene.setPlaceholderText("Ex: Pénicilline")
        reaction = QComboBox(); reaction.addItems(["légère", "modérée", "sévère", "anaphylaxie"])
        desc = QTextEdit(); desc.setPlaceholderText("Description des symptômes...")
        desc.setMaximumHeight(80)
        date_diag = QDateEdit(); date_diag.setCalendarPopup(True)
        date_diag.setDate(QDate.currentDate())

        l.addRow("Allergène:", allergene)
        l.addRow("Réaction:", reaction)
        l.addRow("Description:", desc)
        l.addRow("Date diagnostic:", date_diag)

        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(d.accept); btns.rejected.connect(d.reject)
        l.addRow(btns)

        if d.exec() == QDialog.Accepted and allergene.text().strip():
            PatientModel.create_allergie(
                self.patient['id'], allergene.text().strip(),
                reaction.currentText(), desc.toPlainText().strip() or None,
                date_diag.date().toString("yyyy-MM-dd")
            )
            self._controller.log_action(self.user['id'], "patient", "ADD_ALLERGIE",
                                        "allergies", details=f"allergene={allergene.text()}")
            self._refresh_allergies()
            self.show_toast("Allergie ajoutée avec succès", "success")

    def _delete_allergie(self, aid):
        if QMessageBox.question(self, "Confirmation", "Supprimer cette allergie ?",
                                QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            PatientModel.delete_allergie(aid)
            self._controller.log_action(self.user['id'], "patient", "DELETE_ALLERGIE", "allergies", aid)
            self._refresh_allergies()
            self.show_toast("Allergie supprimée", "success")

    # ======================== EXAMENS ========================
    def _build_examens(self):
        page, layout = self._page_container()

        header = QWidget()
        hl = QHBoxLayout(header)
        hl.setContentsMargins(0, 0, 0, 0)
        hl.addWidget(page_title("Mes Examens"))
        hl.addStretch()
        btn_add = make_btn("+ Ajouter un examen", "primary")
        btn_add.clicked.connect(self._add_examen)
        hl.addWidget(btn_add)
        layout.addWidget(header)

        self.examens_table = TableWithEmpty(
            ["Type", "Date", "Résultats", "Valeurs"],
            "examens"
        )
        layout.addWidget(self.examens_table, 1)
        return page

    def _refresh_examens(self):
        examens = PatientModel.get_examens(self.patient['id'])
        data = [[
            e.get('type_examen', ''), e.get('date_examen', ''),
            e.get('resultats', ''), e.get('valeurs', '')
        ] for e in examens]
        self.examens_table.set_data(data)

    def _add_examen(self):
        d = QDialog(self)
        d.setWindowTitle("Ajouter un examen")
        d.setMinimumWidth(460)
        d.setStyleSheet(f"QDialog {{ background: {C_WHITE}; }}")
        l = QFormLayout(d)
        l.setSpacing(14); l.setContentsMargins(28, 24, 28, 24)

        type_exam = QLineEdit(); type_exam.setPlaceholderText("IRM, prise de sang, radio...")
        date_exam = QDateEdit(); date_exam.setCalendarPopup(True)
        date_exam.setDate(QDate.currentDate())
        resultats = QTextEdit(); resultats.setPlaceholderText("Résultats de l'examen...")
        resultats.setMaximumHeight(100)

        l.addRow("Type:", type_exam)
        l.addRow("Date:", date_exam)
        l.addRow("Résultats:", resultats)

        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(d.accept); btns.rejected.connect(d.reject)
        l.addRow(btns)

        if d.exec() == QDialog.Accepted and type_exam.text().strip():
            PatientModel.create_examen(
                self.patient['id'], type_exam.text().strip(),
                resultats.toPlainText().strip() or None,
                date_exam.date().toString("yyyy-MM-dd")
            )
            self._controller.log_action(self.user['id'], "patient", "ADD_EXAMEN",
                                        "examens", details=f"type={type_exam.text()}")
            self._refresh_examens()
            self.show_toast("Examen ajouté avec succès", "success")
