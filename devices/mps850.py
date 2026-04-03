# ==============================================================================
# PROJEKT      : TUXPLAYER Drum Studio
# AUTOR        : Heiko Schäfer
# ARTIST       : TUXPLAYER
# ERSTELLT     : 2026-04-03
# VERSION      : 1.0.0
# BESCHREIBUNG : MPS850Controller – MIDI-Interface für Millenium MPS-850
#                GM-Drum-Mapping, USB-MIDI-Verbindung, Doppelbase-Erkennung
# STATUS       : development
# DEPENDENCIES : mido, python-rtmidi, tkinter (system)
# KONTAKT      : contact@tuxhs.de
# WEBSITE      : https://tuxhs.de
# GITHUB       : https://github.com/Tuxplayers
# GIT-USER     : Tuxplayers
# LIZENZ       : MIT (Code) | CC BY-SA 4.0 (Assets)
# CHANGELOG    : 2026-04-03 v1.0.0 – Initiale Version
#              :   MPS850Controller: connect, detect_double_kick, test_pad
# ==============================================================================

import time
from typing import Callable

try:
    import rtmidi
    RTMIDI_AVAILABLE = True
except ImportError:
    RTMIDI_AVAILABLE = False

# ── GM-Drum-Mapping (Millenium MPS-850, Werkeinstellung, Kanal 9) ─────────────
KICK1        = 36   # Bass Drum 1 (rechtes Pedal)
KICK2        = 35   # Bass Drum 2 (linkes Pedal, Doppelbase)
SNARE        = 38   # Acoustic Snare (Fell)
SNARE_RIM    = 40   # Electric Snare / Rimshot
HIHAT_CLOSED = 42   # Closed Hi-Hat
HIHAT_PEDAL  = 44   # Pedal Hi-Hat
HIHAT_OPEN   = 46   # Open Hi-Hat
TOM1         = 48   # High Tom
TOM2         = 45   # Mid Tom
TOM3         = 43   # Low/Floor Tom
RIDE         = 51   # Ride Cymbal 1
CRASH        = 49   # Crash Cymbal 1

# Mapping: MIDI-Note → Pad-Bezeichnung (für Anzeige / Debugging)
PAD_NAMES: dict[int, str] = {
    KICK1:        "Kick (rechts)",
    KICK2:        "Kick (links / Doppelbase)",
    SNARE:        "Snare",
    SNARE_RIM:    "Snare Rim",
    HIHAT_CLOSED: "HiHat (geschlossen)",
    HIHAT_PEDAL:  "HiHat (Pedal)",
    HIHAT_OPEN:   "HiHat (offen)",
    TOM1:         "Tom 1 (hoch)",
    TOM2:         "Tom 2 (mitte)",
    TOM3:         "Tom 3 (tief/floor)",
    RIDE:         "Ride",
    CRASH:        "Crash",
}

# Port-Erkennungs-Substrings (case-insensitive)
PORT_HINTS = ("MPS", "Millennium", "Millenium", "MPS-850")

# Zeitfenster für Doppelbase-Erkennung (in Sekunden)
DOUBLE_KICK_WINDOW = 0.050   # 50 ms


# ==============================================================================

class MPS850Controller:
    """
    MIDI-Controller für das Millenium MPS-850 E-Drum-Set.

    Alle Statusmeldungen gehen über den optionalen Callback –
    kein direkter GUI-Zugriff, vollständig entkoppelt.
    """

    def __init__(self, status_callback: Callable[[str, str], None] | None = None):
        """
        status_callback: Funktion(msg: str, level: str)
                         level = "ok" | "warn" | "error"
        """
        self._cb         = status_callback or (lambda msg, level="ok": None)
        self._midi_in    = None
        self._connected  = False
        self._port_name  = ""

        # Doppelbase-Tracking: letzter Zeitstempel für Note 35 und 36
        self._last_kick_time: dict[int, float] = {KICK1: 0.0, KICK2: 0.0}

        # Externer Event-Callback (für Note-Empfang)
        self._note_callback: Callable[[int, int], None] | None = None

    # ── Verbindung ────────────────────────────────────────────────────────────

    def connect(self) -> bool:
        """
        Öffnet den USB-MIDI-Port des MPS-850 via python-rtmidi.

        Rückgabe: True bei Erfolg, False wenn kein passender Port gefunden.
        """
        if not RTMIDI_AVAILABLE:
            self._cb("python-rtmidi nicht installiert.", "error")
            return False

        midi_in = rtmidi.MidiIn()
        ports   = midi_in.get_ports()

        if not ports:
            self._cb("Keine MIDI-Eingänge gefunden.", "warn")
            midi_in.delete()
            return False

        for i, name in enumerate(ports):
            if any(hint.lower() in name.lower() for hint in PORT_HINTS):
                midi_in.open_port(i)
                midi_in.set_callback(self._midi_callback)
                midi_in.ignore_types(sysex=True, timing=True, active_sense=True)
                self._midi_in   = midi_in
                self._connected = True
                self._port_name = name
                self._cb(f"MPS-850 verbunden: {name}", "ok")
                return True

        # Kein passender Port gefunden – alle verfügbaren Ports melden
        port_list = ", ".join(ports) if ports else "(keine)"
        self._cb(
            f"MPS-850 nicht gefunden. Verfügbare Ports: {port_list}", "warn")
        midi_in.delete()
        return False

    def disconnect(self):
        """Schließt den MIDI-Port und gibt Ressourcen frei."""
        if self._midi_in is not None:
            try:
                self._midi_in.close_port()
                self._midi_in.delete()
            except Exception:
                pass
            self._midi_in   = None
            self._connected = False
            self._cb("MPS-850 getrennt.", "ok")

    def is_connected(self) -> bool:
        """Gibt True zurück, wenn ein MIDI-Port geöffnet ist."""
        return self._connected

    # ── MIDI-Empfang ──────────────────────────────────────────────────────────

    def set_note_callback(self, callback: Callable[[int, int], None]):
        """
        Registriert einen Callback für eingehende MIDI-Noten.

        callback: Funktion(note: int, velocity: int)
        """
        self._note_callback = callback

    def _midi_callback(self, message_and_delta, _data=None):
        """Interner rtmidi-Callback – wird in einem Hintergrundthread aufgerufen."""
        message, _delta_time = message_and_delta
        if not message or len(message) < 3:
            return

        status, note, velocity = message[0], message[1], message[2]
        channel = status & 0x0F
        msg_type = status & 0xF0

        # Nur Note-On auf MIDI-Kanal 9 (0-basiert) verarbeiten
        if msg_type == 0x90 and channel == 9 and velocity > 0:
            now = time.monotonic()
            self._last_kick_time[note] = now
            if self._note_callback:
                self._note_callback(note, velocity)

    # ── Doppelbase-Erkennung ─────────────────────────────────────────────────

    def detect_double_kick(
        self,
        note1_time: float,
        note2_time: float,
    ) -> bool:
        """
        Prüft ob zwei Kick-Noten (35 + 36) als Doppelbase gelten.

        note1_time / note2_time: Zeitstempel in Sekunden (z.B. time.monotonic())
        Rückgabe: True wenn Zeitabstand ≤ 50 ms → Doppelbase-Event.
        """
        return abs(note2_time - note1_time) <= DOUBLE_KICK_WINDOW

    def check_double_kick_now(self) -> bool:
        """
        Prüft anhand der zuletzt empfangenen Kick-Zeitstempel, ob
        gerade ein Doppelbase-Ereignis vorliegt.
        """
        t1 = self._last_kick_time.get(KICK1, 0.0)
        t2 = self._last_kick_time.get(KICK2, 0.0)
        if t1 == 0.0 or t2 == 0.0:
            return False
        return self.detect_double_kick(t1, t2)

    # ── Test-Pad ─────────────────────────────────────────────────────────────

    def test_pad(self, note: int, velocity: int = 100):
        """
        Simuliert einen Pad-Anschlag (für Test und Kalibrierung).
        Ruft den Note-Callback auf – als ob die Note vom Gerät käme.

        note     : MIDI-Note (z.B. KICK1 = 36)
        velocity : Anschlagsstärke 1–127
        """
        velocity = max(1, min(127, velocity))
        pad_name = PAD_NAMES.get(note, f"Note {note}")
        self._cb(f"Test-Pad: {pad_name}  Vel={velocity}", "ok")

        now = time.monotonic()
        self._last_kick_time[note] = now

        if self._note_callback:
            self._note_callback(note, velocity)

    # ── Pad-Info ─────────────────────────────────────────────────────────────

    @staticmethod
    def get_pad_name(note: int) -> str:
        """Gibt den Pad-Bezeichner für eine MIDI-Note zurück."""
        return PAD_NAMES.get(note, f"Unbekannt (Note {note})")

    @staticmethod
    def all_notes() -> dict[int, str]:
        """Gibt das vollständige Note→Pad-Mapping zurück."""
        return dict(PAD_NAMES)
