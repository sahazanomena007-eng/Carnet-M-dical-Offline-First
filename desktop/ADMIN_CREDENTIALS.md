# ADMIN CREDENTIALS (Development only)

IMPORTANT: Ce fichier contient des identifiants pour un environnement de développement local. NE PAS COMMITTER dans un dépôt public ni l'utiliser en production.

## Compte administrateur (dev)
- Email: admin@carnetmed.local
- Mot de passe: D3vAdm!n-9u7Xv2$

Ces identifiants servent uniquement pour tester l'application en local. Changez le mot de passe après import ou mieux : créez l'utilisateur via une commande protégée.

## Commande rapide (exécuter depuis la racine du projet) — crée l'utilisateur admin en local
```bash
python -c "import sys; sys.path.insert(0, r'D:/PROJET_TRANSVERSALE/L2/Carnet Médical Offline-First/desktop'); import db; db.create_user('admin@carnetmed.local','D3vAdm!n-9u7Xv2$','admin','Admin','Systeme')"
```

## Sécurité et bonnes pratiques
- Ne laissez jamais de mots de passe en clair dans le code ou le dépôt.
- Ajoutez ce fichier à `.gitignore` (voir section suivante) ou stockez les secrets dans des variables d'environnement ou un gestionnaire de secrets.
- Pour la production, créez les comptes via un workflow sécurisé et forcez le changement de mot de passe.

## `.gitignore` suggestion
Ajoutez la ligne suivante dans votre `.gitignore` pour éviter de committer ce fichier :

```
/desktop/ADMIN_CREDENTIALS.md
```

---
Fichier généré automatiquement pour le développement local. Supprimez-le ou chiffrez-le avant tout partage.
