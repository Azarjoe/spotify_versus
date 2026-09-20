# VS Musique

VS Musique est une application Python connectee a Spotify permettant de creer, classer et comparer une bibliotheque musicale personnelle.

L'application permet de recuperer des morceaux depuis Spotify, d'ajouter des titres manuellement, d'effectuer un tri rapide, d'affiner le classement avec des duels Elo, d'ecouter des extraits, d'afficher les pochettes et de creer une playlist Spotify avec les 100 meilleurs morceaux.

---

## Fonctionnalites

- Menu principal regroupant toutes les fonctions
- Generation de la bibliotheque depuis Spotify
- Import de l'historique Spotify etendu
- Conservation du classement lors d'une nouvelle generation
- Ajout manuel de morceaux
- Recherche de morceaux sur Spotify
- Detection des doublons
- Tri rapide par paliers
- Duels avec classement Elo
- Pochettes d'albums
- Extraits Spotify
- Sauvegarde automatique
- Reprise apres fermeture
- Annulation du dernier choix
- Classement complet avec recherche
- Integration de nouveaux morceaux apres la fin du classement
- Creation d'une playlist Spotify Top 100
- Nom personnalise pour la playlist
- Playlist publique ou privee
- Progression de creation affichee en temps reel

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
```

### Description des fichiers

- main.py : menu general de l'application
- moteur.py : logique Elo, Spotify, extraits et pochettes
- generer_liste.py : genere ou actualise la bibliotheque
- ajouter_musique.py : ajoute manuellement un morceau
- tri_rapide.py : premiere phase de classement
- duels_elo.py : deuxieme phase avec les duels Elo
- playlist_creator.py : genere la playlist Spotify Top 100
- scores.json : stocke les morceaux, les scores et les metadonnees

---

## Prerequis

- Python 3.10 ou plus recent
- Un compte Spotify
- Une application Spotify Developer
- Spotify Premium pour piloter la lecture
- Spotify ouvert sur un appareil pour ecouter les extraits

---

## Installation

Cloner le depot :

```bash
git clone https://github.com/Azarjoe/spotify_versus.git
cd spotify_versus
```

Installer les dependances :

```bash
pip install -r requirements.txt
```

Le fichier requirements.txt doit contenir :

```text
spotipy
pillow
```

---

## Configuration Spotify

Creer un fichier nomme .env a la racine du projet :

```env
SPOTIPY_CLIENT_ID=ton_client_id
SPOTIPY_CLIENT_SECRET=ton_client_secret
SPOTIPY_REDIRECT_URI=http://127.0.0.1:8888/callback
```

Ajouter egalement cette adresse dans les parametres de l'application Spotify Developer :

```text
http://127.0.0.1:8888/callback
```

Ne jamais publier les fichiers suivants :

```text
.env
.cache-spotify-top
.cache-spotify-lecture
.cache-spotify-playlist
scores.json
```

---

## Lancer l'application

```bash
python main.py
```

Le menu principal permet de :

1. Generer ou actualiser la liste Spotify
2. Ajouter une musique
3. Lancer le tri rapide
4. Lancer les duels Elo
5. Voir le classement
6. Creer la playlist Top 100
7. Ouvrir le dossier du projet
8. Actualiser les statistiques

---

## Generer ou actualiser la bibliotheque

Depuis l'API Spotify :

```bash
python generer_liste.py
```

Si scores.json existe deja, les morceaux existants conservent leur Elo, leur palier, leurs victoires, leurs defaites, leurs egalites et leurs metadonnees. Seuls les nouveaux morceaux sont ajoutes.

Depuis un historique Spotify etendu :

```bash
python generer_liste.py --historique mon_export.zip --nombre 200
```

Le script analyse l'historique et compte les ecoutes ayant dure au moins 30 secondes.

---

## Ajouter un morceau

```bash
python ajouter_musique.py
```

L'interface permet de saisir un artiste et un titre, de rechercher le morceau sur Spotify, de choisir la bonne version et d'enregistrer son URI Spotify.

Les doublons sont detectes meme si la casse ou les espaces sont differents.

---

## Tri rapide

```bash
python tri_rapide.py
```

Paliers disponibles :

```text
1 : S - J'adore       - Elo 1120
2 : A - J'aime bien   - Elo 1060
3 : B - Correct       - Elo 1000
4 : C - Bof           - Elo 940
5 : D - Pas pour moi  - Elo 880
```

Autres commandes :

```text
Espace          : reecouter
P               : passer temporairement
Retour arriere  : annuler
```

Le palier sert uniquement de point de depart. Les duels Elo corrigent ensuite le classement.

---

## Duels Elo

```bash
python duels_elo.py
```

Commandes :

```text
Fleche gauche   : voter pour le morceau de gauche
Fleche droite   : voter pour le morceau de droite
Fleche bas      : egalite
1               : ecouter le morceau de gauche
2               : ecouter le morceau de droite
Retour arriere  : annuler le dernier vote
```

Par defaut, chaque morceau doit effectuer huit duels.

Pour demander douze duels :

```bash
python duels_elo.py --matchs 12
```

Les adversaires sont choisis parmi les morceaux ayant un Elo proche.

Un nouveau morceau peut affronter des morceaux ayant deja atteint leur quota. Le classement ne bloque donc plus lorsqu'un seul nouveau morceau est ajoute.

---

## Classement

Le bouton Voir le classement affiche :

- Le rang
- L'artiste
- Le titre
- L'Elo
- Le palier
- Le nombre de matchs
- Les victoires
- Les defaites
- Les egalites

Une barre de recherche permet de filtrer le classement par artiste ou par titre.

---

## Playlist Spotify Top 100

Depuis le menu principal, cliquer sur Creer la playlist Top 100.

L'application demande :

1. Le nom de la playlist
2. Si la playlist doit etre publique ou privee

Les 100 meilleurs morceaux sont selectionnes selon leur Elo.

Une fenetre affiche la progression en temps reel :

- Connexion a Spotify
- Preparation des morceaux
- Recherche des URI manquantes
- Creation de la playlist
- Ajout des morceaux
- Pourcentage de progression
- Confirmation finale
- Erreurs eventuelles

La playlist peut aussi etre creee en ligne de commande :

```bash
python playlist_creator.py --nom "Mon Top 100"
```

Playlist privee :

```bash
python playlist_creator.py --nom "Mon Top 100" --privee
```

Nombre personnalise de morceaux :

```bash
python playlist_creator.py --nom "Mon Top 50" --nombre 50
```

---

## Extraits Spotify

Par defaut, un extrait commence a 35 pour cent du morceau et dure 20 secondes.

Ces reglages se trouvent dans moteur.py :

```python
EXTRAIT_DEBUT = 0.35
EXTRAIT_DUREE_S = 20
```

Spotify doit etre ouvert sur un appareil actif.

Si aucun appareil n'est detecte :

1. Ouvrir Spotify
2. Lancer un morceau
3. Mettre le morceau en pause
4. Reessayer dans VS Musique

---

## Sauvegarde

Les donnees sont enregistrees automatiquement apres chaque choix, duel, annulation, ajout manuel ou recuperation de metadonnees.

L'ecriture de scores.json est atomique afin de reduire le risque de corruption.

Il reste recommande de conserver regulierement une copie de scores.json.

---

## Format de scores.json

Exemple :

```json
{
    "Player - Baby Come Back": {
        "artiste": "Player",
        "musique": "Baby Come Back",
        "elo": 1150,
        "victoires": 5,
        "defaites": 3,
        "egalites": 0,
        "spotify_uri": "spotify:track:41sGGCCoHI2GLV9qadX80A",
        "pochette": "https://i.scdn.co/image/...",
        "duree_ms": 255845,
        "tier": "S"
    }
}
```

---

## Depannage

Installer Spotipy :

```bash
pip install spotipy
```

Installer Pillow :

```bash
pip install pillow
```

Supprimer les caches Spotify si l'authentification ne fonctionne plus :

```bash
rm -f .cache-spotify-top
rm -f .cache-spotify-lecture
rm -f .cache-spotify-playlist
```

Verifier la syntaxe des scripts :

```bash
python -m py_compile main.py moteur.py generer_liste.py ajouter_musique.py tri_rapide.py duels_elo.py playlist_creator.py
```

Pour eviter les erreurs d'encodage Windows dans les sous-processus, main.py utilise :

```python
environnement["PYTHONUNBUFFERED"] = "1"
environnement["PYTHONIOENCODING"] = "utf-8"
```

---

## Securite

Le fichier .gitignore doit au minimum contenir :

```gitignore
.env
.cache-spotify*
scores.json
scores.backup-*.json
pochettes/
__pycache__/
*.pyc
*.tmp
.venv/
```

Si un Client Secret a ete publie, il faut le regenerer immediatement depuis Spotify Developer.

---

## Git

Apres une modification :

```bash
git add .
git commit -m "Description de la modification"
git push
```

---

## Etat actuel

Fonctionnalites disponibles :

- Menu principal
- Generation Spotify
- Fusion avec le classement existant
- Import de l'historique etendu
- Ajout manuel
- Recherche Spotify
- Tri rapide
- Duels Elo
- Ajout tardif de morceaux
- Pochettes
- Extraits
- Classement avec recherche
- Playlist Top 100 personnalisee
- Playlist publique ou privee
- Progression en temps reel
- Sauvegarde automatique

---

## Avertissement

VS Musique est un projet independant et n'est pas affilie a Spotify.

L'utilisateur est responsable de la confidentialite des identifiants Spotify, des fichiers de cache et des donnees d'ecoute.
