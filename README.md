# 🎵 VS Musique

> **VS Musique** est une application Python connectée à Spotify permettant de construire, classer et comparer une bibliothèque musicale personnelle grâce à un système de tri rapide et de duels **Elo**.

L'application permet de récupérer des morceaux depuis Spotify, d'en ajouter manuellement, de les classer, d'écouter des extraits, d'afficher leurs pochettes et de générer automatiquement une playlist Spotify à partir du classement.

---

## ✨ Fonctionnalités

### 🎧 Gestion de la bibliothèque
- Génération de la bibliothèque depuis Spotify
- Import d'un historique Spotify étendu
- Conservation du classement lors d'une nouvelle génération
- Ajout manuel de morceaux
- Recherche de morceaux sur Spotify
- Détection des doublons
- Récupération des pochettes et métadonnées

### 🏆 Système de classement
- Tri rapide par paliers
- Classement avec système **Elo**
- Duels entre morceaux aux scores proches
- Égalités possibles
- Annulation du dernier choix
- Intégration de nouveaux morceaux dans un classement existant
- Classement complet avec recherche par artiste ou titre

### 🎵 Spotify
- Écoute d'extraits directement depuis l'application
- Création d'une playlist Spotify depuis le classement
- Top 100 personnalisable
- Nombre de morceaux personnalisable
- Playlist publique ou privée
- Progression de création affichée en temps réel

### 💾 Sauvegarde
- Sauvegarde automatique après les actions importantes
- Reprise du classement après fermeture
- Écriture atomique de `scores.json`
- Conservation des scores et métadonnées existants lors des mises à jour

---

## 📊 Fonctionnement du classement

VS Musique utilise deux étapes complémentaires.

### 1. Tri rapide

Chaque morceau est d'abord placé dans un palier :

| Palier | Description | Elo initial |
|:------:|-------------|------------:|
| **S** | J'adore | `1120` |
| **A** | J'aime bien | `1060` |
| **B** | Correct | `1000` |
| **C** | Bof | `940` |
| **D** | Pas pour moi | `880` |

Le palier constitue uniquement un **point de départ**. Le classement final est ensuite affiné avec les duels Elo.

Commandes disponibles :

| Touche | Action |
|--------|--------|
| `Espace` | Réécouter |
| `P` | Passer temporairement |
| `Retour arrière` | Annuler |

### 2. Duels Elo

Deux morceaux sont présentés et l'utilisateur choisit celui qu'il préfère.

| Touche | Action |
|--------|--------|
| `←` | Voter pour le morceau de gauche |
| `→` | Voter pour le morceau de droite |
| `↓` | Déclarer une égalité |
| `1` | Écouter le morceau de gauche |
| `2` | Écouter le morceau de droite |
| `Retour arrière` | Annuler le dernier vote |

Par défaut, chaque morceau effectue **8 duels**.

Le nombre de duels peut être personnalisé :

```bash
python duels_elo.py --matchs 12
```

Les adversaires sont sélectionnés parmi les morceaux ayant un Elo proche.

Les nouveaux morceaux peuvent également affronter des morceaux ayant déjà atteint leur quota de duels, afin d'éviter de bloquer le classement lorsqu'un seul titre est ajouté.

---

## 🗂️ Structure du projet

```text
spotify_versus/
├── .env
├── .env.example
├── .gitignore
├── requirements.txt
├── README.md
├── main.py
├── moteur.py
├── generer_liste.py
├── ajouter_musique.py
├── tri_rapide.py
├── duels_elo.py
├── playlist_creator.py
├── scores.json
└── pochettes/
```

### Description des fichiers

| Fichier | Rôle |
|---------|------|
| `main.py` | Menu général de l'application |
| `moteur.py` | Logique Elo, Spotify, extraits et pochettes |
| `generer_liste.py` | Génération ou actualisation de la bibliothèque |
| `ajouter_musique.py` | Ajout manuel d'un morceau |
| `tri_rapide.py` | Première phase de classement |
| `duels_elo.py` | Deuxième phase avec les duels Elo |
| `playlist_creator.py` | Création des playlists Spotify |
| `scores.json` | Stockage des morceaux, scores et métadonnées |
| `pochettes/` | Stockage des pochettes |

---

## 🔧 Prérequis

- **Python 3.10** ou plus récent
- Un compte **Spotify**
- Une application **Spotify Developer**
- **Spotify Premium** pour piloter la lecture
- Spotify ouvert sur un appareil actif pour écouter les extraits

---

## 🚀 Installation

### 1. Cloner le dépôt

```bash
git clone https://github.com/Azarjoe/spotify_versus.git
cd spotify_versus
```

### 2. Installer les dépendances

```bash
pip install -r requirements.txt
```

Le fichier `requirements.txt` doit contenir au minimum :

```text
spotipy
pillow
```

---

## 🔐 Configuration Spotify

Créer un fichier `.env` à la racine du projet :

```env
SPOTIPY_CLIENT_ID=ton_client_id
SPOTIPY_CLIENT_SECRET=ton_client_secret
SPOTIPY_REDIRECT_URI=http://127.0.0.1:8888/callback
```

Ajouter également cette adresse dans les paramètres de l'application Spotify Developer :

```text
http://127.0.0.1:8888/callback
```

> ⚠️ **Ne partagez jamais votre `SPOTIPY_CLIENT_SECRET`.**

---

## ▶️ Lancer l'application

```bash
python main.py
```

Le menu principal permet notamment de :

- Générer ou actualiser la liste Spotify
- Ajouter une musique
- Lancer le tri rapide
- Lancer les duels Elo
- Consulter le classement
- Créer la playlist Top 100
- Ouvrir le dossier du projet
- Actualiser les statistiques

---

## 📚 Générer ou actualiser la bibliothèque

### Depuis l'API Spotify

```bash
python generer_liste.py
```

Si `scores.json` existe déjà, les morceaux présents conservent :

- leur Elo
- leur palier
- leurs victoires
- leurs défaites
- leurs égalités
- leurs métadonnées

Seuls les nouveaux morceaux sont ajoutés.

### Depuis un historique Spotify étendu

```bash
python generer_liste.py --historique mon_export.zip --nombre 200
```

Le script analyse l'historique et compte les écoutes ayant duré **au moins 30 secondes**.

---

## ➕ Ajouter un morceau

```bash
python ajouter_musique.py
```

L'interface permet de :

1. Saisir un artiste et un titre
2. Rechercher le morceau sur Spotify
3. Sélectionner la bonne version
4. Enregistrer son URI Spotify

Les doublons sont détectés même lorsque la casse ou les espaces diffèrent.

---

## 🏅 Consulter le classement

Le classement affiche :

- Le rang
- L'artiste
- Le titre
- L'Elo
- Le palier
- Le nombre de matchs
- Les victoires
- Les défaites
- Les égalités

Une barre de recherche permet de filtrer les résultats par **artiste** ou **titre**.

---

## 🎶 Créer une playlist Spotify

Depuis le menu principal, sélectionner **Créer la playlist Top 100**.

L'application demande :

- Le nom de la playlist
- Si la playlist doit être publique ou privée

Les morceaux sont sélectionnés selon leur **Elo**.

La création affiche sa progression en temps réel :

```text
Connexion à Spotify
        ↓
Préparation des morceaux
        ↓
Recherche des URI manquantes
        ↓
Création de la playlist
        ↓
Ajout des morceaux
        ↓
Pourcentage de progression
        ↓
Confirmation finale
```

### En ligne de commande

Créer un Top 100 :

```bash
python playlist_creator.py --nom "Mon Top 100"
```

Créer une playlist privée :

```bash
python playlist_creator.py --nom "Mon Top 100" --privee
```

Créer un Top 50 :

```bash
python playlist_creator.py --nom "Mon Top 50" --nombre 50
```

---

## 🎧 Extraits Spotify

Par défaut, un extrait :

- commence à **35 %** du morceau
- dure **20 secondes**

Ces réglages se trouvent dans `moteur.py` :

```python
EXTRAIT_DEBUT = 0.35
EXTRAIT_DUREE_S = 20
```

Spotify doit être ouvert sur un appareil actif.

### Si aucun appareil n'est détecté

1. Ouvrir Spotify
2. Lancer un morceau
3. Mettre le morceau en pause
4. Réessayer dans VS Musique

---

## 💾 Sauvegarde des données

Les données sont sauvegardées automatiquement après :

- chaque choix
- chaque duel
- une annulation
- un ajout manuel
- une récupération de métadonnées

L'écriture de `scores.json` est atomique afin de réduire le risque de corruption.

Il reste recommandé de conserver régulièrement une copie de `scores.json`.

### Exemple de `scores.json`

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

## 🛠️ Dépannage

### Installer Spotipy

```bash
pip install spotipy
```

### Installer Pillow

```bash
pip install pillow
```

### Réinitialiser les caches Spotify

Si l'authentification ne fonctionne plus :

```bash
rm -f .cache-spotify-top
rm -f .cache-spotify-lecture
rm -f .cache-spotify-playlist
```

### Vérifier la syntaxe des scripts

```bash
python -m py_compile main.py moteur.py generer_liste.py ajouter_musique.py tri_rapide.py duels_elo.py playlist_creator.py
```

### Encodage Windows

Pour éviter les problèmes d'encodage Windows dans les sous-processus, `main.py` utilise :

```python
environnement["PYTHONUNBUFFERED"] = "1"
environnement["PYTHONIOENCODING"] = "utf-8"
```

---

## 🔒 Sécurité

Le fichier `.gitignore` doit au minimum contenir :

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

### ⚠️ Client Secret exposé

Si un **Client Secret Spotify** a été publié, il faut le régénérer immédiatement depuis Spotify Developer.

Ne publiez jamais :

- `.env`
- les caches Spotify
- `scores.json`
- les sauvegardes de `scores.json`
- les données personnelles ou d'écoute non destinées à être partagées

---

## 🔀 Workflow Git

Après une modification :

```bash
git add .
git commit -m "Description de la modification"
git push
```

---

## 📌 État actuel

Les fonctionnalités actuellement disponibles sont :

- ✅ Menu principal
- ✅ Génération Spotify
- ✅ Fusion avec le classement existant
- ✅ Import de l'historique étendu
- ✅ Ajout manuel
- ✅ Recherche Spotify
- ✅ Détection des doublons
- ✅ Tri rapide
- ✅ Duels Elo
- ✅ Ajout tardif de morceaux
- ✅ Pochettes
- ✅ Extraits
- ✅ Classement avec recherche
- ✅ Playlist Top 100 personnalisée
- ✅ Playlist publique ou privée
- ✅ Progression en temps réel
- ✅ Sauvegarde automatique

---

## ⚠️ Avertissement

**VS Musique est un projet indépendant et n'est pas affilié à Spotify.**

L'utilisateur est responsable de la confidentialité de ses identifiants Spotify, de ses fichiers de cache et de ses données d'écoute.

---

<p align="center">
  <strong>VS Musique</strong><br>
  Classez votre bibliothèque. Affinez vos préférences. Trouvez votre Top 100.
</p>
