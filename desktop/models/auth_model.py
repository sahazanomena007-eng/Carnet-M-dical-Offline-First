import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import db

class AuthModel:
    @staticmethod
    def authenticate(email, password):
        user = db.authenticate_user(email, password)
        return user

    @staticmethod
    def register_patient(email, password, nom, prenom, date_naiss, sexe, tel=None, adresse=None, groupe_sanguin=None):
        if len(password) < 8:
            raise ValueError("Le mot de passe doit contenir au moins 8 caracteres.")
        user_id = db.create_user(email, password, "patient", nom, prenom, tel)
        db.create_patient(user_id, nom, prenom, date_naiss, sexe, adresse=adresse, groupe_sanguin=groupe_sanguin)
        db.log_action(user_id, "patient", "REGISTER", "users", user_id)
        return user_id

    @staticmethod
    def register_medecin(email, password, nom, prenom, num_ordre, specialite, etablissement=None, tel=None):
        if len(password) < 8:
            raise ValueError("Le mot de passe doit contenir au moins 8 caracteres.")
        user_id = db.create_user(email, password, "medecin", nom, prenom, tel)
        db.create_medecin(user_id, num_ordre, nom, prenom, specialite, etablissement, tel, email)
        db.log_action(user_id, "medecin", "REGISTER", "medecins", user_id)
        return user_id

    @staticmethod
    def log_action(user_id, role, action, entite, entite_id=None, details=None):
        db.log_action(user_id, role, action, entite, entite_id, details)

    @staticmethod
    def get_patient_by_user(user_id):
        rows = db.get_patient(user_id=user_id)
        return rows[0] if rows else None

    @staticmethod
    def get_medecin_by_user(user_id):
        rows = db.get_medecin(user_id=user_id)
        return rows[0] if rows else None
