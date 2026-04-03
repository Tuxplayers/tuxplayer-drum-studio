# ==============================================================================
# PROJEKT      : TUXPLAYER Drum Studio
# AUTOR        : Heiko Schäfer
# ARTIST       : TUXPLAYER
# ERSTELLT     : 2026-04-03
# VERSION      : 1.0.0
# BESCHREIBUNG : DrummerBrain – intelligente Drummer-Logik mit 7 Regelsets
#                Generiert MIDI-Nachrichten aus Sektions-Konfigurationen
# STATUS       : development
# DEPENDENCIES : mido, python-rtmidi, tkinter (system)
# KONTAKT      : contact@tuxhs.de
# WEBSITE      : https://tuxhs.de
# GITHUB       : https://github.com/Tuxplayers
# GIT-USER     : Tuxplayers
# LIZENZ       : MIT (Code) | CC BY-SA 4.0 (Assets)
# CHANGELOG    : 2026-04-03 v1.0.0 – Initiale Version (DrummerBrain, 7 Regeln,
#              :                     5 Patterns, 4 Fill-Typen)
# ==============================================================================

import random

try:
    import mido
    MIDO_AVAILABLE = True
except ImportError:
    MIDO_AVAILABLE = False

# ── GM-Drum-Noten (MIDI-Kanal 9, 0-basiert) ───────────────────────────────────
KICK1        = 36   # Bass Drum 1 (rechtes Pedal)
KICK2        = 35   # Bass Drum 2 (linkes Pedal, Doppelbase)
SNARE        = 38   # Acoustic Snare
SNARE_RIM    = 40   # Electric Snare / Rimshot
HIHAT_CLOSED = 42   # Closed Hi-Hat
HIHAT_PEDAL  = 44   # Pedal Hi-Hat
HIHAT_OPEN   = 46   # Open Hi-Hat
TOM1         = 48   # High Tom
TOM2         = 45   # Mid Tom
TOM3         = 43   # Low/Floor Tom
CRASH        = 49   # Crash Cymbal 1
RIDE         = 51   # Ride Cymbal 1
RIDE_BELL    = 53   # Ride Bell

# ── MIDI-Timing-Konstanten ────────────────────────────────────────────────────
TICKS_PER_BEAT    = 480   # Auflösung pro Viertelnote (Standard PPQ)
TICKS_PER_SIXTEEN = 120   # Sechzehntelnote = 480 / 4
TICKS_PER_BAR     = 16 * TICKS_PER_SIXTEEN   # = 1920 Ticks pro 4/4-Takt

# ── Muster-Bibliothek (16 Sechzehntel-Steps pro Takt) ────────────────────────
# 0 = Stille, 1 = Note aktiv
# Step-Index: 0=Beat1, 4=Beat2, 8=Beat3, 12=Beat4
PATTERN_LIB: dict[str, dict[str, list[int]]] = {
    "standard_rock": {
        "kick":  [1,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0],   # Beat 1 + 3
        "snare": [0,0,0,0,1,0,0,0,0,0,0,0,1,0,0,0],   # Beat 2 + 4
        "hihat": [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],   # alle 16tel
    },
    "half_time": {
        "kick":  [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],   # Beat 1
        "snare": [0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0],   # Beat 3
        "hihat": [1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0],   # alle 8tel
    },
    "double_time": {
        "kick":  [1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0],   # alle Beats
        "snare": [0,0,0,0,1,0,0,0,0,0,0,0,1,0,0,0],   # Beat 2 + 4
        "hihat": [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],   # alle 16tel
    },
    "metal_blast": {
        "kick":  [1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0],   # alternierend
        "snare": [0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1],   # alternierend
        "hihat": [0]*16,                                 # kein HiHat
    },
    "punk_beat": {
        "kick":  [1,0,0,0,0,0,0,0,1,0,0,1,0,0,0,0],   # Beat 1 + 3 + 4
        "snare": [0,0,0,0,1,0,0,0,0,0,0,0,1,0,0,0],   # Beat 2 + 4
        "hihat": [1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0],   # alle 8tel
    },
}

# Normalisierungs-Map: GUI-Anzeigename → Library-Key
PATTERN_NAME_MAP: dict[str, str] = {
    "Standard Rock": "standard_rock",
    "Half-Time":     "half_time",
    "Double-Time":   "double_time",
    "Metal Blast":   "metal_blast",
    "Punk Beat":     "punk_beat",
    "Custom":        "standard_rock",   # Fallback auf Standard
}


# ==============================================================================

class DrummerBrain:
    """
    Intelligente Drummer-Logik für den TUXPLAYER Drum Studio.

    Implementiert 7 Regeln für musikalisch sinnvolles Schlagzeugspiel:
      1. Fill IMMER im letzten Takt einer Sektion
      2. BPM-Wechsel nach unten → automatisch Half-Time
      3. Chorus-Start → Crash + Kick auf Beat 1
      4. Bridge → Ride-Bell, Snare nur auf Zählzeit 3
      5. Bridge→Chorus-Übergang → absteigende Tom-Fill erzwingen
      6. Doppelbase → Kick-Noten auf 35 UND 36
      7. Humanize → zufällige Timing- und Velocity-Abweichung

    Ausgabe: Liste von mido.Message-Objekten mit Delta-Zeiten (MIDI-bereit).
    """

    def generate_section(self, config: dict) -> list:
        """
        Generiert alle MIDI-Nachrichten für eine Song-Sektion.

        Parameter (config-Dict):
          name         – Sektionsname (z.B. "Chorus 1", "Bridge")
          bpm          – Tempo dieser Sektion (int)
          bars         – Anzahl Takte (int)
          pattern      – Pattern-Name (str, siehe PATTERN_NAME_MAP)
          fill_type    – Fill-Typ (str, z.B. "tom_fill")
          cymbal_flags – Dict: crash_beat1, ride_instead_of_hihat,
                                open_hihat_upbeat (bool)
          double_kick  – Doppelbase aktiv (bool)
          humanize     – Abweichung in Ticks, 0–30 (int)
          next_bpm     – BPM der nächsten Sektion (für Regel 2)
          next_section – Name der nächsten Sektion (für Regel 5)

        Rückgabe: Liste von mido.Message (note_on mit Delta-Zeiten)
        """
        if not MIDO_AVAILABLE:
            return []

        # Konfiguration auslesen
        name        = config.get("name", "")
        bpm         = int(config.get("bpm", 120))
        bars        = int(config.get("bars", 4))
        pattern_key = PATTERN_NAME_MAP.get(
            config.get("pattern", "Standard Rock"), "standard_rock")
        fill_type   = config.get("fill_type", "tom_fill").lower().replace("-", "_")
        cymbal      = config.get("cymbal_flags", {})
        double_kick = bool(config.get("double_kick", False))
        humanize    = int(config.get("humanize", 0))
        next_bpm    = int(config.get("next_bpm", bpm))
        next_sec    = config.get("next_section", "")

        name_lower    = name.lower()
        is_chorus     = "chorus" in name_lower
        is_bridge     = "bridge" in name_lower
        next_is_ch    = "chorus" in next_sec.lower()

        # Regel 2: BPM-Abfall ≥ 15 % → automatisch Half-Time
        if next_bpm < bpm * 0.85:
            pattern_key = "half_time"

        # Regel 5: Bridge → Chorus-Übergang → Tom-Fill erzwingen
        if is_bridge and next_is_ch:
            fill_type = "tom_fill"

        base = PATTERN_LIB.get(pattern_key, PATTERN_LIB["standard_rock"])

        # Snare-Pattern für Bridge (Regel 4): nur Zählzeit 3 (Step 8)
        snare_bridge = [0]*16
        snare_bridge[8] = 1

        events: list[tuple[int, int, int]] = []  # (abs_tick, note, velocity)

        for bar_i in range(bars):
            offset = bar_i * TICKS_PER_BAR

            # Regel 1: Fill im letzten Takt
            if bar_i == bars - 1 and fill_type:
                events.extend(
                    self._make_fill_events(fill_type, offset, humanize, double_kick))
                continue

            # Regel 3: Chorus → Crash + Kick auf Beat 1 (nur im ersten Takt)
            if is_chorus and bar_i == 0:
                events.append((offset, CRASH, 110))
                events.append((offset + 90, CRASH, 0))

            snare_pat = snare_bridge if is_bridge else base["snare"]

            for s in range(16):
                tick = offset + s * TICKS_PER_SIXTEEN
                ht   = self._humanize_tick(tick, humanize)

                # Kick (Regel 6: Doppelbase → Note 35 + 36)
                if base["kick"][s]:
                    vel = self._humanize_vel(100, humanize)
                    events += [(ht, KICK1, vel), (ht + 90, KICK1, 0)]
                    if double_kick:
                        events += [(ht + 10, KICK2, vel), (ht + 100, KICK2, 0)]

                # Snare
                if snare_pat[s]:
                    vel = self._humanize_vel(100, humanize)
                    events += [(ht, SNARE, vel), (ht + 90, SNARE, 0)]

                # Becken – Reihenfolge: Brücken-Sonderfall > Ride > Open-HH > Closed
                if base["hihat"][s]:
                    vel = self._humanize_vel(80, humanize)
                    if is_bridge:
                        note = RIDE_BELL          # Regel 4: Bridge → Ride-Bell
                    elif cymbal.get("ride_instead_of_hihat"):
                        note = RIDE
                    elif cymbal.get("open_hihat_upbeat") and s % 4 == 2:
                        note = HIHAT_OPEN          # Upbeat (Zählung &)
                    else:
                        note = HIHAT_CLOSED
                    events += [(ht, note, vel), (ht + 90, note, 0)]

                # Zusätzlicher Crash auf Beat 1 (Becken-Flag)
                if cymbal.get("crash_beat1") and s == 0:
                    events += [(ht, CRASH, 90), (ht + 90, CRASH, 0)]

        return self._events_to_messages(events)

    # ── Fill-Erzeugung ────────────────────────────────────────────────────────

    def _make_fill_events(
        self,
        fill_type: str,
        bar_offset: int,
        humanize: int,
        double_kick: bool,
    ) -> list[tuple[int, int, int]]:
        """Erzeugt MIDI-Events für einen Fill-Takt (letzter Takt einer Sektion)."""
        S = TICKS_PER_SIXTEEN
        events = []

        if fill_type == "tom_fill":
            # Absteigende Tom-Fill: TH TH TM TM TL TL KC KC (8 × 8tel-Noten)
            seq = [TOM1, TOM1, TOM2, TOM2, TOM3, TOM3, KICK1, KICK1]
            for i, note in enumerate(seq):
                t  = bar_offset + i * S * 2   # 8tel-Auflösung
                ht = self._humanize_tick(t, humanize)
                vel = self._humanize_vel(100 + i * 3, humanize)  # leichtes Crescendo
                events += [(ht, note, min(vel, 127)), (ht + 180, note, 0)]
                # Doppelbase auch im Fill auf Kick-Noten anwenden
                if double_kick and note == KICK1:
                    events += [(ht + 10, KICK2, min(vel, 127)), (ht + 190, KICK2, 0)]

        elif fill_type == "blast_fill":
            # Snare + Kick alternierend, volle Velocity, alle 16tel
            for i in range(16):
                t  = bar_offset + i * S
                ht = self._humanize_tick(t, humanize)
                note = KICK1 if i % 2 == 0 else SNARE
                events += [(ht, note, 127), (ht + 90, note, 0)]
                if double_kick and note == KICK1:
                    events += [(ht + 10, KICK2, 127), (ht + 100, KICK2, 0)]

        elif fill_type == "drum_roll":
            # Snare-Wirbel 32tel, Crescendo vel 40 → 120
            for i in range(32):
                t   = bar_offset + i * 60      # 60 Ticks = 32tel bei PPQ=480
                ht  = self._humanize_tick(t, humanize)
                vel = int(40 + (80.0 * i / 31))
                events += [(ht, SNARE, vel), (ht + 50, SNARE, 0)]

        elif fill_type == "crash_accent":
            # Crash + Kick auf Beat 1, Rest pausiert
            ht = self._humanize_tick(bar_offset, humanize)
            events += [(ht, CRASH, 110), (ht + 90, CRASH, 0)]
            events += [(ht, KICK1, 110), (ht + 90, KICK1, 0)]
            if double_kick:
                events += [(ht + 10, KICK2, 110), (ht + 100, KICK2, 0)]

        else:
            # Unbekannter Fill-Typ → Standard-Rock-Pattern für letzten Takt
            base = PATTERN_LIB["standard_rock"]
            for s in range(16):
                t  = bar_offset + s * S
                ht = self._humanize_tick(t, humanize)
                for note, pat in [(KICK1, base["kick"]),
                                   (SNARE, base["snare"]),
                                   (HIHAT_CLOSED, base["hihat"])]:
                    if pat[s]:
                        vel = self._humanize_vel(100, humanize)
                        events += [(ht, note, vel), (ht + 90, note, 0)]

        return events

    # ── Hilfsmethoden ─────────────────────────────────────────────────────────

    @staticmethod
    def _humanize_vel(base: int, amount: int) -> int:
        """Zufällige Velocity-Abweichung ±amount, Bereich 1–127."""
        if amount == 0:
            return max(1, min(127, base))
        return max(1, min(127, base + random.randint(-amount, amount)))

    @staticmethod
    def _humanize_tick(tick: int, amount: int) -> int:
        """Zufällige Timing-Abweichung ±amount Ticks, minimal 0."""
        if amount == 0:
            return tick
        return max(0, tick + random.randint(-amount, amount))

    @staticmethod
    def _events_to_messages(events: list[tuple[int, int, int]]) -> list:
        """
        Wandelt absolute (tick, note, velocity)-Tupel in mido.Message-Objekte
        mit Delta-Zeiten um. note_on mit velocity=0 dient als note_off.
        """
        if not MIDO_AVAILABLE:
            return []
        sorted_evts = sorted(events, key=lambda e: e[0])
        messages = []
        prev_tick = 0
        for abs_tick, note, velocity in sorted_evts:
            delta = abs_tick - prev_tick
            messages.append(
                mido.Message("note_on",
                             channel=9,          # MIDI-Kanal 10 (0-basiert = 9)
                             note=note,
                             velocity=velocity,
                             time=delta))
            prev_tick = abs_tick
        return messages

    # ── Statische Hilfsmethode für externe Nutzung ────────────────────────────

    @staticmethod
    def get_tempo_microseconds(bpm: int) -> int:
        """Berechnet Tempo in Mikrosekunden pro Viertelnote (für mido.MetaMessage)."""
        return int(60_000_000 / bpm)
