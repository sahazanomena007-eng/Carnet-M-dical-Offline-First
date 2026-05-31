import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import db

class MedecinModel:
    @staticmethod
    def get_medecin(medecin_id=None, user_id=None):
        rows = db.get_medecin(medecin_id=medecin_id, user_id=user_id)
        return rows[0] if rows else None

    @staticmethod
    def get_patients(medecin_id):
        return db.get_patient_medecins(medecin_id) or []

    @staticmethod
    def get_consultations(medecin_id):
        return db.get_consultations_by_medecin(medecin_id) or []

    @staticmethod
    def get_rendezvous(medecin_id):
        return db.get_rendezvous_by_medecin(medecin_id) or []

    @staticmethod
    def get_prescriptions(medecin_id):
        return db.get_prescriptions_by_medecin(medecin_id) or []

    @staticmethod
    def get_all_patients():
        return db._execute(
            """SELECT p.*, u.nom, u.prenom, u.telephone
               FROM patients p JOIN users u ON p.user_id = u.id""",
            (), fetchall=True) or []

    @staticmethod
    def find_patient_by_id_or_dossier(key):
        rows = db._execute(
            "SELECT p.*, u.nom, u.prenom, u.telephone FROM patients p JOIN users u ON p.user_id=u.id WHERE p.id=? OR p.numero_dossier=?",
            (key, key), fetchall=True)
        return rows[0] if rows else None

    @staticmethod
    def request_association(patient_id, medecin_id):
        return db.create_link(patient_id, medecin_id)

    @staticmethod
    def create_consultation(patient_id, medecin_id, date_c, heure_c, motif, symptomes=None, diagnostic=None, observations=None, traitement=None):
        return db.create_consultation(patient_id, medecin_id, date_c, heure_c, motif, symptomes, diagnostic, observations, traitement)

    @staticmethod
    def create_rendezvous(patient_id, medecin_id, date_rdv, heure_deb, heure_fin, motif, type_rdv, priorite):
        return db.create_rendezvous(patient_id, medecin_id, date_rdv, heure_deb, heure_fin, motif, type_rdv, priorite)

    @staticmethod
    def create_prescription(patient_id, medecin_id, titre, contenu, instructions=None, date_debut=None, date_fin=None):
        return db.create_prescription(0, patient_id, medecin_id, titre, contenu, instructions=instructions, date_debut=date_debut, date_fin=date_fin)

    @staticmethod
    def get_all_medecins():
        return db.get_medecin() or []

    @staticmethod
    def update_medecin_status(medecin_id, statut, verifie_par=None):
        import datetime
        db._execute(
            "UPDATE medecins SET statut=?, date_verification=?, verifie_par=? WHERE id=?",
            (statut, datetime.datetime.now().isoformat(), verifie_par, medecin_id), commit=True)

    @staticmethod
    def get_all_users():
        return db._execute("SELECT * FROM users ORDER BY created_at DESC", (), fetchall=True) or []

    @staticmethod
    def toggle_user_status(user_id, actif):
        db._execute("UPDATE users SET est_actif=? WHERE id=?", (1 if actif else 0, user_id), commit=True)

    @staticmethod
    def delete_user(user_id):
        db._execute("DELETE FROM patients WHERE user_id=?", (user_id,), commit=True)
        db._execute("DELETE FROM medecins WHERE user_id=?", (user_id,), commit=True)
        db._execute("DELETE FROM users WHERE id=?", (user_id,), commit=True)

    @staticmethod
    def get_audit_logs(limit=200):
        return db._execute("SELECT * FROM audit_log ORDER BY created_at DESC LIMIT ?", (limit,), fetchall=True) or []

    @staticmethod
    def get_stats():
        queries = {
            "utilisateurs": "SELECT COUNT(*) as c FROM users",
            "patients": "SELECT COUNT(*) as c FROM patients",
            "medecins": "SELECT COUNT(*) as c FROM medecins",
            "en_attente": "SELECT COUNT(*) as c FROM medecins WHERE statut='en_attente'",
            "consultations": "SELECT COUNT(*) as c FROM consultations",
            "prescriptions": "SELECT COUNT(*) as c FROM prescriptions",
            "rendez_vous": "SELECT COUNT(*) as c FROM rendez_vous",
            "allergies": "SELECT COUNT(*) as c FROM allergies",
            "examens": "SELECT COUNT(*) as c FROM examens",
            "audit_log": "SELECT COUNT(*) as c FROM audit_log",
        }
        stats = {}
        for key, query in queries.items():
            result = db._execute(query, (), fetchone=True)
            stats[key] = result.get('c', 0) if result else 0
        return stats
