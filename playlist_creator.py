#!/usr/bin/env python3
"""Crée une playlist Spotify avec les 100 meilleurs morceaux Elo."""

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
import webbrowser
from pathlib import Path


DOSSIER_APP = Path(__file__).resolve().parent
SCORES_FILE = DOSSIER_APP / "scores.json"
ENV_FILE = DOSSIER_APP / ".env"
CACHE_PATH = DOSSIER_APP / ".cache-spotify-playlist"

SCOPE = "playlist-modify-public playlist-modify-private"
NOMBRE_DEFAUT = 100


def envoyer_progression(etape, total, message):
    """
    Envoie une ligne spéciale que main.py peut lire en temps réel.

    Format :
    PROGRESS|étape|total|message
    """
    message = str(message).replace("\n", " ").replace("|", "-")

    print(
        f"PROGRESS|{etape}|{total}|{message}",
        flush=True,
    )


def envoyer_resultat(message):
    """Envoie le résultat final à main.py."""
    message = str(message).replace("\n", " ").replace("|", "-")

    print(
        f"RESULT|{message}",
        flush=True,
    )


def envoyer_url(url):
    """Envoie l'adresse de la playlist à main.py."""
    if not url:
        return

    print(
        f"PLAYLIST_URL|{url}",
        flush=True,
    )


def charger_env():
    if not ENV_FILE.exists():
        return

    with ENV_FILE.open("r", encoding="utf-8") as fichier:
        for ligne in fichier:
            ligne = ligne.strip()

            if not ligne or ligne.startswith("#") or "=" not in ligne:
                continue

            cle, valeur = ligne.split("=", 1)

            os.environ[cle.strip()] = valeur.strip().strip('"').strip("'")


def charger_scores():
    if not SCORES_FILE.exists():
        raise RuntimeError("scores.json est introuvable.")

    try:
        with SCORES_FILE.open("r", encoding="utf-8") as fichier:
            data = json.load(fichier)

    except json.JSONDecodeError as erreur:
        raise RuntimeError(
            f"scores.json contient un JSON invalide : {erreur}"
        ) from erreur

    except OSError as erreur:
        raise RuntimeError(
            f"Impossible de lire scores.json : {erreur}"
        ) from erreur

    if not isinstance(data, dict) or not data:
        raise RuntimeError(
            "scores.json est vide ou invalide."
        )

    return data


def sauvegarder_scores(data):
    temporaire = SCORES_FILE.with_suffix(".json.tmp")

    with temporaire.open("w", encoding="utf-8") as fichier:
        json.dump(
            data,
            fichier,
            indent=4,
            ensure_ascii=False,
        )

    os.replace(temporaire, SCORES_FILE)


def creer_client_spotify():
    charger_env()

    try:
        import spotipy
        from spotipy.oauth2 import SpotifyOAuth

    except ImportError as erreur:
        raise RuntimeError(
            "Spotipy n'est pas installé. "
            "Lance : pip install spotipy"
        ) from erreur

    manquantes = [
        variable
        for variable in (
            "SPOTIPY_CLIENT_ID",
            "SPOTIPY_CLIENT_SECRET",
        )
        if not os.environ.get(variable)
    ]

    if manquantes:
        raise RuntimeError(
            "Variables manquantes dans .env : "
            + ", ".join(manquantes)
        )

    os.environ.setdefault(
        "SPOTIPY_REDIRECT_URI",
        "http://127.0.0.1:8888/callback",
    )

    auth_manager = SpotifyOAuth(
        scope=SCOPE,
        cache_path=str(CACHE_PATH),
        open_browser=True,
    )

    client = spotipy.Spotify(
        auth_manager=auth_manager,
        requests_timeout=15,
        retries=2,
    )

    client.current_user()

    return client, auth_manager


def obtenir_token(auth_manager):
    token_info = auth_manager.get_cached_token()

    if not token_info:
        token_info = auth_manager.get_access_token(
            as_dict=True
        )

    elif auth_manager.is_token_expired(token_info):
        refresh_token = token_info.get("refresh_token")

        if refresh_token:
            token_info = auth_manager.refresh_access_token(
                refresh_token
            )
        else:
            token_info = auth_manager.get_access_token(
                as_dict=True
            )

    if isinstance(token_info, str):
        return token_info

    token = token_info.get("access_token")

    if not token:
        raise RuntimeError(
            "Impossible d'obtenir le jeton Spotify."
        )

    return token


def requete_spotify(
    methode,
    chemin,
    token,
    donnees=None,
):
    url = "https://api.spotify.com/v1/" + chemin.lstrip("/")
    corps = None

    if donnees is not None:
        corps = json.dumps(donnees).encode("utf-8")

    requete = urllib.request.Request(
        url=url,
        data=corps,
        method=methode,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )

    try:
        with urllib.request.urlopen(
            requete,
            timeout=30,
        ) as reponse:
            contenu = reponse.read()

            if not contenu:
                return {}

            return json.loads(
                contenu.decode("utf-8")
            )

    except urllib.error.HTTPError as erreur:
        contenu = erreur.read().decode(
            "utf-8",
            errors="replace",
        )

        raise RuntimeError(
            f"Erreur Spotify {erreur.code} : {contenu}"
        ) from erreur

    except urllib.error.URLError as erreur:
        raise RuntimeError(
            f"Connexion à Spotify impossible : {erreur}"
        ) from erreur


def rechercher_uri(client, info):
    artiste = str(
        info.get("artiste", "")
    ).strip()

    titre = str(
        info.get(
            "musique",
            info.get("titre", ""),
        )
    ).strip()

    if not artiste or not titre:
        return None

    requetes = (
        f"artist:{artiste} track:{titre}",
        f"{artiste} {titre}",
    )

    for requete in requetes:
        try:
            resultat = client.search(
                q=requete,
                type="track",
                limit=1,
            )

            morceaux = (
                resultat
                .get("tracks", {})
                .get("items", [])
            )

            if morceaux:
                return morceaux[0].get("uri")

        except Exception:
            continue

    return None


def preparer_top(client, data, nombre):
    classement = sorted(
        data.items(),
        key=lambda element: (
            -element[1].get("elo", 1000),
            element[0].casefold(),
        ),
    )

    uris = []
    introuvables = []
    modifications = False

    # On parcourt davantage que les 100 premières entrées si certaines
    # sont introuvables, afin d'essayer de remplir réellement la playlist.
    total_a_parcourir = len(classement)

    for position, (cle, info) in enumerate(
        classement,
        start=1,
    ):
        if len(uris) >= nombre:
            break

        progression = min(
            len(uris) + 1,
            nombre,
        )

        envoyer_progression(
            progression,
            nombre + 3,
            f"Préparation : {cle}",
        )

        uri = info.get("spotify_uri")

        if not uri:
            uri = rechercher_uri(
                client,
                info,
            )

            if uri:
                info["spotify_uri"] = uri
                modifications = True

        if (
            uri
            and uri.startswith("spotify:track:")
            and uri not in uris
        ):
            uris.append(uri)

            print(
                f"[{len(uris)}/{nombre}] {cle}",
                flush=True,
            )
        else:
            introuvables.append(cle)

            print(
                f"[INTROUVABLE] {cle}",
                flush=True,
            )

        if position >= total_a_parcourir:
            break

    if modifications:
        envoyer_progression(
            len(uris),
            nombre + 3,
            "Sauvegarde des URI Spotify retrouvées...",
        )

        sauvegarder_scores(data)

    return uris, introuvables


def creer_playlist(token, nom, publique):
    return requete_spotify(
        "POST",
        "/me/playlists",
        token,
        {
            "name": nom,
            "public": publique,
            "collaborative": False,
            "description": (
                "Playlist générée avec VS Musique "
                "à partir du classement Elo."
            ),
        },
    )


def ajouter_morceaux(
    token,
    playlist_id,
    uris,
    total_progression,
):
    total = len(uris)

    for debut in range(0, total, 100):
        groupe = uris[debut:debut + 100]

        fin = min(
            debut + len(groupe),
            total,
        )

        envoyer_progression(
            min(total_progression - 1, fin + 1),
            total_progression,
            f"Ajout des morceaux {debut + 1} à {fin}...",
        )

        requete_spotify(
            "POST",
            f"/playlists/{playlist_id}/items",
            token,
            {
                "uris": groupe,
            },
        )


def generer_playlist(
    nom,
    nombre=100,
    publique=True,
):
    nom = " ".join(nom.split())

    if not nom:
        raise RuntimeError(
            "Le nom de la playlist est vide."
        )

    if nombre < 1:
        raise RuntimeError(
            "Le nombre de morceaux est invalide."
        )

    total_progression = nombre + 3

    envoyer_progression(
        0,
        total_progression,
        "Chargement du classement...",
    )

    data = charger_scores()

    envoyer_progression(
        1,
        total_progression,
        "Connexion à Spotify...",
    )

    client, auth_manager = creer_client_spotify()

    utilisateur = client.current_user()

    nom_utilisateur = (
        utilisateur.get("display_name")
        or utilisateur.get("id")
        or "Utilisateur"
    )

    envoyer_progression(
        2,
        total_progression,
        f"Connecté à Spotify : {nom_utilisateur}",
    )

    uris, introuvables = preparer_top(
        client,
        data,
        nombre,
    )

    if not uris:
        raise RuntimeError(
            "Aucun morceau Spotify valide trouvé."
        )

    envoyer_progression(
        nombre + 1,
        total_progression,
        f"Création de la playlist « {nom} »...",
    )

    token = obtenir_token(auth_manager)

    playlist = creer_playlist(
        token,
        nom,
        publique,
    )

    playlist_id = playlist.get("id")

    if not playlist_id:
        raise RuntimeError(
            "Spotify n'a pas renvoyé l'identifiant "
            "de la playlist."
        )

    envoyer_progression(
        nombre + 2,
        total_progression,
        f"Ajout de {len(uris)} morceaux...",
    )

    ajouter_morceaux(
        token,
        playlist_id,
        uris,
        total_progression,
    )

    url = (
        playlist
        .get("external_urls", {})
        .get("spotify")
    )

    envoyer_progression(
        total_progression,
        total_progression,
        "Playlist terminée.",
    )

    envoyer_resultat(
        f"Playlist « {nom} » créée avec "
        f"{len(uris)} morceaux. "
        f"{len(introuvables)} morceau(x) introuvable(s)."
    )

    if url:
        envoyer_url(url)

        try:
            webbrowser.open(url)
        except Exception:
            pass

    return {
        "nom": nom,
        "url": url,
        "morceaux": len(uris),
        "introuvables": introuvables,
    }


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Crée une playlist Spotify depuis "
            "le classement Elo."
        )
    )

    parser.add_argument(
        "--nom",
        required=True,
        help="Nom de la playlist.",
    )

    parser.add_argument(
        "--nombre",
        type=int,
        default=NOMBRE_DEFAUT,
        help="Nombre de morceaux.",
    )

    parser.add_argument(
        "--privee",
        action="store_true",
        help="Crée une playlist privée.",
    )

    arguments = parser.parse_args()

    try:
        generer_playlist(
            nom=arguments.nom,
            nombre=arguments.nombre,
            publique=not arguments.privee,
        )

    except Exception as erreur:
        message = str(erreur).replace(
            "\n",
            " ",
        )

        print(
            f"ERROR|{message}",
            flush=True,
        )

        sys.exit(1)


if __name__ == "__main__":
    main()