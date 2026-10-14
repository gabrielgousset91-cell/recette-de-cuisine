# -*- coding: utf-8 -*-
"""
Ce fichier regroupe toutes les fonctions qui parlent à la base de données SQLite.
On utilise le module "sqlite3" de la bibliothèque standard de Python, sans ORM,
pour que le code reste simple à lire et à comprendre.
"""

import sqlite3

# Nom du fichier de base de données (créé automatiquement s'il n'existe pas encore)
NOM_BASE = "recettes.db"

# Liste des catégories proposées pour une recette (utilisée dans les formulaires et les filtres)
CATEGORIES = ["Entrée", "Plat", "Dessert", "Soupe", "Boisson"]


def get_connection():
    """Ouvre une connexion à la base de données et la configure correctement."""
    connexion = sqlite3.connect(NOM_BASE)
    # row_factory permet d'accéder aux colonnes par leur nom (ex: ligne["titre"])
    connexion.row_factory = sqlite3.Row
    # Important : sqlite3 n'active pas les clés étrangères par défaut.
    # Sans cette ligne, le "ON DELETE CASCADE" ne fonctionnerait pas.
    connexion.execute("PRAGMA foreign_keys = ON")
    return connexion


def init_db():
    """Crée les tables de la base de données si elles n'existent pas déjà."""
    connexion = get_connection()
    connexion.execute("""
        CREATE TABLE IF NOT EXISTS recipes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titre TEXT NOT NULL,
            description TEXT,
            temps_preparation INTEGER NOT NULL DEFAULT 0,
            temps_cuisson INTEGER NOT NULL DEFAULT 0,
            nombre_personnes INTEGER NOT NULL DEFAULT 4,
            categorie TEXT NOT NULL,
            favori INTEGER NOT NULL DEFAULT 0,
            date_creation TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)
    connexion.execute("""
        CREATE TABLE IF NOT EXISTS ingredients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            recipe_id INTEGER NOT NULL,
            nom TEXT NOT NULL,
            quantite REAL NOT NULL,
            unite TEXT NOT NULL DEFAULT '',
            ordre INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE
        )
    """)
    connexion.execute("""
        CREATE TABLE IF NOT EXISTS steps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            recipe_id INTEGER NOT NULL,
            numero INTEGER NOT NULL,
            texte TEXT NOT NULL,
            FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE
        )
    """)
    connexion.commit()
    connexion.close()


def base_vide():
    """Retourne True s'il n'y a encore aucune recette dans la base."""
    connexion = get_connection()
    resultat = connexion.execute("SELECT COUNT(*) AS total FROM recipes").fetchone()
    connexion.close()
    return resultat["total"] == 0


def create_recipe(titre, description, temps_preparation, temps_cuisson,
                   nombre_personnes, categorie, ingredients, steps):
    """
    Crée une nouvelle recette.
    - ingredients : liste de tuples (nom, quantite, unite)
    - steps : liste de chaînes de texte, dans l'ordre des étapes
    Retourne l'identifiant de la recette créée.
    """
    connexion = get_connection()
    curseur = connexion.execute("""
        INSERT INTO recipes (titre, description, temps_preparation, temps_cuisson,
                              nombre_personnes, categorie)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (titre, description, temps_preparation, temps_cuisson, nombre_personnes, categorie))

    recipe_id = curseur.lastrowid

    for position, (nom, quantite, unite) in enumerate(ingredients):
        connexion.execute("""
            INSERT INTO ingredients (recipe_id, nom, quantite, unite, ordre)
            VALUES (?, ?, ?, ?, ?)
        """, (recipe_id, nom, quantite, unite, position))

    for position, texte in enumerate(steps):
        connexion.execute("""
            INSERT INTO steps (recipe_id, numero, texte)
            VALUES (?, ?, ?)
        """, (recipe_id, position + 1, texte))

    connexion.commit()
    connexion.close()
    return recipe_id


def update_recipe(recipe_id, titre, description, temps_preparation, temps_cuisson,
                   nombre_personnes, categorie, ingredients, steps):
    """
    Met à jour une recette existante.
    Pour rester simple, on supprime tous ses ingrédients/étapes puis on les
    réinsère, plutôt que de calculer un "diff" ligne par ligne.
    """
    connexion = get_connection()
    connexion.execute("""
        UPDATE recipes
        SET titre = ?, description = ?, temps_preparation = ?, temps_cuisson = ?,
            nombre_personnes = ?, categorie = ?
        WHERE id = ?
    """, (titre, description, temps_preparation, temps_cuisson,
          nombre_personnes, categorie, recipe_id))

    connexion.execute("DELETE FROM ingredients WHERE recipe_id = ?", (recipe_id,))
    connexion.execute("DELETE FROM steps WHERE recipe_id = ?", (recipe_id,))

    for position, (nom, quantite, unite) in enumerate(ingredients):
        connexion.execute("""
            INSERT INTO ingredients (recipe_id, nom, quantite, unite, ordre)
            VALUES (?, ?, ?, ?, ?)
        """, (recipe_id, nom, quantite, unite, position))

    for position, texte in enumerate(steps):
        connexion.execute("""
            INSERT INTO steps (recipe_id, numero, texte)
            VALUES (?, ?, ?)
        """, (recipe_id, position + 1, texte))

    connexion.commit()
    connexion.close()


def delete_recipe(recipe_id):
    """Supprime une recette. Grâce à ON DELETE CASCADE, ses ingrédients et
    étapes sont supprimés automatiquement."""
    connexion = get_connection()
    connexion.execute("DELETE FROM recipes WHERE id = ?", (recipe_id,))
    connexion.commit()
    connexion.close()


def toggle_favori(recipe_id):
    """Inverse le statut favori d'une recette (0 devient 1, 1 devient 0)."""
    connexion = get_connection()
    connexion.execute("UPDATE recipes SET favori = 1 - favori WHERE id = ?", (recipe_id,))
    connexion.commit()
    connexion.close()


def get_toutes_recettes(categorie=None, recherche=None):
    """
    Retourne la liste des recettes, avec filtre optionnel par catégorie et
    recherche optionnelle par mot-clé (sur le titre OU le nom d'un ingrédient).
    """
    connexion = get_connection()

    requete = """
        SELECT DISTINCT r.*
        FROM recipes r
        LEFT JOIN ingredients i ON i.recipe_id = r.id
        WHERE 1 = 1
    """
    parametres = []

    if categorie:
        requete += " AND r.categorie = ?"
        parametres.append(categorie)

    if recherche:
        requete += " AND (r.titre LIKE ? OR i.nom LIKE ?)"
        mot_cle = "%" + recherche + "%"
        parametres.extend([mot_cle, mot_cle])

    requete += " ORDER BY r.titre"

    recettes = connexion.execute(requete, parametres).fetchall()
    connexion.close()
    return recettes


def get_recette(recipe_id):
    """
    Retourne toutes les informations d'une recette (infos, ingrédients, étapes)
    sous la forme d'un dictionnaire, ou None si la recette n'existe pas.
    """
    connexion = get_connection()

    recette = connexion.execute("SELECT * FROM recipes WHERE id = ?", (recipe_id,)).fetchone()
    if recette is None:
        connexion.close()
        return None

    ingredients = connexion.execute(
        "SELECT * FROM ingredients WHERE recipe_id = ? ORDER BY ordre", (recipe_id,)
    ).fetchall()

    steps = connexion.execute(
        "SELECT * FROM steps WHERE recipe_id = ? ORDER BY numero", (recipe_id,)
    ).fetchall()

    connexion.close()
    return {"recette": recette, "ingredients": ingredients, "steps": steps}


def get_favoris():
    """Retourne la liste des recettes marquées comme favorites."""
    connexion = get_connection()
    favoris = connexion.execute(
        "SELECT * FROM recipes WHERE favori = 1 ORDER BY titre"
    ).fetchall()
    connexion.close()
    return favoris


def inserer_recettes_exemple():
    """Ajoute quelques recettes d'exemple pour que l'application ne soit pas vide
    lors du premier lancement."""

    create_recipe(
        titre="Salade de tomates mozzarella",
        description="Une entrée fraîche et simple, parfaite en été.",
        temps_preparation=15,
        temps_cuisson=0,
        nombre_personnes=4,
        categorie="Entrée",
        ingredients=[
            ("Tomates", 4, "pièce"),
            ("Mozzarella", 200, "g"),
            ("Basilic frais", 10, "feuilles"),
            ("Huile d'olive", 3, "c. à soupe"),
            ("Sel", 1, "pincée"),
        ],
        steps=[
            "Laver et couper les tomates en rondelles.",
            "Couper la mozzarella en tranches.",
            "Disposer en alternance sur un plat.",
            "Ajouter le basilic, l'huile d'olive et le sel.",
        ],
    )

    create_recipe(
        titre="Pâtes à la carbonara",
        description="Un classique italien rapide à préparer.",
        temps_preparation=10,
        temps_cuisson=15,
        nombre_personnes=4,
        categorie="Plat",
        ingredients=[
            ("Spaghettis", 400, "g"),
            ("Lardons", 200, "g"),
            ("Œufs", 3, "pièce"),
            ("Parmesan", 100, "g"),
            ("Poivre", 1, "pincée"),
        ],
        steps=[
            "Faire cuire les spaghettis dans l'eau bouillante salée.",
            "Faire revenir les lardons à la poêle.",
            "Battre les œufs avec le parmesan.",
            "Mélanger les pâtes chaudes, les lardons et la préparation aux œufs hors du feu.",
            "Poivrer et servir immédiatement.",
        ],
    )

    create_recipe(
        titre="Poulet rôti aux légumes",
        description="Un plat familial et réconfortant.",
        temps_preparation=20,
        temps_cuisson=60,
        nombre_personnes=6,
        categorie="Plat",
        ingredients=[
            ("Poulet entier", 1, "pièce"),
            ("Pommes de terre", 6, "pièce"),
            ("Carottes", 4, "pièce"),
            ("Oignon", 2, "pièce"),
            ("Huile d'olive", 2, "c. à soupe"),
            ("Thym", 1, "branche"),
        ],
        steps=[
            "Préchauffer le four à 200°C.",
            "Couper les légumes en morceaux.",
            "Disposer le poulet et les légumes dans un plat, arroser d'huile d'olive.",
            "Ajouter le thym, saler, poivrer.",
            "Enfourner 1 heure en arrosant régulièrement.",
        ],
    )

    create_recipe(
        titre="Crêpes faciles",
        description="Un dessert gourmand pour toute la famille.",
        temps_preparation=10,
        temps_cuisson=20,
        nombre_personnes=8,
        categorie="Dessert",
        ingredients=[
            ("Farine", 250, "g"),
            ("Œufs", 3, "pièce"),
            ("Lait", 500, "ml"),
            ("Sucre", 2, "c. à soupe"),
            ("Beurre fondu", 50, "g"),
            ("Sel", 1, "pincée"),
        ],
        steps=[
            "Mélanger la farine, le sucre et le sel.",
            "Ajouter les œufs puis le lait petit à petit.",
            "Incorporer le beurre fondu.",
            "Laisser reposer la pâte 30 minutes.",
            "Cuire les crêpes à la poêle chaude légèrement beurrée.",
        ],
    )
