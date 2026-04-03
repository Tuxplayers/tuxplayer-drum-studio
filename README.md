# 🥁 TUXPLAYER Drum Studio

<p align="center">
  <img src="assets/LOGObranding_logo_Program.png" alt="TUXPLAYER Logo" width="200"/>
</p>

**Autor:** Heiko Schäfer | **Artist:** TUXPLAYER
**Version:** 1.5.0 | **Status:** development
**Lizenz:** MIT (Code) | CC BY-SA 4.0 (Assets)
**Website:** [tuxhs.de](https://tuxhs.de) | **GitHub:** [Tuxplayers](https://github.com/Tuxplayers)

---

## Was ist TUXPLAYER Drum Studio?

Ein **Python/Tkinter MIDI Drum-Pattern-Editor** für Linux – entwickelt von einem
Musiker (Gitarre, seit 1973) für Musiker. Das Ziel: Gitarre in der Hand halten,
Drums per Knopfdruck abspielen lassen – ohne DAW öffnen zu müssen.

### Features

| Feature | Beschreibung |
|---|---|
| 🥁 **Beat-Grid** | 16-Step-Visualizer, Klick = Note an/aus |
| 🎵 **MIDI-Export** | Echter Export via `mido` (480 PPQ, GM Kanal 9) |
| ▶ **FluidSynth-Playback** | Sofort hören – mit Loop-Funktion |
| 🌿 **Hydrogen-Export** | Natives `.h2song` mit Dave Grohl Drumkit |
| 🎛 **Bitwig-Integration** | `.mid` direkt in Bitwig öffnen |
| 🥁 **9 Beat-Patterns** | Bonham Rock, Grohl Grunge, Purdie Shuffle, Reggae… |
| 🦶 **Doppelbase** | Note 35 + 36 alternierend (echter Wechsel-Bass) |
| 🔊 **PipeWire Routing** | Drum-Kanal-Zuweisung via `pw-link` |
| 📖 **Hilfe / Lizenz / Spenden** | Direkt integriert, kein zweites Fenster |

---

## Schnellstart

### Voraussetzungen

```bash
# Python-Pakete
pip install mido python-rtmidi Pillow --break-system-packages

# System-Pakete (Arch / CachyOS)
sudo pacman -S python-tkinter fluidsynth hydrogen soundfont-fluid
```

### Starten

```bash
git clone https://github.com/Tuxplayers/tuxplayer-drum-studio.git
cd tuxplayer-drum-studio
python3 main.py
```

---

## Bedienung

### 1. Beat-Pattern erstellen

- **Beat-Pattern** Dropdown: eines der 9 Presets wählen (oder „Custom")
- **Grid klicken**: einzelne Noten an/ausschalten
- **BPM** und **Takte** einstellen

### 2. Anhören (Gitarre in der Hand!)

```
[▶ Play]          → FluidSynth spielt das Pattern sofort ab
[🔁 Loop]         → Dauerschleife bis [⏹ Stop]
BPM ändern        → neu generieren + sofort abspielen
```

### 3. In Hydrogen öffnen

```
[🌿 Hydrogen]  → exportiert .h2song mit Dave Grohl Drumkit → öffnet Hydrogen
```

### 4. In Bitwig öffnen

```
[🎛 Bitwig]    → exportiert .mid → öffnet Bitwig Studio
```

---

## Beat-Pattern-Presets

| Pattern | Stil |
|---|---|
| Standard Rock | Klassischer 4/4-Beat |
| Half-Time | Halbe Zeit, schwerer Groove |
| Double-Time | Doppeltempo HiHat |
| **Bonham Rock** | Led Zeppelin – schwerer Groove |
| **Grohl Grunge** | Nirvana – treibende 16tel |
| **Purdie Shuffle** | Funk/Soul – Ghost-Notes |
| Reggae One Drop | Kick nur auf Beat 3 |
| Metal Blast | Blast-Beat alternierend |
| Punk Beat | Straightforward Punk |
| Custom | Leeres Grid zum selbst Bauen |

---

## Projektstruktur

```
tuxplayer_drum_studio/
├── main.py                   # Einstiegspunkt
├── gui/
│   └── main_window.py        # Hauptfenster (Dark-UI, Tabs, Beat-Grid)
├── core/
│   ├── fill_logic.py         # DrummerBrain – Fill-Generierung
│   ├── pipewire_manager.py   # PipeWire pw-link Routing
│   ├── drum_patterns.py      # DrumPattern Datenklassen
│   └── midi_generator.py     # MidiGenerator (rtmidi)
├── devices/
│   ├── mps850.py             # Millenium MPS-850 Controller
│   └── presonus_1824c.py     # PreSonus Studio 1824c Interface
├── assets/                   # Logos + Maskottchen (CC BY-SA 4.0)
├── exports/                  # MIDI / H2Song Ausgabe
└── requirements.txt
```

---

## Getestete Hardware

| Gerät | Funktion |
|---|---|
| Millenium MPS-850 | E-Drum-Set (MIDI-Input via USB) |
| PreSonus Studio 1824c | Audio-Interface (18 Eingänge, 8 Drum-Kanäle) |
| Focusrite Scarlett 2i2 | Audio-Interface (Fallback) |

**System:** CachyOS Linux · PipeWire · Python 3.11+ · Hydrogen 1.2.6 · Bitwig Studio

---

## Abhängigkeiten

| Paket | Lizenz |
|---|---|
| `mido` | MIT |
| `python-rtmidi` | MIT |
| `Pillow` | HPND |
| `FluidSynth` | LGPL v2.1+ |
| FluidR3 GM Soundfont | MIT |
| `tkinter` | PSF |

---

## Lizenz

**Code:** MIT License – © 2026 Heiko Schäfer (TUXPLAYER)
**Assets/Grafiken:** CC BY-SA 4.0 – © 2026 Heiko Schäfer (TUXPLAYER)

---

## Verwandte Projekte

- [TUX-Guitar-Tuner](https://github.com/Tuxplayers/TUX-Guitar-Tuner) – Gitarrenstimmer für Linux
- [TuxBackup](https://github.com/Tuxplayers) – Backup-Skript für Linux
- [musikstudio](https://github.com/Tuxplayers) – Audio-Manager-Suite

---

## Support / Spenden

Dieses Tool ist kostenlos und Open Source. Wenn es dir hilft:

[![Buy Me a Coffee](https://img.shields.io/badge/Buy%20Me%20a%20Coffee-FFDD00?style=for-the-badge&logo=buy-me-a-coffee&logoColor=black)](https://buymeacoffee.com/schaefer.heiko)
[![PayPal](https://img.shields.io/badge/PayPal-009CDE?style=for-the-badge&logo=paypal&logoColor=white)](https://paypal.me/tuxplayer)

---

*„Life is a Boomerang" – TUXPLAYER 🎸🥁*
