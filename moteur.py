#!/usr/bin/env python3
"""
moteur.py - Cœur commun de tri_rapide.py et duels_elo.py (aucune interface ici).

Contient :
  - la lecture/écriture sécurisée de scores.json
  - le calcul Elo
  - MoteurTri    : phase 1, classement ultra rapide par paliers (S/A/B/C/D)
  - MoteurDuels  : phase 2, duels Elo entre morceaux de niveau proche
  - Spotify      : connexion, infos du morceau (pochette, durée), lecture d'un extrait
  - Chargeur     : récupère infos + pochettes en arrière-plan (l'interface ne se fige pas)
  - Lecteur      : lance/arrête la musique en arrière-plan

Les réglages importants sont juste en dessous, modifie-les à ta guise.
"""

import hashlib
import json
import os
import queue
import random
import threading
import time
import urllib.request
from io import BytesIO

# ──────────────────────────────────────────────────────────────
# RÉGLAGES
# ──────────────────────────────────────────────────────────────
JSON_FILE = "scores.json"
DOSSIER_POCHETTES = "pochettes"          # cache des images (créé automatiquement)

# Extrait : on démarre à 35 % du morceau (souvent le refrain) et on coupe après 20 s.
EXTRAIT_DEBUT = 0.35
EXTRAIT_DUREE_S = 20                     # 0 = pas d'arrêt automatique

K = 32                                   # sensibilité de l'Elo
MATCHS_MAX_DEFAUT = 8                    # duels par morceau dans la phase précise
FENETRE_DEFAUT = 8                       # adversaire choisi parmi les 8 plus proches de chaque côté

# Paliers de la phase rapide : (code, libellé, Elo de départ, touche, couleur)
# Écarts volontairement modestes (60 points) : testé en simulation, c'est plus robuste quand on
# classe vite et sans trop réfléchir. Les duels de la phase 2 corrigent ensuite les erreurs.
TIERS = [
    ("S", "❤️ J'adore",       1120, "1", "#e74c3c"),
    ("A", "👍 J'aime bien",   1060, "2", "#e67e22"),
    ("B", "😐 Correct",       1000, "3", "#3498db"),
    ("C", "👎 Bof",            940, "4", "#7f8c8d"),
    ("D", "🚫 Pas pour moi",   880, "5", "#8e44ad"),
]
ELO_TIER = {code: elo for code, _, elo, _, _ in TIERS}

# Spotify : lecture pilotée depuis l'appli (Premium + un appareil Spotify ouvert)
SCOPE = "user-modify-playback-state user-read-playback-state"
CACHE_PATH = ".cache-spotify-lecture"

VERROU = threading.Lock()  # protège scores.json (accès depuis l'interface ET l'arrière-plan)


# ──────────────────────────────────────────────────────────────
# Données
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


def charger_scores(chemin=JSON_FILE):
    if not os.path.exists(chemin):
        return {}
    with open(chemin, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            raise ValueError(f"Le fichier {chemin} est corrompu (JSON invalide).")
    for info in data.values():
        info.setdefault("elo", 1000)
        info.setdefault("victoires", 0)
        info.setdefault("defaites", 0)
        info.setdefault("egalites", 0)
    return data


def sauvegarder_scores(data, chemin=JSON_FILE):
    """Écriture atomique (jamais de fichier à moitié écrit) + nouvel essai si OneDrive le verrouille."""
    with VERROU:
        temporaire = chemin + ".tmp"
        with open(temporaire, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        for essai in range(5):
            try:
                os.replace(temporaire, chemin)
                return
            except PermissionError:
                if essai == 4:
                    raise
                time.sleep(0.2)


def nb_matchs(info):
    return info.get("victoires", 0) + info.get("defaites", 0) + info.get("egalites", 0)


def update_elo(rating1, rating2, resultat):
    """resultat : 1 = le 1er gagne, 2 = le 2e gagne, 0 = égalité. Renvoie les deux nouveaux Elo."""
    attendu1 = 1 / (1 + 10 ** ((rating2 - rating1) / 400))
    attendu2 = 1 - attendu1
    if resultat == 1:
        score1, score2 = 1, 0
    elif resultat == 2:
        score1, score2 = 0, 1
    else:
        score1, score2 = 0.5, 0.5
    return round(rating1 + K * (score1 - attendu1)), round(rating2 + K * (score2 - attendu2))


# ──────────────────────────────────────────────────────────────
# Phase 1 : tri rapide par paliers
# ──────────────────────────────────────────────────────────────
class MoteurTri:
    """Un seul choix par morceau. Le palier donne son Elo de départ pour la phase précise."""

    def __init__(self, data, sauvegarder, rng=None):
        self.data = data
        self.sauvegarder = sauvegarder
        rng = rng or random.Random()
        # Reprise possible : on ne présente que les morceaux jamais classés ni jamais joués en duel
        self.file = [k for k, v in data.items() if not v.get("tier") and nb_matchs(v) == 0]
        rng.shuffle(self.file)
        self.total = len(self.file)
        self.historique = []  # (clé, ancien Elo) pour pouvoir annuler

    def courant(self):
        return self.file[0] if self.file else None

    def apercu(self, n=3):
        return self.file[:n]

    def restants(self):
        return len(self.file)

    def assigner(self, code):
        if not self.file:
            return None
        cle = self.file.pop(0)
        with VERROU:
            info = self.data[cle]
            self.historique.append((cle, info.get("elo", 1000)))
            info["tier"] = code
            info["elo"] = ELO_TIER[code]
        self.sauvegarder(self.data)
        return cle

    def passer(self):
        """Reporte le morceau courant à la fin de la file."""
        if len(self.file) > 1:
            self.file.append(self.file.pop(0))

    def annuler(self):
        if not self.historique:
            return None
        cle, ancien_elo = self.historique.pop()
        with VERROU:
            self.data[cle].pop("tier", None)
            self.data[cle]["elo"] = ancien_elo
        self.file.insert(0, cle)
        self.sauvegarder(self.data)
        return cle


# ──────────────────────────────────────────────────────────────
# Phase 2 : duels Elo précis
# ──────────────────────────────────────────────────────────────
class MoteurDuels:
    """
    Choix des duels :
      1. on prend le morceau qui a fait le moins de matchs (les ex æquo au hasard)
      2. son adversaire est tiré parmi les morceaux d'Elo proche, en évitant les
         adversaires déjà rencontrés : un duel entre deux morceaux de même niveau
         apporte beaucoup plus d'information qu'un duel gagné d'avance.
    """

    def __init__(self, data, sauvegarder, matchs_max=MATCHS_MAX_DEFAUT, fenetre=FENETRE_DEFAUT, rng=None):
        self.data = data
        self.sauvegarder = sauvegarder
        self.matchs_max = matchs_max
        self.fenetre = fenetre
        self.rng = rng or random.Random()
        self.vus = set()      # paires déjà proposées pendant cette session
        self.dernier = None   # (clé1, copie1, clé2, copie2) pour annuler

    def eligibles(self):
        """Morceaux qui ont encore besoin de jouer pour atteindre leur quota."""
        return [k for k, v in self.data.items() if nb_matchs(v) < self.matchs_max]

    def prochain(self):
        """
        Construit le prochain duel.

        Le premier morceau est toujours choisi parmi ceux qui n'ont pas encore
        atteint leur quota. Son adversaire peut, lui, être choisi parmi TOUS les
        autres morceaux, y compris ceux qui ont déjà terminé leurs matchs.

        Cela permet d'intégrer un morceau ajouté après la fin du classement :
        il peut affronter des morceaux déjà classés au lieu de rester seul dans
        la liste des morceaux éligibles.
        """
        candidats = self.eligibles()
        if not candidats or len(self.data) < 2:
            return None

        # Priorité au morceau qui a joué le moins de matchs.
        mini = min(nb_matchs(self.data[k]) for k in candidats)
        a = self.rng.choice([
            k for k in candidats
            if nb_matchs(self.data[k]) == mini
        ])

        # L'adversaire est recherché dans le classement COMPLET. Les morceaux
        # ayant déjà atteint leur quota peuvent donc aider à classer un ajout récent.
        classement = sorted(self.data, key=lambda k: -self.data[k]["elo"])
        i = classement.index(a)
        debut = max(0, i - self.fenetre)
        fin = min(len(classement), i + self.fenetre + 1)
        voisins = [k for k in classement[debut:fin] if k != a]

        # Cas rare : avec une très petite fenêtre ou une donnée inhabituelle,
        # on retombe sur tous les autres morceaux plutôt que de bloquer.
        if not voisins:
            voisins = [k for k in classement if k != a]

        # On préfère un adversaire qui a lui aussi encore des matchs à faire,
        # afin que le duel fasse progresser deux morceaux à la fois. Si aucun
        # n'est disponible à proximité, un morceau déjà terminé reste autorisé.
        voisins_eligibles = [
            k for k in voisins
            if nb_matchs(self.data[k]) < self.matchs_max
        ]
        pool = voisins_eligibles or voisins

        # Évite de répéter une paire pendant la session tant que possible.
        neufs = [k for k in pool if frozenset((a, k)) not in self.vus]
        if not neufs and voisins_eligibles:
            # Tous les voisins encore éligibles ont déjà été rencontrés : on
            # tente alors un voisin terminé encore jamais rencontré.
            neufs = [k for k in voisins if frozenset((a, k)) not in self.vus]

        b = self.rng.choice(neufs or pool)
        self.vus.add(frozenset((a, b)))

        paire = [a, b]
        self.rng.shuffle(paire)  # pas de "côté" favori
        return tuple(paire)

    def voter(self, cle1, cle2, resultat):
        """resultat : 1, 2 ou 0 (égalité). Renvoie (variation Elo du 1er, variation Elo du 2e)."""
        with VERROU:
            i1, i2 = self.data[cle1], self.data[cle2]
            self.dernier = (cle1, dict(i1), cle2, dict(i2))
            n1, n2 = update_elo(i1["elo"], i2["elo"], resultat)
            delta = (n1 - i1["elo"], n2 - i2["elo"])
            i1["elo"], i2["elo"] = n1, n2
            if resultat == 1:
                i1["victoires"] += 1
                i2["defaites"] += 1
            elif resultat == 2:
                i2["victoires"] += 1
                i1["defaites"] += 1
            else:
                i1["egalites"] += 1
                i2["egalites"] += 1
        self.sauvegarder(self.data)
        return delta

    def annuler(self):
        """Annule le dernier vote. Renvoie la paire (clé1, clé2) à réafficher, ou None."""
        if not self.dernier:
            return None
        cle1, copie1, cle2, copie2 = self.dernier
        with VERROU:
            self.data[cle1] = copie1
            self.data[cle2] = copie2
        self.dernier = None
        self.sauvegarder(self.data)
        return cle1, cle2

    def progression(self):
        """(duels faits, duels prévus) : un duel compte pour 2 morceaux."""
        faits = sum(min(nb_matchs(v), self.matchs_max) for v in self.data.values()) / 2
        prevus = len(self.data) * self.matchs_max / 2
        return int(faits), int(prevus)

    def classement(self):
        return sorted(self.data.items(), key=lambda kv: -kv[1]["elo"])


# ──────────────────────────────────────────────────────────────
# Spotify : connexion, infos du morceau, pochette
# ──────────────────────────────────────────────────────────────
def creer_client_spotify():
    """Lève RuntimeError avec un message clair si la connexion est impossible."""
    charger_env()
    try:
        import spotipy
        from spotipy.oauth2 import SpotifyOAuth
    except ImportError:
        raise RuntimeError("Le module spotipy n'est pas installé.\nLance :  pip install spotipy")

    manquants = [v for v in ("SPOTIPY_CLIENT_ID", "SPOTIPY_CLIENT_SECRET") if not os.environ.get(v)]
    if manquants:
        raise RuntimeError("Identifiants Spotify manquants dans le fichier .env : " + ", ".join(manquants))
    os.environ.setdefault("SPOTIPY_REDIRECT_URI", "http://127.0.0.1:8888/callback")

    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=SCOPE, cache_path=CACHE_PATH),
                         requests_timeout=10, retries=2)
    sp.current_user()  # force la connexion maintenant (une page peut s'ouvrir dans le navigateur)
    return sp


def message_erreur_spotify(e):
    """Transforme une erreur Spotify en phrase compréhensible."""
    statut = getattr(e, "http_status", None)
    texte = f"{getattr(e, 'reason', '') or ''} {e}"
    if "NO_ACTIVE_DEVICE" in texte:
        return "Aucun appareil Spotify actif : ouvre Spotify (PC ou téléphone) et lance un morceau une fois."
    if "PREMIUM_REQUIRED" in texte or (statut == 403 and "premium" in texte.lower()):
        return "La lecture depuis l'appli demande un compte Spotify Premium."
    if statut == 429:
        return "Spotify demande de ralentir (trop de requêtes). Réessaie dans un instant."
    return f"Erreur Spotify : {e}"


def _piste_par_recherche(sp, artiste, titre):
    for requete in (f"artist:{artiste} track:{titre}", f"{artiste} {titre}"):
        items = sp.search(q=requete, type="track", limit=1)["tracks"]["items"]
        if items:
            return items[0]
    return None


def choisir_image(images, cible=300):
    """Parmi les tailles de pochette proposées par Spotify, prend la plus proche de `cible` px."""
    return min(images, key=lambda im: abs((im.get("width") or cible) - cible))["url"]


def recuperer_metadonnees(sp, info):
    """Renvoie {spotify_uri, pochette, duree_ms} (ce qui a pu être trouvé) pour un morceau."""
    piste = None
    uri = info.get("spotify_uri")
    if uri:
        try:
            piste = sp.track(uri)
        except Exception:
            piste = None
    if piste is None:
        piste = _piste_par_recherche(sp, info.get("artiste", ""), info.get("musique", info.get("titre", "")))
    if not piste:
        return {}

    meta = {"spotify_uri": piste["uri"]}
    images = (piste.get("album") or {}).get("images") or []
    if images:
        meta["pochette"] = choisir_image(images)
    if piste.get("duration_ms"):
        meta["duree_ms"] = piste["duration_ms"]
    return meta


def telecharger_pochette(url):
    """Télécharge la pochette (ou la relit depuis le cache disque). Renvoie les octets de l'image."""
    os.makedirs(DOSSIER_POCHETTES, exist_ok=True)
    chemin = os.path.join(DOSSIER_POCHETTES, hashlib.sha1(url.encode("utf-8")).hexdigest() + ".jpg")
    if os.path.exists(chemin):
        with open(chemin, "rb") as f:
            return f.read()
    requete = urllib.request.Request(url, headers={"User-Agent": "VS-Musique/1.0"})
    with urllib.request.urlopen(requete, timeout=10) as reponse:
        octets = reponse.read()
    with open(chemin, "wb") as f:
        f.write(octets)
    return octets


def octets_vers_photo(octets, taille):
    """Convertit les octets d'une image en image Tkinter (nécessite Pillow : pip install pillow)."""
    from PIL import Image, ImageTk  # import ici : le reste du module marche sans Pillow
    image = Image.open(BytesIO(octets)).convert("RGB").resize((taille, taille), Image.LANCZOS)
    return ImageTk.PhotoImage(image)


class Chargeur:
    """
    Récupère en arrière-plan les infos (uri, pochette, durée) et l'image de chaque morceau demandé.
    L'interface appelle demander(clé), puis lit resultats() régulièrement.
    Les infos trouvées sont enregistrées dans scores.json : elles ne sont demandées qu'une fois.
    """

    def __init__(self, sp, data, sauvegarder):
        self.sp = sp
        self.data = data
        self.sauvegarder = sauvegarder
        self.pochettes = {}  # clé -> octets de l'image
        self._demandes = queue.Queue()
        self._resultats = queue.Queue()
        self._deja = set()
        threading.Thread(target=self._boucle, daemon=True).start()

    def demander(self, cle):
        if cle in self._deja:
            return
        self._deja.add(cle)
        self._demandes.put(cle)

    def resultats(self):
        """Renvoie la liste des (clé, message_d_erreur_ou_None) terminés depuis le dernier appel."""
        sortis = []
        while True:
            try:
                sortis.append(self._resultats.get_nowait())
            except queue.Empty:
                return sortis

    def _boucle(self):
        while True:
            cle = self._demandes.get()
            erreur = None
            try:
                self._traiter(cle)
            except Exception as e:
                erreur = message_erreur_spotify(e) if hasattr(e, "http_status") else f"{type(e).__name__} : {e}"
            self._resultats.put((cle, erreur))

    def _traiter(self, cle):
        with VERROU:
            info = dict(self.data.get(cle, {}))
        if not info:
            return
        manque = [c for c in ("spotify_uri", "pochette", "duree_ms") if not info.get(c)]
        if manque and self.sp:
            meta = recuperer_metadonnees(self.sp, info)
            if meta:
                with VERROU:
                    self.data[cle].update(meta)
                info.update(meta)
                self.sauvegarder(self.data)
        if info.get("pochette"):
            self.pochettes[cle] = telecharger_pochette(info["pochette"])


class Lecteur:
    """
    Joue un extrait sur ton appareil Spotify, sans bloquer l'interface.
    Si plusieurs commandes s'accumulent (tu vas vite), seule la dernière est exécutée.
    """

    def __init__(self, sp):
        self.sp = sp
        self.messages = queue.Queue()
        self._commandes = queue.Queue()
        self._jeton = 0
        threading.Thread(target=self._boucle, daemon=True).start()

    def jouer(self, uri, duree_ms=None, extrait_s=EXTRAIT_DUREE_S, debut=EXTRAIT_DEBUT):
        self._commandes.put(("jouer", uri, duree_ms, extrait_s, debut))

    def arreter(self):
        self._commandes.put(("stop",))

    def arreter_maintenant(self):
        """À utiliser à la fermeture de la fenêtre (exécuté tout de suite, pas en arrière-plan)."""
        self._jeton += 1
        if self.sp:
            try:
                self.sp.pause_playback()
            except Exception:
                pass

    def lire_messages(self):
        sortis = []
        while True:
            try:
                sortis.append(self.messages.get_nowait())
            except queue.Empty:
                return sortis

    def _boucle(self):
        while True:
            cmd = self._commandes.get()
            while True:  # on ne garde que la commande la plus récente
                try:
                    cmd = self._commandes.get_nowait()
                except queue.Empty:
                    break
            try:
                self._executer(cmd)
            except Exception as e:
                self.messages.put(message_erreur_spotify(e))

    def _executer(self, cmd):
        if not self.sp:
            self.messages.put("Spotify n'est pas connecté : pas de son.")
            return
        self._jeton += 1
        if cmd[0] == "stop":
            self.sp.pause_playback()
            return

        _, uri, duree_ms, extrait_s, debut = cmd
        position = 0
        if duree_ms:
            position = int(duree_ms * debut)
            if extrait_s:  # on évite de démarrer trop près de la fin du morceau
                position = min(position, max(0, duree_ms - int((extrait_s + 2) * 1000)))
        self._demarrer(uri, position)

        if extrait_s and extrait_s > 0:
            minuteur = threading.Timer(extrait_s, self._fin_extrait, args=(self._jeton,))
            minuteur.daemon = True
            minuteur.start()

    def _demarrer(self, uri, position):
        try:
            self.sp.start_playback(uris=[uri], position_ms=position)
        except Exception as e:
            if "NO_ACTIVE_DEVICE" not in f"{getattr(e, 'reason', '')} {e}":
                raise
            # Aucun appareil "actif" : on réveille le premier appareil Spotify disponible
            appareils = self.sp.devices().get("devices", [])
            if not appareils:
                raise
            self.sp.start_playback(device_id=appareils[0]["id"], uris=[uri], position_ms=position)

    def _fin_extrait(self, jeton):
        if jeton == self._jeton:  # rien de nouveau n'a été lancé depuis
            try:
                self.sp.pause_playback()
            except Exception:
                pass
