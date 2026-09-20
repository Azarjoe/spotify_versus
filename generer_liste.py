#!/usr/bin/env python3
"""
generer_liste.py - Crée la liste de morceaux (scores.json) de Duel de Musiques
à partir des écoutes Spotify de l'utilisateur.

DEUX SOURCES POSSIBLES
──────────────────────
1) L'historique Spotify (RECOMMANDÉ - vrai classement "de tous les temps")
   L'API Spotify ne donne pas le nombre d'écoutes par morceau. La seule source
   complète est l'export de tes données personnelles :
     a. spotify.com/account/privacy  ->  "Télécharger vos données"
     b. Coche "Historique de streaming étendu" (et pas seulement "Données du compte")
     c. Confirme par mail, puis attends le mail de Spotify (quelques jours,
        jusqu'à 30 jours) avec un .zip
     d. python generer_liste.py --historique mon_export.zip
   Aucun compte développeur Spotify n'est nécessaire dans ce mode.

2) L'API Spotify (approximation rapide, sans attendre l'export)
   python generer_liste.py
   Limites imposées par Spotify : ~1 an de données au maximum et 50 morceaux
   par période (4 semaines / 6 mois / ~1 an). Le total sera donc bien
   inférieur à 200 la plupart du temps. Nécessite un compte développeur Spotify :
   crée un fichier .env à côté du script avec :
       SPOTIPY_CLIENT_ID=ton_client_id
       SPOTIPY_CLIENT_SECRET=ton_client_secret
       SPOTIPY_REDIRECT_URI=http://127.0.0.1:8888/callback

SORTIE
──────
Un fichier JSON au même format que l'actuel scores.json (clé "Artiste - Musique",
Elo à 1000, compteurs à 0), directement utilisable par classement_avecextraits.py
et lissage.py. Si le fichier de sortie existe déjà, il est d'abord sauvegardé.
"""

import argparse
import json
import os
import shutil
import sys
import zipfile
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

ELO_DEPART = 1000
NOMBRE_DEFAUT = 200
SEUIL_STREAM_MS = 30_000  # Spotify compte un "stream" à partir de 30 secondes d'écoute
SCOPE = "user-top-read"
CACHE_PATH = ".cache-spotify-top"  # cache séparé : pas de conflit avec les autres scripts


# ──────────────────────────────────────────────────────────────
# Outils communs
# ──────────────────────────────────────────────────────────────
def charger_env(chemin=".env"):
    """Charge un petit fichier .env (CLE=valeur) sans dépendance externe."""
    if not os.path.exists(chemin):
        return
    with open(chemin, "r", encoding="utf-8") as f:
        for ligne in f:
            ligne = ligne.strip()
            if not ligne or ligne.startswith("#") or "=" not in ligne:
                continue
            cle, valeur = ligne.split("=", 1)
            os.environ.setdefault(cle.strip(), valeur.strip().strip('"').strip("'"))


def cle_normalisee(artiste, musique):
    """Sert à regrouper un même morceau écrit avec une casse/espacement différent."""
    return (" ".join(artiste.casefold().split()), " ".join(musique.casefold().split()))


def nouvelle_entree(artiste, musique, uri=None, streams=None):
    """Même structure que scores.json, + 2 champs bonus ignorés par les autres scripts."""
    entree = {
        "artiste": artiste,
        "musique": musique,
        "elo": ELO_DEPART,
        "victoires": 0,
        "defaites": 0,
        "egalites": 0,
    }
    if uri:
        entree["spotify_uri"] = uri
    if streams is not None:
        entree["streams"] = streams
    return entree


def ecrire_scores(entrees, chemin):
    """
    Fusionne les nouveaux morceaux avec scores.json.

    Les morceaux existants conservent leur Elo, leurs matchs, leur palier
    et leurs métadonnées. Seuls les nouveaux morceaux sont ajoutés.
    """
    data = {}

    if os.path.exists(chemin):
        horodatage = datetime.now().strftime("%Y%m%d-%H%M%S")
        base, ext = os.path.splitext(chemin)
        sauvegarde = f"{base}.backup-{horodatage}{ext}"
        shutil.copy2(chemin, sauvegarde)
        print(f"Sauvegarde créée : {sauvegarde}")

        try:
            with open(chemin, "r", encoding="utf-8") as fichier:
                data = json.load(fichier)
        except (json.JSONDecodeError, OSError) as erreur:
            sys.exit(f"Impossible de lire {chemin} : {erreur}")

    index_existant = {}

    for cle, info in data.items():
        artiste = info.get("artiste", "")
        musique = info.get("musique", info.get("titre", ""))

        if artiste and musique:
            index_existant[cle_normalisee(artiste, musique)] = cle

    ajoutes = 0
    actualises = 0

    for entree in entrees:
        artiste = entree["artiste"]
        musique = entree["musique"]
        identifiant = cle_normalisee(artiste, musique)

        if identifiant in index_existant:
            cle_existante = index_existant[identifiant]
            existant = data[cle_existante]

            # Complète uniquement les métadonnées manquantes.
            # L'Elo, les matchs et le palier ne sont jamais réinitialisés.
            for champ in ("spotify_uri", "streams", "pochette", "duree_ms"):
                if entree.get(champ) is not None and not existant.get(champ):
                    existant[champ] = entree[champ]
                    actualises += 1

            continue

        cle = f"{artiste} - {musique}"

        # Évite également une collision exceptionnelle de clé.
        if cle in data:
            suffixe = 2
            cle_base = cle

            while cle in data:
                cle = f"{cle_base} ({suffixe})"
                suffixe += 1

        data[cle] = entree
        index_existant[identifiant] = cle
        ajoutes += 1

    temporaire = chemin + ".tmp"

    with open(temporaire, "w", encoding="utf-8") as fichier:
        json.dump(data, fichier, indent=4, ensure_ascii=False)

    os.replace(temporaire, chemin)

    print(f"Nouveaux morceaux ajoutés : {ajoutes}")
    print(f"Morceaux déjà présents : {len(entrees) - ajoutes}")

    if actualises:
        print(f"Métadonnées complétées : {actualises}")

    return len(data)

# ──────────────────────────────────────────────────────────────
# Source 1 : historique de streaming (export Spotify)
# ──────────────────────────────────────────────────────────────
def _nom_normalise(nom):
    return os.path.basename(nom).lower().replace("_", "").replace(" ", "")


def _est_fichier_historique(nom):
    n = _nom_normalise(nom)
    return n.endswith(".json") and "streaminghistory" in n and "video" not in n


def lire_fichiers_historique(source):
    """
    Renvoie [(nom_fichier, liste_d_ecoutes), ...] depuis un dossier ou un .zip.
    Si l'historique étendu ("Streaming_History_Audio_*") est présent, on ignore
    l'ancien format d'1 an ("StreamingHistory*") pour ne pas compter deux fois.
    """
    source = Path(source)
    fichiers = []

    if source.is_file() and source.suffix.lower() == ".zip":
        with zipfile.ZipFile(source) as z:
            for nom in sorted(z.namelist()):
                if _est_fichier_historique(nom):
                    with z.open(nom) as f:
                        fichiers.append((nom, json.load(f)))
    elif source.is_dir():
        for chemin in sorted(source.rglob("*.json")):
            if _est_fichier_historique(chemin.name):
                with open(chemin, "r", encoding="utf-8") as f:
                    fichiers.append((str(chemin), json.load(f)))
    else:
        raise FileNotFoundError(f"Introuvable (dossier ou .zip attendu) : {source}")

    etendus = [x for x in fichiers if "streaminghistoryaudio" in _nom_normalise(x[0])]
    return etendus if etendus else fichiers


def compter_streams(fichiers, min_ms=SEUIL_STREAM_MS):
    """Compte les écoutes >= min_ms par morceau. Renvoie une liste triée (plus écouté d'abord)."""
    compteur = Counter()
    noms = defaultdict(Counter)  # écriture la plus fréquente (artiste, titre)
    uris = defaultdict(Counter)

    for _, ecoutes in fichiers:
        for e in ecoutes:
            # Format étendu (master_metadata_*) ou ancien format (artistName/trackName)
            titre = e.get("master_metadata_track_name") or e.get("trackName")
            artiste = e.get("master_metadata_album_artist_name") or e.get("artistName")
            ms = e.get("ms_played", e.get("msPlayed", 0)) or 0

            if not titre or not artiste:  # podcasts / lignes sans métadonnées
                continue
            if ms < min_ms:  # skip rapide : pas un vrai stream
                continue

            k = cle_normalisee(artiste, titre)
            compteur[k] += 1
            noms[k][(artiste.strip(), titre.strip())] += 1
            uri = e.get("spotify_track_uri")
            if uri:
                uris[k][uri] += 1

    resultat = []
    for k, nb in sorted(compteur.items(), key=lambda kv: (-kv[1], kv[0])):
        artiste, titre = noms[k].most_common(1)[0][0]
        uri = uris[k].most_common(1)[0][0] if uris[k] else None
        resultat.append(nouvelle_entree(artiste, titre, uri=uri, streams=nb))
    return resultat


def top_depuis_historique(source, nombre, min_ms):
    try:
        fichiers = lire_fichiers_historique(source)
    except FileNotFoundError as e:
        sys.exit(f"Erreur : {e}")
    except zipfile.BadZipFile:
        sys.exit(f"Erreur : {source} n'est pas un .zip valide.")
    if not fichiers:
        sys.exit(
            "Aucun fichier d'historique trouvé (Streaming_History_Audio_*.json).\n"
            "Vérifie que tu as bien demandé l'« Historique de streaming étendu »."
        )
    nb_ecoutes = sum(len(e) for _, e in fichiers)
    print(f"{len(fichiers)} fichier(s) lu(s), {nb_ecoutes} écoutes au total.")
    return compter_streams(fichiers, min_ms)[:nombre]


# ──────────────────────────────────────────────────────────────
# Source 2 : API Spotify (approximation)
# ──────────────────────────────────────────────────────────────
PERIODES_API = (
    ("long_term", "~12 derniers mois"),
    ("medium_term", "~6 derniers mois"),
    ("short_term", "~4 dernières semaines"),
)


def recuperer_top_api(sp, nombre):
    """Fusionne les tops Spotify des 3 périodes (50 max chacune), sans doublons."""
    vus = {}
    for periode, libelle in PERIODES_API:
        items = sp.current_user_top_tracks(limit=50, time_range=periode).get("items", [])
        nouveaux = 0
        for t in items:
            if not t or not t.get("name"):
                continue
            artiste = t["artists"][0]["name"] if t.get("artists") else "Inconnu"
            k = cle_normalisee(artiste, t["name"])
            if k not in vus:
                vus[k] = nouvelle_entree(artiste, t["name"], uri=t.get("uri"))
                nouveaux += 1
        print(f"  {libelle:<24} : {len(items):>2} morceaux, {nouveaux:>2} nouveaux")
        if len(vus) >= nombre:
            break
    return list(vus.values())[:nombre]


def creer_client_spotify():
    charger_env()
    try:
        import spotipy
        from spotipy.oauth2 import SpotifyOAuth
    except ImportError:
        sys.exit("Le module spotipy est requis pour ce mode :  pip install spotipy")

    manquants = [v for v in ("SPOTIPY_CLIENT_ID", "SPOTIPY_CLIENT_SECRET") if not os.environ.get(v)]
    if manquants:
        sys.exit(
            f"Identifiants Spotify manquants : {', '.join(manquants)}\n"
            "Crée un fichier .env à côté du script (voir l'en-tête de generer_liste.py),\n"
            "ou utilise --historique avec ton export Spotify (aucun identifiant requis)."
        )
    os.environ.setdefault("SPOTIPY_REDIRECT_URI", "http://127.0.0.1:8888/callback")

    return spotipy.Spotify(
        auth_manager=SpotifyOAuth(scope=SCOPE, cache_path=CACHE_PATH)
    )


def top_depuis_api(nombre):
    sp = creer_client_spotify()
    utilisateur = sp.current_user()
    print(f"Connecté à Spotify en tant que : {utilisateur.get('display_name') or utilisateur['id']}")
    print("Récupération des morceaux les plus écoutés :")
    return recuperer_top_api(sp, nombre)


# ──────────────────────────────────────────────────────────────
# Programme principal
# ──────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="Génère scores.json avec tes morceaux les plus écoutés sur Spotify."
    )
    parser.add_argument(
        "--historique", metavar="DOSSIER_OU_ZIP",
        help="Export Spotify (historique de streaming étendu) : vrai classement de tous les temps.",
    )
    parser.add_argument("--nombre", type=int, default=NOMBRE_DEFAUT,
                        help=f"Nombre de morceaux à garder (défaut : {NOMBRE_DEFAUT}).")
    parser.add_argument("--sortie", default="scores.json",
                        help="Fichier JSON à créer (défaut : scores.json).")
    parser.add_argument("--min-ms", type=int, default=SEUIL_STREAM_MS,
                        help="Durée minimale d'écoute en ms pour compter un stream (défaut : 30000).")
    args = parser.parse_args()

    if args.historique:
        entrees = top_depuis_historique(args.historique, args.nombre, args.min_ms)
    else:
        print("Mode API : Spotify ne fournit que ~1 an de données, 50 morceaux par période.")
        print("Pour un vrai top « de tous les temps », utilise --historique (voir l'aide).\n")
        entrees = top_depuis_api(args.nombre)

    if not entrees:
        sys.exit("Aucun morceau récupéré, rien n'a été écrit.")

    total = ecrire_scores(entrees, args.sortie)
    print(f"\n✅ {total} morceaux écrits dans {args.sortie}")
    if total < args.nombre:
        print(f"⚠️  Moins que les {args.nombre} demandés : pas assez de données dans cette source.")


if __name__ == "__main__":
    main()