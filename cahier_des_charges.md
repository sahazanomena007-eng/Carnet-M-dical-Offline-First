# Cahier des Charges — Carnet Medical Numérique

**Projet :** Carnet Médical Numérique Offline-First  
**Version :** 2.0.0  
**Date :** Mai 2026  
**Porté par :** ESMIA INNOVATION — Projet Numérique Malagasy 2035

---

## 1. Présentation du Projet

### 1.1 Contexte
Le Carnet Médical Numérique est une plateforme de santé digitale destinée à la population malgache, dans le cadre du projet **Numérique Malagasy 2035**. L'objectif est de fournir un outil moderne, sécurisé et accessible (même sans connexion internet) permettant aux patients et aux médecins de gérer l'ensemble du cycle de soins.

### 1.2 Objectifs
- Centraliser l'historique médical des patients
- Faciliter la communication patient-médecin
- Permettre un suivi médical continu et délocalisé
- Garantir la disponibilité des données même hors-ligne (offline-first)
- Offrir une interface professionnelle, claire et rassurante (design médical)

### 1.3 Cibles
- **Patients** : tout citoyen souhaitant centraliser son dossier médical
- **Médecins** : professionnels de santé libéraux ou hospitaliers
- **Administrateurs** : gestionnaires de la plateforme

---

## 1.4 Contraintes 2035 déclarées et justifiées

Conformément au cahier des charges du projet transversal, je déclare **3 contraintes minimales** parmi la liste proposée, qui ont guidé l'architecture et les choix algorithmiques :

| # | Contrainte | Justification technique | Impact architectural |
|---|-----------|----------------------|---------------------|
| 1 | **Connectivité intermittente** | SQLite local + sync_queue + IndexedDB web. Toutes les opérations critiques fonctionnent hors-ligne. | Architecture offline-first (desktop + web) |
| 2 | **Faible débit** | Algorithmes optimisés (KMP O(n+m), DP O(n×W), Greedy O(n log n)). Traitement local minimisant les échanges réseau. | Sync diff seulement ; calculs côté client |
| 3 | **Sécurité/Confidentialité** | PBKDF2-SHA256, bcrypt, JWT, RBAC, audit log, validation mutuelle patient-médecin. | Chiffrement, contrôle d'accès, traçabilité |

*Détail complet dans `docs/contraintes_2035.md`*

---

## 2. Architecture Technique

### 2.1 Stack Technologique

| Composant | Technologie | Rôle |
|-----------|-------------|------|
| Desktop | Python 3.10+ / PyQt5 | Application lourde offline-first |
| Web | React 18 + Vite + TypeScript | Interface web responsive |
| Base de données locale | SQLite 3 | Stockage offline desktop |
| Base de données distante | MySQL 8 (ApsaraDB RDS) | Stockage cloud web |
| ORM Web | Drizzle ORM | Gestion des schémas web |
| Authentification | bcrypt + OAuth Kimi | Sécurisation des accès |
| Algorithme de recherche | KMP (Knuth-Morris-Pratt) | Recherche full-text |
| Optimisation RDV | Glouton (Greedy) | Planification rendez-vous |
| Optimisation prescriptions | DP (Sac à dos 0/1) | Budget médicaments |
| Structure historique | AVL Tree | Tri chronologique |
| Cache patients | Hash Table | Lookup rapide |
| Priorité RDV | Heap (tas max) | Gestion priorités |

### 2.2 Principe Offline-First
- L'application desktop fonctionne intégralement sans connexion
- Les données sont stockées localement dans SQLite
- Une file de synchronisation (`sync_queue`) permet la réplication vers MySQL
- En mode connecté, les données sont poussées automatiquement

### 2.3 Arborescence du Projet
```
CarnetMedical/
├── desktop/                    # Application PyQt5
│   ├── main.py                # Interface utilisateur complète
│   ├── db.py                  # Couche base de données SQLite
│   ├── algorithms.py          # Algorithmes (KMP, Glouton, DP, AVL, Hash, Heap)
│   └── carnet_medical.db      # Base SQLite (générée)
├── web/                        # Application React + Vite
│   ├── src/                   # Code source React
│   │   ├── components/        # Composants UI
│   │   ├── api/               # Routeurs API (auth, admin, patient, medecin)
│   │   ├── db/                # Schémas Drizzle ORM
│   │   └── pages/             # Pages (login, register, patient, medecin, admin)
│   ├── package.json           # Dépendances web
│   └── vite.config.ts         # Configuration build
└── README.md
```

---

## 3. Fonctionnalités Détaillées

### 3.1 Authentification (Login / Inscription)

**Pages :** Login, Register Patient, Register Médecin

| Fonctionnalité | Description |
|----------------|-------------|
| Connexion email + mot de passe | Authentification par bcrypt (PBKDF2-SHA256) |
| Œil voir/masquer mot de passe | Toggle visibilité du champ mot de passe |
| Inscription patient | Nom, prénom, email, date naissance, sexe, téléphone, adresse, groupe sanguin |
| Inscription médecin | Nom, prénom, email, numéro ordre, spécialité, établissement |
| Validation administrateur | Les comptes médecins sont soumis à validation |
| Choix de rôle | Dialogue "Patient" ou "Médecin" au moment de l'inscription |
| Barre de progression | Indicateur de chargement pendant l'authentification |

**Maquette UI :**
- Carte centrée avec ombre bleutée et dégradé
- Icône hôpital 🏥 en haut
- Ligne décorative bleue sous le titre
- Champs avec bordure 2px, focus bleu
- Bouton "Se connecter" bleu médical (#0F6CBD)
- Bouton "Créer un compte" vert (#10B981)

### 3.2 Dashboard Patient

**Accès :** Page d'accueil après connexion patient

| Composant | Description |
|-----------|-------------|
| Sidebar | Profil patient (avatar, nom, dossier), navigation 7 sections |
| Carte statistiques | 5 cartes : Consultations, Prescriptions, RDV, Allergies, Médecins |
| Badge alerte | 🔔 "X RDV aujourd'hui" ou 📅 "Prochain RDV: date" |
| Informations personnelles | Dossier, date naissance, sexe, groupe sanguin, taille, poids, téléphone |
| Actions rapides | 3 boutons : Consulter le carnet, RDV, Gérer médecins |

**Indicateurs visuels :**
- StatCard : bordure gauche colorée, ombre légère, icône 22px, valeur 32px
- Carte info : ombre portée, coins arrondis 12px

### 3.3 Dashboard Médecin

**Accès :** Page d'accueil après connexion médecin

| Composant | Description |
|-----------|-------------|
| Sidebar | Profil médecin (avatar 🩺, nom, spécialité) |
| Carte statistiques | 4 cartes : Patients, Consultations, RDV, Prescriptions |
| Badge | 🔔 RDV aujourd'hui |
| Informations | Spécialité, établissement, nº ordre, statut, patients actifs |
| Actions rapides | 3 boutons : Patients, Consultation, RDV |

### 3.4 Gestion des Patients (Carnet Médical)

**Page :** Mon Carnet (patient) / Mes Patients (médecin)

| Fonctionnalité | Description |
|----------------|-------------|
| Historique médical | Tableau des consultations (date, heure, médecin, motif, diagnostic, observations, traitement) |
| Recherche KMP | Recherche full-text dans l'historique avec algorithme KMP (O(n+m)) |
| Tri AVL | Les consultations sont indexées par AVL Tree pour un tri chronologique |
| Cache HashTable | Les consultations sont hashées pour un accès O(1) |
| Vues médecin | Recherche multi-patients avec KMP (parcourt tous les patients liés) |

**Colonnes du tableau :**
1. Date
2. Heure
3. Médecin / Patient
4. Motif
5. Diagnostic
6. Observations
7. Traitement

### 3.5 Liaison Patient ↔ Médecin

**Workflow sécurisé en 3 étapes :**

1. **Le médecin initie** : saisit l'ID ou nº dossier du patient → génère un code unique (`secrets.token_urlsafe(8)`)
2. **Le médecin communique** : le code est transmis au patient (verbalement, SMS, email)
3. **Le patient valide** : saisit le code dans son interface → lien activé (`statut: 'actif'`)

| Statuts de lien | Signification |
|-----------------|---------------|
| `en_attente` | Code généré, patient doit valider |
| `actif` | Patient a validé, accès réciproque |
| `revoqué` | Patient ou médecin a révoqué l'accès |
| `expiré` | Code non utilisé après délai |

**Révocation :**
- Le patient peut révoquer l'accès d'un médecin à tout moment
- Le médecin peut révoquer un patient
- Motif tracé dans `audit_log`

### 3.6 Rendez-vous

| Fonctionnalité | Description |
|----------------|-------------|
| Création RDV | Patient ID, date, heure début/fin, motif, type, priorité |
| Types | Consultation, Suivi, Urgence, Examen, Vaccination |
| Priorités | 1 (Normal), 2 (Urgent), 3 (Critique) |
| Heap | Les RDV sont stockés dans un tas max pour gestion des priorités |
| Optimisation Gloutonne | Algorithme glouton : tri par priorité puis sélection sans chevauchement |
| Conflits | Détection et affichage des conflits horaires |
| Statistiques | `optimisé X/Y planifiables | N conflit(s)` |

### 3.7 Prescriptions

| Fonctionnalité | Description |
|----------------|-------------|
| Création | Patient ID, titre, contenu, instructions, date début/fin |
| Optimisation DP | Sac à dos 0/1 : budget max pour sélection de médicaments |
| Interface DP | Ajout de médicaments (nom, coût Ar, efficacité, durée jours) |
| Résultat DP | Médicaments sélectionnés, coût total, efficacité totale, % budget utilisé |
| Complexité | `O(n × W)` avec n = médicaments, W = budget |

### 3.8 Allergies

| Fonctionnalité | Description |
|----------------|-------------|
| Ajout | Allergène, type réaction (légère/modérée/sévère/anaphylaxie), description, date diagnostic |
| Suppression | Avec confirmation et traçabilité |
| Affichage | Tableau avec allergène, réaction, description, date |

### 3.9 Examens

| Fonctionnalité | Description |
|----------------|-------------|
| Ajout | Type (IRM, prise de sang, radio...), date, résultats |
| Affichage | Tableau type, date, résultats |

### 3.10 Administration

**Page :** Tableau de bord Administrateur (4 onglets)

| Onglet | Fonctionnalités |
|--------|-----------------|
| Valider Médecins | Liste des médecins, boutons Valider/Rejeter/Suspendre/Activer |
| Utilisateurs | Liste des utilisateurs, Suspendre/Activer, Supprimer |
| Journal d'Audit | 200 dernières actions, statut coloré (rouge si échec) |
| Statistiques | 10 compteurs : utilisateurs, patients, médecins, en attente, consultations, prescriptions, RDV, allergies, examens, actions |

---

## 4. Design Système — "Mode Santé"

### 4.1 Palette de Couleurs

| Usage | Couleur | Code Hex | Rôle |
|-------|---------|----------|------|
| Primaire | Bleu Médical | `#0F6CBD` | Boutons, headers, liens |
| Primaire Dark | Bleu Foncé | `#0B5DA8` | Hover, sidebar profile |
| Primaire Light | Bleu Clair | `#EBF4FF` | Hover, fonds légers |
| Succès | Vert | `#10B981` | Validation, création |
| Danger | Rouge | `#EF4444` | Suppression, erreur |
| Warning | Ambre | `#F59E0B` | Alertes, attention |
| Texte | Gris Foncé | `#1F2937` | Corps de texte |
| Texte Secondaire | Gris | `#6B7280` | Labels, sous-titres |
| Bordure | Gris Clair | `#E5E7EB` | Cards, inputs |
| Fond | Blanc Cassé | `#F5F7FA` | Fond principal |

### 4.2 Typographie

| Élément | Police | Taille | Graisse |
|---------|--------|--------|---------|
| Titre page | Segoe UI | 22px | 700 |
| Titre card | Segoe UI | 16px | 700 |
| Valeur StatCard | Segoe UI | 32px | 800 |
| Texte normal | Segoe UI | 13px | 400 |
| Label formulaire | Segoe UI | 14px | 700 |
| Button | Segoe UI | 13px | 600 |
| Header table | Segoe UI | 12px | 700 |

### 4.3 Composants UI

| Composant | Style |
|-----------|-------|
| **Bouton Primary** | Fond `#0F6CBD`, blanc, arrondi 8px, padding 10px 24px, ombre au hover |
| **Bouton Danger** | Fond `#EF4444`, blanc |
| **Bouton Success** | Fond `#10B981`, blanc |
| **Bouton Outline** | Blanc, bordure 2px `#E5E7EB`, texte `#0F6CBD`, hover bleu clair |
| **Input** | Bordure 2px, arrondi 8px, padding 10px 14px, focus bordure bleue |
| **Card** | Blanc, bordure 1px, arrondi 12px, ombre (blur 16, offset 2, noir 10%) |
| **StatCard** | Bordure gauche 5px colorée, ombre (blur 12), valeur 32px |
| **Table** | Header bleu `#0F6CBD` texte blanc uppercase, lignes alternées, hover gris |
| **Toast** | Barre gauche 5px, icône, ombre (blur 24), animation entrée/sortie |
| **Badge** | Pilule colorée 11px bold, arrondi 12px |
| **Sidebar** | Fond `#0F6CBD`, profile `#0B5DA8`, navigation `#DBEAFE` |

### 4.4 Ombres et Élévations

| Composant | Blur | Offset | Couleur |
|-----------|------|--------|---------|
| Card | 16px | 2px | rgba(0,0,0,0.10) |
| StatCard | 12px | 1px | rgba(0,0,0,0.08) |
| Toast | 24px | 3px | rgba(0,0,0,0.24) |
| Login Card | 40px | 4px | rgba(15,108,189,0.20) |

### 4.5 États Visuels

| État | Description |
|------|-------------|
| **Hover bouton** | Couleur plus foncée, curseur pointer |
| **Focus input** | Bordure `#0F6CBD` |
| **Sélection table** | Fond `#EBF4FF` |
| **Ligne survol table** | Fond `#F9FAFB` |
| **Bouton pressed** | Couleur encore plus foncée |
| **Bouton disabled** | Fond `#E5E7EB`, texte `#9CA3AF` |
| **Empty state** | Icône 48px + message + bordure pointillée |

---

## 5. Base de Données

### 5.1 Schéma SQLite / MySQL (11 tables)

#### `users`
| Colonne | Type | Contrainte |
|---------|------|------------|
| id | INTEGER | PK AUTOINCREMENT |
| email | TEXT | UNIQUE NOT NULL |
| password_hash | TEXT | NOT NULL |
| role | TEXT | CHECK IN ('patient','medecin','admin') |
| nom | TEXT | NOT NULL |
| prenom | TEXT | NOT NULL |
| telephone | TEXT | |
| est_actif | INTEGER | DEFAULT 1 |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP |

#### `patients`
| Colonne | Type | Description |
|---------|------|-------------|
| id | INTEGER PK | |
| user_id | INTEGER | FK → users(id) |
| numero_dossier | TEXT | UNIQUE, format DOS-20240515-XXXX |
| date_naissance | TEXT | YYYY-MM-DD |
| sexe | TEXT | 'M' ou 'F' |
| adresse | TEXT | |
| groupe_sanguin | TEXT | A+, A-, B+, B-, AB+, AB-, O+, O- |
| taille_cm | INTEGER | |
| poids_kg | TEXT | |
| antecedents_familiaux | TEXT | |
| antecedents_personnels | TEXT | |

#### `medecins`
| Colonne | Type | Description |
|---------|------|-------------|
| id | INTEGER PK | |
| user_id | INTEGER | FK → users(id) |
| numero_ordre | TEXT | UNIQUE |
| specialite | TEXT | NOT NULL |
| etablissement | TEXT | |
| statut | TEXT | 'en_attente', 'verifie', 'suspendu', 'rejete' |
| verifie_par | INTEGER | FK → users(id) |
| date_verification | TIMESTAMP | |

#### `patient_medecin_links`
| Colonne | Type | Description |
|---------|------|-------------|
| id | INTEGER PK | |
| patient_id | INTEGER | FK → patients(id) |
| medecin_id | INTEGER | FK → medecins(id) |
| code_association | TEXT | NOT NULL |
| statut | TEXT | 'en_attente', 'actif', 'revoque', 'expire' |
| date_demande | TIMESTAMP | |
| date_validation | TIMESTAMP | |
| date_revocation | TIMESTAMP | |
| revoked_by | TEXT | 'patient' ou 'medecin' |
| UNIQUE | (patient_id, medecin_id) | |

#### `consultations`
| Colonne | Type | Description |
|---------|------|-------------|
| id | INTEGER PK | |
| patient_id | INTEGER | FK → patients(id) |
| medecin_id | INTEGER | FK → medecins(id) |
| date_consultation | TEXT | NOT NULL |
| heure_consultation | TEXT | NOT NULL |
| motif | TEXT | NOT NULL |
| symptomes | TEXT | |
| diagnostic | TEXT | |
| observations | TEXT | |
| traitement | TEXT | |
| statut | TEXT | 'planifie', 'en_cours', 'termine', 'annule' |

#### `prescriptions`
| Colonne | Type | Description |
|---------|------|-------------|
| id | INTEGER PK | |
| consultation_id | INTEGER | FK → consultations(id) |
| patient_id | INTEGER | FK → patients(id) |
| medecin_id | INTEGER | FK → medecins(id) |
| titre | TEXT | NOT NULL |
| contenu | TEXT | NOT NULL |
| medicaments | TEXT | |
| instructions | TEXT | |
| date_debut | TEXT | NOT NULL |
| date_fin | TEXT | |
| statut | TEXT | 'active', 'terminee', 'annulee' |

#### `rendez_vous`
| Colonne | Type | Description |
|---------|------|-------------|
| id | INTEGER PK | |
| patient_id | INTEGER | FK → patients(id) |
| medecin_id | INTEGER | FK → medecins(id) |
| date_rdv | TEXT | NOT NULL |
| heure_debut | TEXT | NOT NULL |
| heure_fin | TEXT | NOT NULL |
| motif | TEXT | NOT NULL |
| type | TEXT | 'consultation','suivi','urgence','examen','vaccination' |
| priorite | INTEGER | 1, 2, ou 3 |
| notes | TEXT | |
| statut | TEXT | 'planifie','confirme','en_cours','termine','annule','reporte' |

#### `allergies`
| Colonne | Type | Description |
|---------|------|-------------|
| id | INTEGER PK | |
| patient_id | INTEGER | FK → patients(id) |
| allergene | TEXT | NOT NULL |
| type_reaction | TEXT | 'legere','moderee','severe','anaphylaxie' |
| description | TEXT | |
| date_diagnostic | TEXT | |

#### `examens`
| Colonne | Type | Description |
|---------|------|-------------|
| id | INTEGER PK | |
| patient_id | INTEGER | FK → patients(id) |
| consultation_id | INTEGER | FK |
| medecin_id | INTEGER | FK |
| type_examen | TEXT | NOT NULL |
| resultats | TEXT | |
| valeurs | TEXT | |
| fichier_url | TEXT | |
| date_examen | TEXT | NOT NULL |

#### `audit_log`
| Colonne | Type | Description |
|---------|------|-------------|
| id | INTEGER PK | |
| user_id | INTEGER | |
| user_role | TEXT | |
| action | TEXT | NOT NULL |
| entite | TEXT | NOT NULL |
| entite_id | INTEGER | |
| details | TEXT | |
| ip_address | TEXT | |
| statut | TEXT | 'succes','echec','refuse' |
| created_at | TIMESTAMP | |

#### `sync_queue`
| Colonne | Type | Description |
|---------|------|-------------|
| id | INTEGER PK | |
| table_name | TEXT | NOT NULL |
| record_id | INTEGER | NOT NULL |
| operation | TEXT | 'insert','update','delete' |
| data | TEXT | JSON |
| created_at | TIMESTAMP | |
| synced_at | TIMESTAMP | |

#### `notifications`
| Colonne | Type | Description |
|---------|------|-------------|
| id | INTEGER PK | |
| user_id | INTEGER | NOT NULL |
| type | TEXT | NOT NULL |
| titre | TEXT | NOT NULL |
| message | TEXT | NOT NULL |
| lu | INTEGER | DEFAULT 0 |
| data | TEXT | |
| created_at | TIMESTAMP | |

---

## 6. Algorithmes Implémentés

### 6.1 KMP (Knuth-Morris-Pratt) — Recherche Médicale
- **Usage :** Recherche full-text dans l'historique des consultations
- **Complexité :** O(n + m) où n = texte, m = pattern
- **Fonction :** `search_medical_history(consultations, query)`
- **Application :** Patient cherche dans son carnet, Médecin cherche dans tous ses patients

### 6.2 Glouton (Greedy) — Optimisation des Rendez-vous
- **Usage :** Planification optimale des RDV sans conflit
- **Algorithme :** Tri par priorité décroissante, puis sélection sans chevauchement
- **Complexité :** O(n log n)
- **Fonction :** `greedy_schedule_optimization(appointments)`
- **Détection :** `find_conflicts(appointments)`

### 6.3 Programmation Dynamique — Sac à Dos 0/1 pour Prescriptions
- **Usage :** Sélection de médicaments sous contrainte budgétaire
- **Algorithme :** DP classique O(n × W)
- **Fonction :** `optimize_prescriptions_dp(medicaments, budget)`
- **Retour :** Médicaments sélectionnés, coût total, efficacité totale, % budget utilisé

### 6.4 AVL Tree — Tri Chronologique
- **Usage :** Indexation des consultations par date pour tri croissant
- **Propriété :** Arbre binaire équilibré, hauteur O(log n)
- **Rotation :** Auto-équilibrante après chaque insertion

### 6.5 Hash Table — Cache Patients
- **Usage :** Cache rapide patients (médecin) par ID ou nº dossier
- **Complexité :** Insertion O(1), Recherche O(1) en moyenne
- **Fonction :** `PatientHashTable` avec 1000 buckets

### 6.6 Heap (Tas Max) — Priorité des Rendez-vous
- **Usage :** File de priorité pour les RDV (priorité 3 = critique)
- **Fonction :** `AppointmentHeap` avec `push(priorite, item)` et `pop()`

---

## 7. Sécurité

### 7.1 Authentification
- Hash des mots de passe : **PBKDF2-SHA256** avec sel aléatoire (16 octets)
- 100 000 itérations de dérivation de clé
- Rôles : `patient`, `medecin`, `admin` avec RBAC strict
- Journalisation de toutes les tentatives (succès et échecs)

### 7.2 Traçabilité (Audit)
- Table `audit_log` avec 8 colonnes
- Actions tracées : LOGIN, LOGOUT, REGISTER, LOGIN_FAILED, CREATE_CONSULTATION, CREATE_RDV, CREATE_PRESCRIPTION, ADD_ALLERGIE, DELETE_ALLERGIE, ADD_EXAMEN, VALIDATE_ASSOCIATION, REVOKE_MEDECIN, REQUEST_ASSOCIATION, MEDECIN_VERIFIE, MEDECIN_REJETE, MEDECIN_SUSPENDU, TOGGLE_USER_STATUS, DELETE_USER, SEED, SEED_COMPLETE

### 7.3 Validation des Comptes Médecins
- Inscription → statut `en_attente`
- Validation manuelle par l'administrateur → statut `verifie`
- Possibilité de suspendre ou rejeter
- Traçabilité de l'admin valideur et de la date

---

## 8. Données de Démonstration

### 8.1 Comptes Préchargés (Seed)

| Rôle | Email | Mot de passe | Nom |
|------|-------|-------------|-----|
| Admin | admin@carnetmed.mg | admin123 | Admin Système |
| Patient | patient@exemple.mg | patient123 | Rakoto Jean |
| Médecin | medecin@exemple.mg | medecin123 | Dr. Rasoa Marie |

### 8.2 Données Associées
- Lien patient-médecin (LINK-2024-001)
- Consultation : "Consultation de routine" (15/06/2024)
- Prescription : "Antihistaminique Cetirizine 10mg"
- Rendez-vous : "Suivi mensuel" (15/07/2024, priorité 2)
- Allergie : "Pénicilline" (sévère)
- Examen : "Prise de sang" (15/06/2024)

---

## 9. Interface Desktop — Guide Utilisateur

### 9.1 Navigation
- **Sidebar gauche** (240px) : profil + navigation + déconnexion
- **Contenu principal** : zone de travail avec titres, stats, tableaux
- **Bouton retour** : dans les formulaires d'inscription
- **Onglets** : dans l'interface administrateur

### 9.2 Feedback Utilisateur
- **Toast notifications** : succès (✔ vert), erreur (✘ rouge), info (ℹ bleu), warning (⚠ ambre)
- **ProgressBar** : indéterminée pendant les opérations longues
- **MessageBox** : confirmation pour les actions destructrices
- **Tooltip** : information complémentaire au survol

### 9.3 Shortcuts et UX
- `Enter` dans le champ de recherche → déclenche la recherche KMP
- `Calendar popup` : sélecteur de date intégré
- `ComboBox` : choix prédéfinis pour sexe, groupe sanguin, type RDV, etc.
- `Curseur pointer` : sur tous les boutons et éléments cliquables

---

## 10. Métriques et Statistiques

### 10.1 Tableau de Bord Administrateur
1. Total utilisateurs
2. Total patients
3. Total médecins
4. Médecins en attente de validation
5. Total consultations
6. Total prescriptions
7. Total rendez-vous
8. Total allergies
9. Total examens
10. Total actions auditées

### 10.2 Build Web
| Métrique | Avant | Après |
|----------|-------|-------|
| CSS | 91 kB | 51 kB |
| JS | 612 kB | 612 kB |
| Composants UI | 53 | 17 |
| Dépendances npm | 28 | 21 |
| Erreurs build | 0 | 0 |

---

## 11. Évolutions Futures

- [ ] Service Worker offline-first pour la version web
- [ ] QR Code pour l'association patient-médecin
- [ ] Page de notifications globale
- [ ] Synchronisation automatique desktop ↔ web
- [ ] Téléchargement de fichiers (ordonnances, résultats) via S3
- [ ] Code-splitting du bundle JS (612 kB → chunks)
- [ ] Mode sombre natif (déjà implémenté sur le web)
- [ ] Export PDF du carnet médical
- [ ] Application mobile (Flutter / React Native)
- [ ] Intégration API externe (laboratoires, pharmacies)

---

*Document généré le 29 Mai 2026 — Projet Carnet Médical Numérique — ESMIA INNOVATION*
