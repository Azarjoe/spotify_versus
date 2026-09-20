#!/usr/bin/env python3
"""
ajouter_musique.py - Ajoute manuellement des morceaux à scores.json (interface graphique).

UTILISATION
───────────
    python ajouter_musique.py

  1. Tape l'artiste et le titre, puis clique sur "Ajouter" (ou appuie sur Entrée).
  2. Optionnel : "Chercher sur Spotify" propose des résultats. Un clic sur un résultat
     remplit les champs avec l'orthographe exacte de Spotify (moins de morceaux
     introuvables plus tard pour l'écoute et la playlist).

  Sans identifiants Spotify, l'ajout manuel fonctionne quand même : seule la
  recherche est désactivée. Pour l'activer, crée un fichier .env à côté du script :
      SPOTIPY_CLIENT_ID=ton_client_id
      SPOTIPY_CLIENT_SECRET=ton_client_secret
      SPOTIPY_REDIRECT_URI=http://127.0.0.1:8888/callback

  ⚠️ Ferme les fenêtres de duel (classement_avecextraits.py / lissage.py) avant d'ajouter
     des morceaux : elles gardent les scores en mémoire et écraseraient tes ajouts au
     prochain vote.
"""

import json
import os
import tkinter as tk
from tkinter import messagebox

JSON_FILE = "scores.json"
ELO_DEPART = 1000
SCOPE = "user-top-read"
CACHE_PATH = ".cache-spotify-top"  # même cache que generer_liste.py : pas de nouvelle connexion


# ──────────────────────────────────────────────────────────────
# Données (sans interface : testable seul)
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


def nettoyer(texte):
    """Supprime les espaces en trop (début, fin, doubles)."""
    return " ".join((texte or "").split())


def cle_normalisee(artiste, musique):
    """Sert à repérer un doublon malgré la casse ou les espaces différents."""
    return (nettoyer(artiste).casefold(), nettoyer(musique).casefold())


def charger_scores(chemin=JSON_FILE):
    if not os.path.exists(chemin):
        return {}
    with open(chemin, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            raise ValueError(f"Le fichier {chemin} est corrompu (JSON invalide).")


def sauvegarder_scores(data, chemin=JSON_FILE):
    """Écriture atomique : le fichier n'est jamais laissé à moitié écrit."""
    temporaire = chemin + ".tmp"
    with open(temporaire, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    os.replace(temporaire, chemin)


def ajouter_musique(artiste, titre, uri=None, chemin=JSON_FILE):
    """
    Ajoute un morceau (Elo 1000, compteurs à 0) au fichier.
    Renvoie (statut, clé) avec statut = "ajoute" | "doublon" | "invalide".
    Le fichier est relu à chaque ajout, donc rien n'est écrasé s'il a changé entre-temps.
    """
    artiste, titre = nettoyer(artiste), nettoyer(titre)
    if not artiste or not titre:
        return "invalide", None

    data = charger_scores(chemin)
    cherche = cle_normalisee(artiste, titre)
    for cle, info in data.items():
        existant = cle_normalisee(info.get("artiste", ""), info.get("musique", info.get("titre", "")))
        if existant == cherche:
            return "doublon", cle

    cle = f"{artiste} - {titre}"
    entree = {
        "artiste": artiste,
        "musique": titre,
        "elo": ELO_DEPART,
        "victoires": 0,
        "defaites": 0,
        "egalites": 0,
    }
    if uri:
        entree["spotify_uri"] = uri
    data[cle] = entree
    sauvegarder_scores(data, chemin)
    return "ajoute", cle


# ──────────────────────────────────────────────────────────────
# Recherche Spotify (optionnelle)
# ──────────────────────────────────────────────────────────────
def creer_client_spotify():
    """Crée le client Spotify. Lève RuntimeError avec un message clair si impossible."""
    charger_env()
    try:
        import spotipy
        from spotipy.oauth2 import SpotifyOAuth
    except ImportError:
        raise RuntimeError("Le module spotipy n'est pas installé.\nLance :  pip install spotipy")

    manquants = [v for v in ("SPOTIPY_CLIENT_ID", "SPOTIPY_CLIENT_SECRET") if not os.environ.get(v)]
    if manquants:
        raise RuntimeError(
            "Identifiants Spotify manquants dans le fichier .env :\n"
            + ", ".join(manquants)
            + "\n\nTu peux quand même ajouter des morceaux à la main."
        )
    os.environ.setdefault("SPOTIPY_REDIRECT_URI", "http://127.0.0.1:8888/callback")
    return spotipy.Spotify(auth_manager=SpotifyOAuth(scope=SCOPE, cache_path=CACHE_PATH))


def rechercher_spotify(sp, artiste, titre, limite=8):
    """Renvoie une liste de {artiste, titre, album, uri}. Réessaie en recherche libre si besoin."""
    artiste, titre = nettoyer(artiste), nettoyer(titre)
    filtres = []
    if artiste:
        filtres.append(f"artist:{artiste}")
    if titre:
        filtres.append(f"track:{titre}")

    items = []
    if filtres:
        items = sp.search(q=" ".join(filtres), type="track", limit=limite)["tracks"]["items"]
    if not items and (artiste or titre):  # accents, orthographe... : recherche libre
        items = sp.search(q=f"{artiste} {titre}".strip(), type="track", limit=limite)["tracks"]["items"]

    resultats = []
    for t in items:
        if not t or not t.get("name"):
            continue
        resultats.append({
            "artiste": t["artists"][0]["name"] if t.get("artists") else "Inconnu",
            "titre": t["name"],
            "album": (t.get("album") or {}).get("name", ""),
            "uri": t.get("uri"),
        })
    return resultats


# ──────────────────────────────────────────────────────────────
# Interface graphique
# ──────────────────────────────────────────────────────────────
class App:
    BG = "#2c3e50"

    def __init__(self, root):
        self.root = root
        self.sp = None  # créé à la première recherche (évite d'ouvrir le navigateur au démarrage)
        self.resultats = []
        self.selection = None  # (clé normalisée, uri) du résultat Spotify choisi

        root.title("Ajouter une musique")
        root.geometry("640x520")
        root.configure(bg=self.BG)

        tk.Label(root, text="Ajouter une musique", font=("Arial", 16, "bold"),
                 bg=self.BG, fg="white").pack(pady=(15, 10))

        # -- Champs de saisie --
        cadre = tk.Frame(root, bg=self.BG)
        cadre.pack(fill="x", padx=25)
        cadre.columnconfigure(1, weight=1)

        tk.Label(cadre, text="Artiste", font=("Arial", 11), bg=self.BG, fg="white")\
            .grid(row=0, column=0, sticky="w", pady=4)
        self.entry_artiste = tk.Entry(cadre, font=("Arial", 12))
        self.entry_artiste.grid(row=0, column=1, sticky="ew", padx=(10, 0), pady=4)

        tk.Label(cadre, text="Titre", font=("Arial", 11), bg=self.BG, fg="white")\
            .grid(row=1, column=0, sticky="w", pady=4)
        self.entry_titre = tk.Entry(cadre, font=("Arial", 12))
        self.entry_titre.grid(row=1, column=1, sticky="ew", padx=(10, 0), pady=4)

        self.entry_artiste.bind("<Return>", lambda e: self.entry_titre.focus_set())
        self.entry_titre.bind("<Return>", lambda e: self.ajouter())
        # Si on modifie un champ après avoir choisi un résultat, on oublie le résultat choisi
        self.entry_artiste.bind("<KeyRelease>", lambda e: self._verifier_selection())
        self.entry_titre.bind("<KeyRelease>", lambda e: self._verifier_selection())

        # -- Boutons --
        boutons = tk.Frame(root, bg=self.BG)
        boutons.pack(fill="x", padx=25, pady=10)
        tk.Button(boutons, text="🔍 Chercher sur Spotify", font=("Arial", 11), bg="#1db954", fg="white",
                  command=self.chercher).pack(side="left", expand=True, fill="x", padx=(0, 5))
        tk.Button(boutons, text="➕ Ajouter (Entrée)", font=("Arial", 11, "bold"), bg="#3498db", fg="white",
                  command=self.ajouter).pack(side="left", expand=True, fill="x", padx=(5, 0))

        # -- Résultats Spotify --
        tk.Label(root, text="Résultats Spotify (clique sur un résultat pour remplir les champs)",
                 font=("Arial", 9, "italic"), bg=self.BG, fg="#bdc3c7").pack(anchor="w", padx=25)
        cadre_liste = tk.Frame(root, bg=self.BG)
        cadre_liste.pack(fill="both", expand=True, padx=25, pady=5)
        barre = tk.Scrollbar(cadre_liste)
        barre.pack(side="right", fill="y")
        self.liste = tk.Listbox(cadre_liste, font=("Arial", 10), height=8, exportselection=False,
                                yscrollcommand=barre.set)
        self.liste.pack(side="left", fill="both", expand=True)
        barre.config(command=self.liste.yview)
        self.liste.bind("<<ListboxSelect>>", self.choisir_resultat)

        # -- Retour d'information --
        self.statut = tk.Label(root, text="", font=("Arial", 11, "bold"), bg=self.BG, fg="white",
                               wraplength=580)
        self.statut.pack(pady=(8, 2))
        self.compteur = tk.Label(root, text="", font=("Arial", 10, "italic"), bg=self.BG, fg="#bdc3c7")
        self.compteur.pack(pady=(0, 10))

        self.maj_compteur()
        self.entry_artiste.focus_set()

    # -- Petits utilitaires d'affichage --
    def message(self, texte, couleur="white"):
        self.statut.config(text=texte, fg=couleur)

    def maj_compteur(self):
        try:
            n = len(charger_scores())
            self.compteur.config(text=f"{n} morceaux dans {JSON_FILE}")
        except ValueError as e:
            self.compteur.config(text=str(e))

    def _verifier_selection(self):
        if self.selection and self.selection[0] != cle_normalisee(self.entry_artiste.get(), self.entry_titre.get()):
            self.selection = None

    # -- Actions --
    def chercher(self):
        artiste, titre = self.entry_artiste.get(), self.entry_titre.get()
        if not nettoyer(artiste) and not nettoyer(titre):
            self.message("Tape au moins un artiste ou un titre pour chercher.", "#f1c40f")
            return

        try:
            if self.sp is None:
                self.message("Connexion à Spotify… (une page peut s'ouvrir dans ton navigateur)", "#bdc3c7")
                self.root.update_idletasks()
                self.sp = creer_client_spotify()
            self.message("Recherche en cours…", "#bdc3c7")
            self.root.update_idletasks()
            self.resultats = rechercher_spotify(self.sp, artiste, titre)
        except RuntimeError as e:
            messagebox.showinfo("Recherche Spotify indisponible", str(e))
            self.message("Recherche indisponible : tu peux ajouter à la main.", "#f1c40f")
            return
        except Exception as e:
            self.message(f"Erreur Spotify : {e}", "#e74c3c")
            return

        self.liste.delete(0, "end")
        for r in self.resultats:
            album = f"  ({r['album']})" if r["album"] else ""
            self.liste.insert("end", f"{r['artiste']} - {r['titre']}{album}")
        if self.resultats:
            self.message(f"{len(self.resultats)} résultat(s) : clique sur le bon.", "white")
        else:
            self.message("Aucun résultat sur Spotify. Tu peux quand même ajouter à la main.", "#f1c40f")

    def choisir_resultat(self, _event=None):
        sel = self.liste.curselection()
        if not sel:
            return
        r = self.resultats[sel[0]]
        self.entry_artiste.delete(0, "end")
        self.entry_artiste.insert(0, r["artiste"])
        self.entry_titre.delete(0, "end")
        self.entry_titre.insert(0, r["titre"])
        self.selection = (cle_normalisee(r["artiste"], r["titre"]), r["uri"])

    def ajouter(self):
        artiste, titre = self.entry_artiste.get(), self.entry_titre.get()
        uri = None
        if self.selection and self.selection[0] == cle_normalisee(artiste, titre):
            uri = self.selection[1]

        try:
            statut, cle = ajouter_musique(artiste, titre, uri)
        except (ValueError, OSError) as e:
            messagebox.showerror("Erreur", str(e))
            return

        if statut == "invalide":
            self.message("Il faut un artiste ET un titre.", "#f1c40f")
            return
        if statut == "doublon":
            self.message(f"⚠️ Déjà dans la liste : {cle}", "#f1c40f")
            return

        self.message(f"✅ Ajouté : {cle}", "#2ecc71")
        self.entry_artiste.delete(0, "end")
        self.entry_titre.delete(0, "end")
        self.liste.delete(0, "end")
        self.resultats, self.selection = [], None
        self.maj_compteur()
        self.entry_artiste.focus_set()


if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()