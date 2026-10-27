# Freestyle Swimming Training Audio Generator

Generate custom audio tracks for freestyle swimming training with voice cues, kick beats, and breathing patterns.

## 🏊‍♂️ Overview

This tool creates audio training tracks that help swimmers maintain proper technique by providing:
- **Voice cues** for arm strokes ("Right", "Left")
- **Breathing guidance** ("Breathe", "Down") 
- **Kick beat patterns** (2-beat or 6-beat rhythms)
- **Customizable tempo** (strokes per minute)
- **Multiple breathing patterns** (bilateral or 2-stroke)

## 🎵 How It Works

### Voice Cues
- **"Right"** / **"Left"**: Arm stroke timing
- **"Breathe"**: When to take a breath
- **"Down"**: Head position during breathing (for slower tempos)
- **Count-in**: "Ready, 3, 2, 1, Go" to start each track

### Kick Beat Patterns
- **2-beat kick**: One soft tick per arm stroke (emphasizes hip rotation)
- **6-beat kick**: Three ticks per arm stroke (continuous flutter kick rhythm)

### Breathing Patterns  
- **Bilateral**: Breathe every 3rd stroke (alternating sides)
- **2-stroke**: Breathe every 2nd stroke (same side)

## 🚀 Installation

```bash
# Clone or download the project
cd freestyle

# Install dependencies with uv
uv add gtts pydub tqdm

# Or install with pip
pip install gtts pydub tqdm
```

## 📖 Usage

### Generate a Single Custom Track

```bash
# Basic usage - 60 SPM, 2-beat kick, bilateral breathing, 3 minutes
uv run generate_freestyle_cues.py -s 60 -k 2 -b bilateral

# Custom length (60 seconds)
uv run generate_freestyle_cues.py -s 70 -k 6 -b 2-stroke -l 60

# Custom filename
uv run generate_freestyle_cues.py -s 65 -k 2 -b bilateral -o my_custom_track.mp3
```

### Generate All Predefined Tracks

```bash
# Creates 5 preset training tracks
uv run generate_freestyle_cues.py --batch
```

### Command Line Options

| Flag | Description | Options | Default |
|------|-------------|---------|---------|
| `-s, --spm` | Strokes per minute | Any integer | Required |
| `-k, --kick` | Kick beat pattern | `2`, `6` | Required |
| `-b, --breathing` | Breathing pattern | `bilateral`, `2-stroke` | Required |
| `-l, --length` | Track length in seconds | Any integer | 180 |
| `-o, --output` | Custom filename | Any string | Auto-generated |
| `--batch` | Generate all presets | N/A | Single track |

## 🎯 Example Commands

```bash
# Sprint training: 80 SPM, 6-beat kick, 2-stroke breathing
uv run generate_freestyle_cues.py -s 80 -k 6 -b 2-stroke -l 120

# Technique work: 60 SPM, 2-beat kick, bilateral breathing  
uv run generate_freestyle_cues.py -s 60 -k 2 -b bilateral -l 300

# All preset tracks (60-80 SPM range)
uv run generate_freestyle_cues.py --batch
```

## 📁 Output

- **Audio files**: Saved to `freestyle_mp3s/` directory
- **TTS cache**: Voice segments cached in `tts_cache/` for faster generation
- **File naming**: Auto-generated as `freestyle_{breathing}_{kick}beat_{spm}SPM.mp3`

## 🎚️ Track Types (Batch Mode)

| Track | SPM | Breathing | Kick | Duration |
|-------|-----|-----------|------|----------|
| freestyle_bilateral_2beat_60SPM.mp3 | 60 | Bilateral | 2-beat | 3:00 |
| freestyle_bilateral_6beat_70SPM.mp3 | 70 | Bilateral | 6-beat | 3:00 |
| freestyle_2stroke_2beat_70SPM.mp3 | 70 | 2-stroke | 2-beat | 3:00 |
| freestyle_2stroke_6beat_80SPM.mp3 | 80 | 2-stroke | 6-beat | 3:00 |
| freestyle_transition_60to80SPM.mp3 | 60→80 | Bilateral | 2-beat | 3:00 |

## 🔧 Technical Details

- **TTS Engine**: Google Text-to-Speech (gTTS) via Google Translate
- **Audio Processing**: pydub for audio manipulation
- **Progress Tracking**: tqdm for progress bars
- **Caching**: Intelligent caching reduces API calls from 1,500+ to just 9
- **Rate Limiting**: Built-in delays and retry logic to handle API limits

## ⚡ Performance

- **First run**: ~30 seconds (generates TTS cache)
- **Subsequent runs**: Near-instant (uses cached audio)
- **Memory efficient**: Audio segments cached intelligently
- **API optimized**: 99.4% reduction in TTS API calls

## 🏊‍♂️ Swimming Training Tips

### 2-Beat Kick Tracks
- Focus on **hip rotation** and **body roll**
- Each kick drives from the **core**, not just legs
- Perfect for **distance** and **technique** work

### 6-Beat Kick Tracks  
- Emphasizes **continuous propulsion**
- Good for **sprint training** and **tempo work**
- Builds **kick endurance**

### Bilateral Breathing
- Promotes **balanced technique**
- Reduces **shoulder strain**
- Better for **open water** swimming

### 2-Stroke Breathing
- Higher **oxygen intake**
- Good for **sprint intervals**
- Allows **race pace** simulation

## 🛠️ Development

```bash
# Run with development environment
uv run generate_freestyle_cues.py --help

# Clean cache if needed
rm -rf tts_cache/
```

## License

[PolyForm Noncommercial 1.0.0](LICENSE.md): free for personal use, research, education and noncommercial organizations. Commercial use requires a separate license; contact Spencer Boucher.

Outside contributions require agreeing to a contributor license agreement; open an issue before sending a pull request.

## 🤝 Contributing

Open an issue to discuss a change before sending a pull request; see [License](#license) for the contributor license agreement.

---

**Happy Swimming!** 🏊‍♂️💪