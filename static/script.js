// Ce fichier contient deux fonctionnalités JavaScript indépendantes :
// 1. Le recalcul automatique des quantités d'ingrédients sur la page détail.
// 2. L'ajout/suppression dynamique de lignes dans le formulaire ingrédients/étapes.
// Chaque bloc vérifie que les éléments existent avant d'agir, car ce même
// fichier est chargé sur plusieurs pages différentes.

// --- 1. Recalcul des quantités selon le nombre de personnes ---

const inputPersonnes = document.getElementById("personnes");

if (inputPersonnes) {
    const portionsBase = parseFloat(inputPersonnes.dataset.portionsBase);

    function recalculerQuantites() {
        let personnesVoulues = parseFloat(inputPersonnes.value);
        if (!personnesVoulues || personnesVoulues <= 0) {
            personnesVoulues = portionsBase;
        }
        const ratio = personnesVoulues / portionsBase;

        document.querySelectorAll("#liste-ingredients li").forEach(function (ligne) {
            const quantiteBase = parseFloat(ligne.dataset.quantiteBase);
            const nouvelleQuantite = Math.round(quantiteBase * ratio * 100) / 100;
            ligne.querySelector(".quantite-affichee").textContent = nouvelleQuantite;
        });
    }

    inputPersonnes.addEventListener("input", recalculerQuantites);
}

// --- 2. Ajout et suppression dynamique de lignes dans le formulaire ---

function ajouterLigne(idBoutonAjout, idModele, idConteneur) {
    const boutonAjout = document.getElementById(idBoutonAjout);
    const modele = document.getElementById(idModele);
    const conteneur = document.getElementById(idConteneur);

    if (!boutonAjout || !modele || !conteneur) {
        return;
    }

    boutonAjout.addEventListener("click", function () {
        const nouvelleLigne = modele.content.cloneNode(true);
        conteneur.appendChild(nouvelleLigne);
    });
}

ajouterLigne("ajouter-ingredient", "modele-ligne-ingredient", "lignes-ingredients");
ajouterLigne("ajouter-etape", "modele-ligne-etape", "lignes-etapes");

// Suppression d'une ligne : on écoute les clics sur les conteneurs plutôt que
// sur chaque bouton individuellement, pour que ça fonctionne aussi sur les
// lignes ajoutées dynamiquement.
["lignes-ingredients", "lignes-etapes"].forEach(function (idConteneur) {
    const conteneur = document.getElementById(idConteneur);
    if (!conteneur) {
        return;
    }
    conteneur.addEventListener("click", function (evenement) {
        if (evenement.target.classList.contains("bouton-supprimer-ligne")) {
            evenement.target.closest(".ligne-ingredient, .ligne-etape").remove();
        }
    });
});
