# -*- coding: utf-8 -*-
"""
Application Flask de gestion de recettes de cuisine.
Toutes les routes (pages web) de l'application sont définies dans ce fichier.
L'accès à la base de données se fait via les fonctions du fichier database.py.
"""

from flask import Flask, render_template, request, redirect, url_for, flash, abort

import database

app = Flask(__name__)
# Clé secrète nécessaire pour utiliser les messages flash (confirmation/erreur)
app.secret_key = "cle-secrete-pour-un-exercice-pedagogique"


@app.template_filter("quantite")
def formater_quantite(valeur):
    """Affiche un nombre entier sans décimale (ex: 4 plutôt que 4.0)."""
    if valeur == int(valeur):
        return int(valeur)
    return valeur


def lire_ingredients_du_formulaire():
    """
    Lit les listes d'ingrédients envoyées par le formulaire (noms, quantités,
    unités) et les transforme en liste de tuples (nom, quantite, unite).
    Les lignes sans nom sont ignorées (ligne vide laissée par l'utilisateur).
    """
    noms = request.form.getlist("ingredient_nom[]")
    quantites = request.form.getlist("ingredient_quantite[]")
    unites = request.form.getlist("ingredient_unite[]")

    ingredients = []
    for nom, quantite_texte, unite in zip(noms, quantites, unites):
        nom = nom.strip()
        if not nom:
            continue
        try:
            quantite = float(quantite_texte.replace(",", "."))
        except ValueError:
            quantite = 0
        ingredients.append((nom, quantite, unite.strip()))
    return ingredients


def lire_etapes_du_formulaire():
    """Lit la liste des étapes envoyées par le formulaire, en ignorant les lignes vides."""
    textes = request.form.getlist("etape_texte[]")
    return [texte.strip() for texte in textes if texte.strip()]


@app.route("/")
def index():
    """Page d'accueil : liste des recettes, avec filtre par catégorie et recherche."""
    categorie = request.args.get("categorie") or None
    recherche = request.args.get("q") or None

    recettes = database.get_toutes_recettes(categorie=categorie, recherche=recherche)

    return render_template(
        "index.html",
        recettes=recettes,
        categories=database.CATEGORIES,
        categorie_selectionnee=categorie,
        recherche=recherche,
    )


@app.route("/favoris")
def favoris():
    """Page listant uniquement les recettes marquées comme favorites."""
    recettes = database.get_favoris()
    return render_template("favoris.html", recettes=recettes)


@app.route("/recette/<int:recipe_id>")
def detail(recipe_id):
    """Page de détail d'une recette."""
    donnees = database.get_recette(recipe_id)
    if donnees is None:
        abort(404)
    return render_template(
        "detail.html",
        recette=donnees["recette"],
        ingredients=donnees["ingredients"],
        steps=donnees["steps"],
    )


@app.route("/recette/ajouter", methods=["GET", "POST"])
def ajouter_recette():
    """Affiche le formulaire d'ajout (GET) et traite son envoi (POST)."""
    if request.method == "POST":
        titre = request.form.get("titre", "").strip()
        ingredients = lire_ingredients_du_formulaire()
        steps = lire_etapes_du_formulaire()

        # Validation minimale côté serveur
        if not titre:
            flash("Le titre de la recette est obligatoire.")
        elif not ingredients:
            flash("Merci d'ajouter au moins un ingrédient.")
        elif not steps:
            flash("Merci d'ajouter au moins une étape de préparation.")
        else:
            recipe_id = database.create_recipe(
                titre=titre,
                description=request.form.get("description", "").strip(),
                temps_preparation=int(request.form.get("temps_preparation") or 0),
                temps_cuisson=int(request.form.get("temps_cuisson") or 0),
                nombre_personnes=int(request.form.get("nombre_personnes") or 4),
                categorie=request.form.get("categorie"),
                ingredients=ingredients,
                steps=steps,
            )
            flash("Recette ajoutée avec succès !")
            return redirect(url_for("detail", recipe_id=recipe_id))

    return render_template(
        "_form.html",
        mode="ajout",
        categories=database.CATEGORIES,
        recette=None,
        ingredients=[],
        steps=[],
    )


@app.route("/recette/<int:recipe_id>/modifier", methods=["GET", "POST"])
def modifier_recette(recipe_id):
    """Affiche le formulaire de modification pré-rempli (GET) et traite son envoi (POST)."""
    donnees = database.get_recette(recipe_id)
    if donnees is None:
        abort(404)

    if request.method == "POST":
        titre = request.form.get("titre", "").strip()
        ingredients = lire_ingredients_du_formulaire()
        steps = lire_etapes_du_formulaire()

        if not titre:
            flash("Le titre de la recette est obligatoire.")
        elif not ingredients:
            flash("Merci d'ajouter au moins un ingrédient.")
        elif not steps:
            flash("Merci d'ajouter au moins une étape de préparation.")
        else:
            database.update_recipe(
                recipe_id,
                titre=titre,
                description=request.form.get("description", "").strip(),
                temps_preparation=int(request.form.get("temps_preparation") or 0),
                temps_cuisson=int(request.form.get("temps_cuisson") or 0),
                nombre_personnes=int(request.form.get("nombre_personnes") or 4),
                categorie=request.form.get("categorie"),
                ingredients=ingredients,
                steps=steps,
            )
            flash("Recette modifiée avec succès !")
            return redirect(url_for("detail", recipe_id=recipe_id))

    return render_template(
        "_form.html",
        mode="modification",
        categories=database.CATEGORIES,
        recette=donnees["recette"],
        ingredients=donnees["ingredients"],
        steps=donnees["steps"],
    )


@app.route("/recette/<int:recipe_id>/supprimer", methods=["POST"])
def supprimer_recette(recipe_id):
    """Supprime une recette. La confirmation est demandée côté client (JS)."""
    database.delete_recipe(recipe_id)
    flash("Recette supprimée.")
    return redirect(url_for("index"))


@app.route("/recette/<int:recipe_id>/favori", methods=["POST"])
def basculer_favori(recipe_id):
    """Ajoute ou retire une recette des favoris, puis revient sur la page d'origine."""
    database.toggle_favori(recipe_id)
    return redirect(request.referrer or url_for("detail", recipe_id=recipe_id))


# Initialisation de la base de données au démarrage de l'application
database.init_db()
if database.base_vide():
    database.inserer_recettes_exemple()


if __name__ == "__main__":
    app.run(debug=True)
