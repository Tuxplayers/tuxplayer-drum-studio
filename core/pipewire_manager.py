# ==============================================================================
# PROJEKT      : TUXPLAYER Drum Studio
# AUTOR        : Heiko Schäfer
# ARTIST       : TUXPLAYER
# ERSTELLT     : 2026-04-03
# VERSION      : 1.0.0
# BESCHREIBUNG : PipeWireManager – Audio-/MIDI-Routing via pw-cli und pw-link
#                Unterstützt PreSonus 1824c (Multitrack) und Scarlett 2i2
# STATUS       : development
# DEPENDENCIES : mido, python-rtmidi, tkinter (system)
# KONTAKT      : contact@tuxhs.de
# WEBSITE      : https://tuxhs.de
# GITHUB       : https://github.com/Tuxplayers
# GIT-USER     : Tuxplayers
# LIZENZ       : MIT (Code) | CC BY-SA 4.0 (Assets)
# CHANGELOG    : 2026-04-03 v1.0.0 – Initiale Version
#              :   detect_devices, setup_drum_routing, export_qpwgraph_session
# ==============================================================================

import json
import re
import subprocess
from typing import Callable

# ── Geräte-Erkennungs-Muster (Substrings in pw-cli-Ausgabe) ───────────────────
DEVICE_HINTS = {
    "presonus_1824c": ["PreSonus", "1824c", "Studio 18"],
    "scarlett_2i2":   ["Focusrite", "Scarlett", "USB Audio CODEC"],
    "mps850":         ["MPS", "Millennium", "MPS-850"],
}

# ── Drum-Kanal-Zuweisung: PreSonus 1824c ─────────────────────────────────────
# Instrument → AUX-Kanal (1-basiert)
PRESONUS_DRUM_ROUTING: dict[str, int] = {
    "Kick":       1,
    "Snare":      2,
    "HiHat":      3,
    "Tom 1":      4,
    "Tom 2":      5,
    "Tom 3":      6,
    "Overhead L": 7,
    "Overhead R": 8,
}

# ── Drum-Kanal-Zuweisung: Scarlett 2i2 ───────────────────────────────────────
SCARLETT_DRUM_ROUTING: dict[str, int] = {
    "Overhead L": 1,
    "Overhead R": 2,
    # Hinweis: kein Multitrack möglich (nur 2 Eingänge)
}

SCARLETT_LIMITATION = (
    "Hinweis: Scarlett 2i2 hat nur 2 Eingänge – "
    "kein Multitrack-Drum-Recording möglich."
)

# ── Port-Name-Templates (für pw-link) ────────────────────────────────────────
# Werden mit dem erkannten Gerätenamen befüllt
PORT_TEMPLATE_SRC  = "{node}:capture_{ch}"    # Eingangs-Port des Interfaces
PORT_TEMPLATE_DST  = "{node}:playback_{ch}"   # Ausgangs-Port / DAW-Input


# ==============================================================================

class PipeWireManager:
    """
    Schnittstelle zu PipeWire für Drum-Studio-Routing.

    Alle Fehler werden über den optionalen Status-Callback gemeldet
    (kein sys.exit, kein direkter GUI-Zugriff).
    """

    def __init__(self, status_callback: Callable[[str, str], None] | None = None):
        """
        status_callback: Funktion(msg: str, level: str)
                         level = "ok" | "warn" | "error"
        """
        self._cb = status_callback or (lambda msg, level="ok": None)

    # ── Geräte-Erkennung ──────────────────────────────────────────────────────

    def detect_devices(self) -> dict[str, list[str]]:
        """
        Erkennt angeschlossene Audio- und MIDI-Geräte via pw-cli.

        Rückgabe: {"audio": [Gerätename, ...], "midi": [Gerätename, ...]}
        """
        result: dict[str, list[str]] = {"audio": [], "midi": []}

        try:
            proc = subprocess.run(
                ["pw-cli", "list-objects"],
                capture_output=True, text=True, timeout=5, check=False,
            )
        except FileNotFoundError:
            self._cb("pw-cli nicht gefunden – PipeWire aktiv?", "error")
            return result
        except subprocess.TimeoutExpired:
            self._cb("pw-cli: Timeout beim Geräte-Scan.", "error")
            return result

        raw = proc.stdout

        # Blöcke nach Gerätename durchsuchen
        for line in raw.splitlines():
            # Audio: PreSonus 1824c
            if any(h in line for h in DEVICE_HINTS["presonus_1824c"]):
                name = self._extract_node_name(line, "PreSonus Studio 1824c")
                if name not in result["audio"]:
                    result["audio"].append(name)

            # Audio: Scarlett 2i2
            elif any(h in line for h in DEVICE_HINTS["scarlett_2i2"]):
                name = self._extract_node_name(line, "Focusrite Scarlett 2i2")
                if name not in result["audio"]:
                    result["audio"].append(name)

            # MIDI: MPS-850
            if any(h in line for h in DEVICE_HINTS["mps850"]):
                name = self._extract_node_name(line, "Millennium MPS-850")
                if name not in result["midi"]:
                    result["midi"].append(name)

        if not result["audio"] and not result["midi"]:
            self._cb("Keine bekannten Drum-Geräte gefunden.", "warn")
        else:
            total = len(result["audio"]) + len(result["midi"])
            self._cb(f"{total} Gerät(e) erkannt.", "ok")

        return result

    # ── Drum-Routing aufbauen ─────────────────────────────────────────────────

    def setup_drum_routing(self, device: str) -> bool:
        """
        Baut das Drum-Multitrack-Routing auf.

        device: "presonus_1824c" oder "scarlett_2i2"
        Rückgabe: True bei Erfolg, False bei Fehler.
        """
        d = device.lower()

        if "scarlett" in d or "2i2" in d:
            self._cb(SCARLETT_LIMITATION, "warn")
            routing = SCARLETT_DRUM_ROUTING
            node    = "Focusrite Scarlett 2i2"
        else:
            routing = PRESONUS_DRUM_ROUTING
            node    = "PreSonus Studio 1824c"

        success = True
        for instrument, channel in routing.items():
            src = PORT_TEMPLATE_SRC.format(node=node, ch=channel)
            dst = f"JACK:drumtrack_{channel}"   # Zielport im Mixer/DAW
            ok  = self._link_ports(src, dst)
            if not ok:
                self._cb(f"Routing fehlgeschlagen: {instrument} → Kanal {channel}", "error")
                success = False

        if success:
            self._cb(f"Drum-Routing ({node}) erfolgreich aufgebaut.", "ok")

        return success

    def _link_ports(self, src: str, dst: str) -> bool:
        """Verbindet zwei PipeWire-Ports via pw-link."""
        try:
            subprocess.run(
                ["pw-link", src, dst],
                capture_output=True, text=True, timeout=3, check=True,
            )
            return True
        except subprocess.CalledProcessError as e:
            # pw-link gibt Fehler zurück (z.B. Port nicht gefunden)
            self._cb(f"pw-link: {e.stderr.strip()}", "warn")
            return False
        except FileNotFoundError:
            self._cb("pw-link nicht gefunden.", "error")
            return False
        except subprocess.TimeoutExpired:
            self._cb("pw-link: Timeout.", "error")
            return False

    def unlink_ports(self, src: str, dst: str) -> bool:
        """Trennt eine PipeWire-Port-Verbindung via pw-link --disconnect."""
        try:
            subprocess.run(
                ["pw-link", "--disconnect", src, dst],
                capture_output=True, text=True, timeout=3, check=True,
            )
            return True
        except (subprocess.CalledProcessError,
                FileNotFoundError,
                subprocess.TimeoutExpired) as e:
            self._cb(f"pw-link disconnect: {e}", "warn")
            return False

    def list_links(self) -> list[str]:
        """Gibt alle aktiven PipeWire-Verbindungen als Liste zurück."""
        try:
            result = subprocess.run(
                ["pw-link", "--list"],
                capture_output=True, text=True, timeout=3, check=False,
            )
            return [line for line in result.stdout.splitlines() if line.strip()]
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return []

    # ── qpwgraph-Session exportieren ─────────────────────────────────────────

    def export_qpwgraph_session(self, filepath: str) -> bool:
        """
        Exportiert die aktuellen Port-Verbindungen als qpwgraph-Session.

        Format: JSON (kompatibel mit qpwgraph ≥ 0.4, .qpwgraph-Datei).
        Rückgabe: True bei Erfolg, False bei Fehler.
        """
        links = self.list_links()
        if not links:
            self._cb("Keine aktiven Verbindungen für Session-Export.", "warn")
            return False

        connections = []
        # pw-link --list gibt aus: "  output_port  ->  input_port"
        pattern = re.compile(r"^\s*(.+?)\s*->\s*(.+?)\s*$")
        for line in links:
            m = pattern.match(line)
            if m:
                src_port, dst_port = m.group(1), m.group(2)
                src_node, src_port_name = self._split_port(src_port)
                dst_node, dst_port_name = self._split_port(dst_port)
                connections.append({
                    "source_node": src_node,
                    "source_port": src_port_name,
                    "target_node": dst_node,
                    "target_port": dst_port_name,
                })

        session = {
            "qpwgraph_version": "1",
            "type": "qpwgraph-session",
            "connections": connections,
        }

        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(session, f, indent=2, ensure_ascii=False)
            self._cb(f"Session gespeichert: {filepath}", "ok")
            return True
        except OSError as e:
            self._cb(f"Datei-Fehler beim Session-Export: {e}", "error")
            return False

    # ── Hilfsmethoden ─────────────────────────────────────────────────────────

    @staticmethod
    def _extract_node_name(line: str, fallback: str) -> str:
        """Extrahiert den Gerätenamen aus einer pw-cli-Ausgabezeile."""
        # Sucht nach: node.name = "..." oder node.description = "..."
        m = re.search(r'"([^"]{3,})"', line)
        return m.group(1) if m else fallback

    @staticmethod
    def _split_port(port_string: str) -> tuple[str, str]:
        """Trennt 'node_name:port_name' in (node, port). Fallback: ('', port)."""
        if ":" in port_string:
            node, port = port_string.split(":", 1)
            return node.strip(), port.strip()
        return "", port_string.strip()
