# ==============================================================================
# PROJEKT      : TUXPLAYER Drum Studio
# AUTOR        : Heiko Schäfer
# ARTIST       : TUXPLAYER
# ERSTELLT     : 2026-04-03
# VERSION      : 1.0.0
# BESCHREIBUNG : PreSonus Studio 1824c – Audio-Interface-Konfiguration
#                18 Eingänge, 8 dedizierte Drum-Kanäle für Multitrack-Recording
# STATUS       : development
# DEPENDENCIES : mido, python-rtmidi, tkinter (system)
# KONTAKT      : contact@tuxhs.de
# WEBSITE      : https://tuxhs.de
# GITHUB       : https://github.com/Tuxplayers
# GIT-USER     : Tuxplayers
# LIZENZ       : MIT (Code) | CC BY-SA 4.0 (Assets)
# CHANGELOG    : 2026-04-03 v1.0.0 – Initiale Version (Presonus1824c-Klasse)
# ==============================================================================

DEVICE_NAME        = "PreSonus Studio 1824c"
PIPEWIRE_NODE_HINT = "1824c"           # Substring zur PipeWire-Node-Erkennung

# Vollständige Kanal-Belegung (18 Eingänge)
INPUT_CHANNELS: dict[int, str] = {
    1:  "Mic/Line 1",  2:  "Mic/Line 2",
    3:  "Mic/Line 3",  4:  "Mic/Line 4",
    5:  "Mic/Line 5",  6:  "Mic/Line 6",
    7:  "Mic/Line 7",  8:  "Mic/Line 8",
    9:  "ADAT 1",     10:  "ADAT 2",
    11: "ADAT 3",     12:  "ADAT 4",
    13: "ADAT 5",     14:  "ADAT 6",
    15: "ADAT 7",     16:  "ADAT 8",
    17: "S/PDIF L",   18:  "S/PDIF R",
}

OUTPUT_CHANNELS: dict[int, str] = {
    1: "Main L",    2: "Main R",
    3: "Line Out 3", 4: "Line Out 4",
    5: "Line Out 5", 6: "Line Out 6",
    7: "Line Out 7", 8: "Line Out 8",
}

# Drum-Kanal-Zuweisung: Instrument → AUX-Eingangskanal
DRUM_ROUTING: dict[str, int] = {
    "Kick":       1,   # AUX 1
    "Snare":      2,   # AUX 2
    "HiHat":      3,   # AUX 3
    "Tom 1":      4,   # AUX 4
    "Tom 2":      5,   # AUX 5
    "Tom 3":      6,   # AUX 6
    "Overhead L": 7,   # AUX 7
    "Overhead R": 8,   # AUX 8
}


class Presonus1824c:
    """
    Repräsentiert das PreSonus Studio 1824c Audio-Interface.
    Bietet 8 Drum-Kanäle für vollständiges Multitrack-Recording.
    """

    device_name:        str            = DEVICE_NAME
    pipewire_node_hint: str            = PIPEWIRE_NODE_HINT
    inputs:             dict[int, str] = INPUT_CHANNELS
    outputs:            dict[int, str] = OUTPUT_CHANNELS
    drum_routing:       dict[str, int] = DRUM_ROUTING

    def describe(self) -> str:
        """Gibt eine kurze Geräte-Beschreibung zurück."""
        return (
            f"{self.device_name}: "
            f"{len(self.inputs)} Eingänge, "
            f"{len(self.outputs)} Ausgänge, "
            f"{len(self.drum_routing)} Drum-Kanäle"
        )

    def routing_map(self) -> dict[str, int]:
        """
        Gibt die empfohlene Drum-Kanal-Zuordnung für PipeWireManager zurück.
        """
        return dict(DRUM_ROUTING)

    def get_channel_name(self, channel: int) -> str:
        """Gibt die Bezeichnung eines Eingangskanals zurück."""
        return self.inputs.get(channel, f"Kanal {channel}")
