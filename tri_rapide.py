#!/usr/bin/env python3
"""
tri_rapide.py - PHASE 1 : classement ultra rapide de tes morceaux.

Un morceau s'affiche avec sa pochette, un extrait se lance tout seul, et tu
appuies sur UNE touche pour le ranger dans un palier :

    1 = ❤️ J'adore   2 = 👍 J'aime bien   3 = 😐 Correct   4 = 👎 Bof   5 = 🚫 Pas pour moi

Autres touches :  Espace = réécouter   P = passer   Retour arrière = annuler le dernier choix

Chaque palier donne un Elo de départ au morceau. Ensuite, lance duels_elo.py (PHASE 2)
pour départager précisément les morceaux d'un même niveau.

Prérequis : Spotify ouvert sur un appareil (PC/téléphone), compte Premium pour la lecture,
et  pip install pillow  pour voir les pochettes.
"""

import tkinter as tk
from collections import Counter
from tkinter import messagebox, ttk

import moteur as m

BG = "#2c3e50"
TAILLE_POCHETTE = 300


class App:
    def __init__(self, root, data):
        self.root = root
        self.data = data

        # -- Connexion Spotify (l'appli reste utilisable sans : pas de son ni de pochette) --
        try:
            print("Connexion à Spotify…")
            self.sp = m.creer_client_spotify()
        except Exception as e:
            self.sp = None
            messagebox.showwarning(
                "Spotify non connecté",
                f"{e}\n\nTu peux classer sans son ni pochette, mais c'est moins pratique.",
            )

        self.moteur = m.MoteurTri(data, m.sauvegarder_scores)
        self.chargeur = m.Chargeur(self.sp, data, m.sauvegarder_scores)
        self.lecteur = m.Lecteur(self.sp)
        self.total = self.moteur.total
        self.attendu = None       # clé du morceau affiché
        self.photo = None         # référence à garder pour que Tkinter n'efface pas l'image
        self.photo_cle = None
        self.deja_joue = set()

        root.title("Tri rapide - Phase 1")
        root.geometry("560x780")
        root.configure(bg=BG)
        root.protocol("WM_DELETE_WINDOW", self.quitter)

        # -- Progression --
        self.lbl_progression = tk.Label(root, text="", font=("Arial", 11), bg=BG, fg="#bdc3c7")
        self.lbl_progression.pack(pady=(12, 2))
        self.barre = ttk.Progressbar(root, maximum=max(1, self.total), length=420)
        self.barre.pack(pady=(0, 10))

        # -- Pochette --
        cadre_pochette = tk.Frame(root, width=TAILLE_POCHETTE, height=TAILLE_POCHETTE, bg="#1e2b37")
        cadre_pochette.pack_propagate(False)
        cadre_pochette.pack()
        self.lbl_pochette = tk.Label(cadre_pochette, text="…", font=("Arial", 12), bg="#1e2b37", fg="#bdc3c7")
        self.lbl_pochette.pack(expand=True, fill="both")

        # -- Titre / artiste --
        self.lbl_titre = tk.Label(root, text="", font=("Arial", 16, "bold"), bg=BG, fg="white", wraplength=520)
        self.lbl_titre.pack(pady=(12, 0))
        self.lbl_artiste = tk.Label(root, text="", font=("Arial", 13), bg=BG, fg="#ecf0f1", wraplength=520)
        self.lbl_artiste.pack(pady=(0, 8))

        # -- Paliers --
        cadre_tiers = tk.Frame(root, bg=BG)
        cadre_tiers.pack(fill="x", padx=20, pady=6)
        self.boutons_tiers = []
        for code, libelle, _elo, touche, couleur in m.TIERS:
            b = tk.Button(cadre_tiers, text=f"{libelle}\n[{touche}]", font=("Arial", 10, "bold"),
                          bg=couleur, fg="white", takefocus=0,
                          command=lambda c=code: self.choisir(c))
            b.pack(side="left", expand=True, fill="both", padx=3, ipady=8)
            self.boutons_tiers.append(b)
            root.bind(f"<Key-{touche}>", lambda e, c=code: self.choisir(c))

        # -- Actions secondaires --
        cadre_actions = tk.Frame(root, bg=BG)
        cadre_actions.pack(fill="x", padx=20, pady=6)
        for texte, cmd in (("🔁 Réécouter [Espace]", self.reecouter),
                           ("⏭ Passer [P]", self.passer),
                           ("↩ Annuler [Retour]", self.annuler)):
            tk.Button(cadre_actions, text=texte, font=("Arial", 10), bg="#34495e", fg="white",
                      takefocus=0, command=cmd).pack(side="left", expand=True, fill="x", padx=3)
        root.bind("<space>", lambda e: self.reecouter())
        root.bind("<Key-p>", lambda e: self.passer())
        root.bind("<BackSpace>", lambda e: self.annuler())

        self.auto = tk.BooleanVar(value=True)
        tk.Checkbutton(root, text="Lancer l'extrait automatiquement", variable=self.auto,
                       bg=BG, fg="white", selectcolor="#34495e", activebackground=BG,
                       activeforeground="white", takefocus=0).pack(pady=(4, 0))

        self.lbl_statut = tk.Label(root, text="", font=("Arial", 10, "italic"), bg=BG, fg="#bdc3c7",
                                   wraplength=520)
        self.lbl_statut.pack(pady=8)

        self.afficher_courant()
        self.root.after(100, self.poll)

    # ── Affichage ─────────────────────────────────────────────
    def message(self, texte, couleur="#bdc3c7"):
        self.lbl_statut.config(text=texte, fg=couleur)

    def maj_progression(self):
        faits = self.total - self.moteur.restants()
        self.lbl_progression.config(text=f"{faits} / {self.total} classés  ·  {self.moteur.restants()} restants")
        self.barre["value"] = faits

    def afficher_courant(self):
        cle = self.moteur.courant()
        self.attendu = cle
        self.photo_cle = None
        self.maj_progression()
        if cle is None:
            self.fin()
            return

        info = self.data[cle]
        self.lbl_titre.config(text=info.get("musique", ""))
        self.lbl_artiste.config(text=info.get("artiste", ""))
        self.lbl_pochette.config(image="", text="…")
        for c in self.moteur.apercu(3):  # on prépare aussi les 2 suivants
            self.chargeur.demander(c)
        self.rafraichir()

    def rafraichir(self):
        """Affiche la pochette dès qu'elle est prête et lance l'extrait dès qu'on connaît le morceau."""
        cle = self.attendu
        if not cle:
            return
        info = self.data[cle]

        octets = self.chargeur.pochettes.get(cle)
        if octets and self.photo_cle != cle:
            try:
                self.photo = m.octets_vers_photo(octets, TAILLE_POCHETTE)
                self.lbl_pochette.config(image=self.photo, text="")
                self.photo_cle = cle
            except ImportError:
                self.lbl_pochette.config(text="Pochettes indisponibles\n(pip install pillow)")
                self.photo_cle = cle
            except Exception:
                self.lbl_pochette.config(text="(pochette illisible)")
                self.photo_cle = cle

        if self.auto.get() and info.get("spotify_uri") and cle not in self.deja_joue:
            self.deja_joue.add(cle)
            self.lecteur.jouer(info["spotify_uri"], info.get("duree_ms"))

    def poll(self):
        for cle, erreur in self.chargeur.resultats():
            if cle == self.attendu:
                if erreur:
                    self.message(f"⚠️ {erreur}", "#f1c40f")
                elif self.sp and not self.data[cle].get("spotify_uri"):
                    self.message("⚠️ Introuvable sur Spotify : classe-le à l'oreille ou passe-le [P].", "#f1c40f")
                self.rafraichir()
        for texte in self.lecteur.lire_messages():
            self.message(f"🔇 {texte}", "#f1c40f")
        self.root.after(100, self.poll)

    # ── Actions ───────────────────────────────────────────────
    def choisir(self, code):
        if self.attendu is None:
            return
        self.moteur.assigner(code)
        self.message("")
        self.afficher_courant()

    def passer(self):
        if self.attendu is None:
            return
        self.moteur.passer()
        self.afficher_courant()

    def annuler(self):
        cle = self.moteur.annuler()
        if cle is None:
            self.message("Rien à annuler.")
            return
        self.deja_joue.discard(cle)
        self.message("↩ Dernier choix annulé.")
        self.afficher_courant()

    def reecouter(self):
        cle = self.attendu
        if not cle:
            return
        info = self.data[cle]
        if info.get("spotify_uri"):
            self.lecteur.jouer(info["spotify_uri"], info.get("duree_ms"))
        else:
            self.message("⚠️ Morceau introuvable sur Spotify : classe-le à l'oreille ou passe-le.", "#f1c40f")

    def fin(self):
        self.lecteur.arreter()
        for b in self.boutons_tiers:
            b.config(state="disabled")
        repartition = Counter(v.get("tier") for v in self.data.values() if v.get("tier"))
        resume = "   ".join(f"{code}: {repartition.get(code, 0)}" for code, *_ in m.TIERS)
        self.lbl_titre.config(text="Tri rapide terminé ! 🎉")
        self.lbl_artiste.config(text=resume)
        self.lbl_pochette.config(image="", text="✅")
        self.message("Lance maintenant  python duels_elo.py  pour affiner le classement.", "#2ecc71")

    def quitter(self):
        self.lecteur.arreter_maintenant()
        self.root.destroy()


if __name__ == "__main__":
    try:
        donnees = m.charger_scores()
    except ValueError as e:
        raise SystemExit(f"Erreur : {e}")
    if not donnees:
        raise SystemExit("scores.json est vide ou introuvable : lance d'abord generer_liste.py.")
    if not any(not v.get("tier") and m.nb_matchs(v) == 0 for v in donnees.values()):
        raise SystemExit("Tous tes morceaux sont déjà classés ! Lance  python duels_elo.py  pour affiner.")

    racine = tk.Tk()
    App(racine, donnees)
    racine.mainloop()
