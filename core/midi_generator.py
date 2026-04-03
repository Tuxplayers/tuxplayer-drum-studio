# ==============================================================================
# PROJEKT      : TUXPLAYER Drum Studio
# AUTOR        : Heiko Schäfer
# ARTIST       : TUXPLAYER
# ERSTELLT     : 2026-04-03
# VERSION      : 1.0.0
# BESCHREIBUNG : MidiGenerator – erzeugt MIDI-Dateien aus Drum-Pattern-Daten
#                und sendet Noten an offene MIDI-Ports
# STATUS       : development
# DEPENDENCIES : mido, python-rtmidi, tkinter (system)
# KONTAKT      : contact@tuxhs.de
# WEBSITE      : https://tuxhs.de
# GITHUB       : https://github.com/Tuxplayers
# GIT-USER     : Tuxplayers
# LIZENZ       : MIT (Code) | CC BY-SA 4.0 (Assets)
# CHANGELOG    : 2026-04-03 v1.0.0 – Initiale Version
#              :   open_port, close_port, send_note, save_to_file, list_ports
# ==============================================================================

from typing import Callable

try:
    import mido
    MIDO_AVAILABLE = True
except ImportError:
    MIDO_AVAILABLE = False

# Standard-Auflösung (Ticks pro Viertelnote)
TICKS_PER_BEAT = 480


class MidiGenerator:
    """
    Wandelt Drum-Pattern-Daten in MIDI-Nachrichten um und sendet sie
    an einen geöffneten MIDI-Ausgangsport oder speichert sie als Datei.
    """

    def __init__(
        self,
        status_callback: Callable[[str, str], None] | None = None,
    ):
        """
        status_callback: Funktion(msg: str, level: str)
                         level = "ok" | "warn" | "error"
        """
        self._cb       = status_callback or (lambda msg, level="ok": None)
        self._outport  = None
        self.port_name = ""

    # ── Port-Verwaltung ───────────────────────────────────────────────────────

    def open_port(self, port_name: str) -> bool:
        """
        Öffnet einen MIDI-Ausgangsport.
        Rückgabe: True bei Erfolg, False bei Fehler (kein sys.exit).
        """
        if not MIDO_AVAILABLE:
            self._cb("mido nicht installiert.", "error")
            return False
        try:
            self._outport  = mido.open_output(port_name)
            self.port_name = port_name
            self._cb(f"MIDI-Port geöffnet: {port_name}", "ok")
            return True
        except Exception as e:
            self._cb(f"Port-Fehler: {e}", "error")
            return False

    def close_port(self):
        """Schließt den aktuellen MIDI-Ausgangsport."""
        if self._outport is not None:
            try:
                self._outport.close()
            except Exception:
                pass
            self._outport  = None
            self.port_name = ""
            self._cb("MIDI-Port geschlossen.", "ok")

    def is_open(self) -> bool:
        """Gibt True zurück, wenn ein Port geöffnet ist."""
        return self._outport is not None

    # ── Noten senden ─────────────────────────────────────────────────────────

    def send_note(self, channel: int, note: int, velocity: int):
        """
        Sendet eine einzelne note_on-Nachricht an den offenen Port.

        channel  : MIDI-Kanal 0–15 (Kanal 9 = GM-Drums)
        note     : MIDI-Note 0–127
        velocity : Anschlagsstärke 0–127
        """
        if not MIDO_AVAILABLE or self._outport is None:
            return
        try:
            msg = mido.Message(
                "note_on", channel=channel, note=note, velocity=velocity)
            self._outport.send(msg)
        except Exception as e:
            self._cb(f"Send-Fehler: {e}", "error")

    # ── MIDI-Datei erzeugen ───────────────────────────────────────────────────

    def save_to_file(
        self,
        filepath: str,
        sections: list[dict],
        bpm: int = 120,
    ) -> bool:
        """
        Speichert mehrere Song-Sektionen als MIDI-Datei.

        filepath : Ausgabepfad (.mid)
        sections : Liste von Sektion-Dicts mit 'messages' (List[mido.Message])
                   und 'bpm' (int)
        bpm      : Globales Fallback-Tempo
        Rückgabe : True bei Erfolg, False bei Fehler.
        """
        if not MIDO_AVAILABLE:
            self._cb("mido nicht installiert – kein MIDI-Export.", "error")
            return False

        try:
            mid   = mido.MidiFile(ticks_per_beat=TICKS_PER_BEAT)
            track = mido.MidiTrack()
            mid.tracks.append(track)

            # Globales Tempo-Event am Anfang
            tempo = mido.bpm2tempo(bpm)
            track.append(mido.MetaMessage("set_tempo", tempo=tempo, time=0))
            track.append(mido.MetaMessage("track_name", name="Drums", time=0))

            for section in sections:
                sec_bpm  = int(section.get("bpm", bpm))
                messages = section.get("messages", [])

                # Tempo-Wechsel einfügen, wenn BPM der Sektion abweicht
                if sec_bpm != bpm:
                    track.append(mido.MetaMessage(
                        "set_tempo",
                        tempo=mido.bpm2tempo(sec_bpm),
                        time=0))

                for msg in messages:
                    track.append(msg)

            mid.save(filepath)
            self._cb(f"MIDI gespeichert: {filepath}", "ok")
            return True

        except OSError as e:
            self._cb(f"Datei-Fehler: {e}", "error")
            return False
        except Exception as e:
            self._cb(f"MIDI-Export-Fehler: {e}", "error")
            return False

    # ── Port-Liste ────────────────────────────────────────────────────────────

    def list_ports(self) -> list[str]:
        """Gibt alle verfügbaren MIDI-Ausgangsports zurück."""
        if not MIDO_AVAILABLE:
            return []
        try:
            return mido.get_output_names()
        except Exception:
            return []
