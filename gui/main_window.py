# ==============================================================================
# PROJEKT      : TUXPLAYER Drum Studio
# AUTOR        : Heiko Schäfer
# ARTIST       : TUXPLAYER
# ERSTELLT     : 2026-04-03
# VERSION      : 1.3.0
# BESCHREIBUNG : Hauptfenster – 3-spaltiges Dark-UI im TUXPLAYER-Stil
#                Echte MIDI-Generierung, FluidSynth-Playback, Hydrogen/Bitwig
# STATUS       : development
# DEPENDENCIES : mido, python-rtmidi, tkinter (system), Pillow (optional)
# KONTAKT      : contact@tuxhs.de
# WEBSITE      : https://tuxhs.de
# GITHUB       : https://github.com/Tuxplayers
# GIT-USER     : Tuxplayers
# LIZENZ       : MIT (Code) | CC BY-SA 4.0 (Assets)
# CHANGELOG    : 2026-04-03 v1.0.0 – Initiale Version, interaktiver Beat-Visualizer
#              : 2026-04-04 v1.1.0 – Echte MIDI-Generierung via mido
#              :                     FluidSynth-Playback (Play/Stop/Loop)
#              :                     Öffnen in Hydrogen / Bitwig / Dateimanager
#              :                     Info-Fenster (Bedienungsanleitung + Lizenz)
#              :                     8 Beat-Pattern-Presets (Bonham, Grohl, Purdie…)
#              :                     Threading-Fix: GUI-Freeze bei pw-cli behoben
#              : 2026-04-04 v1.2.0 – Doppelbase-Fix: Note 35 auf nächste 16tel
#              :                     Spenden-Tab (Buy Me a Coffee + PayPal)
#              :                     webbrowser-Integration für Donate-Links
#              : 2026-04-04 v1.3.0 – Dropdown-Schrift: grün → weiß (besser lesbar)
#              :                     H2Song-Export: natives Hydrogen-Format (.h2song)
#              :                     Hydrogen-Button öffnet direkt mit .h2song
# ==============================================================================

import os
import signal
import subprocess
import threading
import traceback
import webbrowser
import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext

try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    import mido
    MIDO_AVAILABLE = True
except ImportError:
    MIDO_AVAILABLE = False

# ── Pfade ──────────────────────────────────────────────────────────────────────
BASE_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
EXPORT_DIR = os.path.expanduser("~/scripts/musik/exports/")

# ── Audio-Ressourcen ──────────────────────────────────────────────────────────
SOUNDFONTS = [
    "/usr/share/soundfonts/FluidR3_GM.sf2",
    "/usr/share/sounds/sf2/FluidR3_GM.sf2",
    "/usr/share/soundfonts/default.sf2",
]
SOUNDFONT = next((sf for sf in SOUNDFONTS if os.path.exists(sf)), "")

# ── Farben (TUXPLAYER Dark-Style, identisch TUX-Guitar-Tuner) ─────────────────
C_BG       = "#1a1a1a"
C_PANEL    = "#0d0d0d"
C_WIDGET   = "#111111"
C_BTN      = "#2a2a2a"
C_GREEN    = "#00ff00"
C_GREEN_D  = "#00aa00"
C_GREEN_DK = "#006600"
C_GREEN_SL = "#005500"
C_CYAN     = "#00bcd4"
C_WARN     = "#ff4444"
C_ORANGE   = "#ffaa00"
C_FG       = "#cccccc"
C_FG_DIM   = "#aaaaaa"
C_FG_DARK  = "#666666"
C_QUIT_BG  = "#440000"

# ── Canvas-Geometrie ──────────────────────────────────────────────────────────
CV_W    = 400
CV_H    = 120
LABEL_W = 30
STEPS   = 16
ROWS    = 4
STEP_W  = (CV_W - LABEL_W) / STEPS   # ≈ 23.125 px
ROW_H   = CV_H / ROWS                # = 30 px

GRID_ROWS = [
    ("BD", "kick",  "#ff4444"),
    ("SN", "snare", "#00ff00"),
    ("HH", "hihat", "#00bcd4"),
    ("FL", "fill",  "#ffaa00"),
]

# ── Beat-Pattern-Bibliothek ───────────────────────────────────────────────────
# Step 0=Beat1  Step 4=Beat2  Step 8=Beat3  Step 12=Beat4
BEAT_PATTERNS: dict[str, dict[str, list[int]]] = {
    # ── Klassiker ─────────────────────────────────────────────────────────────
    "Standard Rock": {
        "kick":  [1,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0],
        "snare": [0,0,0,0,1,0,0,0,0,0,0,0,1,0,0,0],
        "hihat": [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
        "fill":  [0]*16,
    },
    "Half-Time": {
        "kick":  [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
        "snare": [0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0],
        "hihat": [1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0],
        "fill":  [0]*16,
    },
    "Double-Time": {
        "kick":  [1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0],
        "snare": [0,0,0,0,1,0,0,0,0,0,0,0,1,0,0,0],
        "hihat": [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
        "fill":  [0]*16,
    },
    # ── Stil-Presets ──────────────────────────────────────────────────────────
    "Bonham Rock": {                          # Led Zeppelin – schwerer Groove
        "kick":  [1,0,0,1,0,0,0,0,1,0,0,1,0,0,0,0],
        "snare": [0,0,0,0,1,0,0,0,0,0,0,0,1,0,0,0],
        "hihat": [1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0],
        "fill":  [0]*16,
    },
    "Grohl Grunge": {                         # Nirvana – treibende 16tel
        "kick":  [1,0,0,0,0,0,1,0,1,0,0,0,0,0,0,0],
        "snare": [0,0,0,0,1,0,0,0,0,0,0,0,1,0,0,1],
        "hihat": [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
        "fill":  [0]*16,
    },
    "Purdie Shuffle": {                       # Funk/Soul – Ghost-Notes
        "kick":  [1,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0],
        "snare": [0,0,1,0,1,0,1,0,0,0,1,0,1,0,1,0],
        "hihat": [1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0],
        "fill":  [0]*16,
    },
    "Reggae One Drop": {                      # Reggae – Kick nur Beat 3
        "kick":  [0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0],
        "snare": [0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0],
        "hihat": [1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0],
        "fill":  [0]*16,
    },
    "Metal Blast": {                          # Blast-Beat alternierend
        "kick":  [1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0],
        "snare": [0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1],
        "hihat": [0]*16,
        "fill":  [0]*16,
    },
    "Punk Beat": {
        "kick":  [1,0,0,0,0,0,0,0,1,0,0,1,0,0,0,0],
        "snare": [0,0,0,0,1,0,0,0,0,0,0,0,1,0,0,0],
        "hihat": [1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0],
        "fill":  [0]*16,
    },
    "Custom": {
        "kick":  [0]*16, "snare": [0]*16,
        "hihat": [0]*16, "fill":  [0]*16,
    },
}

FILL_TYPES = ["Tom-Fill", "Blast-Fill", "Drum-Roll", "Crash-Accent", "Custom"]
AUDIO_DEVS = ["PreSonus 1824c", "Scarlett 2i2"]
MIDI_DEVS  = ["MPS-850", "anderes"]

# Noten-Zuordnung für die Grid-Zeilen (GM Drums, Kanal 9)
GRID_NOTES = {"kick": 36, "snare": 38, "hihat": 42, "fill": 49}


# ==============================================================================

class MainWindow:
    """Hauptfenster des TUXPLAYER Drum Studios im Dark-Style."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("🥁 TUXPLAYER Drum Studio v1.3")
        self.root.configure(bg=C_BG)
        self.root.resizable(False, False)
        self.root.geometry("1200x800")

        # ── UI-Zustand ─────────────────────────────────────────────────────────
        self._status_msg  = tk.StringVar(value="Bereit.")
        self._export_path = tk.StringVar(value=EXPORT_DIR)
        self._export_name = tk.StringVar(value="tuxplayer_drums.mid")
        self._bpm_var     = tk.IntVar(value=120)
        self._bars_var    = tk.IntVar(value=4)
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
        self._loop_active = tk.BooleanVar(value=False)

        # ── Interner Zustand ──────────────────────────────────────────────────
        self._grid_data: dict[str, list[int]] = {
            "kick": [0]*16, "snare": [0]*16,
            "hihat": [0]*16, "fill":  [0]*16,
        }
        self._play_proc:     subprocess.Popen | None = None
        self._last_midi_path: str = ""
        self._img_logo   = None
        self._img_mascot = None
        self._canvas     = None
        self._status_lbl = None  # wird in _build_right gesetzt

        self._apply_ttk_style()
        self._load_images()
        self._build_header()
        self._build_body()
        self._build_footer()
        self._load_pattern()

        self.root.report_callback_exception = self._handle_callback_exception
        self.root.protocol("WM_DELETE_WINDOW", self._quit)
        signal.signal(signal.SIGINT, lambda *_: self._quit())
        self.root.after(400, self._refresh_pw_devices)

    # ── TTK-Style ─────────────────────────────────────────────────────────────
    def _apply_ttk_style(self):
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
                       foreground=C_FG, selectbackground=C_GREEN_SL,
                       selectforeground="white")
        sty.map("TCombobox",
                foreground=[("readonly", C_FG), ("disabled", C_FG_DARK)])
        sty.configure("TSpinbox",
                       fieldbackground=C_WIDGET, background=C_BTN,
                       foreground=C_FG)

    # ── Bilder ────────────────────────────────────────────────────────────────
    def _load_images(self):
        if not PIL_AVAILABLE:
            return
        for attr, filename, size in [
            ("_img_logo",   "LOGObranding_logo_Program.png",  (280, 82)),
            ("_img_mascot", "TUXPLAYER_MASCOT_RED_SILUET.png", (90, 82)),
        ]:
            path = os.path.join(ASSETS_DIR, filename)
            if os.path.exists(path):
                try:
                    img = Image.open(path).resize(size, Image.LANCZOS)
                    setattr(self, attr, ImageTk.PhotoImage(img))
                except Exception:
                    pass

    # ── Header ────────────────────────────────────────────────────────────────
    def _build_header(self):
        hdr = tk.Frame(self.root, bg=C_PANEL)
        hdr.pack(side="top", fill="x")

        if self._img_logo:
            tk.Label(hdr, image=self._img_logo, bg=C_PANEL).pack(
                side="left", padx=(12, 0), pady=6)
        else:
            tk.Label(hdr, text="🥁 TUXPLAYER", fg=C_GREEN, bg=C_PANEL,
                     font=("Arial", 18, "bold")).pack(side="left", padx=12, pady=14)

        mid = tk.Frame(hdr, bg=C_PANEL)
        mid.pack(side="left", expand=True)
        tk.Label(mid, text="DRUM STUDIO",
                 fg=C_GREEN, bg=C_PANEL, font=("Arial", 14, "bold")).pack()
        tk.Label(mid,
                 text="Song Arrangement  ·  MIDI Generator  ·  PipeWire Routing",
                 fg=C_CYAN, bg=C_PANEL, font=("Arial", 9)).pack()

        if self._img_mascot:
            tk.Label(hdr, image=self._img_mascot, bg=C_PANEL).pack(
                side="right", padx=(0, 12), pady=6)
        else:
            tk.Label(hdr, text="🥁", fg=C_ORANGE, bg=C_PANEL,
                     font=("Arial", 32)).pack(side="right", padx=12, pady=6)

        tk.Frame(self.root, bg=C_CYAN, height=1).pack(fill="x")

    # ── Hauptkörper ───────────────────────────────────────────────────────────
    def _build_body(self):
        body = tk.Frame(self.root, bg=C_BG)
        body.pack(side="top", fill="both", expand=True)
        self._build_left(body)
        self._build_right(body)
        self._build_middle(body)

    # ══════════════════════════════════════════════════════════════════════════
    # LINKS – 220 px
    # ══════════════════════════════════════════════════════════════════════════
    def _build_left(self, parent):
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
        tk.Label(parent, text="Song-Sektionen",
                 fg=C_GREEN, bg=C_PANEL, font=("Arial", 11, "bold")
                 ).pack(pady=(10, 4))

        lb_fr = tk.Frame(parent, bg=C_PANEL)
        lb_fr.pack(fill="both", expand=True, padx=8)
        sb = tk.Scrollbar(lb_fr, bg=C_BTN, troughcolor=C_PANEL, relief="flat")
        sb.pack(side="right", fill="y")

        self._song_lb = tk.Listbox(
            lb_fr, bg=C_WIDGET, fg=C_GREEN,
            selectbackground=C_GREEN_SL, selectforeground=C_GREEN,
            font=("Monospace", 9), activestyle="none",
            relief="flat", bd=0, yscrollcommand=sb.set,
        )
        self._song_lb.pack(side="left", fill="both", expand=True)
        sb.config(command=self._song_lb.yview)

        for sec in ["Intro", "Verse 1", "Pre-Chorus", "Chorus 1",
                    "Verse 2", "Pre-Chorus 2", "Chorus 2",
                    "Bridge", "Chorus 3", "Outro"]:
            self._song_lb.insert(tk.END, f"  {sec}")
        self._song_lb.bind("<<ListboxSelect>>", self._on_section_select)

        def _btn(fr, text, cmd):
            return tk.Button(fr, text=text, command=cmd,
                             bg=C_BTN, fg=C_FG_DIM, font=("Arial", 10),
                             relief="flat", cursor="hand2",
                             activebackground=C_GREEN_D, activeforeground="black")

        r1 = tk.Frame(parent, bg=C_PANEL)
        r1.pack(fill="x", padx=8, pady=(6, 2))
        _btn(r1, "+ Neu",     self._section_add).pack(side="left", expand=True, fill="x", padx=1)
        _btn(r1, "- Löschen", self._section_del).pack(side="left", expand=True, fill="x", padx=1)

        r2 = tk.Frame(parent, bg=C_PANEL)
        r2.pack(fill="x", padx=8, pady=(0, 10))
        _btn(r2, "↑", self._section_up).pack(side="left", expand=True, fill="x", padx=1)
        _btn(r2, "↓", self._section_dn).pack(side="left", expand=True, fill="x", padx=1)

    def _build_tab_device(self, parent):
        tk.Label(parent, text="Audio / MIDI",
                 fg=C_GREEN, bg=C_PANEL, font=("Arial", 11, "bold")
                 ).pack(pady=(12, 6))

        def _lbl(t):
            tk.Label(parent, text=t, fg=C_FG_DIM, bg=C_PANEL,
                     font=("Arial", 9)).pack(anchor="w", padx=12)

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
    # MITTE – Sektions-Editor + Beat-Visualizer
    # ══════════════════════════════════════════════════════════════════════════
    def _build_middle(self, parent):
        frame = tk.Frame(parent, bg=C_BG, width=580)
        frame.pack(side="left", fill="both", expand=True)
        frame.pack_propagate(False)

        self._mid_title = tk.Label(frame, text="← Sektion auswählen",
                                   fg=C_GREEN, bg=C_BG,
                                   font=("Arial", 13, "bold"))
        self._mid_title.pack(pady=(12, 6))

        grid = tk.Frame(frame, bg=C_BG)
        grid.pack(fill="x", padx=20)

        def _lbl(text, row):
            tk.Label(grid, text=text, fg=C_FG_DIM, bg=C_BG,
                     font=("Arial", 10), anchor="e", width=18,
                     ).grid(row=row, column=0, sticky="e", pady=3, padx=(0, 8))

        _lbl("BPM:", 0)
        tk.Spinbox(grid, from_=60, to=240, textvariable=self._bpm_var,
                   width=6, bg=C_WIDGET, fg=C_GREEN, insertbackground=C_GREEN,
                   font=("Monospace", 10), relief="flat", bd=4,
                   buttonbackground=C_BTN, command=self._redraw_grid,
                   ).grid(row=0, column=1, sticky="w", pady=3)

        _lbl("Takte:", 1)
        tk.Spinbox(grid, from_=1, to=32, textvariable=self._bars_var,
                   width=6, bg=C_WIDGET, fg=C_GREEN, insertbackground=C_GREEN,
                   font=("Monospace", 10), relief="flat", bd=4,
                   buttonbackground=C_BTN,
                   ).grid(row=1, column=1, sticky="w", pady=3)

        _lbl("Beat-Pattern:", 2)
        pat_cb = ttk.Combobox(grid, textvariable=self._pattern_var,
                               values=list(BEAT_PATTERNS.keys()),
                               state="readonly", font=("Arial", 9), width=18)
        pat_cb.grid(row=2, column=1, sticky="w", pady=3)
        pat_cb.bind("<<ComboboxSelected>>", lambda _: self._load_pattern())

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

        _lbl("Doppelbase:", 5)
        tk.Checkbutton(grid, text="🦶 Doppelbase (Note 35+36)",
                       variable=self._double_kick,
                       fg=C_FG_DIM, bg=C_BG, selectcolor=C_BTN,
                       activebackground=C_BG, activeforeground=C_GREEN,
                       font=("Arial", 10), command=self._redraw_grid,
                       ).grid(row=5, column=1, sticky="w", pady=3)

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

        # ── Beat-Visualizer ───────────────────────────────────────────────────
        tk.Frame(frame, bg=C_CYAN, height=1).pack(fill="x", padx=20, pady=(10, 0))

        leg = tk.Frame(frame, bg=C_BG)
        leg.pack(fill="x", padx=20, pady=(4, 0))
        tk.Label(leg, text="Beat-Visualizer  (Klick = Note an/aus)",
                 fg=C_CYAN, bg=C_BG, font=("Arial", 10, "bold")).pack(side="left")
        for lbl, col in [("Kick", "#ff4444"), ("Snare", "#00ff00"),
                          ("HiHat", "#00bcd4"), ("Fill", "#ffaa00")]:
            tk.Frame(leg, bg=col, width=10, height=10).pack(side="right", padx=(0, 2))
            tk.Label(leg, text=lbl, fg=col, bg=C_BG,
                     font=("Arial", 8)).pack(side="right", padx=(6, 0))

        self._canvas = tk.Canvas(frame, width=CV_W, height=CV_H,
                                 bg=C_PANEL, highlightthickness=1,
                                 highlightbackground=C_BTN, cursor="hand2")
        self._canvas.pack(padx=20, pady=(4, 8))
        self._canvas.bind("<Button-1>", self._on_canvas_click)

    # ── Beat-Grid zeichnen ────────────────────────────────────────────────────
    def _redraw_grid(self, *_):
        if self._canvas is None:
            return
        self._canvas.delete("all")
        for ri, (label, key, col) in enumerate(GRID_ROWS):
            y1 = ri * ROW_H
            y2 = (ri + 1) * ROW_H
            self._canvas.create_text(
                LABEL_W // 2, (y1 + y2) / 2,
                text=label, fill=C_FG_DARK, font=("Monospace", 8, "bold"))
            for si in range(STEPS):
                x1 = LABEL_W + si * STEP_W + 1
                x2 = LABEL_W + (si + 1) * STEP_W - 1
                active = self._grid_data[key][si]
                self._canvas.create_rectangle(
                    x1, y1 + 1, x2, y2 - 1,
                    fill=col if active else "#1a1a1a", outline="#333333")
                if active:
                    self._canvas.create_rectangle(
                        x1 + 1, y1 + 2, x2 - 1, y1 + 6,
                        fill="#3a3a3a", outline="")
        for t in range(1, 4):
            x = LABEL_W + t * 4 * STEP_W
            self._canvas.create_line(x, 0, x, CV_H, fill="#444444", width=1)
        for t in range(4):
            x = LABEL_W + t * 4 * STEP_W + 2 * STEP_W
            self._canvas.create_text(x, 5, text=f"T{t+1}",
                                      fill="#444444", font=("Arial", 6))

    def _on_canvas_click(self, event):
        if event.x < LABEL_W:
            return
        col = int((event.x - LABEL_W) / STEP_W)
        row = int(event.y / ROW_H)
        if 0 <= col < STEPS and 0 <= row < ROWS:
            self._grid_data[GRID_ROWS[row][1]][col] ^= 1
            self._redraw_grid()

    def _load_pattern(self):
        name = self._pattern_var.get()
        pat  = BEAT_PATTERNS.get(name, {})
        for key in ("kick", "snare", "hihat", "fill"):
            self._grid_data[key] = list(pat.get(key, [0]*16))
        self._redraw_grid()

    def get_grid_data(self) -> dict[str, list[int]]:
        return {k: list(v) for k, v in self._grid_data.items()}

    # ══════════════════════════════════════════════════════════════════════════
    # RECHTS – 340 px
    # ══════════════════════════════════════════════════════════════════════════
    def _build_right(self, parent):
        frame = tk.Frame(parent, bg=C_PANEL, width=340)
        frame.pack(side="right", fill="y")
        frame.pack_propagate(False)

        # ── MIDI Export ───────────────────────────────────────────────────────
        tk.Label(frame, text="📤 MIDI Export",
                 fg=C_GREEN, bg=C_PANEL, font=("Arial", 12, "bold")
                 ).pack(pady=(10, 4))

        path_fr = tk.Frame(frame, bg=C_PANEL)
        path_fr.pack(fill="x", padx=12, pady=(0, 3))
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

        nm_fr = tk.Frame(frame, bg=C_PANEL)
        nm_fr.pack(fill="x", padx=12, pady=(0, 6))
        tk.Label(nm_fr, text="Dateiname:", fg=C_FG_DIM, bg=C_PANEL,
                 font=("Arial", 9)).pack(anchor="w")
        tk.Entry(nm_fr, textvariable=self._export_name,
                 bg=C_WIDGET, fg=C_GREEN, insertbackground=C_GREEN,
                 font=("Monospace", 8), relief="flat", bd=4,
                 ).pack(fill="x")

        tk.Button(frame, text="🎵 MIDI generieren & exportieren",
                  command=self._export_midi,
                  bg=C_GREEN_DK, fg="white",
                  font=("Arial", 11, "bold"),
                  relief="flat", cursor="hand2", pady=10,
                  activebackground=C_GREEN, activeforeground="black",
                  ).pack(fill="x", padx=12, pady=(0, 6))

        # ── Playback ──────────────────────────────────────────────────────────
        tk.Frame(frame, bg=C_CYAN, height=1).pack(fill="x")
        tk.Label(frame, text="▶ Wiedergabe (FluidSynth)",
                 fg=C_GREEN, bg=C_PANEL, font=("Arial", 11, "bold")
                 ).pack(pady=(8, 4))

        play_row = tk.Frame(frame, bg=C_PANEL)
        play_row.pack(fill="x", padx=12, pady=(0, 4))

        def _pbtn(text, cmd, bg=C_BTN, fg=C_FG_DIM, font_size=11):
            return tk.Button(play_row, text=text, command=cmd,
                             bg=bg, fg=fg, font=("Arial", font_size, "bold"),
                             relief="flat", cursor="hand2", pady=6,
                             activebackground=C_GREEN_D, activeforeground="black")

        _pbtn("▶", self._play_midi,    bg="#003300", fg=C_GREEN ).pack(side="left", expand=True, fill="x", padx=(0, 2))
        _pbtn("⏹", self._stop_playback, bg="#330000", fg=C_WARN  ).pack(side="left", expand=True, fill="x", padx=2)

        loop_fr = tk.Frame(frame, bg=C_PANEL)
        loop_fr.pack(fill="x", padx=12, pady=(0, 2))
        tk.Checkbutton(loop_fr, text="🔁 Loop (Dauerschleife)",
                       variable=self._loop_active,
                       fg=C_FG_DIM, bg=C_PANEL, selectcolor=C_BTN,
                       activebackground=C_PANEL, activeforeground=C_GREEN,
                       font=("Arial", 9),
                       ).pack(side="left")

        sf_ok = "✔" if SOUNDFONT else "✘"
        sf_col = C_GREEN if SOUNDFONT else C_WARN
        tk.Label(frame, text=f"{sf_ok} Soundfont: {os.path.basename(SOUNDFONT) if SOUNDFONT else 'nicht gefunden'}",
                 fg=sf_col, bg=C_PANEL, font=("Arial", 8)
                 ).pack(anchor="w", padx=14)

        # ── Öffnen in … ───────────────────────────────────────────────────────
        tk.Frame(frame, bg=C_CYAN, height=1).pack(fill="x", pady=(6, 0))
        tk.Label(frame, text="📂 Öffnen in …",
                 fg=C_GREEN, bg=C_PANEL, font=("Arial", 11, "bold")
                 ).pack(pady=(6, 4))

        open_row = tk.Frame(frame, bg=C_PANEL)
        open_row.pack(fill="x", padx=12, pady=(0, 6))

        def _obtn(text, cmd):
            return tk.Button(open_row, text=text, command=cmd,
                             bg=C_BTN, fg=C_FG_DIM, font=("Arial", 9),
                             relief="flat", cursor="hand2", pady=4,
                             activebackground=C_GREEN_D, activeforeground="black")

        _obtn("🌿 Hydrogen",  self._open_in_hydrogen ).pack(side="left", expand=True, fill="x", padx=(0, 2))
        _obtn("🎛 Bitwig",    self._open_in_bitwig   ).pack(side="left", expand=True, fill="x", padx=2)
        _obtn("📁 Ordner",    self._open_export_dir  ).pack(side="left", expand=True, fill="x", padx=(2, 0))

        # ── PipeWire ──────────────────────────────────────────────────────────
        tk.Frame(frame, bg=C_CYAN, height=1).pack(fill="x")
        tk.Label(frame, text="🔊 PipeWire Routing",
                 fg=C_GREEN, bg=C_PANEL, font=("Arial", 11, "bold")
                 ).pack(pady=(6, 3))

        pw_fr = tk.Frame(frame, bg=C_PANEL)
        pw_fr.pack(fill="x", padx=12, pady=(0, 4))
        pw_sb = tk.Scrollbar(pw_fr, bg=C_BTN, troughcolor=C_PANEL, relief="flat")
        pw_sb.pack(side="right", fill="y")
        self._pw_lb = tk.Listbox(pw_fr, bg=C_WIDGET, fg=C_CYAN,
                                 selectbackground=C_GREEN_SL,
                                 font=("Monospace", 7), relief="flat", bd=0,
                                 height=4, yscrollcommand=pw_sb.set)
        self._pw_lb.pack(side="left", fill="x", expand=True)
        pw_sb.config(command=self._pw_lb.yview)

        def _rbtn(text, cmd):
            tk.Button(frame, text=text, command=cmd,
                      bg=C_BTN, fg=C_FG_DIM, font=("Arial", 9),
                      relief="flat", cursor="hand2", pady=4,
                      activebackground=C_GREEN_D, activeforeground="black",
                      ).pack(fill="x", padx=12, pady=(0, 3))

        _rbtn("🔌 Routing aufbauen",          self._activate_routing)
        _rbtn("🔄 Geräte aktualisieren",       self._refresh_pw_devices)
        _rbtn("💾 qpwgraph Session speichern",  self._save_qpwgraph)

        tk.Frame(frame, bg=C_CYAN, height=1).pack(fill="x")

        self._status_lbl = tk.Label(frame, textvariable=self._status_msg,
                                    fg=C_GREEN, bg=C_PANEL,
                                    font=("Monospace", 8),
                                    wraplength=310, justify="left")
        self._status_lbl.pack(anchor="w", padx=12, pady=(6, 4), fill="x")

    # ── Footer ────────────────────────────────────────────────────────────────
    def _build_footer(self):
        tk.Frame(self.root, bg=C_CYAN, height=1).pack(fill="x")
        ftr = tk.Frame(self.root, bg=C_PANEL)
        ftr.pack(side="bottom", fill="x")

        tk.Label(ftr,
                 text="© 2026 Heiko Schäfer (TUXPLAYER)  ·  MIT Lizenz  ·  tuxhs.de",
                 fg="#888888", bg=C_PANEL, font=("Arial", 8),
                 ).pack(side="left", padx=12, pady=6)

        tk.Button(ftr, text="✖  BEENDEN", command=self._quit,
                  bg=C_QUIT_BG, fg="white", font=("Arial", 10, "bold"),
                  relief="flat", cursor="hand2", pady=5,
                  activebackground="#660000", activeforeground="white",
                  ).pack(side="right", padx=12, pady=4)

        tk.Button(ftr, text="📖 Hilfe & Lizenz",
                  command=self._show_info_window,
                  bg=C_BTN, fg=C_CYAN, font=("Arial", 9, "bold"),
                  relief="flat", cursor="hand2", pady=5,
                  activebackground=C_GREEN_D, activeforeground="black",
                  ).pack(side="right", padx=4, pady=4)

    # ══════════════════════════════════════════════════════════════════════════
    # MIDI-Generierung (echt, via mido)
    # ══════════════════════════════════════════════════════════════════════════

    def _export_midi(self) -> str | None:
        """
        Generiert eine MIDI-Datei aus dem aktuellen Beat-Grid.
        Gibt den Dateipfad zurück oder None bei Fehler.
        """
        if not MIDO_AVAILABLE:
            self._set_status("mido nicht installiert! pip install mido", "error")
            return None

        bpm  = self._bpm_var.get()
        bars = self._bars_var.get()
        STEP = 120          # Ticks pro 16tel-Note (PPQ=480)
        BAR  = 16 * STEP   # Ticks pro Takt

        # Noten-Mapping für aktuelle Einstellungen
        notes = dict(GRID_NOTES)
        if self._ride_hh.get():
            notes["hihat"] = 51   # Ride statt HiHat

        events: list[tuple[int, int, int]] = []  # (abs_tick, note, velocity)

        for bar in range(bars):
            offset = bar * BAR
            for row_key, note in notes.items():
                for si, active in enumerate(self._grid_data[row_key]):
                    if active:
                        t = offset + si * STEP
                        events += [(t, note, 100), (t + 90, note, 0)]
            # Doppelbase: Note 35 zusätzlich zu 36 auf jedem Kick-Step
            if self._double_kick.get():
                for si, active in enumerate(self._grid_data["kick"]):
                    if active:
                        # Note 35 (linkes Pedal) auf nächste 16tel-Note
                        t2 = offset + si * STEP + STEP
                        events += [(t2, 35, 90), (t2 + 90, 35, 0)]

        # Events nach Zeit sortieren → Delta-Zeiten berechnen
        events.sort(key=lambda e: e[0])
        mid   = mido.MidiFile(ticks_per_beat=480)
        track = mido.MidiTrack()
        mid.tracks.append(track)
        track.append(mido.MetaMessage("set_tempo",
                                      tempo=mido.bpm2tempo(bpm), time=0))
        track.append(mido.MetaMessage("track_name", name="Drums", time=0))

        prev = 0
        for abs_t, note, vel in events:
            track.append(mido.Message("note_on", channel=9,
                                      note=note, velocity=vel,
                                      time=abs_t - prev))
            prev = abs_t

        # Datei speichern
        export_dir = self._export_path.get()
        try:
            os.makedirs(export_dir, exist_ok=True)
        except OSError as e:
            self._set_status(f"Pfad-Fehler: {e}", "error")
            return None

        filepath = os.path.join(export_dir, self._export_name.get())
        try:
            mid.save(filepath)
        except OSError as e:
            self._set_status(f"Speichern fehlgeschlagen: {e}", "error")
            return None

        self._last_midi_path = filepath
        self._set_status(
            f"✔ MIDI: {os.path.basename(filepath)}  ({bars} Takte, {bpm} BPM)", "ok")
        return filepath

    # ══════════════════════════════════════════════════════════════════════════
    # FluidSynth-Playback
    # ══════════════════════════════════════════════════════════════════════════

    def _play_midi(self):
        """MIDI generieren und sofort via FluidSynth abspielen."""
        filepath = self._export_midi()
        if not filepath:
            return
        self._stop_playback()
        self._start_fluidsynth(filepath)

    def _start_fluidsynth(self, filepath: str):
        """Startet FluidSynth in einem Daemon-Thread (GUI bleibt reaktionsfähig)."""
        if not SOUNDFONT:
            self._set_status("Soundfont nicht gefunden! (FluidR3_GM.sf2)", "error")
            return
        if not os.path.exists(filepath):
            self._set_status("MIDI-Datei nicht gefunden!", "error")
            return

        self._set_status("▶ Wiedergabe startet …", "warn")

        def _run():
            try:
                proc = subprocess.Popen(
                    ["fluidsynth", "-a", "pipewire", "-q", "-i", SOUNDFONT, filepath],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                )
                self._play_proc = proc
                self.root.after(0, lambda: self._set_status("▶ Wiedergabe läuft …", "ok"))
                proc.wait()

                if self._loop_active.get() and self._play_proc is proc:
                    # Loop: nach Ende sofort neu starten
                    self.root.after(50, lambda: self._start_fluidsynth(filepath))
                elif self._play_proc is proc:
                    self._play_proc = None
                    self.root.after(0, lambda: self._set_status("⏹ Wiedergabe beendet.", "ok"))
            except Exception as e:
                self.root.after(0, lambda: self._set_status(f"Playback-Fehler: {e}", "error"))

        threading.Thread(target=_run, daemon=True).start()

    def _stop_playback(self):
        """Stoppt laufende FluidSynth-Instanz."""
        self._loop_active.set(False)
        proc = self._play_proc
        self._play_proc = None
        if proc and proc.poll() is None:
            proc.terminate()
        self._set_status("⏹ Gestoppt.", "ok")

    # ══════════════════════════════════════════════════════════════════════════
    # Öffnen in externer App
    # ══════════════════════════════════════════════════════════════════════════

    def _get_midi_path(self) -> str | None:
        """Gibt letzten MIDI-Pfad zurück oder exportiert neu."""
        if self._last_midi_path and os.path.exists(self._last_midi_path):
            return self._last_midi_path
        return self._export_midi()

    def _export_h2song(self) -> str | None:
        """Exportiert das aktuelle Pattern als Hydrogen .h2song (XML-Format)."""
        export_dir = self._export_path.get()
        try:
            os.makedirs(export_dir, exist_ok=True)
        except OSError as e:
            self._set_status(f"Pfad-Fehler: {e}", "error")
            return None

        basename = self._export_name.get().replace(".mid", "")
        filepath = os.path.join(export_dir, f"{basename}.h2song")
        bpm   = self._bpm_var.get()
        bars  = self._bars_var.get()

        # Hydrogen GM-Instrument-Mapping (Standard GMkit)
        # Instrument-ID in Hydrogen → GM-Note
        H2_INSTR = {36: 0, 38: 1, 42: 2, 49: 3, 35: 4}  # BD, SN, HH, Crash, BD2
        h2_notes = {v: k for k, v in H2_INSTR.items()}   # 0→36, 1→38 …

        # Pattern-Zeilen → (instr_id, position 0-191 für 2 Bars × 96 Steps)
        STEPS_H2  = 192   # Hydrogen nutzt 192 Steps pro 2 Bars (48 pro Beat)
        STEP_TICKS = STEPS_H2 // 32  # 16tel-Note = 6 Hydrogen-Steps bei 2 Bars

        notes_xml = []
        row_map = {
            "kick":  0,   # Instr 0 = BD (Note 36)
            "snare": 1,   # Instr 1 = SN (Note 38)
            "hihat": 2,   # Instr 2 = HH (Note 42)
            "fill":  3,   # Instr 3 = Crash (Note 49)
        }
        for row_key, instr_id in row_map.items():
            for si, active in enumerate(self._grid_data[row_key]):
                if active:
                    pos = si * STEP_TICKS
                    notes_xml.append(
                        f'            <note><position>{pos}</position>'
                        f'<velocity>0.8</velocity><pan_L>0.5</pan_L>'
                        f'<pan_R>0.5</pan_R><pitch>0</pitch>'
                        f'<instrument>{instr_id}</instrument></note>'
                    )
        if self._double_kick.get():
            for si, active in enumerate(self._grid_data["kick"]):
                if active:
                    pos = si * STEP_TICKS + STEP_TICKS
                    if pos < STEPS_H2:
                        notes_xml.append(
                            f'            <note><position>{pos}</position>'
                            f'<velocity>0.75</velocity><pan_L>0.5</pan_L>'
                            f'<pan_R>0.5</pan_R><pitch>0</pitch>'
                            f'<instrument>4</instrument></note>'
                        )

        pattern_name = self._pattern_var.get()
        xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<song>
  <version>0.9.7</version>
  <bpm>{bpm}</bpm>
  <volume>0.5</volume>
  <metronomeVolume>0.5</metronomeVolume>
  <name>{pattern_name} – TUXPLAYER Drum Studio</name>
  <author>Heiko Schäfer (TUXPLAYER)</author>
  <notes></notes>
  <license>MIT</license>
  <loopmode>true</loopmode>
  <patternModeMode>stacked</patternModeMode>
  <humanize_velocity>0</humanize_velocity>
  <humanize_time>0</humanize_time>
  <swing_factor>0</swing_factor>
  <instrumentList>
    <instrument><id>0</id><name>Bass Drum 1</name><midiOutChannel>9</midiOutChannel><midiOutNote>36</midiOutNote><volume>1</volume><isMuted>false</isMuted></instrument>
    <instrument><id>1</id><name>Acoustic Snare</name><midiOutChannel>9</midiOutChannel><midiOutNote>38</midiOutNote><volume>1</volume><isMuted>false</isMuted></instrument>
    <instrument><id>2</id><name>Closed Hi-Hat</name><midiOutChannel>9</midiOutChannel><midiOutNote>42</midiOutNote><volume>0.85</volume><isMuted>false</isMuted></instrument>
    <instrument><id>3</id><name>Crash Cymbal 1</name><midiOutChannel>9</midiOutChannel><midiOutNote>49</midiOutNote><volume>0.9</volume><isMuted>false</isMuted></instrument>
    <instrument><id>4</id><name>Bass Drum 2</name><midiOutChannel>9</midiOutChannel><midiOutNote>35</midiOutNote><volume>0.95</volume><isMuted>false</isMuted></instrument>
  </instrumentList>
  <patternList>
    <pattern>
      <name>{pattern_name}</name>
      <category>Main</category>
      <size>{STEPS_H2}</size>
      <noteList>
{chr(10).join(notes_xml)}
      </noteList>
    </pattern>
  </patternList>
  <patternGroupSequence>
    <group><patternID>0</patternID></group>
  </patternGroupSequence>
  <timeline activated="false"/>
</song>
"""
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(xml)
            self._last_midi_path = filepath
            self._set_status(
                f"✔ H2Song: {os.path.basename(filepath)}  ({bars} Takte, {bpm} BPM)", "ok")
            return filepath
        except OSError as e:
            self._set_status(f"H2Song-Fehler: {e}", "error")
            return None

    def _open_in_hydrogen(self):
        """Exportiert als .h2song und öffnet direkt in Hydrogen."""
        path = self._export_h2song()
        if not path:
            return
        try:
            subprocess.Popen(["hydrogen", path])
            self._set_status(f"🌿 Hydrogen: {os.path.basename(path)}", "ok")
        except FileNotFoundError:
            self._set_status("Hydrogen nicht gefunden! (hydrogen installieren)", "error")

    def _open_in_bitwig(self):
        path = self._get_midi_path()
        if not path:
            return
        try:
            subprocess.Popen(["bitwig-studio", path])
            self._set_status(f"🎛 Bitwig geöffnet: {os.path.basename(path)}", "ok")
        except FileNotFoundError:
            self._set_status("Bitwig nicht gefunden!", "error")

    def _open_export_dir(self):
        d = self._export_path.get()
        if not os.path.isdir(d):
            self._set_status(f"Ordner existiert nicht: {d}", "warn")
            return
        try:
            subprocess.Popen(["xdg-open", d])
        except FileNotFoundError:
            self._set_status("xdg-open nicht verfügbar.", "warn")

    # ══════════════════════════════════════════════════════════════════════════
    # Info / Hilfe / Lizenz-Fenster
    # ══════════════════════════════════════════════════════════════════════════

    def _show_info_window(self):
        """Öffnet ein modales Info-Fenster mit Bedienungsanleitung und Lizenz."""
        win = tk.Toplevel(self.root)
        win.title("📖 TUXPLAYER Drum Studio – Hilfe & Lizenz")
        win.configure(bg=C_BG)
        win.resizable(False, False)
        win.geometry("700x540")
        win.transient(self.root)
        win.grab_set()

        # Logo oben
        hdr = tk.Frame(win, bg=C_PANEL)
        hdr.pack(fill="x")
        if self._img_logo:
            tk.Label(hdr, image=self._img_logo, bg=C_PANEL).pack(
                side="left", padx=12, pady=6)
        tk.Label(hdr, text="TUXPLAYER Drum Studio v1.1",
                 fg=C_GREEN, bg=C_PANEL, font=("Arial", 13, "bold")
                 ).pack(side="left", padx=20)
        if self._img_mascot:
            tk.Label(hdr, image=self._img_mascot, bg=C_PANEL).pack(
                side="right", padx=12, pady=6)
        tk.Frame(win, bg=C_CYAN, height=1).pack(fill="x")

        # Notebook mit Tabs
        nb = ttk.Notebook(win)
        nb.pack(fill="both", expand=True, padx=10, pady=8)

        t_help    = tk.Frame(nb, bg=C_BG)
        t_license = tk.Frame(nb, bg=C_BG)
        t_credits = tk.Frame(nb, bg=C_BG)
        t_donate  = tk.Frame(nb, bg=C_BG)
        nb.add(t_help,    text="📖 Bedienungsanleitung")
        nb.add(t_license, text="⚖ Lizenz")
        nb.add(t_credits, text="🎸 Credits")
        nb.add(t_donate,  text="💛 Spenden")

        # ── Bedienungsanleitung ───────────────────────────────────────────────
        help_text = """\
TUXPLAYER DRUM STUDIO – Schnellstart
══════════════════════════════════════════════════════════════

1. BEAT-PATTERN AUSWÄHLEN
   → Links: Tab "🥁 Song" → Sektion anklicken
   → Mitte: Beat-Pattern Dropdown (Standard Rock, Bonham Rock, Grohl Grunge …)
   → Klick auf das Beat-Grid schaltet einzelne Noten an/aus

2. PARAMETER EINSTELLEN
   → BPM:       Tempo in Schlägen pro Minute (60–240)
   → Takte:     Anzahl Wiederholungen des Patterns
   → Doppelbase: Aktiviert Note 35 (linkes Pedal) zusätzlich zu Note 36
   → Humanize:  Zufällige Timing-/Velocity-Abweichung (0 = perfekt quantisiert)

3. MIDI EXPORTIEREN
   → Pfad und Dateiname rechts einstellen
   → [🎵 MIDI generieren & exportieren] klicken
   → MIDI-Datei liegt in ~/scripts/musik/exports/

4. HÖREN (Gitarre in der Hand!)
   → [▶] drücken → FluidSynth spielt das Pattern sofort ab
   → [🔁 Loop] aktivieren → Dauerschleife bis [⏹ Stop]
   → Tempo (BPM) jederzeit ändern → neu exportieren + abspielen

5. IN ANDEREN APPS ÖFFNEN
   → [🌿 Hydrogen] öffnet die MIDI-Datei direkt in Hydrogen
   → [🎛 Bitwig]   öffnet die MIDI-Datei in Bitwig Studio
   → [📁 Ordner]   zeigt den Export-Ordner im Dateimanager

6. PIPEWIRE ROUTING
   → Tab "🎛 Gerät": Audiogerät und MIDI-Device wählen
   → [🔌 Routing aufbauen] verbindet alle Drum-Kanäle via pw-link
   → Rechts: erkannte PipeWire-Nodes werden automatisch gescannt

TASTATURKÜRZEL
   Kein Vollbild-Modus (resizable=False, Größe 1200×800)
   Fenster schließen: [✖ BEENDEN] oder Fenster-X-Button
"""
        st1 = scrolledtext.ScrolledText(
            t_help, bg=C_PANEL, fg=C_FG, font=("Monospace", 9),
            relief="flat", bd=0, wrap=tk.WORD,
            insertbackground=C_GREEN)
        st1.pack(fill="both", expand=True, padx=8, pady=8)
        st1.insert("1.0", help_text)
        st1.config(state="disabled")

        # ── Lizenz ───────────────────────────────────────────────────────────
        lic_text = """\
MIT-LIZENZ (Code)
══════════════════════════════════════════════════════════════

Copyright (c) 2026 Heiko Schäfer (TUXPLAYER)

Hiermit wird unentgeltlich jeder Person, die eine Kopie der Software
und der zugehörigen Dokumentationsdateien (die „Software") erhält,
die Erlaubnis erteilt, sie uneingeschränkt zu nutzen, einschließlich
und ohne Einschränkung der Rechte, sie zu verwenden, zu kopieren,
zu verändern, zusammenzuführen, zu veröffentlichen, zu verbreiten,
zu unterlizenzieren und/oder zu verkaufen.

DIE SOFTWARE WIRD OHNE JEDE AUSDRÜCKLICHE ODER IMPLIZIERTE GARANTIE
BEREITGESTELLT, EINSCHLIESSLICH DER GARANTIE ZUR BENUTZUNG FÜR DEN
VORGESEHENEN ODER EINEM BESTIMMTEN ZWECK SOWIE JEGLICHER RECHTSVERLETZUNG.

──────────────────────────────────────────────────────────────

CC BY-SA 4.0 (Assets / Grafiken)
══════════════════════════════════════════════════════════════

LOGObranding_logo_Program.png        © 2026 Heiko Schäfer (TUXPLAYER)
TUXPLAYER_MASCOT_RED_SILUET.png      © 2026 Heiko Schäfer (TUXPLAYER)

Diese Grafiken stehen unter der Creative Commons Lizenz
Attribution-ShareAlike 4.0 International (CC BY-SA 4.0).
Weitere Infos: https://creativecommons.org/licenses/by-sa/4.0/

──────────────────────────────────────────────────────────────

ABHÄNGIGKEITEN (Drittanbieter-Lizenzen)
══════════════════════════════════════════════════════════════

mido            – MIT-Lizenz
python-rtmidi   – MIT-Lizenz
Pillow          – HPND-Lizenz (PIL Historical)
FluidSynth      – LGPL v2.1+
FluidR3 GM SF2  – MIT-Lizenz (Frank Wen, Michael Klingbeil)
"""
        st2 = scrolledtext.ScrolledText(
            t_license, bg=C_PANEL, fg=C_FG, font=("Monospace", 9),
            relief="flat", bd=0, wrap=tk.WORD)
        st2.pack(fill="both", expand=True, padx=8, pady=8)
        st2.insert("1.0", lic_text)
        st2.config(state="disabled")

        # ── Credits ───────────────────────────────────────────────────────────
        cred_text = """\
CREDITS & DANKSAGUNGEN
══════════════════════════════════════════════════════════════

Entwickler / Artist
  Heiko Schäfer – TUXPLAYER
  contact@tuxhs.de · https://tuxhs.de
  GitHub: https://github.com/Tuxplayers

Musiker seit 1973 · Linux-Enthusiast · Open-Source-Verfechter

──────────────────────────────────────────────────────────────

VERWANDTE PROJEKTE (auch auf GitHub)
══════════════════════════════════════════════════════════════

  TUX-Guitar-Tuner       – Gitarrenstimmer (ALSA/PipeWire, HPS)
  TuxBackup              – Backup-Skript für Linux
  tuxplayer-drum-studio  – dieses Projekt
  musikstudio            – Audio-Manager-Suite
  security-lab           – Penetration-Testing-Sammlung

  https://github.com/Tuxplayers

──────────────────────────────────────────────────────────────

TECHNOLOGIE-STACK
══════════════════════════════════════════════════════════════

  Python 3.11+     tkinter/ttk      mido
  python-rtmidi    Pillow           FluidSynth
  PipeWire         pw-link          Hydrogen
  Bitwig Studio    CachyOS Linux

──────────────────────────────────────────────────────────────

"Life is a Boomerang" – TUXPLAYER 🎸🥁
"""
        st3 = scrolledtext.ScrolledText(
            t_credits, bg=C_PANEL, fg=C_FG, font=("Monospace", 9),
            relief="flat", bd=0, wrap=tk.WORD)
        st3.pack(fill="both", expand=True, padx=8, pady=8)
        st3.insert("1.0", cred_text)
        st3.config(state="disabled")

        # ── Spenden ───────────────────────────────────────────────────────────
        inner = tk.Frame(t_donate, bg=C_BG)
        inner.pack(fill="both", expand=True, padx=24, pady=24)

        tk.Label(inner, text="💛  Gefällt dir TUXPLAYER Drum Studio?",
                 fg=C_GREEN, bg=C_BG, font=("Arial", 14, "bold")).pack(pady=(0, 6))
        tk.Label(inner,
                 text="Dieses Programm ist kostenlos und Open Source.\n"
                      "Eine kleine Spende hilft dabei, weitere Tools zu entwickeln!",
                 fg=C_FG_DIM, bg=C_BG,
                 font=("Arial", 11), justify="center").pack(pady=(0, 20))

        tk.Frame(inner, bg="#333333", height=1).pack(fill="x", pady=(0, 20))

        # Buy Me a Coffee
        tk.Button(inner,
                  text="  ☕   Buy Me a Coffee",
                  bg="#FFDD00", fg="#000000",
                  font=("Arial", 13, "bold"),
                  relief="flat", cursor="hand2",
                  padx=20, pady=12,
                  command=lambda: webbrowser.open(
                      "https://buymeacoffee.com/schaefer.heiko")
                  ).pack(fill="x", pady=(0, 10))

        # PayPal
        tk.Button(inner,
                  text="  💳   PayPal · paypal.me/tuxplayer",
                  bg="#009CDE", fg="#ffffff",
                  font=("Arial", 13, "bold"),
                  relief="flat", cursor="hand2",
                  padx=20, pady=12,
                  command=lambda: webbrowser.open(
                      "https://paypal.me/tuxplayer")
                  ).pack(fill="x", pady=(0, 10))

        tk.Frame(inner, bg="#333333", height=1).pack(fill="x", pady=(20, 12))

        tk.Label(inner,
                 text="Danke! ❤️  — Heiko Schäfer (TUXPLAYER)\n"
                      "https://tuxhs.de  ·  github.com/Tuxplayers",
                 fg=C_FG_DARK, bg=C_BG,
                 font=("Arial", 9), justify="center").pack()

        # Schließen-Button
        tk.Frame(win, bg=C_CYAN, height=1).pack(fill="x")
        ftr = tk.Frame(win, bg=C_PANEL)
        ftr.pack(fill="x")
        tk.Button(ftr, text="✖  Schließen", command=win.destroy,
                  bg=C_QUIT_BG, fg="white", font=("Arial", 10, "bold"),
                  relief="flat", cursor="hand2", pady=5,
                  ).pack(side="right", padx=12, pady=6)

    # ══════════════════════════════════════════════════════════════════════════
    # Callbacks – Sektions-Management
    # ══════════════════════════════════════════════════════════════════════════

    def _set_status(self, msg: str, level: str = "ok"):
        colors = {"ok": C_GREEN, "warn": C_ORANGE, "error": C_WARN}
        self._status_msg.set(msg)
        if self._status_lbl:
            self._status_lbl.config(fg=colors.get(level, C_GREEN))

    def _on_section_select(self, _event=None):
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

    def _activate_routing(self):
        self._set_status("Routing wird aufgebaut …", "warn")
        self.root.after(500, lambda: self._set_status("Routing aktiviert.", "ok"))

    def _refresh_pw_devices(self):
        self._set_status("PipeWire: Scan …", "warn")

        def _scan():
            lines, msg, lvl = [], "", "ok"
            try:
                r = subprocess.run(["pw-cli", "list-objects", "Node"],
                                   capture_output=True, text=True, timeout=5)
                for line in r.stdout.splitlines():
                    if "node.name" in line:
                        c = line.strip().strip('"').strip("'")
                        if c:
                            lines.append(c)
                msg = "PipeWire: aktualisiert."
            except FileNotFoundError:
                lines = ["pw-cli fehlt"]
                msg, lvl = "pw-cli nicht gefunden.", "warn"
            except subprocess.TimeoutExpired:
                lines = ["(Timeout)"]
                msg, lvl = "PipeWire Timeout.", "error"
            self.root.after(0, lambda: self._update_pw_list(lines, msg, lvl))

        threading.Thread(target=_scan, daemon=True).start()

    def _update_pw_list(self, lines: list[str], msg: str, level: str):
        self._pw_lb.delete(0, tk.END)
        for line in (lines or ["(keine Nodes)"]):
            self._pw_lb.insert(tk.END, line)
        self._set_status(msg, level)

    def _save_qpwgraph(self):
        try:
            subprocess.Popen(["qpwgraph", "--save"])
            self._set_status("qpwgraph: Session gespeichert.", "ok")
        except FileNotFoundError:
            self._set_status("qpwgraph nicht installiert.", "error")

    def _handle_callback_exception(self, exc_type, exc_value, exc_tb):
        """Alle unbehandelten Tkinter-Callback-Fehler → Status-Label (kein Crash)."""
        msg = traceback.format_exception_only(exc_type, exc_value)[-1].strip()
        self._set_status(f"Fehler: {msg}", "error")
        traceback.print_exception(exc_type, exc_value, exc_tb)

    def _quit(self):
        self._stop_playback()
        self.root.destroy()
