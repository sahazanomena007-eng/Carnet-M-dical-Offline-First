import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import db

class PatientModel:
    @staticmethod
    def get_patient(patient_id=None, user_id=None):
        rows = db.get_patient(patient_id=patient_id, user_id=user_id)
        return rows[0] if rows else None

    @staticmethod
    def get_consultations(patient_id):
        return db.get_consultations_by_patient(patient_id) or []

    @staticmethod
    def get_prescriptions(patient_id):
        return db.get_prescriptions_by_patient(patient_id) or []

    @staticmethod
    def get_rendezvous(patient_id):
        return db.get_rendezvous_by_patient(patient_id) or []

    @staticmethod
    def get_allergies(patient_id):
        return db.get_allergies_by_patient(patient_id) or []

    @staticmethod
    def get_examens(patient_id):
        return db.get_examens_by_patient(patient_id) or []

    @staticmethod
    def get_links(patient_id):
        return db._execute(
            """SELECT l.*, m.specialite, m.etablissement, u.nom, u.prenom, u.telephone
               FROM patient_medecin_links l
               JOIN medecins m ON l.medecin_id = m.id
               JOIN users u ON m.user_id = u.id
               WHERE l.patient_id = ?""",
            (patient_id,), fetchall=True) or []

    @staticmethod
    def get_active_links_count(patient_id):
        links = db._execute(
            "SELECT * FROM patient_medecin_links WHERE patient_id=? AND statut='actif'",
            (patient_id,), fetchall=True) or []
        return len(links)

    @staticmethod
    def accept_link(link_id):
        return db.accept_link(link_id)

    @staticmethod
    def refuse_link(link_id):
        return db.refuse_link(link_id)

    @staticmethod
    def revoke_link(link_id):
        db.revoke_link(link_id, "patient")

    @staticmethod
    def create_allergie(patient_id, allergene, reaction, description, date_diag):
        return db.create_allergie(patient_id, allergene, reaction, description, date_diag)

    @staticmethod
    def delete_allergie(allergy_id):
        db.delete_allergie(allergy_id)

    @staticmethod
    def create_examen(patient_id, type_examen, resultats, date_examen):
        return db.create_examen(patient_id, 0, 0, type_examen, resultats, date_examen=date_examen)

    @staticmethod
    def get_vaccins(patient_id):
        return db.get_vaccins(patient_id)

    @staticmethod
    def get_notifications(user_id):
        return db.get_notifications(user_id)

    @staticmethod
    def calcul_age(date_naissance):
        return db.calcul_age(date_naissance)
