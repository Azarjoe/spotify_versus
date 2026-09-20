#!/usr/bin/env python3
"""
duels_elo.py - PHASE 2 : affine le classement avec des duels Elo.

À lancer après tri_rapide.py. Deux morceaux de niveau proche s'affrontent, avec leur
pochette et un extrait à la demande. Tu choisis celui que tu préfères.

    ←  /  →   voter pour le morceau de gauche / de droite
    ↓         égalité ("je sais pas")
    1  /  2   écouter l'extrait de gauche / de droite
    Retour arrière   annuler le dernier vote

Les duels s'arrêtent quand chaque morceau a fait N matchs (8 par défaut) :
    python duels_elo.py --matchs 12      pour un classement encore plus précis
Tu peux fermer la fenêtre à tout moment : le classement est sauvegardé à chaque vote.
(L'Elo n'est volontairement pas affiché pendant le vote, pour ne pas t'influencer.)
"""

import argparse
import tkinter as tk
from tkinter import messagebox, ttk

import moteur as m

BG = "#2c3e50"
TAILLE_POCHETTE = 250


class App:
    def __init__(self, root, data, matchs_max):
        self.root = root
        self.data = data

        try:
            print("Connexion à Spotify…")
            self.sp = m.creer_client_spotify()
        except Exception as e:
            self.sp = None
            messagebox.showwarning(
                "Spotify non connecté",
                f"{e}\n\nTu peux voter sans son ni pochette, mais c'est moins pratique.",
            )

        self.moteur = m.MoteurDuels(data, m.sauvegarder_scores, matchs_max=matchs_max)
        self.chargeur = m.Chargeur(self.sp, data, m.sauvegarder_scores)
        self.lecteur = m.Lecteur(self.sp)
        self.cles = {1: None, 2: None}
        self.photos = {1: None, 2: None}
        self.photo_cle = {1: None, 2: None}
        self.termine = False

        root.title("Duels Elo - Phase 2")
        root.geometry("900x640")
        root.configure(bg=BG)
        root.protocol("WM_DELETE_WINDOW", self.quitter)

        tk.Label(root, text="Quel son préfères-tu ?", font=("Arial", 16, "bold"), bg=BG, fg="white").pack(pady=(12, 2))
        self.lbl_progression = tk.Label(root, text="", font=("Arial", 10), bg=BG, fg="#bdc3c7")
        self.lbl_progression.pack()
        self.barre = ttk.Progressbar(root, maximum=1, length=500)
        self.barre.pack(pady=(2, 8))

        # -- Zone principale : carte 1 | centre | carte 2 --
        cadre = tk.Frame(root, bg=BG)
        cadre.pack(expand=True, fill="both", padx=15)
        self.cartes = {1: self.creer_carte(cadre, 1, "#3498db", "←", "1")}

        centre = tk.Frame(cadre, bg=BG)
        centre.pack(side="left", fill="y", padx=6)
        self.btn_egalite = tk.Button(centre, text="Je sais pas\n(=)\n[↓]", font=("Arial", 11, "bold"),
                                     bg="#95a5a6", fg="white", takefocus=0, command=lambda: self.vote(0))
        self.btn_egalite.pack(expand=True, fill="x", pady=5, ipady=12)
        tk.Button(centre, text="↩ Annuler\n[Retour]", font=("Arial", 10), bg="#34495e", fg="white",
                  takefocus=0, command=self.annuler).pack(fill="x", pady=5)
        tk.Button(centre, text="🏆 Classement", font=("Arial", 10), bg="#34495e", fg="white",
                  takefocus=0, command=self.afficher_classement).pack(fill="x", pady=5)

        self.cartes[2] = self.creer_carte(cadre, 2, "#e74c3c", "→", "2")

        self.lbl_statut = tk.Label(root, text="", font=("Arial", 10, "italic"), bg=BG, fg="#bdc3c7", wraplength=840)
        self.lbl_statut.pack(pady=8)

        root.bind("<Left>", lambda e: self.vote(1))
        root.bind("<Right>", lambda e: self.vote(2))
        root.bind("<Down>", lambda e: self.vote(0))
        root.bind("<Key-1>", lambda e: self.ecouter(1))
        root.bind("<Key-2>", lambda e: self.ecouter(2))
        root.bind("<BackSpace>", lambda e: self.annuler())

        self.nouveau_duel()
        self.root.after(100, self.poll)

    def creer_carte(self, parent, numero, couleur, fleche, touche):
        cadre = tk.Frame(parent, bg=BG)
        cadre.pack(side="left", expand=True, fill="both", padx=6)

        cadre_img = tk.Frame(cadre, width=TAILLE_POCHETTE, height=TAILLE_POCHETTE, bg="#1e2b37")
        cadre_img.pack_propagate(False)
        cadre_img.pack(pady=(4, 8))
        img = tk.Label(cadre_img, text="…", font=("Arial", 12), bg="#1e2b37", fg="#bdc3c7")
        img.pack(expand=True, fill="both")
        img.bind("<Button-1>", lambda e: self.vote(numero))  # cliquer sur la pochette = voter

        titre = tk.Label(cadre, text="", font=("Arial", 13, "bold"), bg=BG, fg="white", wraplength=320)
        titre.pack()
        artiste = tk.Label(cadre, text="", font=("Arial", 11), bg=BG, fg="#ecf0f1", wraplength=320)
        artiste.pack(pady=(0, 8))

        ecouter = tk.Button(cadre, text=f"🎧 Écouter [{touche}]", font=("Arial", 10), bg="#1db954", fg="white",
                            takefocus=0, command=lambda: self.ecouter(numero))
        ecouter.pack(fill="x", pady=2)
        voter = tk.Button(cadre, text=f"✅ Je préfère celui-ci [{fleche}]", font=("Arial", 11, "bold"),
                          bg=couleur, fg="white", takefocus=0, command=lambda: self.vote(numero))
        voter.pack(fill="x", pady=2, ipady=6)
        return {"img": img, "titre": titre, "artiste": artiste, "ecouter": ecouter, "voter": voter}

    # ── Affichage ─────────────────────────────────────────────
    def message(self, texte, couleur="#bdc3c7"):
        self.lbl_statut.config(text=texte, fg=couleur)

    def maj_progression(self):
        faits, prevus = self.moteur.progression()
        pct = min(100, round(100 * faits / prevus)) if prevus else 100
        self.lbl_progression.config(text=f"Duels : {faits} / ~{prevus}  ({pct} %)")
        self.barre.config(maximum=max(1, prevus))
        self.barre["value"] = min(faits, prevus)

    def nouveau_duel(self):
        self.maj_progression()
        paire = self.moteur.prochain()
        if paire is None:
            self.fin()
            return
        self.cles[1], self.cles[2] = paire
        self.afficher_paire()

    def afficher_paire(self):
        for n in (1, 2):
            cle = self.cles[n]
            info = self.data[cle]
            carte = self.cartes[n]
            carte["titre"].config(text=info.get("musique", ""))
            carte["artiste"].config(text=info.get("artiste", ""))
            carte["img"].config(image="", text="…")
            self.photo_cle[n] = None
            self.chargeur.demander(cle)
            self.rafraichir(n)

    def rafraichir(self, n):
        cle = self.cles[n]
        octets = self.chargeur.pochettes.get(cle) if cle else None
        if not octets or self.photo_cle[n] == cle:
            return
        img = self.cartes[n]["img"]
        try:
            self.photos[n] = m.octets_vers_photo(octets, TAILLE_POCHETTE)
            img.config(image=self.photos[n], text="")
        except ImportError:
            img.config(text="Pochettes indisponibles\n(pip install pillow)")
        except Exception:
            img.config(text="(pochette illisible)")
        self.photo_cle[n] = cle

    def poll(self):
        for cle, erreur in self.chargeur.resultats():
            for n in (1, 2):
                if cle == self.cles[n]:
                    if erreur:
                        self.message(f"⚠️ {erreur}", "#f1c40f")
                    elif self.sp and not self.data[cle].get("spotify_uri"):
                        self.message(f"⚠️ « {self.data[cle]['musique']} » introuvable sur Spotify : pas d'extrait.", "#f1c40f")
                    self.rafraichir(n)
        for texte in self.lecteur.lire_messages():
            self.message(f"🔇 {texte}", "#f1c40f")
        self.root.after(100, self.poll)

    # ── Actions ───────────────────────────────────────────────
    def ecouter(self, n):
        cle = self.cles[n]
        if not cle or self.termine:
            return
        info = self.data[cle]
        if info.get("spotify_uri"):
            self.lecteur.jouer(info["spotify_uri"], info.get("duree_ms"))
        else:
            self.message("⚠️ Morceau introuvable sur Spotify : pas d'extrait possible.", "#f1c40f")

    def vote(self, resultat):
        if self.termine or not self.cles[1] or not self.cles[2]:
            return
        c1, c2 = self.cles[1], self.cles[2]
        self.moteur.voter(c1, c2, resultat)
        if resultat == 0:
            self.message("= Égalité enregistrée.")
        else:
            gagnant = self.data[self.cles[resultat]]
            self.message(f"✅ {gagnant['artiste']} - {gagnant['musique']}", "#2ecc71")
        self.nouveau_duel()

    def annuler(self):
        paire = self.moteur.annuler()
        if paire is None:
            self.message("Rien à annuler.")
            return
        if self.termine:
            self.termine = False
            for c in self.cartes.values():
                c["voter"].config(state="normal")
                c["ecouter"].config(state="normal")
            self.btn_egalite.config(state="normal")
        self.cles[1], self.cles[2] = paire
        self.maj_progression()
        self.afficher_paire()
        self.message("↩ Dernier vote annulé.")

    def afficher_classement(self):
        fenetre = tk.Toplevel(self.root)
        fenetre.title("Classement actuel")
        fenetre.geometry("520x560")
        fenetre.configure(bg=BG)
        cadre = tk.Frame(fenetre, bg=BG)
        cadre.pack(expand=True, fill="both", padx=10, pady=10)
        barre = tk.Scrollbar(cadre)
        barre.pack(side="right", fill="y")
        liste = tk.Listbox(cadre, font=("Arial", 10), yscrollcommand=barre.set)
        liste.pack(side="left", expand=True, fill="both")
        barre.config(command=liste.yview)
        for rang, (_cle, info) in enumerate(self.moteur.classement(), start=1):
            liste.insert("end", f"{rang:>3}.  {info['artiste']} - {info['musique']}   ({info['elo']})")

    def fin(self):
        self.termine = True
        self.lecteur.arreter()
        for c in self.cartes.values():
            c["voter"].config(state="disabled")
            c["ecouter"].config(state="disabled")
        self.btn_egalite.config(state="disabled")
        self.message("Tous les morceaux ont atteint leur quota de duels : classement terminé ! 🏆", "#2ecc71")
        self.afficher_classement()

    def quitter(self):
        self.lecteur.arreter_maintenant()
        self.root.destroy()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Phase 2 : duels Elo entre morceaux de niveau proche.")
    parser.add_argument("--matchs", type=int, default=m.MATCHS_MAX_DEFAUT,
                        help=f"Nombre de duels par morceau (défaut : {m.MATCHS_MAX_DEFAUT}).")
    args = parser.parse_args()

    try:
        donnees = m.charger_scores()
    except ValueError as e:
        raise SystemExit(f"Erreur : {e}")
    if len(donnees) < 2:
        raise SystemExit("Il faut au moins 2 morceaux dans scores.json : lance d'abord generer_liste.py.")
    if not any(v.get("tier") for v in donnees.values()):
        print("ℹ️  Aucun morceau n'a été classé par palier : conseil, lance d'abord  python tri_rapide.py\n"
              "   (les duels marchent quand même, mais il faudra beaucoup plus de matchs).")

    racine = tk.Tk()
    App(racine, donnees, args.matchs)
    racine.mainloop()
