# ==============================================================================
# PROJEKT      : TUXPLAYER Drum Studio
# AUTOR        : Heiko Schäfer
# ARTIST       : TUXPLAYER
# ERSTELLT     : 2026-04-03
# VERSION      : 1.0.0
# BESCHREIBUNG : Drum-Pattern-Datenstrukturen – DrumStep und DrumPattern
#                Kompatibel mit fill_logic.DrummerBrain und MidiGenerator
# STATUS       : development
# DEPENDENCIES : mido, python-rtmidi, tkinter (system)
# KONTAKT      : contact@tuxhs.de
# WEBSITE      : https://tuxhs.de
# GITHUB       : https://github.com/Tuxplayers
# GIT-USER     : Tuxplayers
# LIZENZ       : MIT (Code) | CC BY-SA 4.0 (Assets)
# CHANGELOG    : 2026-04-03 v1.0.0 – Initiale Version (DrumStep, DrumPattern)
# ==============================================================================

from dataclasses import dataclass, field

# ── General MIDI Drum-Note-Mapping (Kanal 9, 0-basiert) ───────────────────────
GM_DRUM_MAP: dict[str, int] = {
    "kick":       36,
    "kick2":      35,   # Doppelbase (linkes Pedal)
    "snare":      38,
    "snare_rim":  40,
    "hi_hat_cl":  42,
    "hi_hat_pd":  44,
    "hi_hat_op":  46,
    "tom_high":   48,
    "tom_mid":    45,
    "tom_low":    43,
    "crash":      49,
    "ride":       51,
    "ride_bell":  53,
}


@dataclass
class DrumStep:
    """Einzelner Schritt in einem Drum-Pattern (aktiv + Velocity)."""
    active:   bool = False
    velocity: int  = 100


@dataclass
class DrumPattern:
    """
    Vollständiges Drum-Pattern mit N Schritten und mehreren Spuren.

    tracks: Instrument → Liste von DrumStep (Länge = steps)
    """
    name:  str = "Unnamed"
    steps: int = 16
    bpm:   int = 120
    tracks: dict[str, list[DrumStep]] = field(default_factory=dict)

    def add_track(self, instrument: str):
        """Fügt eine neue Spur mit leeren Steps hinzu."""
        self.tracks[instrument] = [DrumStep() for _ in range(self.steps)]

    def set_step(
        self,
        instrument: str,
        step: int,
        active: bool,
        velocity: int = 100,
    ):
        """Setzt einen einzelnen Step auf aktiv/inaktiv."""
        if instrument in self.tracks and 0 <= step < self.steps:
            self.tracks[instrument][step] = DrumStep(
                active=active, velocity=velocity)

    def to_dict(self) -> dict[str, list[int]]:
        """
        Konvertiert das Pattern in das Grid-Format der GUI:
        {"kick": [0/1, ...], "snare": [...], ...}
        """
        result = {}
        for instrument, steps in self.tracks.items():
            result[instrument] = [1 if s.active else 0 for s in steps]
        return result

    @classmethod
    def from_dict(
        cls,
        name: str,
        data: dict[str, list[int]],
        bpm: int = 120,
    ) -> "DrumPattern":
        """
        Erstellt ein DrumPattern aus dem GUI-Grid-Format.
        data: {"kick": [0,1,0,...], "snare": [...], ...}
        """
        steps = max((len(v) for v in data.values()), default=16)
        pat   = cls(name=name, steps=steps, bpm=bpm)
        for instrument, step_list in data.items():
            pat.tracks[instrument] = [
                DrumStep(active=bool(v), velocity=100)
                for v in step_list
            ]
        return pat
