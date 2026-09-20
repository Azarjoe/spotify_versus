#!/usr/bin/env python3
"""main.py - Menu principal de VS Musique."""

import json
import os
import queue
import subprocess
import sys
import threading
import tkinter as tk
import webbrowser
from pathlib import Path
from tkinter import messagebox, simpledialog, ttk


DOSSIER_APP = Path(__file__).resolve().parent
SCORES_FILE = DOSSIER_APP / "scores.json"

BG = "#17212b"
CARD = "#22303c"
TEXT = "#ffffff"
MUTED = "#aeb8c2"
GREEN = "#1db954"
BLUE = "#3498db"
ORANGE = "#e67e22"
RED = "#e74c3c"
PURPLE = "#8e44ad"
CYAN = "#0097a7"


def charger_scores():
    if not SCORES_FILE.exists():
        return {}

    try:
        with SCORES_FILE.open(
            "r",
            encoding="utf-8",
        ) as fichier:
            data = json.load(fichier)

    except json.JSONDecodeError as erreur:
        raise RuntimeError(
            f"scores.json contient un JSON invalide : {erreur}"
        ) from erreur

    except OSError as erreur:
        raise RuntimeError(
            f"Impossible de lire scores.json : {erreur}"
        ) from erreur

    if not isinstance(data, dict):
        raise RuntimeError(
            "scores.json doit contenir un objet JSON."
        )

    return data


def nb_matchs(info):
    return (
        info.get("victoires", 0)
        + info.get("defaites", 0)
        + info.get("egalites", 0)
    )


class FenetreProgressionPlaylist:
    def __init__(
        self,
        parent,
        nom_playlist,
    ):
        self.parent = parent
        self.nom_playlist = nom_playlist
        self.processus = None
        self.file_messages = queue.Queue()
        self.termine = False
        self.url_playlist = None
        self.erreur = None

        self.fenetre = tk.Toplevel(parent)
        self.fenetre.title("Création de la playlist")
        self.fenetre.geometry("590x330")
        self.fenetre.resizable(False, False)
        self.fenetre.configure(bg=BG)
        self.fenetre.transient(parent)
        self.fenetre.grab_set()

        self.fenetre.protocol(
            "WM_DELETE_WINDOW",
            self.demander_fermeture,
        )

        tk.Label(
            self.fenetre,
            text="Création de la playlist",
            font=("Arial", 18, "bold"),
            bg=BG,
            fg=TEXT,
        ).pack(pady=(24, 4))

        tk.Label(
            self.fenetre,
            text=f"« {nom_playlist} »",
            font=("Arial", 12, "bold"),
            bg=BG,
            fg=GREEN,
            wraplength=540,
        ).pack(pady=(0, 20))

        cadre = tk.Frame(
            self.fenetre,
            bg=CARD,
            padx=20,
            pady=20,
        )

        cadre.pack(
            fill="x",
            padx=24,
        )

        self.lbl_etape = tk.Label(
            cadre,
            text="Démarrage...",
            font=("Arial", 10, "bold"),
            bg=CARD,
            fg=TEXT,
            wraplength=500,
            justify="left",
        )

        self.lbl_etape.pack(
            anchor="w",
            pady=(0, 10),
        )

        self.barre = ttk.Progressbar(
            cadre,
            style="App.Horizontal.TProgressbar",
            maximum=103,
            value=0,
        )

        self.barre.pack(
            fill="x",
            pady=(0, 8),
        )

        self.lbl_compteur = tk.Label(
            cadre,
            text="0 %",
            font=("Arial", 9),
            bg=CARD,
            fg=MUTED,
        )

        self.lbl_compteur.pack(
            anchor="e",
        )

        self.lbl_statut = tk.Label(
            self.fenetre,
            text=(
                "Ne ferme pas cette fenêtre pendant "
                "la création de la playlist."
            ),
            font=("Arial", 9, "italic"),
            bg=BG,
            fg=MUTED,
            wraplength=540,
        )

        self.lbl_statut.pack(
            pady=(15, 10),
        )

        self.cadre_boutons = tk.Frame(
            self.fenetre,
            bg=BG,
        )

        self.cadre_boutons.pack(
            fill="x",
            padx=24,
            pady=(0, 18),
        )

        self.btn_annuler = tk.Button(
            self.cadre_boutons,
            text="Annuler",
            font=("Arial", 10, "bold"),
            bg="#7f1d1d",
            fg=TEXT,
            activebackground="#991b1b",
            activeforeground=TEXT,
            relief="flat",
            cursor="hand2",
            command=self.annuler,
        )

        self.btn_annuler.pack(
            fill="x",
            ipady=7,
        )

    def lancer(
        self,
        commande,
    ):
        thread = threading.Thread(
            target=self.executer,
            args=(commande,),
            daemon=True,
        )

        thread.start()

        self.fenetre.after(
            100,
            self.lire_messages,
        )

    def executer(
        self,
        commande,
    ):
        try:
            environnement = os.environ.copy()
            environnement["PYTHONUNBUFFERED"] = "1"
            environnement["PYTHONIOENCODING"] = "utf-8"

            creationflags = 0

            if os.name == "nt":
                creationflags = (
                    subprocess.CREATE_NO_WINDOW
                )

            self.processus = subprocess.Popen(
                commande,
                cwd=str(DOSSIER_APP),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
                env=environnement,
                creationflags=creationflags,
            )

            if self.processus.stdout:
                for ligne in iter(
                    self.processus.stdout.readline,
                    "",
                ):
                    ligne = ligne.strip()

                    if ligne:
                        self.file_messages.put(
                            ("ligne", ligne)
                        )

            code_retour = self.processus.wait()

            self.file_messages.put(
                ("fin", code_retour)
            )

        except Exception as erreur:
            self.file_messages.put(
                ("erreur_interne", str(erreur))
            )

    def lire_messages(self):
        while True:
            try:
                type_message, contenu = (
                    self.file_messages.get_nowait()
                )

            except queue.Empty:
                break

            if type_message == "ligne":
                self.traiter_ligne(contenu)

            elif type_message == "fin":
                self.terminer(contenu)

            elif type_message == "erreur_interne":
                self.erreur = contenu
                self.terminer(1)

        if not self.termine:
            self.fenetre.after(
                100,
                self.lire_messages,
            )

    def traiter_ligne(
        self,
        ligne,
    ):
        if ligne.startswith("PROGRESS|"):
            morceaux = ligne.split(
                "|",
                3,
            )

            if len(morceaux) != 4:
                return

            try:
                valeur = int(morceaux[1])
                total = int(morceaux[2])

            except ValueError:
                return

            message = morceaux[3]

            total = max(
                1,
                total,
            )

            valeur = max(
                0,
                min(valeur, total),
            )

            pourcentage = round(
                100 * valeur / total
            )

            self.barre.config(
                maximum=total,
            )

            self.barre["value"] = valeur

            self.lbl_etape.config(
                text=message
            )

            self.lbl_compteur.config(
                text=f"{pourcentage} %"
            )

        elif ligne.startswith("RESULT|"):
            self.lbl_statut.config(
                text=ligne.split("|", 1)[1],
                fg=GREEN,
            )

        elif ligne.startswith("PLAYLIST_URL|"):
            self.url_playlist = ligne.split(
                "|",
                1,
            )[1]

        elif ligne.startswith("ERROR|"):
            self.erreur = ligne.split(
                "|",
                1,
            )[1]

        else:
            self.lbl_statut.config(
                text=ligne,
                fg=MUTED,
            )

    def terminer(
        self,
        code_retour,
    ):
        self.termine = True
        self.barre.stop()
        self.btn_annuler.destroy()

        if code_retour == 0 and not self.erreur:
            self.barre["value"] = (
                self.barre["maximum"]
            )

            self.lbl_compteur.config(
                text="100 %"
            )

            self.lbl_etape.config(
                text="Playlist créée avec succès."
            )

            self.lbl_statut.config(
                text=(
                    f"La playlist « {self.nom_playlist} » "
                    "est disponible sur Spotify."
                ),
                fg=GREEN,
            )

            if self.url_playlist:
                bouton_ouvrir = tk.Button(
                    self.cadre_boutons,
                    text="Ouvrir dans Spotify",
                    font=("Arial", 10, "bold"),
                    bg=GREEN,
                    fg=TEXT,
                    activebackground="#159447",
                    activeforeground=TEXT,
                    relief="flat",
                    cursor="hand2",
                    command=lambda: webbrowser.open(
                        self.url_playlist
                    ),
                )

                bouton_ouvrir.pack(
                    side="left",
                    expand=True,
                    fill="x",
                    padx=(0, 5),
                    ipady=7,
                )

            bouton_fermer = tk.Button(
                self.cadre_boutons,
                text="Fermer",
                font=("Arial", 10, "bold"),
                bg="#34495e",
                fg=TEXT,
                activebackground="#415b72",
                activeforeground=TEXT,
                relief="flat",
                cursor="hand2",
                command=self.fermer,
            )

            bouton_fermer.pack(
                side="left",
                expand=True,
                fill="x",
                padx=(5, 0),
                ipady=7,
            )

        else:
            message = (
                self.erreur
                or "La création de la playlist a échoué."
            )

            self.lbl_etape.config(
                text="Erreur pendant la création."
            )

            self.lbl_statut.config(
                text=message,
                fg=RED,
            )

            bouton_fermer = tk.Button(
                self.cadre_boutons,
                text="Fermer",
                font=("Arial", 10, "bold"),
                bg=RED,
                fg=TEXT,
                activebackground="#c0392b",
                activeforeground=TEXT,
                relief="flat",
                cursor="hand2",
                command=self.fermer,
            )

            bouton_fermer.pack(
                fill="x",
                ipady=7,
            )

    def demander_fermeture(self):
        if self.termine:
            self.fermer()
            return

        doit_annuler = messagebox.askyesno(
            "Annuler la création",
            (
                "La playlist est encore en cours de création.\n\n"
                "Veux-tu vraiment annuler ?"
            ),
            parent=self.fenetre,
        )

        if doit_annuler:
            self.annuler()

    def annuler(self):
        if self.processus and self.processus.poll() is None:
            try:
                self.processus.terminate()
            except OSError:
                pass

        self.termine = True
        self.fermer()

    def fermer(self):
        try:
            self.fenetre.grab_release()
        except tk.TclError:
            pass

        self.fenetre.destroy()


class App:
    def __init__(self, root):
        self.root = root

        root.title("VS Musique")
        root.geometry("780x780")
        root.minsize(700, 700)
        root.configure(bg=BG)

        self.configurer_style()
        self.creer_interface()
        self.actualiser()

        root.after(
            5000,
            self.actualisation_auto,
        )

    def configurer_style(self):
        self.style = ttk.Style()

        try:
            self.style.theme_use("clam")
        except tk.TclError:
            pass

        self.style.configure(
            "App.Horizontal.TProgressbar",
            troughcolor=CARD,
            background=GREEN,
            bordercolor=CARD,
            lightcolor=GREEN,
            darkcolor=GREEN,
        )

        self.style.configure(
            "Classement.Treeview",
            background="#263746",
            foreground="white",
            fieldbackground="#263746",
            borderwidth=0,
            rowheight=28,
            font=("Arial", 10),
        )

        self.style.map(
            "Classement.Treeview",
            background=[
                ("selected", BLUE),
            ],
            foreground=[
                ("selected", "white"),
            ],
        )

        self.style.configure(
            "Classement.Treeview.Heading",
            background="#34495e",
            foreground="white",
            relief="flat",
            font=("Arial", 10, "bold"),
        )

    def creer_interface(self):
        tk.Label(
            self.root,
            text="VS MUSIQUE",
            font=("Arial", 25, "bold"),
            bg=BG,
            fg=TEXT,
        ).pack(pady=(24, 2))

        tk.Label(
            self.root,
            text=(
                "Classe tes morceaux rapidement, puis "
                "affine le résultat avec les duels Elo."
            ),
            font=("Arial", 10),
            bg=BG,
            fg=MUTED,
        ).pack(pady=(0, 18))

        cadre_stats = tk.Frame(
            self.root,
            bg=CARD,
            padx=18,
            pady=14,
        )

        cadre_stats.pack(
            fill="x",
            padx=28,
            pady=(0, 18),
        )

        self.lbl_stats = tk.Label(
            cadre_stats,
            text="Chargement...",
            font=("Arial", 11, "bold"),
            bg=CARD,
            fg=TEXT,
        )

        self.lbl_stats.pack(anchor="w")

        self.lbl_details = tk.Label(
            cadre_stats,
            text="",
            font=("Arial", 9),
            bg=CARD,
            fg=MUTED,
        )

        self.lbl_details.pack(
            anchor="w",
            pady=(5, 8),
        )

        self.progression = ttk.Progressbar(
            cadre_stats,
            style="App.Horizontal.TProgressbar",
            maximum=100,
        )

        self.progression.pack(fill="x")

        zone = tk.Frame(
            self.root,
            bg=BG,
        )

        zone.pack(
            fill="both",
            expand=True,
            padx=28,
        )

        zone.columnconfigure(
            0,
            weight=1,
        )

        zone.columnconfigure(
            1,
            weight=1,
        )

        for ligne in range(4):
            zone.rowconfigure(
                ligne,
                weight=1,
            )

        self.creer_bouton(
            zone,
            "1. Générer / actualiser la liste",
            GREEN,
            lambda: self.lancer(
                "generer_liste.py",
                terminal=True,
            ),
            0,
            0,
        )

        self.creer_bouton(
            zone,
            "2. Ajouter une musique",
            BLUE,
            lambda: self.lancer(
                "ajouter_musique.py"
            ),
            0,
            1,
        )

        self.creer_bouton(
            zone,
            "3. Tri rapide",
            ORANGE,
            lambda: self.lancer(
                "tri_rapide.py",
                scores_requis=True,
            ),
            1,
            0,
        )

        self.creer_bouton(
            zone,
            "4. Duels Elo",
            RED,
            lambda: self.lancer(
                "duels_elo.py",
                scores_requis=True,
            ),
            1,
            1,
        )

        self.creer_bouton(
            zone,
            "5. Voir le classement",
            PURPLE,
            self.afficher_classement,
            2,
            0,
        )

        self.creer_bouton(
            zone,
            "6. Créer la playlist Top 100",
            GREEN,
            self.demander_nom_playlist,
            2,
            1,
        )

        self.creer_bouton(
            zone,
            "7. Ouvrir le dossier",
            "#607d8b",
            self.ouvrir_dossier,
            3,
            0,
        )

        self.creer_bouton(
            zone,
            "8. Actualiser",
            CYAN,
            self.actualiser,
            3,
            1,
        )

        tk.Button(
            self.root,
            text="Quitter",
            font=("Arial", 10, "bold"),
            bg="#7f1d1d",
            fg=TEXT,
            activebackground="#991b1b",
            activeforeground=TEXT,
            relief="flat",
            cursor="hand2",
            command=self.root.destroy,
        ).pack(
            fill="x",
            padx=28,
            pady=(14, 8),
            ipady=8,
        )

        self.lbl_statut = tk.Label(
            self.root,
            text="Prêt.",
            font=("Arial", 9, "italic"),
            bg=BG,
            fg=MUTED,
            wraplength=700,
        )

        self.lbl_statut.pack(
            pady=(4, 15)
        )

    def creer_bouton(
        self,
        parent,
        texte,
        couleur,
        commande,
        ligne,
        colonne,
    ):
        tk.Button(
            parent,
            text=texte,
            font=("Arial", 11, "bold"),
            bg=couleur,
            fg=TEXT,
            activebackground=couleur,
            activeforeground=TEXT,
            relief="flat",
            cursor="hand2",
            command=commande,
        ).grid(
            row=ligne,
            column=colonne,
            sticky="nsew",
            padx=6,
            pady=6,
            ipady=14,
        )

    def message(
        self,
        texte,
        couleur=MUTED,
    ):
        self.lbl_statut.config(
            text=texte,
            fg=couleur,
        )

    def actualiser(
        self,
        afficher_message=True,
    ):
        try:
            data = charger_scores()

        except RuntimeError as erreur:
            self.lbl_stats.config(
                text="scores.json illisible"
            )

            self.lbl_details.config(
                text=str(erreur)
            )

            self.progression["value"] = 0
            self.message(
                str(erreur),
                RED,
            )

            return

        total = len(data)

        classes = sum(
            1
            for info in data.values()
            if info.get("tier")
        )

        matchs_cumules = sum(
            nb_matchs(info)
            for info in data.values()
        )

        termines = sum(
            1
            for info in data.values()
            if nb_matchs(info) >= 8
        )

        if total == 0:
            self.lbl_stats.config(
                text="Aucune liste chargée"
            )

            self.lbl_details.config(
                text=(
                    "Commence par générer une liste "
                    "ou ajouter des morceaux."
                )
            )

            self.progression["value"] = 0

        else:
            pourcentage = round(
                100 * termines / total
            )

            self.lbl_stats.config(
                text=(
                    f"{total} morceaux "
                    "dans la bibliothèque"
                )
            )

            self.lbl_details.config(
                text=(
                    f"Tri rapide : {classes}/{total}  |  "
                    f"Quota Elo atteint : {termines}/{total}  |  "
                    f"Matchs cumulés : {matchs_cumules}"
                )
            )

            self.progression["value"] = pourcentage

        if afficher_message:
            self.message(
                "Informations actualisées."
            )

    def actualisation_auto(self):
        try:
            self.actualiser(
                afficher_message=False
            )

        finally:
            self.root.after(
                5000,
                self.actualisation_auto,
            )

    def lancer(
        self,
        nom_script,
        terminal=False,
        scores_requis=False,
        arguments=None,
    ):
        script = DOSSIER_APP / nom_script

        if not script.exists():
            messagebox.showerror(
                "Fichier introuvable",
                f"Le fichier {nom_script} est absent.",
            )
            return

        if scores_requis:
            try:
                if not charger_scores():
                    messagebox.showwarning(
                        "Liste manquante",
                        (
                            "scores.json est vide ou introuvable.\n\n"
                            "Génère d'abord une liste."
                        ),
                    )
                    return

            except RuntimeError as erreur:
                messagebox.showerror(
                    "Erreur",
                    str(erreur),
                )
                return

        commande = [
            sys.executable,
            str(script),
        ]

        if arguments:
            commande.extend(arguments)

        try:
            creationflags = 0

            if terminal and os.name == "nt":
                creationflags = (
                    subprocess.CREATE_NEW_CONSOLE
                )

            subprocess.Popen(
                commande,
                cwd=str(DOSSIER_APP),
                creationflags=creationflags,
            )

            self.message(
                f"{nom_script} lancé.",
                GREEN,
            )

        except OSError as erreur:
            messagebox.showerror(
                "Erreur de lancement",
                str(erreur),
            )

    def demander_nom_playlist(self):
        script = DOSSIER_APP / "playlist_creator.py"

        if not script.exists():
            messagebox.showerror(
                "Fichier introuvable",
                "playlist_creator.py est absent.",
            )
            return

        try:
            data = charger_scores()

        except RuntimeError as erreur:
            messagebox.showerror(
                "Erreur",
                str(erreur),
            )
            return

        if not data:
            messagebox.showwarning(
                "Classement vide",
                "Aucun morceau dans scores.json.",
            )
            return

        nom = simpledialog.askstring(
            "Créer une playlist",
            (
                "Entre le nom de la playlist Spotify.\n\n"
                "Les 100 meilleurs morceaux Elo seront ajoutés."
            ),
            parent=self.root,
        )

        if nom is None:
            return

        nom = " ".join(
            nom.split()
        )

        if not nom:
            messagebox.showwarning(
                "Nom invalide",
                "Le nom ne peut pas être vide.",
            )
            return

        privee = messagebox.askyesno(
            "Visibilité",
            (
                "Créer une playlist privée ?\n\n"
                "Oui : privée\n"
                "Non : publique"
            ),
            parent=self.root,
        )

        commande = [
            sys.executable,
            str(script),
            "--nom",
            nom,
            "--nombre",
            "100",
        ]

        if privee:
            commande.append(
                "--privee"
            )

        progression = FenetreProgressionPlaylist(
            self.root,
            nom,
        )

        progression.lancer(
            commande
        )

        self.message(
            f"Création de la playlist « {nom} »...",
            GREEN,
        )

    def ouvrir_dossier(self):
        try:
            if os.name == "nt":
                os.startfile(DOSSIER_APP)

            elif sys.platform == "darwin":
                subprocess.Popen(
                    [
                        "open",
                        str(DOSSIER_APP),
                    ]
                )

            else:
                subprocess.Popen(
                    [
                        "xdg-open",
                        str(DOSSIER_APP),
                    ]
                )

        except OSError as erreur:
            messagebox.showerror(
                "Erreur",
                str(erreur),
            )

    def afficher_classement(self):
        try:
            data = charger_scores()

        except RuntimeError as erreur:
            messagebox.showerror(
                "Erreur",
                str(erreur),
            )
            return

        if not data:
            messagebox.showwarning(
                "Classement vide",
                "Aucun morceau dans scores.json.",
            )
            return

        classement = sorted(
            data.items(),
            key=lambda element: (
                -element[1].get(
                    "elo",
                    1000,
                ),
                element[0].casefold(),
            ),
        )

        fenetre = tk.Toplevel(
            self.root
        )

        fenetre.title(
            "Classement VS Musique"
        )

        fenetre.geometry(
            "1050x650"
        )

        fenetre.minsize(
            820,
            450,
        )

        fenetre.configure(
            bg=BG
        )

        haut = tk.Frame(
            fenetre,
            bg=BG,
        )

        haut.pack(
            fill="x",
            padx=15,
            pady=(15, 8),
        )

        tk.Label(
            haut,
            text="Classement actuel",
            font=("Arial", 18, "bold"),
            bg=BG,
            fg=TEXT,
        ).pack(
            side="left"
        )

        recherche = tk.StringVar()

        champ_recherche = tk.Entry(
            haut,
            textvariable=recherche,
            font=("Arial", 11),
            width=28,
        )

        champ_recherche.pack(
            side="right"
        )

        cadre_table = tk.Frame(
            fenetre,
            bg=BG,
        )

        cadre_table.pack(
            fill="both",
            expand=True,
            padx=15,
            pady=(0, 15),
        )

        cadre_table.rowconfigure(
            0,
            weight=1,
        )

        cadre_table.columnconfigure(
            0,
            weight=1,
        )

        colonnes = (
            "rang",
            "artiste",
            "titre",
            "elo",
            "tier",
            "matchs",
            "v",
            "d",
            "e",
        )

        arbre = ttk.Treeview(
            cadre_table,
            columns=colonnes,
            show="headings",
            style="Classement.Treeview",
        )

        barre_y = ttk.Scrollbar(
            cadre_table,
            orient="vertical",
            command=arbre.yview,
        )

        arbre.configure(
            yscrollcommand=barre_y.set,
        )

        arbre.grid(
            row=0,
            column=0,
            sticky="nsew",
        )

        barre_y.grid(
            row=0,
            column=1,
            sticky="ns",
        )

        configuration = {
            "rang": ("#", 50, "center"),
            "artiste": ("Artiste", 190, "w"),
            "titre": ("Titre", 320, "w"),
            "elo": ("Elo", 75, "center"),
            "tier": ("Palier", 70, "center"),
            "matchs": ("Matchs", 75, "center"),
            "v": ("V", 50, "center"),
            "d": ("D", 50, "center"),
            "e": ("É", 50, "center"),
        }

        for colonne, (
            titre_colonne,
            largeur,
            alignement,
        ) in configuration.items():
            arbre.heading(
                colonne,
                text=titre_colonne,
            )

            arbre.column(
                colonne,
                width=largeur,
                anchor=alignement,
            )

        def remplir(*_args):
            terme = (
                recherche.get()
                .strip()
                .casefold()
            )

            arbre.delete(
                *arbre.get_children()
            )

            for rang, (
                cle,
                info,
            ) in enumerate(
                classement,
                start=1,
            ):
                artiste = info.get(
                    "artiste",
                    "",
                )

                titre = info.get(
                    "musique",
                    info.get(
                        "titre",
                        "",
                    ),
                )

                contenu = (
                    f"{cle} {artiste} {titre}"
                    .casefold()
                )

                if terme and terme not in contenu:
                    continue

                arbre.insert(
                    "",
                    "end",
                    values=(
                        rang,
                        artiste,
                        titre,
                        info.get(
                            "elo",
                            1000,
                        ),
                        info.get(
                            "tier",
                            "-",
                        ),
                        nb_matchs(info),
                        info.get(
                            "victoires",
                            0,
                        ),
                        info.get(
                            "defaites",
                            0,
                        ),
                        info.get(
                            "egalites",
                            0,
                        ),
                    ),
                )

        recherche.trace_add(
            "write",
            remplir,
        )

        remplir()
        champ_recherche.focus_set()


if __name__ == "__main__":
    racine = tk.Tk()
    App(racine)
    racine.mainloop()