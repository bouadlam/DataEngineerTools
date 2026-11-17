# Introduction — solutions et mode d'emploi

Les énoncés du professeur sont conservés. Les solutions de la partie 4 sont placées après les exercices et les fonctions de la partie 5 sont complétées.

## Démarrage sur Windows

Ouvrir le dossier du dépôt dans VS Code, puis dans PowerShell :

```powershell
uv sync --locked --python 3.12
uv run python -c "import sys; print(sys.version); print(sys.executable)"
```

Installer les extensions Microsoft Python et Jupyter dans VS Code. Ouvrir un notebook et sélectionner le Python du dossier `.venv` comme kernel. Exécuter les cellules de haut en bas. Autre possibilité : `uv run jupyter notebook`.

## Contenu

- Partie 1 : environnement Python et vérification Windows ; `.python-version` ajouté à la racine.
- Partie 2 : commandes Git adaptées au fork et fichier `gittest.txt`.
- Partie 3 : précisions Docker, Dockerfile et programme minimal de démonstration.
- Partie 4 : client HTTP avec reprises récursives bornées, nettoyage, parsing, extraction Google et collecte RSS avec export JSON.
- Partie 5 : prix en GBP, URL d'image, note de 1 à 5, tableau des livres, attente explicite et fermeture du navigateur.
- `intro_solutions.py` : mêmes fonctions de la partie 4, utilisables sans notebook.
- `test_intro.py` : tests déterministes, sans dépendre de sites externes.

## Validation effectuée le 17 novembre 2026

- Installation des dépendances verrouillées avec Python 3.12.14 : réussie.
- Structure des quatre notebooks et syntaxe de toutes leurs cellules : valides.
- Sept tests : réussis (retries, arrêt sur 404, HTML, résultats Google, RSS et fonctions Selenium).
- Cellules Python de la partie 4 : exécutées directement dans l'ordre avec succès.
- Projet final : deux vrais articles publics BBC collectés ; résultats dans `results/news_bbc.json`.
- Flux Le Monde accessible, mais les trois articles essayés répondent HTTP 402 ; journal dans `results/news.json`. Aucune tentative de contournement.
- Google : HTTP 429 dans cet environnement. Le parseur a été testé sur un exemple HTML ; aucun résultat Google réel n'est prétendu.
- Selenium : fonctions testées, mais le navigateur ne démarre pas ici (`SessionNotCreatedException`). Une exécution complète sur le site Books to Scrape reste à faire sur un PC équipé de Chrome.
- Docker : moteur absent ici, Dockerfile fourni mais construction non exécutée.
- Jupyter : démarrage d'un kernel bloqué par l'environnement distant ; exécution Python directe utilisée pour vérifier la partie 4.

Les cellules de collecte contactent des sites réels et peuvent échouer si leur structure, leur accès ou leur disponibilité change. Respecter les règles du site ; aucun contournement des pages protégées n'est fourni. Le nettoyage du texte principal est une heuristique à adapter au média.

## Rejouer les tests

Depuis la racine :

```powershell
uv run python -m unittest discover -s 1Introduction -p "test_*.py" -v
```

## Récupération et publication

Le dépôt distant n'a pas été modifié : le plugin GitHub est indisponible et Git ne dispose pas d'authentification pour envoyer les changements.
L'archive livrée contient les fichiers du projet, sans `.git` ni `.venv`. Copier son dossier `1Introduction` et son fichier `.python-version` dans votre clone existant. Les autres chapitres sont inchangés.
Puis, pour publier depuis votre PC connecté à GitHub :

```powershell
git switch -c introduction-complete
git add .python-version 1Introduction
git commit -m "Compléter les exercices Introduction"
git push -u origin introduction-complete
```

Lire et comprendre les solutions avant de les présenter ; les étapes non exécutées ci-dessus restent à vérifier sur votre PC.
