# ==============================================================================
# PROJEKT      : TUXPLAYER Drum Studio
# AUTOR        : Heiko Schäfer
# ARTIST       : TUXPLAYER
# ERSTELLT     : 2026-04-03
# VERSION      : 1.0.0
# BESCHREIBUNG : SongEditor – Song-Arrangement und Pattern-Sequenzierung
#                (Reserviert für zukünftige eigenständige Ansicht)
# STATUS       : development
# DEPENDENCIES : mido, python-rtmidi, tkinter (system)
# KONTAKT      : contact@tuxhs.de
# WEBSITE      : https://tuxhs.de
# GITHUB       : https://github.com/Tuxplayers
# GIT-USER     : Tuxplayers
# LIZENZ       : MIT (Code) | CC BY-SA 4.0 (Assets)
# CHANGELOG    : 2026-04-03 v1.0.0 – Initiale Version (Platzhalter)
# ==============================================================================

import tkinter as tk
from tkinter import ttk

# Farben (TUXPLAYER Dark-Style)
C_BG    = "#1a1a1a"
C_PANEL = "#0d0d0d"
C_GREEN = "#00ff00"
C_CYAN  = "#00bcd4"


class SongEditor(ttk.Frame):
    """
    Song-Editor-Panel für zukünftige eigenständige Arrangement-Ansicht.
    Aktuelle Song-Logik ist in MainWindow (gui/main_window.py) integriert.
    """

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.configure(style="Dark.TFrame")
        self._build_ui()

    def _build_ui(self):
        """Baut die Platzhalter-UI auf."""
        ttk.Label(self,
                  text="Song Editor",
                  foreground=C_GREEN,
                  background=C_BG,
                  font=("Arial", 13, "bold"),
                  ).pack(expand=True)
