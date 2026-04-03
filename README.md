# TUXPLAYER Drum Studio

**Autor:** Heiko Schäfer | **Artist:** TUXPLAYER  
**Version:** 1.0.0 | **Status:** development  
**Lizenz:** MIT (Code) | CC BY-SA 4.0 (Assets)

---

## Beschreibung

TUXPLAYER Drum Studio ist eine Python/Tkinter-Anwendung zur MIDI-basierten
Drum-Pattern-Erstellung, Song-Arrangierung und Audio-Routing unter Linux
(PipeWire).

## Geräte

| Gerät | Funktion |
|-------|----------|
| Millenium MPS-850 | E-Drum-Set (MIDI-Input) |
| Focusrite Scarlett 2i2 | Audio-Interface |
| PreSonus Studio 1824c | Audio-Interface (Hauptinterface) |

## Voraussetzungen

- Python 3.11+
- PipeWire (Audio-Backend)
- `pip install -r requirements.txt`
- `tkinter` als System-Paket (`python-tk`)

## Start

```bash
python main.py
```

## Projektstruktur

```
tuxplayer_drum_studio/
├── main.py                  # Einstiegspunkt
├── gui/                     # Tkinter-UI-Module
│   ├── main_window.py
│   ├── song_editor.py
│   └── routing_panel.py
├── core/                    # Logik & Engine
│   ├── midi_generator.py
│   ├── drum_patterns.py
│   ├── fill_logic.py
│   └── pipewire_manager.py
├── devices/                 # Gerätekonfigurationen
│   ├── mps850.py
│   ├── scarlett_2i2.py
│   └── presonus_1824c.py
├── assets/                  # Logos & Branding
├── exports/                 # MIDI- und Audio-Exporte
├── .tuxproject              # Projektmetadaten
└── requirements.txt
```

## Kontakt

- Web: https://tuxhs.de
- GitHub: https://github.com/Tuxplayers
- E-Mail: contact@tuxhs.de
