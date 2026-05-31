# Contraintes 2035 — Carnet Medical Numérique

**Projet :** Carnet Médical Numérique Offline-First  
**Auteur :** RANDRIANANTENAINA Nomena Sahaza (SI20240010)  
**Contexte :** Projet Numérique Malagasy 2035 — ESMIA INNOVATION

---

## Déclaration des contraintes

Conformément au cahier des charges, je déclare et justifie les **3 contraintes minimales** suivantes, parmi la liste proposée, qui ont guidé l’architecture et les choix algorithmiques du projet.

---

### Contrainte 1 — Connectivité intermittente

**Déclaration :** Le système doit fonctionner en l’absence totale ou partielle de connexion internet.

**Justification technique :**
- **Architecture offline-first :** L’application desktop utilise **SQLite** comme base de données locale. Toutes les opérations (consultations, prescriptions, rendez-vous) sont possibles hors-ligne.
- **File de synchronisation :** Une table `sync_queue` enregistre les modifications en local. Lorsque la connexion revient, les données sont poussées vers MySQL.
- **Gestion des conflits :** Chaque enregistrement porte un timestamp. En cas de conflit, la version la plus récente est prioritaire.
- **Côté web :** Le hook `useOfflineSync.ts` utilise **IndexedDB** pour mettre en cache les données et les mutations en attente.

**Impact algorithmique :** Implémentation d’une **liste chaînée** (file d’attente de synchronisation) pour stocker les opérations en attente avant réplication.

---

### Contrainte 2 — Faible débit / optimisation des ressources

**Déclaration :** Le système doit minimiser le volume de données échangées et le temps de traitement pour fonctionner sur des connexions à faible débit.

**Justification technique :**
- **Algorithmes optimisés en temps :** KMP (O(n+m)) pour la recherche textuelle, DP (O(n×W)) pour les prescriptions, Greedy (O(n log n)) pour les rendez-vous réduisent le temps de calcul local.
- **Stockage local :** Les données sont traitées et stockées localement, minimisant les échanges réseau. Seules les modifications sont synchronisées.
- **Compression implicite :** Les champs texte sont stockés en SQLite sans indexation lourde côté serveur ; la recherche KMP se fait côté client.

**Impact algorithmique :** Choix du **KMP** (évite le backtracking de la recherche naïve O(n×m)) et du **DP** (évite l’explosion combinatoire O(2^n)).

---

### Contrainte 3 — Sécurité et confidentialité des données médicales

**Déclaration :** Le système doit garantir la confidentialité, l’intégrité et la traçabilité des données médicales (données sensibles).

**Justification technique :**
- **Authentification forte :** Mots de passe hachés avec **PBKDF2-SHA256** (desktop) et **bcrypt** (web). Sessions protégées par **JWT** avec cookies signés (jose).
- **Contrôle d’accès RBAC :** Trois rôles (Patient, Médecin, Administrateur) avec permissions granulaires. Un médecin ne peut accéder qu’aux patients qui l’ont autorisé via un **code de validation mutuelle**.
- **Journal d’audit :** Une table `audit_log` enregistre toutes les actions (connexion, consultation, modification) avec horodatage, adresse IP, utilisateur et statut.
- **Révocation d’accès :** Le patient peut révoquer instantanément l’accès d’un médecin.

**Impact algorithmique :** Utilisation d’une **table de hachage** pour le cache patients (accès O(1) aux dossiers autorisés) et de l’**arbre AVL** pour l’indexation chronologique des consultations (recherche par date en O(log n)).

---

## Tableau récapitulatif

| Contrainte | Architecture | Algorithme associé | Structure de données |
|------------|-------------|-------------------|---------------------|
| Connectivité intermittente | Offline-first (SQLite + sync_queue) | — | Liste chaînée (sync queue) |
| Faible débit / optimisation | Traitement local, sync diff | KMP, DP, Greedy | Hash Table, Heap |
| Sécurité / confidentialité | RBAC, JWT, PBKDF2, audit | — | AVL Tree (indexation) |
