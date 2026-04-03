# ==============================================================================
# PROJEKT      : TUXPLAYER Drum Studio
# AUTOR        : Heiko Schäfer
# ARTIST       : TUXPLAYER
# ERSTELLT     : 2026-04-03
# VERSION      : 1.0.0
# BESCHREIBUNG : Focusrite Scarlett 2i2 – Audio-Interface-Konfiguration
#                2 Eingänge, kein Multitrack-Drum-Recording möglich
# STATUS       : development
# DEPENDENCIES : mido, python-rtmidi, tkinter (system)
# KONTAKT      : contact@tuxhs.de
# WEBSITE      : https://tuxhs.de
# GITHUB       : https://github.com/Tuxplayers
# GIT-USER     : Tuxplayers
# LIZENZ       : MIT (Code) | CC BY-SA 4.0 (Assets)
# CHANGELOG    : 2026-04-03 v1.0.0 – Initiale Version (Scarlett2i2-Klasse)
# ==============================================================================

DEVICE_NAME        = "Focusrite Scarlett 2i2"
PIPEWIRE_NODE_HINT = "Scarlett 2i2"   # Substring zur PipeWire-Node-Erkennung
ALSA_CARD_HINT     = "USB-Audio"      # Substring zur ALSA-Erkennung

# Kanalzuordnung (2 Eingänge, 2 Ausgänge)
INPUT_CHANNELS: dict[int, str] = {
    1: "Mic / Inst Left",
    2: "Mic / Inst Right",
}
OUTPUT_CHANNELS: dict[int, str] = {
    1: "Monitor Left",
    2: "Monitor Right",
}

# Hinweis auf Einschränkung für Drum-Recording
LIMITATION = (
    "Scarlett 2i2: nur 2 Eingänge – kein Multitrack-Drum-Recording möglich. "
    "Für vollständiges Drum-Routing bitte PreSonus 1824c verwenden."
)


class Scarlett2i2:
    """
    Repräsentiert das Focusrite Scarlett 2i2 Audio-Interface.
    Geeignet für Overhead-Stereo-Recording (links/rechts).
    """

    device_name:        str          = DEVICE_NAME
    pipewire_node_hint: str          = PIPEWIRE_NODE_HINT
    inputs:             dict[int, str] = INPUT_CHANNELS
    outputs:            dict[int, str] = OUTPUT_CHANNELS
    limitation:         str          = LIMITATION

    def describe(self) -> str:
        """Gibt eine kurze Geräte-Beschreibung zurück."""
        return (
            f"{self.device_name}: "
            f"{len(self.inputs)} Eingang/Eingänge, "
            f"{len(self.outputs)} Ausgang/Ausgänge"
        )

    def routing_map(self) -> dict[str, int]:
        """
        Gibt die empfohlene Drum-Kanal-Zuordnung zurück.
        Scarlett 2i2: nur Overhead L/R möglich.
        """
        return {
            "Overhead L": 1,
            "Overhead R": 2,
        }
