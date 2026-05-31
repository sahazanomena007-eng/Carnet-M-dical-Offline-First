"""
Module de base de données SQLite pour le carnet médical (mode offline-first)
Synchronisation avec MySQL via l'API backend
"""
import os
import sqlite3
import hashlib
import secrets
import json
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

DB_PATH = Path(__file__).parent / "carnet_medical.db"
MYSQL_DATABASE_URL = os.environ.get("MYSQL_DATABASE_URL")

try:
    import mysql.connector
except ImportError:
    mysql = None


def _is_mysql(conn) -> bool:
    return mysql is not None and conn.__class__.__module__.startswith('mysql')


def _to_dict(row):
    if row is None:
        return None
    if isinstance(row, dict):
        return row
    try:
        return dict(row)
    except Exception:
        return row


def _rows_to_dict(rows):
    return [dict(r) if not isinstance(r, dict) else r for r in rows]


def _format_query(query: str, conn):
    if _is_mysql(conn):
        return query.replace('?', '%s')
    return query


def _execute(query: str, params=None, fetchone=False, fetchall=False, commit=False):
    params = params or ()
    conn = get_db()
    try:
        cursor = conn.cursor()
        sql = _format_query(query, conn)
        cursor.execute(sql, params)
        if commit:
            conn.commit()
        if fetchone:
            return _to_dict(cursor.fetchone())
        if fetchall:
            return _rows_to_dict(cursor.fetchall())
        return cursor.lastrowid
    finally:
        try:
            cursor.close()
        except Exception:
            pass
        conn.close()


def init_db():
    """Initialise la base de données SQLite avec toutes les tables"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('patient', 'medecin', 'admin')),
            nom TEXT NOT NULL,
            prenom TEXT NOT NULL,
            telephone TEXT,
            est_actif INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE REFERENCES users(id),
            numero_dossier TEXT UNIQUE NOT NULL,
            date_naissance TEXT,
            sexe TEXT CHECK(sexe IN ('M', 'F')),
            adresse TEXT,
            groupe_sanguin TEXT,
            taille_cm INTEGER,
            poids_kg TEXT,
            antecedents_familiaux TEXT,
            antecedents_personnels TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS medecins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE REFERENCES users(id),
            numero_ordre TEXT UNIQUE NOT NULL,
            specialite TEXT NOT NULL,
            etablissement TEXT,
            statut TEXT DEFAULT 'en_attente' CHECK(statut IN ('en_attente', 'verifie', 'suspendu', 'rejete')),
            verifie_par INTEGER,
            date_verification TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS patient_medecin_links (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL REFERENCES patients(id),
            medecin_id INTEGER NOT NULL REFERENCES medecins(id),
            code_association TEXT NOT NULL,
            statut TEXT DEFAULT 'en_attente' CHECK(statut IN ('en_attente', 'actif', 'revoque', 'expire')),
            date_demande TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            date_validation TIMESTAMP,
            date_revocation TIMESTAMP,
            revoked_by TEXT CHECK(revoked_by IN ('patient', 'medecin')),
            UNIQUE(patient_id, medecin_id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS consultations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL REFERENCES patients(id),
            medecin_id INTEGER NOT NULL REFERENCES medecins(id),
            date_consultation TEXT NOT NULL,
            heure_consultation TEXT NOT NULL,
            motif TEXT NOT NULL,
            symptomes TEXT,
            diagnostic TEXT,
            observations TEXT,
            traitement TEXT,
            statut TEXT DEFAULT 'termine' CHECK(statut IN ('planifie', 'en_cours', 'termine', 'annule')),
            sync_status TEXT DEFAULT 'synced' CHECK(sync_status IN ('synced', 'pending', 'conflict')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS prescriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            consultation_id INTEGER REFERENCES consultations(id),
            patient_id INTEGER NOT NULL REFERENCES patients(id),
            medecin_id INTEGER NOT NULL REFERENCES medecins(id),
            titre TEXT NOT NULL,
            contenu TEXT NOT NULL,
            medicaments TEXT,
            instructions TEXT,
            date_debut TEXT NOT NULL,
            date_fin TEXT,
            statut TEXT DEFAULT 'active' CHECK(statut IN ('active', 'terminee', 'annulee')),
            sync_status TEXT DEFAULT 'synced',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS rendez_vous (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL REFERENCES patients(id),
            medecin_id INTEGER NOT NULL REFERENCES medecins(id),
            date_rdv TEXT NOT NULL,
            heure_debut TEXT NOT NULL,
            heure_fin TEXT NOT NULL,
            motif TEXT NOT NULL,
            type TEXT DEFAULT 'consultation' CHECK(type IN ('consultation', 'suivi', 'urgence', 'examen', 'vaccination')),
            priorite INTEGER DEFAULT 1 CHECK(priorite IN (1, 2, 3)),
            notes TEXT,
            statut TEXT DEFAULT 'planifie' CHECK(statut IN ('planifie', 'confirme', 'en_cours', 'termine', 'annule', 'reporte')),
            sync_status TEXT DEFAULT 'synced',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS allergies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL REFERENCES patients(id),
            allergene TEXT NOT NULL,
            type_reaction TEXT DEFAULT 'legere' CHECK(type_reaction IN ('legere', 'moderee', 'severe', 'anaphylaxie')),
            description TEXT,
            date_diagnostic TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS examens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL REFERENCES patients(id),
            consultation_id INTEGER REFERENCES consultations(id),
            medecin_id INTEGER REFERENCES medecins(id),
            type_examen TEXT NOT NULL,
            resultats TEXT,
            valeurs TEXT,
            fichier_url TEXT,
            date_examen TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            user_role TEXT,
            action TEXT NOT NULL,
            entite TEXT NOT NULL,
            entite_id INTEGER,
            details TEXT,
            ip_address TEXT,
            statut TEXT DEFAULT 'succes' CHECK(statut IN ('succes', 'echec', 'refuse')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            type TEXT NOT NULL,
            titre TEXT NOT NULL,
            message TEXT NOT NULL,
            lu INTEGER DEFAULT 0,
            data TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sync_queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            table_name TEXT NOT NULL,
            record_id INTEGER NOT NULL,
            operation TEXT NOT NULL CHECK(operation IN ('insert', 'update', 'delete')),
            data TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            synced_at TIMESTAMP
        )
    ''')

    conn.commit()
    cursor.close()
    conn.close()


def get_db():
    if MYSQL_DATABASE_URL and mysql:
        url = urlparse(MYSQL_DATABASE_URL)
        conn = mysql.connector.connect(
            host=url.hostname or "localhost",
            port=url.port or 3306,
            user=url.username or "",
            password=url.password or "",
            database=(url.path or "").lstrip("/"),
            autocommit=True,
            connection_timeout=10,
            charset="utf8mb4",
            use_pure=True,
            dictionary=True,
        )
        return conn

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    pwdhash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
    return salt + pwdhash.hex()


def verify_password(password: str, hashed: str) -> bool:
    salt = hashed[:32]
    pwdhash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
    return hashed == salt + pwdhash.hex()


def _generate_num_dossier() -> str:
    return f"DOS-{datetime.now().strftime('%Y%m%d')}-{secrets.token_hex(3)}"


def create_user(email: str, password: str, role: str, nom: str, prenom: str, telephone: str = None) -> int:
    if role not in ('patient', 'medecin', 'admin'):
        raise ValueError('Role invalide')
    password_hash = hash_password(password)
    return _execute(
        '''INSERT INTO users (email, password_hash, role, nom, prenom, telephone, est_actif)
           VALUES (?, ?, ?, ?, ?, ?, 1)''',
        (email.lower(), password_hash, role, nom.strip(), prenom.strip(), telephone),
        commit=True
    )


def authenticate_user(email: str, password: str):
    user = _execute('SELECT * FROM users WHERE email = ?', (email.lower(),), fetchone=True)
    if not user or not verify_password(password, user.get('password_hash', '')):
        return None
    user.pop('password_hash', None)
    return user


def log_action(user_id: int, user_role: str, action: str, entite: str, entite_id: int = None,
               details: str = None, ip_address: str = None, statut: str = 'succes') -> int:
    return _execute(
        '''INSERT INTO audit_log (user_id, user_role, action, entite, entite_id, details, ip_address, statut)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
        (user_id, user_role, action, entite, entite_id, details, ip_address, statut),
        commit=True
    )


def add_sync_queue(table_name: str, record_id: int, operation: str, data=None) -> int:
    return _execute(
        '''INSERT INTO sync_queue (table_name, record_id, operation, data)
           VALUES (?, ?, ?, ?)''',
        (table_name, record_id, operation, json.dumps(data) if data else None),
        commit=True
    )


def create_patient(user_id: int, nom: str, prenom: str, date_naissance: str, sexe: str,
                   numero_dossier: str = None, adresse: str = None, groupe_sanguin: str = None,
                   taille_cm: int = None, poids_kg: str = None, antecedents_familiaux: str = None,
                   antecedents_personnels: str = None) -> tuple:
    if sexe not in ('M', 'F'):
        raise ValueError('Sexe invalide')
    numero_dossier = numero_dossier or _generate_num_dossier()
    patient_id = _execute(
        '''INSERT INTO patients (user_id, numero_dossier, date_naissance, sexe, adresse,
            groupe_sanguin, taille_cm, poids_kg, antecedents_familiaux, antecedents_personnels)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
        (user_id, numero_dossier, date_naissance, sexe, adresse, groupe_sanguin,
         taille_cm, poids_kg, antecedents_familiaux, antecedents_personnels),
        commit=True
    )
    return patient_id, numero_dossier


def create_medecin(user_id: int, numero_ordre: str, nom: str, prenom: str, specialite: str,
                   etablissement: str = None, telephone: str = None, email: str = None,
                   statut: str = 'en_attente', verifie_par: int = None) -> int:
    return _execute(
        '''INSERT INTO medecins (user_id, numero_ordre, specialite, etablissement, statut, verifie_par)
           VALUES (?, ?, ?, ?, ?, ?)''',
        (user_id, numero_ordre, specialite, etablissement, statut, verifie_par),
        commit=True
    )


def create_link(patient_id: int, medecin_id: int, code_association: str = None) -> tuple:
    code_association = code_association or secrets.token_urlsafe(8)
    link_id = _execute(
        '''INSERT INTO patient_medecin_links (patient_id, medecin_id, code_association)
           VALUES (?, ?, ?)''',
        (patient_id, medecin_id, code_association),
        commit=True
    )
    return link_id, code_association


def validate_link(code: str, patient_id: int) -> bool:
    link = _execute(
        '''SELECT * FROM patient_medecin_links WHERE code_association = ? AND patient_id = ?''',
        (code, patient_id),
        fetchone=True
    )
    if not link or link.get('statut') != 'en_attente':
        return False
    _execute(
        '''UPDATE patient_medecin_links
           SET statut = 'actif', date_validation = ?, date_revocation = NULL, revoked_by = NULL
           WHERE id = ?''',
        (datetime.now().isoformat(), link['id']),
        commit=True
    )
    return True


def revoke_link(link_id: int, revoked_by: str = 'patient') -> bool:
    if revoked_by not in ('patient', 'medecin'):
        revoked_by = 'patient'
    _execute(
        '''UPDATE patient_medecin_links
           SET statut = 'revoque', date_revocation = ?, revoked_by = ?
           WHERE id = ?''',
        (datetime.now().isoformat(), revoked_by, link_id),
        commit=True
    )
    return True


def get_patient(user_id: int = None, patient_id: int = None):
    if patient_id is not None:
        return _execute('SELECT * FROM patients WHERE id = ?', (patient_id,), fetchall=True)
    if user_id is not None:
        return _execute('SELECT * FROM patients WHERE user_id = ?', (user_id,), fetchall=True)
    return _execute('SELECT * FROM patients ORDER BY created_at DESC', (), fetchall=True)


def get_medecin(user_id: int = None, medecin_id: int = None):
    if medecin_id is not None:
        return _execute(
            '''SELECT m.*, u.nom, u.prenom, u.telephone
               FROM medecins m
               JOIN users u ON m.user_id = u.id
               WHERE m.id = ?''',
            (medecin_id,),
            fetchall=True
        )
    if user_id is not None:
        return _execute(
            '''SELECT m.*, u.nom, u.prenom, u.telephone
               FROM medecins m
               JOIN users u ON m.user_id = u.id
               WHERE m.user_id = ?''',
            (user_id,),
            fetchall=True
        )
    return _execute(
        '''SELECT m.*, u.nom, u.prenom, u.telephone
           FROM medecins m
           JOIN users u ON m.user_id = u.id
           ORDER BY m.created_at DESC''',
        (),
        fetchall=True
    )


def get_patient_medecins(medecin_id: int):
    return _execute(
        '''SELECT p.*, u.nom, u.prenom, u.telephone, l.statut
           FROM patient_medecin_links l
           JOIN patients p ON l.patient_id = p.id
           JOIN users u ON p.user_id = u.id
           WHERE l.medecin_id = ?''',
        (medecin_id,),
        fetchall=True
    )


def get_consultations_by_patient(patient_id: int):
    return _execute(
        '''SELECT c.*, u.nom AS medecin_nom, u.prenom AS medecin_prenom
           FROM consultations c
           JOIN medecins m ON c.medecin_id = m.id
           JOIN users u ON m.user_id = u.id
           WHERE c.patient_id = ?
           ORDER BY c.date_consultation DESC, c.heure_consultation DESC''',
        (patient_id,),
        fetchall=True
    )


def get_consultations_by_medecin(medecin_id: int):
    return _execute(
        '''SELECT c.*, u.nom AS patient_nom, u.prenom AS patient_prenom, p.numero_dossier
           FROM consultations c
           JOIN patients p ON c.patient_id = p.id
           JOIN users u ON p.user_id = u.id
           WHERE c.medecin_id = ?
           ORDER BY c.date_consultation DESC, c.heure_consultation DESC''',
        (medecin_id,),
        fetchall=True
    )


def get_rendezvous_by_patient(patient_id: int, date_rdv: str = None):
    if date_rdv:
        return _execute(
            '''SELECT * FROM rendez_vous WHERE patient_id = ? AND date_rdv = ?
               ORDER BY date_rdv DESC, heure_debut ASC''',
            (patient_id, date_rdv),
            fetchall=True
        )
    return _execute(
        '''SELECT * FROM rendez_vous WHERE patient_id = ?
           ORDER BY date_rdv DESC, heure_debut ASC''',
        (patient_id,),
        fetchall=True
    )


def get_rendezvous_by_medecin(medecin_id: int, date_rdv: str = None):
    if date_rdv:
        return _execute(
            '''SELECT * FROM rendez_vous WHERE medecin_id = ? AND date_rdv = ?
               ORDER BY date_rdv DESC, heure_debut ASC''',
            (medecin_id, date_rdv),
            fetchall=True
        )
    return _execute(
        '''SELECT * FROM rendez_vous WHERE medecin_id = ?
           ORDER BY date_rdv DESC, heure_debut ASC''',
        (medecin_id,),
        fetchall=True
    )


def get_prescriptions_by_patient(patient_id: int):
    return _execute(
        '''SELECT p.*, u.nom AS medecin_nom, u.prenom AS medecin_prenom
           FROM prescriptions p
           JOIN medecins m ON p.medecin_id = m.id
           JOIN users u ON m.user_id = u.id
           WHERE p.patient_id = ?
           ORDER BY p.date_debut DESC''',
        (patient_id,),
        fetchall=True
    )


def get_prescriptions_by_medecin(medecin_id: int):
    return _execute(
        '''SELECT p.*, u.nom AS patient_nom, u.prenom AS patient_prenom
           FROM prescriptions p
           JOIN patients pa ON p.patient_id = pa.id
           JOIN users u ON pa.user_id = u.id
           WHERE p.medecin_id = ?
           ORDER BY p.date_debut DESC''',
        (medecin_id,),
        fetchall=True
    )


def get_allergies_by_patient(patient_id: int):
    return _execute(
        '''SELECT * FROM allergies WHERE patient_id = ? ORDER BY created_at DESC''',
        (patient_id,),
        fetchall=True
    )


def get_examens_by_patient(patient_id: int):
    return _execute(
        '''SELECT * FROM examens WHERE patient_id = ? ORDER BY date_examen DESC''',
        (patient_id,),
        fetchall=True
    )


def create_consultation(patient_id: int, medecin_id: int, date_consultation: str,
                        heure_consultation: str, motif: str, symptomes: str = None,
                        diagnostic: str = None, observations: str = None,
                        traitement: str = None, statut: str = 'termine') -> int:
    return _execute(
        '''INSERT INTO consultations (patient_id, medecin_id, date_consultation, heure_consultation,
            motif, symptomes, diagnostic, observations, traitement, statut)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
        (patient_id, medecin_id, date_consultation, heure_consultation, motif,
         symptomes, diagnostic, observations, traitement, statut),
        commit=True
    )


def create_rendezvous(patient_id: int, medecin_id: int, date_rdv: str, heure_debut: str,
                      heure_fin: str, motif: str, type: str = 'consultation', priorite: int = 1,
                      notes: str = None, statut: str = 'planifie') -> int:
    return _execute(
        '''INSERT INTO rendez_vous (patient_id, medecin_id, date_rdv, heure_debut,
            heure_fin, motif, type, priorite, notes, statut)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
        (patient_id, medecin_id, date_rdv, heure_debut, heure_fin, motif,
         type, priorite, notes, statut),
        commit=True
    )


def create_prescription(consultation_id: int, patient_id: int, medecin_id: int,
                        titre: str, contenu: str, medicaments: str = None,
                        instructions: str = None, date_debut: str = None,
                        date_fin: str = None, statut: str = 'active') -> int:
    return _execute(
        '''INSERT INTO prescriptions (consultation_id, patient_id, medecin_id, titre, contenu,
            medicaments, instructions, date_debut, date_fin, statut)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
        (consultation_id, patient_id, medecin_id, titre, contenu,
         medicaments, instructions, date_debut, date_fin, statut),
        commit=True
    )


def create_allergie(patient_id: int, allergene: str, type_reaction: str = 'legere',
                    description: str = None, date_diagnostic: str = None) -> int:
    return _execute(
        '''INSERT INTO allergies (patient_id, allergene, type_reaction, description, date_diagnostic)
           VALUES (?, ?, ?, ?, ?)''',
        (patient_id, allergene, type_reaction, description, date_diagnostic),
        commit=True
    )


def delete_allergie(allergy_id: int) -> bool:
    _execute('DELETE FROM allergies WHERE id = ?', (allergy_id,), commit=True)
    return True


def create_examen(patient_id: int, consultation_id: int, medecin_id: int, type_examen: str,
                  resultats: str = None, valeurs: str = None, fichier_url: str = None,
                  date_examen: str = None) -> int:
    if not date_examen:
        date_examen = datetime.now().strftime('%Y-%m-%d')
    return _execute(
        '''INSERT INTO examens (patient_id, consultation_id, medecin_id, type_examen,
            resultats, valeurs, fichier_url, date_examen)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
        (patient_id, consultation_id, medecin_id, type_examen,
         resultats, valeurs, fichier_url, date_examen),
        commit=True
    )
