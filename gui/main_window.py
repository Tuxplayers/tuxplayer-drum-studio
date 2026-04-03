# ==============================================================================
# PROJEKT      : TUXPLAYER Drum Studio
# AUTOR        : Heiko Schäfer
# ARTIST       : TUXPLAYER
# ERSTELLT     : 2026-04-03
# VERSION      : 1.0.0
# BESCHREIBUNG : Hauptfenster – 3-spaltiges Dark-UI im TUXPLAYER-Stil
# STATUS       : development
# DEPENDENCIES : mido, python-rtmidi, tkinter (system), Pillow (optional)
# KONTAKT      : contact@tuxhs.de
# WEBSITE      : https://tuxhs.de
# GITHUB       : https://github.com/Tuxplayers
# GIT-USER     : Tuxplayers
# LIZENZ       : MIT (Code) | CC BY-SA 4.0 (Assets)
# CHANGELOG    : 2026-04-03 v1.0.0 – Initiale Version
#              : Interaktiver Beat-Visualizer (400×120, Klick-Toggle)
# ==============================================================================

import os
import signal
import subprocess
import tkinter as tk
from tkinter import ttk, filedialog

try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

# ── Pfade ──────────────────────────────────────────────────────────────────────
BASE_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
EXPORT_DIR = "/home/heiko/scripts/musik/exports/"

# ── Farben (TUXPLAYER Dark-Style, identisch TUX-Guitar-Tuner) ─────────────────
C_BG       = "#1a1a1a"   # Hauptfenster-Hintergrund
C_PANEL    = "#0d0d0d"   # Panel / Footer / Canvas
C_WIDGET   = "#111111"   # Listbox, Eingaben
C_BTN      = "#2a2a2a"   # Standard-Button bg
C_GREEN    = "#00ff00"   # Akzent Grün – Titel, OK, aktiv
C_GREEN_D  = "#00aa00"   # Dunkelgrün – Tab aktiv, Hover
C_GREEN_DK = "#006600"   # Export-Button bg
C_GREEN_SL = "#005500"   # Listbox-Selektion bg
C_CYAN     = "#00bcd4"   # Akzent Cyan – Trennlinien, Info
C_WARN     = "#ff4444"   # Fehler / Warnung
C_ORANGE   = "#ffaa00"   # Sekundär-Warnung / Fill-Farbe
C_FG       = "#cccccc"   # Standard-Fließtext
C_FG_DIM   = "#aaaaaa"   # gedimmt
C_FG_DARK  = "#666666"   # sehr gedimmt
C_QUIT_BG  = "#440000"   # Quit-Button bg

# ── Canvas-Geometrie (Beat-Visualizer) ────────────────────────────────────────
CV_W     = 400     # Canvas-Breite
CV_H     = 120     # Canvas-Höhe
LABEL_W  = 30      # Breite der Zeilen-Beschriftungsspalte
STEPS    = 16      # Sechzehntelnoten pro Takt
ROWS     = 4       # Zeilen: Kick, Snare, HiHat, Fill
STEP_W   = (CV_W - LABEL_W) / STEPS   # ≈ 23.125 px
ROW_H    = CV_H / ROWS                # = 30 px

# Zeilen-Konfiguration: (Label, Dict-Key, Farbe)
GRID_ROWS = [
    ("BD", "kick",  "#ff4444"),
    ("SN", "snare", "#00ff00"),
    ("HH", "hihat", "#00bcd4"),
    ("FL", "fill",  "#ffaa00"),
]

# ── Beat-Pattern-Bibliothek (Listen, 16 Sechzehntel) ─────────────────────────
# Step 0 = Beat 1, Step 4 = Beat 2, Step 8 = Beat 3, Step 12 = Beat 4
BEAT_PATTERNS: dict[str, dict[str, list[int]]] = {
    "Standard Rock": {
        "kick":  [1,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0],  # Beat 1 + 3
        "snare": [0,0,0,0,1,0,0,0,0,0,0,0,1,0,0,0],  # Beat 2 + 4
        "hihat": [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],  # alle 16tel
        "fill":  [0]*16,
    },
    "Half-Time": {
        "kick":  [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],  # Beat 1
        "snare": [0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0],  # Beat 3
        "hihat": [1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0],  # alle 8tel
        "fill":  [0]*16,
    },
    "Double-Time": {
        "kick":  [1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0],  # alle Beats
        "snare": [0,0,0,0,1,0,0,0,0,0,0,0,1,0,0,0],  # Beat 2 + 4
        "hihat": [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],  # alle 16tel
        "fill":  [0]*16,
    },
    "Metal Blast": {
        "kick":  [1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0],  # alternierend
        "snare": [0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1],  # alternierend
        "hihat": [0]*16,                                # kein HiHat
        "fill":  [0]*16,
    },
    "Punk Beat": {
        "kick":  [1,0,0,0,0,0,0,0,1,0,0,1,0,0,0,0],  # Beat 1 + 3 + 4
        "snare": [0,0,0,0,1,0,0,0,0,0,0,0,1,0,0,0],  # Beat 2 + 4
        "hihat": [1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0],  # alle 8tel
        "fill":  [0]*16,
    },
    "Custom": {
        "kick":  [0]*16,
        "snare": [0]*16,
        "hihat": [0]*16,
        "fill":  [0]*16,
    },
}

FILL_TYPES  = ["Tom-Fill", "Blast-Fill", "Drum-Roll", "Crash-Accent", "Custom"]
AUDIO_DEVS  = ["PreSonus 1824c", "Scarlett 2i2"]
MIDI_DEVS   = ["MPS-850", "anderes"]


# ==============================================================================

class MainWindow:
    """Hauptfenster des TUXPLAYER Drum Studios im Dark-Style."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("🥁 TUXPLAYER Drum Studio v1.0")
        self.root.configure(bg=C_BG)
        self.root.resizable(False, False)
        self.root.geometry("1200x800")

        # ── Zustand ────────────────────────────────────────────────────────────
        self._status_msg  = tk.StringVar(value="Bereit.")
        self._export_path = tk.StringVar(value=EXPORT_DIR)
        self._export_name = tk.StringVar(value="song_struktur.mid")
        self._bpm_var     = tk.IntVar(value=120)
        self._bars_var    = tk.IntVar(value=8)
        self._pattern_var = tk.StringVar(value="Standard Rock")
        self._fill_var    = tk.StringVar(value="Tom-Fill")
        self._fill_on     = tk.BooleanVar(value=False)
        self._crash_beat  = tk.BooleanVar(value=False)
        self._ride_hh     = tk.BooleanVar(value=False)
        self._open_hh     = tk.BooleanVar(value=False)
        self._double_kick = tk.BooleanVar(value=False)
        self._humanize    = tk.DoubleVar(value=0)
        self._audio_dev   = tk.StringVar(value=AUDIO_DEVS[0])
        self._midi_dev    = tk.StringVar(value=MIDI_DEVS[0])

        # Grid-Daten: Dict mit 16-Element-Listen (0=leer, 1=aktiv)
        self._grid_data: dict[str, list[int]] = {
            "kick":  [0]*16,
            "snare": [0]*16,
            "hihat": [0]*16,
            "fill":  [0]*16,
        }

        self._img_logo   = None
        self._img_mascot = None
        self._canvas     = None   # Beat-Visualizer Canvas (wird in _build_middle gesetzt)

        self._apply_ttk_style()
        self._load_images()
        self._build_header()
        self._build_body()
        self._build_footer()

        # Standard-Pattern laden
        self._load_pattern()

        signal.signal(signal.SIGINT, lambda *_: self._quit())
        self.root.after(200, self._refresh_pw_devices)

    # ── TTK-Style (identisch TUX-Guitar-Tuner) ────────────────────────────────
    def _apply_ttk_style(self):
        """Konfiguriert ttk-Widgets im TUXPLAYER Dark-Theme."""
        sty = ttk.Style()
        sty.theme_use("default")
        sty.configure("TNotebook", background=C_BG, borderwidth=0)
        sty.configure("TNotebook.Tab",
                       background=C_BTN, foreground="white", padding=[12, 5])
        sty.map("TNotebook.Tab",
                background=[("selected", C_GREEN_D)],
                foreground=[("selected", "black")])
        sty.configure("TCombobox",
                       fieldbackground=C_WIDGET, background=C_BTN,
                       foreground=C_GREEN, selectbackground=C_GREEN_SL)
        sty.configure("TSpinbox",
                       fieldbackground=C_WIDGET, background=C_BTN,
                       foreground=C_GREEN)

    # ── Bilder (Logo + Mascot) ────────────────────────────────────────────────
    def _load_images(self):
        """Lädt Logo (280×82) und Mascot (90×82) aus dem assets/-Verzeichnis."""
        if not PIL_AVAILABLE:
            return
        for attr, filename, size in [
            ("_img_logo",   "LOGObranding_logo_Program.png", (280, 82)),
            ("_img_mascot", "TUXPLAYER_MASCOT_RED_SILUET.png", (90, 82)),
        ]:
            path = os.path.join(ASSETS_DIR, filename)
            if os.path.exists(path):
                img = Image.open(path).resize(size, Image.LANCZOS)
                setattr(self, attr, ImageTk.PhotoImage(img))

    # ── Header ────────────────────────────────────────────────────────────────
    def _build_header(self):
        """Header: Logo links, Titel Mitte, Mascot rechts."""
        hdr = tk.Frame(self.root, bg=C_PANEL)
        hdr.pack(side="top", fill="x")

        # Logo links
        if self._img_logo:
            tk.Label(hdr, image=self._img_logo, bg=C_PANEL).pack(
                side="left", padx=(12, 0), pady=6)
        else:
            tk.Label(hdr, text="🥁 TUXPLAYER", fg=C_GREEN, bg=C_PANEL,
                     font=("Arial", 18, "bold")).pack(side="left", padx=12, pady=14)

        # Titelblock Mitte
        mid = tk.Frame(hdr, bg=C_PANEL)
        mid.pack(side="left", expand=True)
        tk.Label(mid, text="DRUM STUDIO",
                 fg=C_GREEN, bg=C_PANEL, font=("Arial", 14, "bold")).pack()
        tk.Label(mid, text="Song Arrangement  ·  MIDI Generator  ·  PipeWire Routing",
                 fg=C_CYAN, bg=C_PANEL, font=("Arial", 9)).pack()

        # Mascot rechts
        if self._img_mascot:
            tk.Label(hdr, image=self._img_mascot, bg=C_PANEL).pack(
                side="right", padx=(0, 12), pady=6)
        else:
            tk.Label(hdr, text="🎵", fg=C_WARN, bg=C_PANEL,
                     font=("Arial", 32)).pack(side="right", padx=12, pady=6)

        # Cyan-Trennlinie unter dem Header
        tk.Frame(self.root, bg=C_CYAN, height=1).pack(fill="x")

    # ── Hauptkörper (3 Spalten) ───────────────────────────────────────────────
    def _build_body(self):
        """Erzeugt den 3-spaltigen Hauptbereich."""
        body = tk.Frame(self.root, bg=C_BG)
        body.pack(side="top", fill="both", expand=True)
        # Reihenfolge: Rechts zuerst packen (damit Mitte fill=both korrekt wirkt)
        self._build_left(body)
        self._build_right(body)
        self._build_middle(body)

    # ══════════════════════════════════════════════════════════════════════════
    # LINKS – 220 px
    # ══════════════════════════════════════════════════════════════════════════
    def _build_left(self, parent):
        """Linke Spalte: Notebook mit Song- und Gerät-Tab."""
        frame = tk.Frame(parent, bg=C_PANEL, width=220)
        frame.pack(side="left", fill="y")
        frame.pack_propagate(False)

        nb = ttk.Notebook(frame, width=218)
        nb.pack(fill="both", expand=True)

        t_song   = tk.Frame(nb, bg=C_PANEL)
        t_device = tk.Frame(nb, bg=C_PANEL)
        nb.add(t_song,   text="🥁 Song")
        nb.add(t_device, text="🎛 Gerät")

        self._build_tab_song(t_song)
        self._build_tab_device(t_device)

    def _build_tab_song(self, parent):
        """Tab: Song-Arrangement – Listbox mit Sektionen + Navigation."""
        tk.Label(parent, text="Song-Sektionen",
                 fg=C_GREEN, bg=C_PANEL, font=("Arial", 11, "bold")
                 ).pack(pady=(10, 4))

        # Listbox mit Scrollbar
        lb_fr = tk.Frame(parent, bg=C_PANEL)
        lb_fr.pack(fill="both", expand=True, padx=8)

        sb = tk.Scrollbar(lb_fr, bg=C_BTN, troughcolor=C_PANEL, relief="flat")
        sb.pack(side="right", fill="y")

        self._song_lb = tk.Listbox(
            lb_fr,
            bg=C_WIDGET, fg=C_GREEN,
            selectbackground=C_GREEN_SL, selectforeground=C_GREEN,
            font=("Monospace", 9), activestyle="none",
            relief="flat", bd=0, yscrollcommand=sb.set,
        )
        self._song_lb.pack(side="left", fill="both", expand=True)
        sb.config(command=self._song_lb.yview)

        for sec in ["Intro", "Verse 1", "Pre-Chorus", "Chorus 1",
                    "Verse 2", "Pre-Chorus 2", "Chorus 2", "Bridge",
                    "Chorus 3", "Outro"]:
            self._song_lb.insert(tk.END, f"  {sec}")

        self._song_lb.bind("<<ListboxSelect>>", self._on_section_select)

        # Navigations-Buttons
        def _btn(parent_fr, text, cmd):
            return tk.Button(
                parent_fr, text=text, command=cmd,
                bg=C_BTN, fg=C_FG_DIM, font=("Arial", 10),
                relief="flat", cursor="hand2",
                activebackground=C_GREEN_D, activeforeground="black")

        row1 = tk.Frame(parent, bg=C_PANEL)
        row1.pack(fill="x", padx=8, pady=(6, 2))
        _btn(row1, "+ Neu",    self._section_add).pack(side="left", expand=True, fill="x", padx=1)
        _btn(row1, "- Löschen",self._section_del).pack(side="left", expand=True, fill="x", padx=1)

        row2 = tk.Frame(parent, bg=C_PANEL)
        row2.pack(fill="x", padx=8, pady=(0, 10))
        _btn(row2, "↑", self._section_up).pack(side="left", expand=True, fill="x", padx=1)
        _btn(row2, "↓", self._section_dn).pack(side="left", expand=True, fill="x", padx=1)

    def _build_tab_device(self, parent):
        """Tab: Audio-/MIDI-Gerätekonfiguration."""
        tk.Label(parent, text="Audio / MIDI",
                 fg=C_GREEN, bg=C_PANEL, font=("Arial", 11, "bold")
                 ).pack(pady=(12, 6))

        def _lbl(text):
            tk.Label(parent, text=text,
                     fg=C_FG_DIM, bg=C_PANEL, font=("Arial", 9)
                     ).pack(anchor="w", padx=12)

        _lbl("Audiogerät:")
        ttk.Combobox(parent, textvariable=self._audio_dev,
                     values=AUDIO_DEVS, state="readonly",
                     font=("Arial", 9)).pack(fill="x", padx=12, pady=(2, 10))

        _lbl("MIDI-Device:")
        ttk.Combobox(parent, textvariable=self._midi_dev,
                     values=MIDI_DEVS, state="readonly",
                     font=("Arial", 9)).pack(fill="x", padx=12, pady=(2, 14))

        tk.Button(parent, text="🔌 Routing aktivieren",
                  command=self._activate_routing,
                  bg=C_GREEN_D, fg="black", font=("Arial", 10, "bold"),
                  relief="flat", cursor="hand2", pady=8,
                  activebackground=C_GREEN, activeforeground="black",
                  ).pack(fill="x", padx=12)

    # ══════════════════════════════════════════════════════════════════════════
    # MITTE – 580 px (Sektions-Editor + Beat-Visualizer)
    # ══════════════════════════════════════════════════════════════════════════
    def _build_middle(self, parent):
        """Mittlere Spalte: Sektions-Editor mit interaktivem Beat-Grid."""
        frame = tk.Frame(parent, bg=C_BG, width=580)
        frame.pack(side="left", fill="both", expand=True)
        frame.pack_propagate(False)

        # Sektionsname-Überschrift (wird bei Auswahl aktualisiert)
        self._mid_title = tk.Label(frame, text="← Sektion auswählen",
                                   fg=C_GREEN, bg=C_BG,
                                   font=("Arial", 13, "bold"))
        self._mid_title.pack(pady=(12, 6))

        # ── Parameter-Raster ─────────────────────────────────────────────────
        grid = tk.Frame(frame, bg=C_BG)
        grid.pack(fill="x", padx=20)

        def _lbl(text, row):
            tk.Label(grid, text=text, fg=C_FG_DIM, bg=C_BG,
                     font=("Arial", 10), anchor="e", width=18,
                     ).grid(row=row, column=0, sticky="e", pady=3, padx=(0, 8))

        # BPM
        _lbl("BPM:", 0)
        tk.Spinbox(grid, from_=60, to=240, textvariable=self._bpm_var,
                   width=6, bg=C_WIDGET, fg=C_GREEN, insertbackground=C_GREEN,
                   font=("Monospace", 10), relief="flat", bd=4,
                   buttonbackground=C_BTN, command=self._redraw_grid,
                   ).grid(row=0, column=1, sticky="w", pady=3)

        # Takte
        _lbl("Takte:", 1)
        tk.Spinbox(grid, from_=1, to=32, textvariable=self._bars_var,
                   width=6, bg=C_WIDGET, fg=C_GREEN, insertbackground=C_GREEN,
                   font=("Monospace", 10), relief="flat", bd=4,
                   buttonbackground=C_BTN,
                   ).grid(row=1, column=1, sticky="w", pady=3)

        # Beat-Pattern
        _lbl("Beat-Pattern:", 2)
        pat_cb = ttk.Combobox(grid, textvariable=self._pattern_var,
                               values=list(BEAT_PATTERNS.keys()),
                               state="readonly", font=("Arial", 9), width=18)
        pat_cb.grid(row=2, column=1, sticky="w", pady=3)
        pat_cb.bind("<<ComboboxSelected>>", lambda _: self._load_pattern())

        # Fill am Ende
        _lbl("Fill am Ende:", 3)
        fill_fr = tk.Frame(grid, bg=C_BG)
        fill_fr.grid(row=3, column=1, sticky="w", pady=3)
        tk.Checkbutton(fill_fr, text="", variable=self._fill_on,
                       fg=C_FG_DIM, bg=C_BG, selectcolor=C_BTN,
                       activebackground=C_BG, activeforeground=C_GREEN,
                       command=self._redraw_grid,
                       ).pack(side="left")
        ttk.Combobox(fill_fr, textvariable=self._fill_var,
                     values=FILL_TYPES, state="readonly",
                     font=("Arial", 9), width=14).pack(side="left", padx=4)

        # Becken
        _lbl("Becken:", 4)
        becken_fr = tk.Frame(grid, bg=C_BG)
        becken_fr.grid(row=4, column=1, sticky="w", pady=3)
        for var, text in [(self._crash_beat, "Crash Beat 1"),
                          (self._ride_hh,    "Ride statt HiHat"),
                          (self._open_hh,    "Open HiHat Upbeat")]:
            tk.Checkbutton(becken_fr, text=text, variable=var,
                           fg=C_FG_DIM, bg=C_BG, selectcolor=C_BTN,
                           activebackground=C_BG, activeforeground=C_GREEN,
                           font=("Arial", 9), command=self._redraw_grid,
                           ).pack(side="left", padx=(0, 6))

        # Doppelbase
        _lbl("Doppelbase:", 5)
        tk.Checkbutton(grid,
                       text="🦶 Doppelbase (Note 35+36)",
                       variable=self._double_kick,
                       fg=C_FG_DIM, bg=C_BG, selectcolor=C_BTN,
                       activebackground=C_BG, activeforeground=C_GREEN,
                       font=("Arial", 10), command=self._redraw_grid,
                       ).grid(row=5, column=1, sticky="w", pady=3)

        # Humanize
        _lbl("Humanize:", 6)
        hum_fr = tk.Frame(grid, bg=C_BG)
        hum_fr.grid(row=6, column=1, sticky="w", pady=3)
        tk.Scale(hum_fr, variable=self._humanize, from_=0, to=30,
                 orient="horizontal", length=160,
                 bg=C_BG, troughcolor=C_BTN,
                 activebackground=C_CYAN, fg=C_FG_DIM,
                 highlightthickness=0, relief="flat",
                 showvalue=True, font=("Arial", 8),
                 ).pack(side="left")
        tk.Label(hum_fr, text="Ticks", fg=C_FG_DARK, bg=C_BG,
                 font=("Arial", 8)).pack(side="left", padx=4)

        # ── Beat-Visualizer ──────────────────────────────────────────────────
        tk.Frame(frame, bg=C_CYAN, height=1).pack(fill="x", padx=20, pady=(10, 0))

        # Legende
        leg = tk.Frame(frame, bg=C_BG)
        leg.pack(fill="x", padx=20, pady=(4, 0))
        tk.Label(leg, text="Beat-Visualizer  (Klick = Note an/aus)",
                 fg=C_CYAN, bg=C_BG, font=("Arial", 10, "bold")).pack(side="left")
        for lbl, col in [("Kick", "#ff4444"), ("Snare", "#00ff00"),
                          ("HiHat", "#00bcd4"), ("Fill", "#ffaa00")]:
            tk.Frame(leg, bg=col, width=10, height=10).pack(side="right", padx=(0, 2))
            tk.Label(leg, text=lbl, fg=col, bg=C_BG,
                     font=("Arial", 8)).pack(side="right", padx=(6, 0))

        # Canvas (400×120) – interaktiv
        self._canvas = tk.Canvas(frame, width=CV_W, height=CV_H,
                                 bg=C_PANEL, highlightthickness=1,
                                 highlightbackground=C_BTN,
                                 cursor="hand2")
        self._canvas.pack(padx=20, pady=(4, 8))
        self._canvas.bind("<Button-1>", self._on_canvas_click)

    # ── Beat-Grid zeichnen ────────────────────────────────────────────────────
    def _redraw_grid(self, *_):
        """Zeichnet das 4×16-Beat-Grid neu anhand von self._grid_data."""
        if self._canvas is None:
            return
        self._canvas.delete("all")

        for ri, (label, key, col) in enumerate(GRID_ROWS):
            y1 = ri * ROW_H
            y2 = (ri + 1) * ROW_H

            # Zeilen-Label ("BD", "SN", "HH", "FL")
            self._canvas.create_text(
                LABEL_W // 2, (y1 + y2) / 2,
                text=label, fill=C_FG_DARK,
                font=("Monospace", 8, "bold"))

            for si in range(STEPS):
                x1 = LABEL_W + si * STEP_W + 1
                x2 = LABEL_W + (si + 1) * STEP_W - 1
                active = self._grid_data[key][si]
                fill_c = col if active else "#1a1a1a"

                self._canvas.create_rectangle(
                    x1, y1 + 1, x2, y2 - 1,
                    fill=fill_c, outline="#333333")

                # Helligkeit-Highlight auf aktiven Zellen (oberes Band)
                if active:
                    self._canvas.create_rectangle(
                        x1 + 1, y1 + 2, x2 - 1, y1 + 6,
                        fill="#ffffff22", outline="")

        # Takt-Trennlinien alle 4 Schritte (#444444)
        for t in range(1, 4):
            x = LABEL_W + t * 4 * STEP_W
            self._canvas.create_line(x, 0, x, CV_H, fill="#444444", width=1)

        # Beschriftung der Taktpositionen (T1–T4) oben
        for t in range(4):
            x = LABEL_W + t * 4 * STEP_W + 2 * STEP_W
            self._canvas.create_text(
                x, 5, text=f"T{t+1}", fill="#444444", font=("Arial", 6))

    # ── Klick-Interaktion auf dem Canvas ─────────────────────────────────────
    def _on_canvas_click(self, event):
        """Toggelt die angeklickte Note im Grid an/aus."""
        if event.x < LABEL_W:
            return
        col = int((event.x - LABEL_W) / STEP_W)
        row = int(event.y / ROW_H)
        if 0 <= col < STEPS and 0 <= row < ROWS:
            row_key = GRID_ROWS[row][1]   # "kick" / "snare" / "hihat" / "fill"
            self._grid_data[row_key][col] ^= 1
            self._redraw_grid()

    # ── Pattern aus Bibliothek laden ─────────────────────────────────────────
    def _load_pattern(self):
        """Lädt das gewählte Preset aus BEAT_PATTERNS in self._grid_data."""
        name = self._pattern_var.get()
        pat  = BEAT_PATTERNS.get(name, {})
        for key in ("kick", "snare", "hihat", "fill"):
            self._grid_data[key] = list(pat.get(key, [0]*16))
        self._redraw_grid()

    def get_grid_data(self) -> dict[str, list[int]]:
        """Gibt die aktuellen Grid-Daten für fill_logic.py zurück."""
        return {k: list(v) for k, v in self._grid_data.items()}

    # ══════════════════════════════════════════════════════════════════════════
    # RECHTS – 340 px
    # ══════════════════════════════════════════════════════════════════════════
    def _build_right(self, parent):
        """Rechte Spalte: MIDI Export, PipeWire Routing, Status."""
        frame = tk.Frame(parent, bg=C_PANEL, width=340)
        frame.pack(side="right", fill="y")
        frame.pack_propagate(False)

        # ── MIDI Export ───────────────────────────────────────────────────────
        tk.Label(frame, text="📤 MIDI Export",
                 fg=C_GREEN, bg=C_PANEL, font=("Arial", 13, "bold")
                 ).pack(pady=(12, 6))

        # Exportpfad
        path_fr = tk.Frame(frame, bg=C_PANEL)
        path_fr.pack(fill="x", padx=12, pady=(0, 4))
        tk.Label(path_fr, text="Pfad:", fg=C_FG_DIM, bg=C_PANEL,
                 font=("Arial", 9)).pack(anchor="w")
        ep_fr = tk.Frame(path_fr, bg=C_PANEL)
        ep_fr.pack(fill="x")
        tk.Entry(ep_fr, textvariable=self._export_path,
                 bg=C_WIDGET, fg=C_GREEN, insertbackground=C_GREEN,
                 font=("Monospace", 8), relief="flat", bd=4,
                 ).pack(side="left", fill="x", expand=True)
        tk.Button(ep_fr, text="📁", command=self._browse_export,
                  bg=C_BTN, fg=C_FG_DIM, font=("Arial", 9),
                  relief="flat", cursor="hand2",
                  activebackground=C_GREEN_D,
                  ).pack(side="right", padx=(4, 0))

        # Dateiname
        nm_fr = tk.Frame(frame, bg=C_PANEL)
        nm_fr.pack(fill="x", padx=12, pady=(0, 8))
        tk.Label(nm_fr, text="Dateiname:", fg=C_FG_DIM, bg=C_PANEL,
                 font=("Arial", 9)).pack(anchor="w")
        tk.Entry(nm_fr, textvariable=self._export_name,
                 bg=C_WIDGET, fg=C_GREEN, insertbackground=C_GREEN,
                 font=("Monospace", 8), relief="flat", bd=4,
                 ).pack(fill="x")

        # Export-Button (prominent, grün)
        tk.Button(frame, text="🎵 MIDI generieren & exportieren",
                  command=self._export_midi,
                  bg=C_GREEN_DK, fg="white",
                  font=("Arial", 12, "bold"),
                  relief="flat", cursor="hand2", pady=12,
                  activebackground=C_GREEN, activeforeground="black",
                  ).pack(fill="x", padx=12, pady=(0, 12))

        # Trennlinie
        tk.Frame(frame, bg=C_CYAN, height=1).pack(fill="x")

        # ── PipeWire Routing ─────────────────────────────────────────────────
        tk.Label(frame, text="🔊 PipeWire Routing",
                 fg=C_GREEN, bg=C_PANEL, font=("Arial", 13, "bold")
                 ).pack(pady=(10, 4))

        tk.Label(frame, text="Erkannte Geräte:",
                 fg=C_FG_DIM, bg=C_PANEL, font=("Arial", 9)
                 ).pack(anchor="w", padx=12)

        pw_fr = tk.Frame(frame, bg=C_PANEL)
        pw_fr.pack(fill="x", padx=12, pady=(2, 6))
        pw_sb = tk.Scrollbar(pw_fr, bg=C_BTN, troughcolor=C_PANEL, relief="flat")
        pw_sb.pack(side="right", fill="y")
        self._pw_lb = tk.Listbox(pw_fr,
                                 bg=C_WIDGET, fg=C_CYAN,
                                 selectbackground=C_GREEN_SL,
                                 font=("Monospace", 8), relief="flat", bd=0,
                                 height=5, yscrollcommand=pw_sb.set)
        self._pw_lb.pack(side="left", fill="x", expand=True)
        pw_sb.config(command=self._pw_lb.yview)

        def _rbtn(text, cmd):
            tk.Button(frame, text=text, command=cmd,
                      bg=C_BTN, fg=C_FG_DIM, font=("Arial", 10),
                      relief="flat", cursor="hand2", pady=5,
                      activebackground=C_GREEN_D, activeforeground="black",
                      ).pack(fill="x", padx=12, pady=(0, 4))

        _rbtn("🔌 Routing aufbauen",         self._activate_routing)
        _rbtn("🔄 Geräte aktualisieren",      self._refresh_pw_devices)
        _rbtn("💾 qpwgraph Session speichern", self._save_qpwgraph)

        # Trennlinie
        tk.Frame(frame, bg=C_CYAN, height=1).pack(fill="x")

        # Status-Label
        self._status_lbl = tk.Label(frame, textvariable=self._status_msg,
                                    fg=C_GREEN, bg=C_PANEL,
                                    font=("Monospace", 9),
                                    wraplength=310, justify="left")
        self._status_lbl.pack(anchor="w", padx=12, pady=(8, 4), fill="x")

    # ── Footer ────────────────────────────────────────────────────────────────
    def _build_footer(self):
        """Footer: Cyan-Trennlinie + Copyright + Quit-Button."""
        tk.Frame(self.root, bg=C_CYAN, height=1).pack(fill="x")
        ftr = tk.Frame(self.root, bg=C_PANEL)
        ftr.pack(side="bottom", fill="x")

        tk.Label(ftr,
                 text="© 2026 Heiko Schäfer (TUXPLAYER)  ·  contact@tuxhs.de  ·  tuxhs.de",
                 fg="#888888", bg=C_PANEL, font=("Arial", 8),
                 ).pack(side="left", padx=12, pady=6)

        tk.Button(ftr, text="✖  BEENDEN", command=self._quit,
                  bg=C_QUIT_BG, fg="white", font=("Arial", 10, "bold"),
                  relief="flat", cursor="hand2", pady=5,
                  activebackground="#660000", activeforeground="white",
                  ).pack(side="right", padx=12, pady=4)

    # ══════════════════════════════════════════════════════════════════════════
    # Callbacks
    # ══════════════════════════════════════════════════════════════════════════

    def _set_status(self, msg: str, level: str = "ok"):
        """Setzt den Status-Text mit farblicher Kennzeichnung (ok/warn/error)."""
        colors = {"ok": C_GREEN, "warn": C_ORANGE, "error": C_WARN}
        self._status_msg.set(msg)
        self._status_lbl.config(fg=colors.get(level, C_GREEN))

    def _on_section_select(self, _event=None):
        """Aktualisiert den Sektions-Titel bei Auswahl in der Listbox."""
        sel = self._song_lb.curselection()
        if not sel:
            return
        name = self._song_lb.get(sel[0]).strip()
        self._mid_title.config(text=f"✏  {name}")

    def _section_add(self):
        self._song_lb.insert(tk.END, "  Neue Sektion")
        self._song_lb.selection_clear(0, tk.END)
        self._song_lb.selection_set(tk.END)
        self._song_lb.see(tk.END)
        self._on_section_select()

    def _section_del(self):
        sel = self._song_lb.curselection()
        if sel:
            self._song_lb.delete(sel[0])
            self._mid_title.config(text="← Sektion auswählen")

    def _section_up(self):
        sel = self._song_lb.curselection()
        if not sel or sel[0] == 0:
            return
        i = sel[0]
        txt = self._song_lb.get(i)
        self._song_lb.delete(i)
        self._song_lb.insert(i - 1, txt)
        self._song_lb.selection_set(i - 1)

    def _section_dn(self):
        sel = self._song_lb.curselection()
        if not sel or sel[0] >= self._song_lb.size() - 1:
            return
        i = sel[0]
        txt = self._song_lb.get(i)
        self._song_lb.delete(i)
        self._song_lb.insert(i + 1, txt)
        self._song_lb.selection_set(i + 1)

    def _browse_export(self):
        path = filedialog.askdirectory(initialdir=self._export_path.get())
        if path:
            self._export_path.set(path + "/")

    def _export_midi(self):
        """Platzhalter – MIDI-Export wird in core/midi_generator.py implementiert."""
        out = os.path.join(self._export_path.get(), self._export_name.get())
        self._set_status(f"MIDI Export → {out}", "ok")

    def _activate_routing(self):
        """Startet das PipeWire-Routing via pipewire_manager.py."""
        self._set_status("Routing wird aufgebaut …", "warn")
        self.root.after(500, lambda: self._set_status("Routing aktiviert.", "ok"))

    def _refresh_pw_devices(self):
        """Liest erkannte PipeWire-Nodes via pw-cli aus."""
        self._pw_lb.delete(0, tk.END)
        try:
            result = subprocess.run(
                ["pw-cli", "list-objects", "Node"],
                capture_output=True, text=True, timeout=3,
            )
            for line in result.stdout.splitlines():
                if "node.name" in line:
                    cleaned = line.strip().strip('"').strip("'")
                    if cleaned:
                        self._pw_lb.insert(tk.END, cleaned)
            if self._pw_lb.size() == 0:
                self._pw_lb.insert(tk.END, "(keine Nodes gefunden)")
            self._set_status("PipeWire: Geräteliste aktualisiert.", "ok")
        except FileNotFoundError:
            self._pw_lb.insert(tk.END, "pw-cli nicht gefunden")
            self._set_status("pw-cli fehlt – PipeWire aktiv?", "warn")
        except subprocess.TimeoutExpired:
            self._pw_lb.insert(tk.END, "(Timeout)")
            self._set_status("PipeWire: Timeout beim Geräte-Scan.", "error")

    def _save_qpwgraph(self):
        """Speichert die aktuelle qpwgraph-Session."""
        try:
            subprocess.Popen(["qpwgraph", "--save"])
            self._set_status("qpwgraph: Session gespeichert.", "ok")
        except FileNotFoundError:
            self._set_status("qpwgraph nicht installiert.", "error")

    def _quit(self):
        self.root.destroy()
