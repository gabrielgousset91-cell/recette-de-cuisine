# Mes Recettes

Application web de gestion de recettes de cuisine, réalisée dans le cadre d'un exercice de formation avec **Python / Flask** et **SQLite**.

## Fonctionnalités

- Ajouter une recette : titre, description, temps de préparation, temps de cuisson, nombre de personnes, catégorie, ingrédients (nom, quantité, unité) et étapes de préparation.
- Lister toutes les recettes, avec filtre par catégorie et recherche par mot-clé (sur le titre ou sur un ingrédient).
- Voir le détail complet d'une recette.
- Modifier ou supprimer une recette (une confirmation est demandée avant toute suppression).
- Marquer une recette en favori et consulter la page "Mes favoris".
- Sur la page détail, ajuster le nombre de personnes : les quantités d'ingrédients se recalculent automatiquement.
- Au premier lancement, quelques recettes d'exemple sont ajoutées automatiquement pour ne pas démarrer avec une application vide.

## Organisation du code

- `app.py` : toutes les routes Flask (pages de l'application).
- `database.py` : toutes les fonctions d'accès à la base de données SQLite (pas d'ORM, requêtes SQL directes).
- `templates/` : les pages HTML (Jinja2).
- `static/` : feuille de style CSS et script JavaScript.
- `recettes.db` : la base de données SQLite, créée automatiquement au premier lancement.

## Installation

Depuis le dossier `site_web`, créez un environnement virtuel puis installez les dépendances :

```bash
python -m venv venv
venv\Scripts\activate       # sur Windows
pip install -r requirements.txt
```

## Lancement

```bash
python app.py
```

Ouvrez ensuite votre navigateur à l'adresse [http://127.0.0.1:5000](http://127.0.0.1:5000).

La base de données `recettes.db` est créée automatiquement lors du premier lancement, avec quelques recettes d'exemple.

## Limitations (volontaires, dans un but pédagogique)

- Pas de système d'authentification : l'application est pensée pour un seul utilisateur.
- Pas d'ORM : les requêtes SQL sont écrites directement dans `database.py` pour rester simples à lire.
- Base de données locale (fichier SQLite), non adaptée à un déploiement multi-utilisateurs.
