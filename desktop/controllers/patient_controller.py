import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import db


class PatientController:
    def __init__(self, app_manager):
        self.app = app_manager

    def open_patient_window(self, patient, user, login_view=None):
        from views.patient_view import PatientView
        self.window = PatientView(patient, user, self)
        self.window.show()
        if login_view:
            login_view.hide()

    def logout(self, user_id, role):
        db.log_action(user_id, role, "LOGOUT", "users", user_id)
        from views.login_view import LoginView
        from controllers.auth_controller import AuthController
        auth = AuthController(self.app)
        self.app.show_login(auth)

    @staticmethod
    def log_action(user_id, role, action, entite, entite_id=None, details=None):
        db.log_action(user_id, role, action, entite, entite_id, details)
