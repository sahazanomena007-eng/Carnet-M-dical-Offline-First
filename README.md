# Carnet Medical Numerique - Numerique Malagasy 2035

## Projet academique - L2 SIO - ESMIA INNOVATION

Systeme de gestion de carnet medical numerique, offline-first, securise et multilingue (FR/MG), conqu pour le contexte malgache 2035 avec connectivite intermittente.

---

## Architecture

```
.
├── web/                    # Application Web (Node.js + React)
│   ├── api/               # Backend tRPC + Hono
│   ├── db/                # Schema Drizzle ORM + MySQL
│   ├── src/               # Frontend React + Tailwind
│   └── dist/              # Build production
├── desktop/               # Application Desktop (PyQt5)
│   ├── main.py            # Point d'entree
│   ├── db.py              # Base SQLite + sync
│   ├── algorithms.py      # Algorithmes (KMP, Greedy, DP, AVL, Hash, Heap)
│   └── requirements.txt   # Dependances Python
└── README.md              # Ce fichier
```

---

## Technologies

| Composant | Technologie |
|-----------|-------------|
| Frontend Web | React 19 + TypeScript + Tailwind CSS + shadcn/ui |
| Backend Web | Hono + tRPC 11 + Drizzle ORM |
| Base de donnees | MySQL (cloud) + SQLite (local/offline) |
| Auth | OAuth 2.0 + Sessions JWT |
| Desktop | PyQt5 + SQLite |
| Algorithme 1 | Glouton - Optimisation des rendez-vous O(n log n) |
| Algorithme 2 | KMP - Recherche dans l'historique O(n+m) |
| Algorithme 3 | Programmation Dynamique (Sac a dos) - Prescriptions O(nxW) |
| Structures | Table de hachage, AVL, Heap, Liste chainee |

---

## Rôles et Permissions

### Patient
- Consulter son carnet medical
- Gerer ses allergies
- Voir ses rendez-vous et prescriptions
- Revquer l'acces d'un medecin
- Valider une association medecin par code

### Medecin
- Consulter les dossiers patients (apres autorisation)
- Ajouter des consultations, prescriptions, rendez-vous
- Rechercher dans l'historique (KMP)
- Planifier et optimiser les rendez-vous
- Optimiser les prescriptions (programmation dynamique)

### Administrateur
- Valider les comptes medecins
- Gerer les utilisateurs et permissions
- Consulter le journal d'audit
- Suspendre/Reactiver des comptes

---

## Lancer l'application Web

```bash
cd web
npm install
npm run db:push    # Sync schema MySQL
npm run dev        # Dev server http://localhost:3000
npm run build      # Production build
```

## Lancer l'application Desktop

```bash
cd desktop
pip install -r requirements.txt
python main.py
```

---

## Algorithmes implementes

### 1. Optimisation des rendez-vous (Glouton)
- **Objectif**: Minimiser les conflits horaires
- **Methode**: Trier par priorite decroissante, selection gloutonne sans chevauchement
- **Complexite**: O(n log n)

### 2. Recherche rapide dans l'historique (KMP)
- **Objectif**: Rechercher efficacement dans le texte medical
- **Methode**: Pretraitement LPS, recherche sans retour arriere
- **Complexite**: O(n + m)

### 3. Optimisation des prescriptions (Programmation Dynamique)
- **Objectif**: Selection optimale de medicaments selon le budget
- **Methode**: Algorithme du sac a dos 0/1
- **Complexite**: O(n x W)

### Structures de donnees
- **Table de hachage**: Acces rapide O(1) aux patients par numero de dossier
- **Arbre AVL**: Stockage equilibre de l'historique des consultations
- **Heap (Tas)**: Gestion prioritaire des rendez-vous urgents
- **Liste chainee**: Stockage offline leger des donnees en attente de sync

---

## Securite

- Authentification par mot de passe fort (PBKDF2)
- Chiffrement des donnees sensibles
- Gestion RBAC (Role-Based Access Control)
- Journal d'audit complet des actions
- Association patient-medecin par code de validation mutuelle
- Revocation d'acces instantanee
- Protection contre les acces non autorises

---

## Synchronisation Offline-First

1. Les donnees sont stockees localement en SQLite
2. Une file de synchronisation (sync_queue) enregistre les modifications
3. Lorsque la connexion revient, les donnees sont synchronisees avec MySQL
4. Gestion des conflits par timestamp

---

## Auteur

**RANDRIANANTENAINA Nomena Sahaza**
- NIE: SI20240010
- L2 SIO - ESMIA INNOVATION
- Projet Numerique Malagasy 2035
