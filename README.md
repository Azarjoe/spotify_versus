# VS Musique

Application de classement musical personnel connectée à Spotify.

VS Musique permet de créer une bibliothèque à partir des morceaux préférés d’un utilisateur, de les classer rapidement par catégories, puis d’affiner le classement grâce à des duels utilisant le système Elo.

L’application permet également :

- de récupérer les morceaux préférés d’un compte Spotify ;
- d’exploiter un historique d’écoute Spotify complet ;
- d’ajouter manuellement un morceau ;
- de rechercher un morceau sur Spotify ;
- d’afficher les pochettes des albums ;
- d’écouter un extrait pendant le classement ;
- de reprendre le classement après avoir fermé l’application ;
- d’annuler le dernier choix ;
- d’intégrer de nouveaux morceaux dans un classement déjà terminé ;
- de conserver toutes les données dans un fichier JSON local.

---

# Sommaire

1. #présentation
2. #objectif-du-projet
3. #fonctionnement-général
4. #structure-du-projet
5. #prérequis
6. #installation
7. #configuration-spotify
8. #générer-une-liste-de-morceaux
9. #ajouter-un-morceau-manuellement
10. #phase-1--tri-rapide
11. #phase-2--duels-elo
12. #ajouter-des-morceaux-après-le-classement
13. #format-de-scoresjson
14. #fonctionnement-du-système-elo
15. #pochettes-et-métadonnées
16. #lecture-des-extraits
17. #sauvegarde-et-reprise
18. #commandes-disponibles
19. #dépannage
20. #sécurité
21. #limites-actuelles
22. #feuille-de-route
23. #architecture-technique
24. #développement
25. #licence

---

# Présentation

VS Musique est une application Python permettant de construire un classement musical personnel.

Le projet utilise deux méthodes complémentaires :

1. un tri rapide par catégories ;
2. un classement précis par duels Elo.

Le tri rapide permet de donner une première position approximative à chaque morceau en un seul choix.

Les duels Elo permettent ensuite de comparer des morceaux de niveau proche afin d’obtenir un classement beaucoup plus précis.

Cette approche est plus rapide que de commencer directement avec des centaines de duels aléatoires.

---

# Objectif du projet

L’objectif est de transformer VS Musique en une application réutilisable par différents utilisateurs.

Chaque utilisateur doit pouvoir :

1. connecter son compte Spotify ;
2. récupérer une première liste de morceaux ;
3. compléter cette liste manuellement ;
4. classer rapidement les morceaux ;
5. affiner le classement avec des duels ;
6. consulter son classement final ;
7. intégrer de nouveaux morceaux plus tard ;
8. créer éventuellement une playlist Spotify à partir du classement.

Le projet doit rester simple à utiliser, même pour une personne qui ne connaît pas Python.

À terme, une interface principale permettra de lancer toutes les fonctionnalités depuis une seule fenêtre.

---

# Fonctionnement général

Le processus recommandé est le suivant :

## Étape 1 : création de la bibliothèque

La bibliothèque peut être générée de deux façons :

- récupération des morceaux favoris via l’API Spotify ;
- analyse de l’historique d’écoute étendu de Spotify.

Le résultat est enregistré dans :

    scores.json

## Étape 2 : ajout manuel

L’utilisateur peut ajouter des morceaux absents de la liste avec une interface graphique.

Il peut :

- saisir directement l’artiste et le titre ;
- rechercher le morceau sur Spotify ;
- sélectionner le résultat Spotify exact ;
- enregistrer automatiquement son URI Spotify.

## Étape 3 : tri rapide

Chaque morceau est présenté une seule fois.

L’utilisateur le place dans l’un des cinq paliers suivants :

- S : J’adore ;
- A : J’aime bien ;
- B : Correct ;
- C : Bof ;
- D : Pas pour moi.

Chaque palier donne un Elo de départ au morceau.

## Étape 4 : duels Elo

Deux morceaux de niveau proche sont affichés.

L’utilisateur choisit :

- le morceau de gauche ;
- le morceau de droite ;
- une égalité s’il ne sait pas choisir.

Après chaque vote, le score Elo des deux morceaux est recalculé.

## Étape 5 : classement final

Les morceaux sont triés du plus grand Elo au plus petit Elo.

Plus un morceau gagne contre des adversaires bien classés, plus son Elo augmente.

---

# Structure du projet

La structure actuelle recommandée est la suivante :

    VS Musique/
    │
    ├── .env
    ├── .gitignore
    ├── ajouter_musique.py
    ├── duels_elo.py
    ├── generer_liste.py
    ├── moteur.py
    ├── README.md
    ├── requirements.txt
    ├── scores.json
    ├── tri_rapide.py
    │
    ├── pochettes/
    │   └── fichiers temporaires des pochettes
    │
    ├── .cache-spotify-top
    └── .cache-spotify-lecture

## generer_liste.py

Ce script crée le fichier `scores.json`.

Il propose deux sources possibles :

- l’API Spotify ;
- l’historique de streaming étendu.

Le mode API récupère les morceaux favoris disponibles sur plusieurs périodes Spotify.

Le mode historique analyse les fichiers JSON présents dans l’export Spotify de l’utilisateur.

Lorsqu’un fichier `scores.json` existe déjà, une sauvegarde est créée avant son remplacement.

## ajouter_musique.py

Ce script ouvre une interface graphique permettant d’ajouter un morceau dans `scores.json`.

Fonctionnalités :

- saisie de l’artiste ;
- saisie du titre ;
- recherche Spotify ;
- affichage de plusieurs résultats ;
- sélection du résultat correct ;
- récupération de l’URI Spotify ;
- détection des doublons ;
- compteur du nombre de morceaux.

## moteur.py

Ce fichier contient le cœur logique de l’application.

Il ne doit normalement pas être lancé directement.

Il contient :

- la lecture de `scores.json` ;
- la sauvegarde sécurisée ;
- la gestion du tri rapide ;
- le calcul Elo ;
- la génération des duels ;
- la récupération des métadonnées Spotify ;
- le téléchargement des pochettes ;
- la lecture des extraits ;
- les traitements en arrière-plan.

Les autres interfaces importent ce fichier avec :

    import moteur as m

## tri_rapide.py

Ce script correspond à la première phase du classement.

Chaque morceau est présenté une fois et placé dans un palier.

Le script affiche :

- le titre ;
- l’artiste ;
- la pochette ;
- la progression ;
- les boutons de classement ;
- les commandes secondaires.

## duels_elo.py

Ce script correspond à la deuxième phase du classement.

Deux morceaux sont comparés à chaque duel.

Le script permet :

- d’écouter le morceau de gauche ;
- d’écouter le morceau de droite ;
- de voter pour le morceau de gauche ;
- de voter pour le morceau de droite ;
- de déclarer une égalité ;
- d’annuler le dernier vote ;
- d’afficher le classement actuel.

## scores.json

Ce fichier constitue la base de données locale du projet.

Il contient :

- l’artiste ;
- le titre ;
- le score Elo ;
- le nombre de victoires ;
- le nombre de défaites ;
- le nombre d’égalités ;
- le palier du tri rapide ;
- l’URI Spotify ;
- l’adresse de la pochette ;
- la durée du morceau ;
- éventuellement le nombre d’écoutes.

## dossier pochettes

Ce dossier est créé automatiquement.

Il contient les pochettes téléchargées depuis Spotify.

Les fichiers sont mis en cache afin d’éviter de télécharger plusieurs fois la même image.

## fichiers .cache-spotify-*

Ces fichiers sont créés automatiquement par Spotipy.

Ils contiennent les informations de session nécessaires à l’authentification Spotify.

Ils ne doivent pas être publiés sur GitHub ni envoyés à une autre personne.

---

# Prérequis

## Système

Le projet est principalement développé et testé pour Windows.

Il peut également fonctionner sur Linux ou macOS, sous réserve que Python, Tkinter et les dépendances nécessaires soient disponibles.

## Python

Python 3.10 ou une version plus récente est recommandé.

Pour vérifier la version installée :

    python --version

Sous certains systèmes :

    python3 --version

## Spotify

Pour utiliser les fonctionnalités Spotify, il faut :

- un compte Spotify ;
- une application créée dans Spotify for Developers ;
- Spotify ouvert sur un ordinateur ou un téléphone ;
- un compte Spotify Premium pour piloter la lecture depuis l’application.

Sans connexion Spotify, certaines parties du projet restent utilisables, mais les pochettes et l’écoute peuvent être indisponibles.

---

# Installation

## 1. Télécharger ou copier le projet

Place tous les fichiers Python dans le même dossier.

Exemple :

    C:\Users\VotreNom\Documents\VS Musique

## 2. Ouvrir PowerShell

Dans l’explorateur Windows :

1. ouvre le dossier du projet ;
2. clique dans la barre d’adresse ;
3. tape `powershell` ;
4. appuie sur Entrée.

## 3. Créer un environnement virtuel

Cette étape est recommandée.

    python -m venv .venv

Active ensuite l’environnement :

    .\.venv\Scripts\Activate.ps1

Si PowerShell bloque l’activation :

    Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

Puis relance :

    .\.venv\Scripts\Activate.ps1

## 4. Installer les dépendances

    pip install spotipy pillow

Si un fichier `requirements.txt` est présent :

    pip install -r requirements.txt

## Contenu recommandé de requirements.txt

    spotipy
    pillow

Tkinter est généralement inclus avec Python sous Windows.

---

# Configuration Spotify

## 1. Créer une application Spotify

Crée une application dans le tableau de bord Spotify Developer.

Récupère ensuite :

- le Client ID ;
- le Client Secret.

## 2. Configurer l’URL de redirection

Ajoute cette adresse dans les paramètres de l’application Spotify :

    http://127.0.0.1:8888/callback

L’adresse doit être identique dans les paramètres Spotify et dans le fichier `.env`.

## 3. Créer le fichier .env

À la racine du projet, crée un fichier nommé exactement :

    .env

Attention à ne pas créer involontairement un fichier `.env.txt`.

Ajoute le contenu suivant :

    SPOTIPY_CLIENT_ID=ton_client_id
    SPOTIPY_CLIENT_SECRET=ton_client_secret
    SPOTIPY_REDIRECT_URI=http://127.0.0.1:8888/callback

Remplace les valeurs par tes propres identifiants.

Exemple fictif :

    SPOTIPY_CLIENT_ID=123456789abcdef
    SPOTIPY_CLIENT_SECRET=abcdef123456789
    SPOTIPY_REDIRECT_URI=http://127.0.0.1:8888/callback

Ne mets pas d’espace avant ou après le signe `=`.

## 4. Première connexion

Lors du premier lancement d’une fonctionnalité Spotify :

1. une page peut s’ouvrir dans le navigateur ;
2. connecte-toi à Spotify ;
3. autorise l’application ;
4. Spotify redirige vers l’adresse locale configurée ;
5. Spotipy enregistre la session dans un fichier de cache.

Le projet utilise actuellement plusieurs caches selon le type d’autorisation :

    .cache-spotify-top
    .cache-spotify-lecture

Il est donc possible que Spotify demande une autorisation une première fois pour la récupération des favoris, puis une autre fois pour la lecture.

---

# Générer une liste de morceaux

Le script utilisé est :

    generer_liste.py

Deux méthodes sont disponibles.

---

## Méthode 1 : API Spotify

Commande :

    python generer_liste.py

Le programme :

1. se connecte au compte Spotify ;
2. récupère les morceaux favoris sur plusieurs périodes ;
3. élimine les doublons ;
4. ajoute les URI Spotify disponibles ;
5. crée `scores.json`.

Cette méthode est rapide, mais elle ne représente pas nécessairement l’intégralité de l’historique du compte.

Le nombre de morceaux récupérés peut être inférieur au nombre demandé.

Exemple de résultat :

    118 morceaux écrits dans scores.json

Pour demander un autre nombre :

    python generer_liste.py --nombre 100

Pour choisir un autre fichier de sortie :

    python generer_liste.py --sortie ma_liste.json

---

## Méthode 2 : historique Spotify étendu

Cette méthode permet d’analyser les données d’écoute exportées par Spotify.

Une fois l’archive reçue, elle peut être utilisée directement sans être extraite.

Commande :

    python generer_liste.py --historique mon_export.zip

Pour conserver les 200 morceaux les plus écoutés :

    python generer_liste.py --historique mon_export.zip --nombre 200

Le programme :

1. ouvre l’archive ZIP ou le dossier ;
2. trouve les fichiers d’historique audio ;
3. ignore les podcasts et les entrées sans titre ;
4. ignore les écoutes trop courtes ;
5. regroupe les variantes d’écriture ;
6. compte les écoutes ;
7. trie les morceaux ;
8. crée `scores.json`.

Par défaut, une écoute est comptée à partir de 30 secondes :

    30000 millisecondes

Le seuil peut être modifié :

    python generer_liste.py --historique mon_export.zip --min-ms 20000

---

## Attention lors de la génération

Si `scores.json` existe déjà, le programme crée une sauvegarde.

Exemple :

    scores.backup-20260920-192000.json

La génération d’une nouvelle liste remplace ensuite le fichier principal.

Si un classement important existe déjà, conserve toujours une copie manuelle avant de relancer la génération.

---

# Ajouter un morceau manuellement

Commande :

    python ajouter_musique.py

Une fenêtre s’ouvre.

## Ajout direct

1. saisis le nom de l’artiste ;
2. saisis le titre ;
3. clique sur `Ajouter` ;
4. le morceau est ajouté à `scores.json`.

Le morceau commence avec :

- un Elo de 1000 ;
- zéro victoire ;
- zéro défaite ;
- zéro égalité.

## Recherche Spotify

Pour éviter les erreurs d’orthographe :

1. saisis un artiste ou un titre ;
2. clique sur `Chercher sur Spotify` ;
3. sélectionne le bon résultat ;
4. clique sur `Ajouter`.

La sélection Spotify permet d’enregistrer directement :

- l’artiste exact ;
- le titre exact ;
- l’URI Spotify.

Les autres métadonnées pourront être complétées plus tard par le moteur.

## Détection des doublons

Le programme compare les titres sans tenir compte :

- des différences de majuscules ;
- des espaces en trop ;
- de la casse.

Ainsi, les valeurs suivantes sont considérées comme identiques :

    Nina Simone - Feeling Good
    nina simone - feeling good
    NINA SIMONE - FEELING GOOD

---

# Phase 1 : tri rapide

Commande :

    python tri_rapide.py

Le tri rapide présente chaque morceau qui n’a pas encore été classé.

## Paliers disponibles

### Palier S

Libellé :

    J’adore

Elo initial :

    1120

Touche :

    1

### Palier A

Libellé :

    J’aime bien

Elo initial :

    1060

Touche :

    2

### Palier B

Libellé :

    Correct

Elo initial :

    1000

Touche :

    3

### Palier C

Libellé :

    Bof

Elo initial :

    940

Touche :

    4

### Palier D

Libellé :

    Pas pour moi

Elo initial :

    880

Touche :

    5

## Autres commandes

Réécouter l’extrait :

    Espace

Passer temporairement un morceau :

    P

Annuler le dernier choix :

    Retour arrière

## Lecture automatique

L’option `Lancer l’extrait automatiquement` permet de démarrer automatiquement l’extrait lorsque le morceau est affiché.

Elle peut être désactivée depuis l’interface.

## Reprise

Les choix sont enregistrés dans `scores.json`.

Si l’application est fermée, les morceaux ayant déjà reçu un palier ne sont pas reproposés au prochain lancement.

Le tri reprend avec les morceaux restants.

## Ajouter un morceau après le tri rapide

Un morceau ajouté manuellement possède :

- aucun palier ;
- zéro match.

Il sera donc détecté par `tri_rapide.py` lors du prochain lancement.

---

# Phase 2 : duels Elo

Commande :

    python duels_elo.py

Deux morceaux de niveau proche sont affichés.

## Commandes du duel

Voter pour le morceau de gauche :

    Flèche gauche

Voter pour le morceau de droite :

    Flèche droite

Déclarer une égalité :

    Flèche bas

Écouter le morceau de gauche :

    1

Écouter le morceau de droite :

    2

Annuler le dernier vote :

    Retour arrière

## Boutons disponibles

L’interface contient également des boutons pour :

- écouter chaque morceau ;
- voter pour chaque morceau ;
- choisir `Je sais pas` ;
- annuler ;
- afficher le classement actuel.

## Nombre de matchs

Par défaut, chaque morceau doit effectuer huit duels.

Commande standard :

    python duels_elo.py

Pour demander douze matchs par morceau :

    python duels_elo.py --matchs 12

Plus le nombre de matchs est élevé, plus le classement peut être précis, mais plus le processus demande de votes.

## Sélection des adversaires

Le moteur :

1. choisit un morceau n’ayant pas atteint son quota ;
2. donne la priorité aux morceaux ayant joué le moins de matchs ;
3. cherche un adversaire ayant un Elo proche ;
4. évite autant que possible les paires déjà proposées ;
5. mélange les côtés gauche et droit.

Les duels équilibrés donnent généralement plus d’informations que les duels opposant deux morceaux très éloignés.

---

# Ajouter des morceaux après le classement

Le moteur permet d’intégrer un nouveau morceau même si tous les anciens morceaux ont déjà atteint leur quota.

## Procédure

1. lance `ajouter_musique.py` ;
2. ajoute le nouveau morceau ;
3. lance `tri_rapide.py` ;
4. attribue un palier au nouveau morceau ;
5. lance `duels_elo.py`.

Le nouveau morceau peut affronter les morceaux déjà classés.

## Fonctionnement interne

Le moteur distingue désormais :

- les morceaux qui ont encore besoin de jouer ;
- les morceaux pouvant servir d’adversaires.

Un ancien morceau ayant déjà atteint huit matchs peut donc être sélectionné comme adversaire d’un nouveau morceau.

Cela signifie qu’un ancien morceau peut dépasser légèrement son quota.

Exemple :

    Ancien morceau : 9 matchs
    Nouveau morceau : 1 match

Ce comportement est volontaire.

Le classement ne bloque plus lorsqu’un seul nouveau morceau est ajouté.

---

# Format de scores.json

Le fichier contient un objet JSON.

Chaque clé correspond généralement à :

    Artiste - Titre

Exemple :

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

## artiste

Nom de l’artiste principal.

Exemple :

    "artiste": "Player"

## musique

Titre du morceau.

Exemple :

    "musique": "Baby Come Back"

## elo

Score de classement du morceau.

Exemple :

    "elo": 1150

## victoires

Nombre de duels gagnés.

Exemple :

    "victoires": 5

## defaites

Nombre de duels perdus.

Exemple :

    "defaites": 3

## egalites

Nombre de duels déclarés comme égalités.

Exemple :

    "egalites": 0

## spotify_uri

Identifiant Spotify utilisé pour lancer directement le morceau.

Exemple :

    "spotify_uri": "spotify:track:41sGGCCoHI2GLV9qadX80A"

## pochette

Adresse de l’image de l’album.

Exemple :

    "pochette": "https://i.scdn.co/image/..."

## duree_ms

Durée du morceau en millisecondes.

Exemple :

    "duree_ms": 255845

## tier

Palier choisi pendant le tri rapide.

Valeurs possibles :

    S
    A
    B
    C
    D

## streams

Ce champ peut être présent lorsque le morceau provient d’un historique Spotify.

Exemple :

    "streams": 154

Il représente le nombre d’écoutes comptabilisées par le script d’import.

---

# Fonctionnement du système Elo

Le système Elo est à l’origine utilisé pour classer des joueurs.

Dans VS Musique, chaque morceau est considéré comme un participant.

## Probabilité attendue

Si deux morceaux ont le même Elo, chacun est considéré comme ayant environ 50 % de chances de gagner.

Si un morceau possède un Elo supérieur, il est considéré comme favori.

## Résultat d’un duel

Les scores utilisés sont :

- victoire : 1 ;
- égalité : 0,5 ;
- défaite : 0.

## Facteur K

Le projet utilise actuellement :

    K = 32

Cette valeur contrôle la vitesse à laquelle l’Elo évolue.

Une valeur plus élevée provoque des changements plus importants.

Une valeur plus faible rend le classement plus stable.

## Formule simplifiée

Le nouvel Elo dépend :

- de l’ancien Elo ;
- du niveau de l’adversaire ;
- du résultat réel ;
- du résultat attendu.

Battre un adversaire mieux classé rapporte généralement plus de points.

Perdre contre un adversaire moins bien classé fait généralement perdre plus de points.

## Rôle des paliers

Le palier n’est pas le classement final.

Il sert uniquement à donner un point de départ approximatif.

Un morceau classé en S peut ensuite descendre s’il perd plusieurs duels.

Un morceau classé en B peut remonter s’il gagne contre des morceaux mieux classés.

Ce comportement est normal et souhaité.

---

# Pochettes et métadonnées

Les pochettes sont récupérées depuis les métadonnées Spotify.

Le moteur recherche :

- l’URI Spotify ;
- la pochette ;
- la durée du morceau.

Les informations obtenues sont ensuite enregistrées dans `scores.json`.

## Cache local

Les images sont enregistrées dans :

    pochettes/

Le nom du fichier est généré à partir de l’adresse de l’image.

Cela évite de télécharger la même pochette à chaque affichage.

## Pillow

L’affichage des images nécessite Pillow.

Installation :

    pip install pillow

Si Pillow n’est pas installé, le classement peut continuer, mais les pochettes ne seront pas affichées.

---

# Lecture des extraits

Spotify ne fournit pas toujours un fichier d’extrait audio directement exploitable.

VS Musique pilote donc la lecture sur un appareil Spotify actif.

## Fonctionnement actuel

Par défaut, le moteur :

1. lance le morceau ;
2. démarre à environ 35 % de sa durée ;
3. joue pendant 20 secondes ;
4. met automatiquement la lecture en pause.

Les réglages sont situés dans `moteur.py` :

    EXTRAIT_DEBUT = 0.35
    EXTRAIT_DUREE_S = 20

## Modifier la position de départ

Pour démarrer à la moitié du morceau :

    EXTRAIT_DEBUT = 0.50

## Modifier la durée

Pour jouer pendant 30 secondes :

    EXTRAIT_DUREE_S = 30

## Désactiver l’arrêt automatique

    EXTRAIT_DUREE_S = 0

## Appareil actif

Spotify doit être ouvert sur au moins un appareil.

Si aucun appareil n’est actif, le moteur tente d’utiliser le premier appareil disponible.

Si cela échoue :

1. ouvre Spotify ;
2. lance manuellement un morceau ;
3. mets-le en pause ;
4. réessaie dans VS Musique.

---

# Sauvegarde et reprise

Les données sont enregistrées après chaque action importante.

Cela concerne notamment :

- l’attribution d’un palier ;
- un vote Elo ;
- une annulation ;
- la récupération de métadonnées Spotify ;
- l’ajout d’un morceau.

## Écriture atomique

Le fichier est d’abord écrit dans :

    scores.json.tmp

Il remplace ensuite le fichier principal.

Cette méthode limite le risque d’obtenir un fichier JSON partiellement écrit en cas de problème.

## Compatibilité avec OneDrive

Le moteur réessaie plusieurs fois si OneDrive verrouille temporairement le fichier.

Il attend brièvement entre les tentatives.

## Recommandation

Même si les écritures sont sécurisées, conserve des sauvegardes régulières de `scores.json`.

Exemple :

    scores_backup_2026-09-20.json

---

# Commandes disponibles

## Générer depuis l’API Spotify

    python generer_liste.py

## Générer depuis un historique

    python generer_liste.py --historique mon_export.zip

## Choisir le nombre de morceaux

    python generer_liste.py --nombre 200

## Choisir un fichier de sortie

    python generer_liste.py --sortie scores.json

## Ajouter un morceau

    python ajouter_musique.py

## Lancer le tri rapide

    python tri_rapide.py

## Lancer les duels Elo

    python duels_elo.py

## Lancer douze matchs par morceau

    python duels_elo.py --matchs 12

---

# Dépannage

## Python n’est pas reconnu

Erreur possible :

    python n’est pas reconnu en tant que commande

Solutions :

- installer Python ;
- cocher `Add Python to PATH` pendant l’installation ;
- essayer la commande `py` à la place de `python`.

Exemple :

    py tri_rapide.py

---

## Spotipy n’est pas installé

Erreur :

    ModuleNotFoundError: No module named 'spotipy'

Solution :

    pip install spotipy

Si un environnement virtuel est utilisé, vérifie qu’il est activé.

---

## Pillow n’est pas installé

Erreur :

    ModuleNotFoundError: No module named 'PIL'

Solution :

    pip install pillow

---

## Tkinter est indisponible

Erreur :

    ModuleNotFoundError: No module named 'tkinter'

Sous Windows, réinstalle Python en vérifiant que Tcl/Tk est inclus.

Sous certaines distributions Linux :

    sudo apt install python3-tk

---

## Identifiants Spotify manquants

Message possible :

    Identifiants Spotify manquants dans le fichier .env

Vérifie que :

- le fichier s’appelle exactement `.env` ;
- il est dans le même dossier que les scripts ;
- il ne s’appelle pas `.env.txt` ;
- le Client ID est présent ;
- le Client Secret est présent ;
- l’URL de redirection est présente.

---

## URL de redirection incorrecte

Vérifie que l’adresse suivante est enregistrée dans Spotify Developer :

    http://127.0.0.1:8888/callback

Elle doit être identique dans le fichier `.env`.

---

## Aucun appareil Spotify actif

Message possible :

    Aucun appareil Spotify actif

Solution :

1. ouvre Spotify sur ton ordinateur ou ton téléphone ;
2. lance un morceau ;
3. mets-le en pause ;
4. relance l’écoute depuis VS Musique.

---

## La lecture Spotify demande Premium

Le pilotage de la lecture Spotify peut nécessiter un compte Premium.

Le classement reste possible sans lecture automatique, mais il faudra écouter les morceaux séparément.

---

## Un morceau est introuvable sur Spotify

Causes possibles :

- faute dans le nom de l’artiste ;
- titre différent sur Spotify ;
- version remixée ;
- plusieurs artistes ;
- morceau retiré de Spotify ;
- résultat incorrect enregistré précédemment.

Solution recommandée :

1. ouvre `ajouter_musique.py` ;
2. recherche le morceau ;
3. sélectionne le bon résultat Spotify ;
4. vérifie l’URI enregistrée.

---

## La mauvaise version d’un morceau est trouvée

La recherche automatique prend généralement le premier résultat correspondant.

Pour obtenir une version précise, utilise la recherche Spotify dans `ajouter_musique.py`.

Cela permet de sélectionner manuellement :

- la version originale ;
- un remix ;
- une version live ;
- une réédition ;
- une version remasterisée.

---

## scores.json est corrompu

Message possible :

    Le fichier scores.json est corrompu

Évite de modifier manuellement le JSON sans vérifier sa syntaxe.

Utilise une sauvegarde récente si nécessaire.

Un fichier JSON valide doit respecter les règles suivantes :

- guillemets doubles autour des clés ;
- virgules entre les propriétés ;
- aucune virgule après la dernière propriété ;
- accolades correctement fermées.

---

## Tous les morceaux sont déjà classés

Message possible dans le tri rapide :

    Tous tes morceaux sont déjà classés

Cela signifie que tous les morceaux ont déjà un palier ou ont commencé des duels.

Tu peux lancer :

    python duels_elo.py

Si tu ajoutes ensuite un nouveau morceau, il sera disponible lors du prochain lancement du tri rapide.

---

## Les duels se terminent immédiatement

Vérifie :

- qu’il existe au moins deux morceaux ;
- qu’au moins un morceau n’a pas atteint son quota ;
- que tu utilises la version corrigée de `moteur.py`.

La version corrigée autorise les morceaux déjà terminés à servir d’adversaires aux nouveaux morceaux.

---

## L’application semble figée

Les appels Spotify et les téléchargements peuvent prendre quelques secondes.

Le moteur utilise des threads pour éviter de bloquer l’interface, mais une connexion lente peut retarder :

- l’affichage de la pochette ;
- la récupération de l’URI ;
- le lancement de la lecture.

Attends quelques secondes avant de relancer plusieurs fois la même action.

---

# Sécurité

## Ne jamais publier le fichier .env

Le fichier `.env` contient le Client Secret Spotify.

Il ne doit jamais être :

- publié sur GitHub ;
- envoyé dans une archive publique ;
- partagé sur un forum ;
- intégré dans une capture d’écran ;
- envoyé à un autre utilisateur.

## Ne jamais publier les caches Spotify

Les fichiers suivants doivent rester privés :

    .cache-spotify-top
    .cache-spotify-lecture

## Régénérer un secret exposé

Si le Client Secret a été publié ou envoyé accidentellement :

1. ouvre Spotify Developer ;
2. ouvre l’application concernée ;
3. régénère le secret ;
4. remplace l’ancien secret dans `.env` ;
5. supprime les anciens caches si nécessaire ;
6. reconnecte l’application.

## Fichier .gitignore recommandé

Crée un fichier nommé `.gitignore` contenant :

    .env
    .cache-spotify*
    __pycache__/
    *.pyc
    .venv/
    pochettes/
    scores.json
    scores.backup-*.json
    *.tmp

Si tu souhaites fournir un exemple de données, crée plutôt :

    scores.example.json

## Fichier .env.example recommandé

Crée un fichier `.env.example` contenant :

    SPOTIPY_CLIENT_ID=
    SPOTIPY_CLIENT_SECRET=
    SPOTIPY_REDIRECT_URI=http://127.0.0.1:8888/callback

Ce fichier peut être partagé, car il ne contient aucun secret réel.

---

# Limites actuelles

## Plusieurs fenêtres indépendantes

Chaque fonctionnalité possède encore son propre script.

L’utilisateur doit lancer séparément :

- la génération ;
- l’ajout manuel ;
- le tri rapide ;
- les duels Elo.

Un lanceur central est prévu.

## Classement stocké dans un seul fichier

Le projet utilise actuellement un unique `scores.json`.

Il n’existe pas encore de gestion intégrée de plusieurs profils ou plusieurs classements.

## Annulation limitée

L’annulation concerne uniquement la dernière action conservée en mémoire.

Après fermeture de l’application, l’ancien vote ne peut plus être annulé depuis l’interface.

## Dépendance à Spotify pour l’écoute

L’écoute nécessite :

- une connexion Internet ;
- Spotify disponible ;
- un appareil Spotify ;
- les autorisations nécessaires ;
- éventuellement un compte Premium.

## Interface de classement simple

La fenêtre de classement affiche actuellement une liste textuelle.

Une vue plus complète pourra inclure :

- la pochette ;
- le rang ;
- l’Elo ;
- les victoires ;
- les défaites ;
- les égalités ;
- le palier ;
- un bouton d’écoute ;
- une recherche ;
- des filtres.

## Pas encore de playlist automatique

La création d’une playlist Spotify à partir du classement est prévue, mais elle n’est pas intégrée dans la version actuelle documentée ici.

---

# Feuille de route

## Priorité 1 : lanceur principal

Créer un fichier :

    main.py

Il ouvrira une fenêtre avec les boutons suivants :

- Générer ma liste ;
- Importer mon historique Spotify ;
- Ajouter un morceau ;
- Lancer le tri rapide ;
- Lancer les duels Elo ;
- Voir le classement ;
- Créer une playlist ;
- Configurer l’application ;
- Quitter.

## Priorité 2 : écran de classement

Créer une interface dédiée avec :

- position ;
- pochette ;
- artiste ;
- titre ;
- Elo ;
- palier ;
- nombre de matchs ;
- nombre de victoires ;
- nombre de défaites ;
- nombre d’égalités ;
- bouton d’écoute ;
- barre de recherche ;
- filtres par palier ;
- tri par colonne.

## Priorité 3 : création de playlist Spotify

Créer un script :

    playlist_creator.py

Le script devra :

1. lire `scores.json` ;
2. trier les morceaux par Elo ;
3. utiliser directement les URI Spotify ;
4. rechercher uniquement les URI manquantes ;
5. créer une playlist Spotify ;
6. ajouter les morceaux dans l’ordre ;
7. signaler les morceaux introuvables.

## Priorité 4 : gestion de plusieurs profils

Structure possible :

    profils/
    ├── julien/
    │   └── scores.json
    ├── profil_2/
    │   └── scores.json
    └── profil_3/
        └── scores.json

Chaque utilisateur pourrait posséder :

- son classement ;
- ses caches ;
- sa configuration ;
- ses sauvegardes.

## Priorité 5 : historique des votes

Créer un fichier :

    historique_votes.json

Chaque vote pourrait contenir :

    {
        "date": "2026-09-20T19:30:00",
        "morceau_1": "Artiste A - Titre A",
        "morceau_2": "Artiste B - Titre B",
        "resultat": 1,
        "ancien_elo_1": 1050,
        "nouvel_elo_1": 1063,
        "ancien_elo_2": 1070,
        "nouvel_elo_2": 1057
    }

Cela permettrait :

- d’annuler plusieurs votes ;
- de consulter l’historique ;
- de produire des statistiques ;
- de restaurer un classement.

## Priorité 6 : sauvegardes intégrées

Ajouter :

- sauvegarde automatique quotidienne ;
- bouton de sauvegarde ;
- bouton de restauration ;
- export du classement ;
- import d’un classement existant.

## Priorité 7 : export

Formats envisagés :

- JSON ;
- CSV ;
- Excel ;
- HTML ;
- image du classement ;
- playlist Spotify.

## Priorité 8 : exécutable Windows

Créer une version `.exe` avec PyInstaller.

Exemple :

    pyinstaller --onefile --windowed main.py

Il faudra inclure correctement :

- les modules Python ;
- les ressources ;
- les icônes ;
- la gestion des chemins ;
- le dossier de données utilisateur.

---

# Architecture technique

## Séparation des responsabilités

L’application suit une séparation simple :

### Interface

Les fichiers d’interface sont :

    ajouter_musique.py
    tri_rapide.py
    duels_elo.py

Ils gèrent :

- les fenêtres ;
- les boutons ;
- les touches ;
- les messages ;
- la progression ;
- l’affichage.

### Logique

Le fichier principal de logique est :

    moteur.py

Il gère :

- les données ;
- les scores ;
- les duels ;
- Spotify ;
- les pochettes ;
- la lecture ;
- les tâches en arrière-plan.

### Données

Le fichier principal de données est :

    scores.json

Cette séparation facilite :

- les corrections ;
- les tests ;
- la maintenance ;
- l’ajout de nouvelles interfaces ;
- la transformation future en application complète.

## Threads

Le moteur utilise des threads pour :

- récupérer les métadonnées ;
- télécharger les pochettes ;
- lancer les commandes Spotify ;
- arrêter automatiquement les extraits.

L’interface Tkinter reste ainsi réactive pendant les opérations réseau.

## Verrou

Un verrou protège les modifications de `scores.json`.

Cela évite que deux opérations écrivent simultanément dans le fichier.

## Files de messages

Le chargeur et le lecteur utilisent des files pour communiquer avec l’interface.

L’interface vérifie régulièrement :

- les métadonnées terminées ;
- les images disponibles ;
- les erreurs Spotify ;
- les messages du lecteur.

---

# Développement

## Modifier le nombre de matchs par défaut

Dans `moteur.py` :

    MATCHS_MAX_DEFAUT = 8

Exemple avec douze matchs :

    MATCHS_MAX_DEFAUT = 12

Il est également possible de le régler au lancement :

    python duels_elo.py --matchs 12

## Modifier la proximité des adversaires

Dans `moteur.py` :

    FENETRE_DEFAUT = 8

Cette valeur indique approximativement combien de voisins sont considérés de chaque côté dans le classement.

Une petite valeur produit des duels très proches.

Une valeur plus grande ajoute davantage de variété.

## Modifier le facteur Elo

Dans `moteur.py` :

    K = 32

Exemples :

    K = 16

Classement plus stable et changements plus faibles.

    K = 40

Classement plus réactif et changements plus importants.

## Modifier les paliers

Dans `moteur.py` :

    TIERS = [
        ("S", "❤️ J'adore", 1120, "1", "#e74c3c"),
        ("A", "👍 J'aime bien", 1060, "2", "#e67e22"),
        ("B", "😐 Correct", 1000, "3", "#3498db"),
        ("C", "👎 Bof", 940, "4", "#7f8c8d"),
        ("D", "🚫 Pas pour moi", 880, "5", "#8e44ad"),
    ]

Chaque ligne contient :

1. le code du palier ;
2. le libellé ;
3. l’Elo initial ;
4. la touche ;
5. la couleur.

## Tester sans modifier le vrai classement

Avant un test important :

1. copie `scores.json` ;
2. renomme la copie ;
3. effectue le test ;
4. restaure le fichier si nécessaire.

Exemple :

    Copy-Item .\scores.json .\scores_test_backup.json

Pour restaurer :

    Copy-Item .\scores_test_backup.json .\scores.json -Force

## Vérifier la syntaxe des scripts

Commande :

    python -m py_compile moteur.py

Pour vérifier plusieurs fichiers :

    python -m py_compile moteur.py tri_rapide.py duels_elo.py ajouter_musique.py generer_liste.py

L’absence de message signifie généralement que la syntaxe est valide.

---

# Utilisation recommandée

Pour une première utilisation complète :

## 1. Installer les dépendances

    pip install spotipy pillow

## 2. Configurer .env

    SPOTIPY_CLIENT_ID=ton_client_id
    SPOTIPY_CLIENT_SECRET=ton_client_secret
    SPOTIPY_REDIRECT_URI=http://127.0.0.1:8888/callback

## 3. Générer la liste

    python generer_liste.py

Ou avec l’historique :

    python generer_liste.py --historique mon_export.zip --nombre 200

## 4. Ajouter les morceaux manquants

    python ajouter_musique.py

## 5. Effectuer le tri rapide

    python tri_rapide.py

## 6. Effectuer les duels Elo

    python duels_elo.py

## 7. Ajouter de nouveaux morceaux plus tard

    python ajouter_musique.py

Puis :

    python tri_rapide.py
    python duels_elo.py

---

# Conseils d’utilisation

## Ne réfléchis pas trop pendant le tri rapide

Le tri rapide doit rester rapide.

Choisis le palier correspondant à ton impression générale.

Les duels Elo corrigeront ensuite les approximations.

## Utilise l’égalité si le choix est réellement difficile

Le bouton d’égalité est utile lorsque :

- les morceaux sont de niveau similaire ;
- tu ne connais pas assez un morceau ;
- ton choix dépend trop de ton humeur ;
- tu ne veux pas forcer une préférence artificielle.

## Évite de regarder l’Elo avant de voter

L’Elo n’est volontairement pas affiché dans la fenêtre principale des duels.

Cela limite l’influence du classement existant sur les choix.

## Fais des pauses

Un grand nombre de votes peut provoquer de la fatigue et rendre les décisions moins cohérentes.

Il est préférable de faire plusieurs sessions courtes.

Les données étant sauvegardées après chaque vote, tu peux fermer l’application sans perdre ta progression.

---

# Nom du projet

Nom actuel :

    VS Musique

Autres noms potentiels :

- Music Duel ;
- Elo Music ;
- Rank My Music ;
- SoundRank ;
- Track Duel ;
- Mon classement musical ;
- Duel de Musiques.

---

# État actuel

Fonctionnalités disponibles :

- génération depuis l’API Spotify ;
- génération depuis un historique étendu ;
- sauvegarde de l’ancien fichier ;
- ajout manuel ;
- recherche Spotify ;
- détection des doublons ;
- tri rapide ;
- paliers configurables ;
- duels Elo ;
- adversaires de niveau proche ;
- pochettes ;
- extraits Spotify ;
- arrêt automatique ;
- annulation du dernier vote ;
- classement temporaire ;
- reprise après fermeture ;
- ajout tardif de nouveaux morceaux ;
- sauvegarde atomique ;
- compatibilité améliorée avec OneDrive.

Fonctionnalités restant à développer :

- lanceur principal ;
- écran de classement complet ;
- création de playlist ;
- export Excel ou CSV ;
- historique persistant des votes ;
- gestion de plusieurs profils ;
- paramètres accessibles depuis l’interface ;
- création d’un exécutable Windows ;
- installateur ;
- tests automatisés complets.

---

# Contribution

Pour proposer une amélioration :

1. crée une copie du projet ;
2. crée une branche dédiée ;
3. effectue la modification ;
4. teste la syntaxe ;
5. vérifie le comportement avec une copie de `scores.json` ;
6. documente le changement ;
7. crée une demande de fusion.

Exemple de nom de branche :

    feature/classement-interface

Exemple pour une correction :

    fix/nouveaux-morceaux-duels

---

# Licence

La licence du projet reste à définir.

Avant une publication publique, ajoute un fichier :

    LICENSE

Licences possibles :

- MIT ;
- Apache 2.0 ;
- GPLv3 ;
- projet privé sans redistribution.

La licence MIT est souvent adaptée aux petits projets open source permissifs.

---

# Avertissement

VS Musique est un projet personnel indépendant.

Le projet n’est pas affilié, sponsorisé ou approuvé par Spotify.

Spotify, ses marques et ses services appartiennent à leurs propriétaires respectifs.

L’utilisateur est responsable :

- de ses identifiants Spotify ;
- de la confidentialité de son Client Secret ;
- de ses fichiers de cache ;
- de ses données d’écoute ;
- du respect des conditions d’utilisation des services utilisés.

---

# Résumé rapide

Installation :

    pip install spotipy pillow

Configuration :

    SPOTIPY_CLIENT_ID=ton_client_id
    SPOTIPY_CLIENT_SECRET=ton_client_secret
    SPOTIPY_REDIRECT_URI=http://127.0.0.1:8888/callback

Génération :

    python generer_liste.py

Ajout manuel :

    python ajouter_musique.py

Tri rapide :

    python tri_rapide.py

Duels Elo :

    python duels_elo.py

Duels plus précis :

    python duels_elo.py --matchs 12

Fichier principal de données :

    scores.json

Cœur de l’application :

    moteur.py

---

# VS Musique

Crée ta bibliothèque, classe rapidement tes morceaux, puis affine ton classement grâce aux duels Elo.