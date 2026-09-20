Markdown
# VS Musique

**VS Musique** est une application Python connectée à Spotify permettant de créer, classer et comparer une bibliothèque musicale personnelle.

L'application permet de récupérer des morceaux depuis Spotify, d'ajouter des titres manuellement, d'effectuer un tri rapide, d'affiner le classement avec des duels Elo, d'écouter des extraits, d'afficher les pochettes et de créer une playlist Spotify avec les 100 meilleurs morceaux.

---

## Fonctionnalités

- Menu principal regroupant toutes les fonctions
- Génération de la bibliothèque depuis Spotify
- Import de l'historique Spotify étendu
- Conservation du classement lors d'une nouvelle génération
- Ajout manuel de morceaux
- Recherche de morceaux sur Spotify
- Détection des doublons
- Tri rapide par paliers
- Duels avec classement Elo
- Pochettes d'albums
- Extraits Spotify
- Sauvegarde automatique
- Reprise après fermeture
- Annulation du dernier choix
- Classement complet avec recherche
- Intégration de nouveaux morceaux après la fin du classement
- Création d'une playlist Spotify Top 100
- Nom personnalisé pour la playlist
- Playlist publique ou privée
- Progression de création affichée en temps réel

---

## Structure du projet

```text
spotify_versus/
|-- .env
|-- .env.example
|-- .gitignore
|-- requirements.txt
|-- README.md
|-- main.py
|-- moteur.py
|-- generer_liste.py
|-- ajouter_musique.py
|-- tri_rapide.py
|-- duels_elo.py
|-- playlist_creator.py
|-- scores.json
`-- pochettes/
Description des fichiers
main.py : menu général de l'application

moteur.py : logique Elo, Spotify, extraits et pochettes

generer_liste.py : génère ou actualise la bibliothèque

ajouter_musique.py : ajoute manuellement un morceau

tri_rapide.py : première phase de classement

duels_elo.py : deuxième phase avec les duels Elo

playlist_creator.py : génère la playlist Spotify Top 100

scores.json : stocke les morceaux, les scores et les métadonnées

Prérequis
Python 3.10 ou plus récent

Un compte Spotify

Une application Spotify Developer

Spotify Premium pour piloter la lecture

Spotify ouvert sur un appareil pour écouter les extraits

Installation
Cloner le dépôt :

Bash
git clone [https://github.com/Azarjoe/spotify_versus.git](https://github.com/Azarjoe/spotify_versus.git)
cd spotify_versus
Installer les dépendances :

Bash
pip install -r requirements.txt
Le fichier requirements.txt doit contenir :

Plaintext
spotipy
pillow
Configuration Spotify
Créer un fichier nommé .env à la racine du projet :

Extrait de code
SPOTIPY_CLIENT_ID=ton_client_id
SPOTIPY_CLIENT_SECRET=ton_client_secret
SPOTIPY_REDIRECT_URI=[http://127.0.0.1:8888/callback](http://127.0.0.1:8888/callback)
Ajouter également cette adresse dans les paramètres de l'application Spotify Developer :

Plaintext
[http://127.0.0.1:8888/callback](http://127.0.0.1:8888/callback)
Ne jamais publier les fichiers suivants :

Plaintext
.env
.cache-spotify-top
.cache-spotify-lecture
.cache-spotify-playlist
scores.json
Lancer l'application
Bash
python main.py
Le menu principal permet de :

Générer ou actualiser la liste Spotify

Ajouter une musique

Lancer le tri rapide

Lancer les duels Elo

Voir le classement

Créer la playlist Top 100

Ouvrir le dossier du projet

Actualiser les statistiques

Générer ou actualiser la bibliothèque
Depuis l'API Spotify :

Bash
python generer_liste.py
Si scores.json existe déjà, les morceaux existants conservent leur Elo, leur palier, leurs victoires, leurs défaites, leurs égalités et leurs métadonnées. Seuls les nouveaux morceaux sont ajoutés.

Depuis un historique Spotify étendu :

Bash
python generer_liste.py --historique mon_export.zip --nombre 200
Le script analyse l'historique et compte les écoutes ayant duré au moins 30 secondes.

Ajouter un morceau
Bash
python ajouter_musique.py
L'interface permet de saisir un artiste et un titre, de rechercher le morceau sur Spotify, de choisir la bonne version et d'enregistrer son URI Spotify.

Les doublons sont détectés même si la casse ou les espaces sont différents.

Tri rapide
Bash
python tri_rapide.py
Paliers disponibles :

Plaintext
1 : S - J'adore       - Elo 1120
2 : A - J'aime bien   - Elo 1060
3 : B - Correct       - Elo 1000
4 : C - Bof           - Elo 940
5 : D - Pas pour moi  - Elo 880
Autres commandes :

Plaintext
Espace          : réécouter
P               : passer temporairement
Retour arrière  : annuler
Le palier sert uniquement de point de départ. Les duels Elo corrigent ensuite le classement.

Duels Elo
Bash
python duels_elo.py
Commandes :

Plaintext
Flèche gauche   : voter pour le morceau de gauche
Flèche droite   : voter pour le morceau de droite
Flèche bas      : égalité
1               : écouter le morceau de gauche
2               : écouter le morceau de droite
Retour arrière  : annuler le dernier vote
Par défaut, chaque morceau doit effectuer huit duels.

Pour demander douze duels :

Bash
python duels_elo.py --matchs 12
Les adversaires sont choisis parmi les morceaux ayant un Elo proche.

Un nouveau morceau peut affronter des morceaux ayant déjà atteint leur quota. Le classement ne bloque donc plus lorsqu'un seul nouveau morceau est ajouté.

Classement
Le bouton Voir le classement affiche :

Le rang

L'artiste

Le titre

L'Elo

Le palier

Le nombre de matchs

Les victoires

Les défaites

Les égalités

Une barre de recherche permet de filtrer le classement par artiste ou par titre.

Playlist Spotify Top 100
Depuis le menu principal, cliquer sur Créer la playlist Top 100.

L'application demande :

Le nom de la playlist

Si la playlist doit être publique ou privée

Les 100 meilleurs morceaux sont sélectionnés selon leur Elo.

Une fenêtre affiche la progression en temps réel :

Connexion à Spotify

Préparation des morceaux

Recherche des URI manquantes

Création de la playlist

Ajout des morceaux

Pourcentage de progression

Confirmation finale

Erreurs éventuelles

La playlist peut aussi être créée en ligne de commande :

Bash
python playlist_creator.py --nom "Mon Top 100"
Playlist privée :

Bash
python playlist_creator.py --nom "Mon Top 100" --privee
Nombre personnalisé de morceaux :

Bash
python playlist_creator.py --nom "Mon Top 50" --nombre 50
Extraits Spotify
Par défaut, un extrait commence à 35 % du morceau et dure 20 secondes.

Ces réglages se trouvent dans moteur.py :

Python
EXTRAIT_DEBUT = 0.35
EXTRAIT_DUREE_S = 20
Spotify doit être ouvert sur un appareil actif.

Si aucun appareil n'est détecté :

Ouvrir Spotify

Lancer un morceau

Mettre le morceau en pause

Réessayer dans VS Musique

Sauvegarde
Les données sont enregistrées automatiquement après chaque choix, duel, annulation, ajout manuel ou récupération de métadonnées.

L'écriture de scores.json est atomique afin de réduire le risque de corruption.

Il reste recommandé de conserver régulièrement une copie de scores.json.

Format de scores.json
Exemple :

JSON
{
    "Player - Baby Come Back": {
        "artiste": "Player",
        "musique": "Baby Come Back",
        "elo": 1150,
        "victoires": 5,
        "defaites": 3,
        "egalites": 0,
        "spotify_uri": "spotify:track:41sGGCCoHI2GLV9qadX80A",
        "pochette": "[https://i.scdn.co/image/](https://i.scdn.co/image/)...",
        "duree_ms": 255845,
        "tier": "S"
    }
}
Dépannage
Installer Spotipy :

Bash
pip install spotipy
Installer Pillow :

Bash
pip install pillow
Supprimer les caches Spotify si l'authentification ne fonctionne plus :

Bash
rm -f .cache-spotify-top
rm -f .cache-spotify-lecture
rm -f .cache-spotify-playlist
Vérifier la syntaxe des scripts :

Bash
python -m py_compile main.py moteur.py generer_liste.py ajouter_musique.py tri_rapide.py duels_elo.py playlist_creator.py
Pour éviter les erreurs d'encodage Windows dans les sous-processus, main.py utilise :

Python
environnement["PYTHONUNBUFFERED"] = "1"
environnement["PYTHONIOENCODING"] = "utf-8"
Sécurité
Le fichier .gitignore doit au minimum contenir :

Extrait de code
.env
.cache-spotify*
scores.json
scores.backup-*.json
pochettes/
__pycache__/
*.pyc
*.tmp
.venv/
Si un Client Secret a été publié, il faut le régénérer immédiatement depuis Spotify Developer.

Git
Après une modification :

Bash
git add .
git commit -m "Description de la modification"
git push
État actuel
Fonctionnalités disponibles :

Menu principal

Génération Spotify

Fusion avec le classement existant

Import de l'historique étendu

Ajout manuel

Recherche Spotify

Tri rapide

Duels Elo

Ajout tardif de morceaux

Pochettes

Extraits

Classement avec recherche

Playlist Top 100 personnalisée

Playlist publique ou privée

Progression en temps réel

Sauvegarde automatique

Avertissement
VS Musique est un projet indépendant et n'est pas affilié à Spotify.

L'utilisateur est responsable de la confidentialité des identifiants Spotify, des fichiers de cache et des données d'écoute.