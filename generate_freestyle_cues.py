from gtts import gTTS
from pydub import AudioSegment
from pydub.generators import Sine
from tqdm import tqdm
import math, os, sys, argparse, time

def parse_arguments():
    parser = argparse.ArgumentParser(description='Generate freestyle swimming training audio cues')
    parser.add_argument('-l', '--length', type=int, default=180, 
                       help='Length of track in seconds (default: 180)')
    parser.add_argument('-s', '--spm', type=int, default=70,
                       help='Strokes per minute (SPM) (default: 70)')
    parser.add_argument('-k', '--kick', choices=['2', '6'],
                       help='Kick beat pattern: 2 or 6 beat')
    parser.add_argument('-b', '--breathing', choices=['bilateral', '2-stroke'],
                       help='Breathing pattern: bilateral or 2-stroke')
    parser.add_argument('--side', choices=['left', 'right'], 
                       help='Breathing side for 2-stroke breathing (required for 2-stroke, ignored for bilateral)')
    parser.add_argument('-o', '--output', type=str,
                       help='Output filename (if not specified, will be auto-generated)')
    parser.add_argument('--batch', action='store_true',
                       help='Generate all predefined tracks (ignores other options)')
    
    args = parser.parse_args()
    
    # Validate arguments
    if not args.batch:
        if args.kick is None or args.breathing is None:
            parser.error('Arguments -k/--kick and -b/--breathing are required unless using --batch mode')
        if args.breathing == '2-stroke' and args.side is None:
            parser.error('Argument --side is required when using 2-stroke breathing')
        if args.breathing == 'bilateral' and args.side is not None:
            parser.error('Argument --side is not used with bilateral breathing')
    
    return args

# Configuration for batch mode (all predefined tracks)
TRACKS = [
    ("freestyle_bilateral_2beat_60SPM.mp3", 60, "bilateral", "2beat", None),
    ("freestyle_bilateral_6beat_70SPM.mp3", 70, "bilateral", "6beat", None),
    ("freestyle_2stroke_2beat_70SPM.mp3", 70, "right2", "2beat", "right"),
    ("freestyle_2stroke_6beat_80SPM.mp3", 80, "right2", "6beat", "right"),
    ("freestyle_transition_60to80SPM.mp3", "60-80", "bilateral", "2beat", None),
]

OUTPUT_DIR = "freestyle_mp3s"
CACHE_DIR = "tts_cache"
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(CACHE_DIR, exist_ok=True)

# Cache for TTS audio segments
_tts_cache = {}

def make_tick(freq=800, dur_ms=40, vol_db=-18):
    return Sine(freq).to_audio_segment(duration=dur_ms).apply_gain(vol_db)

def get_voice_segment(text):
    """Get cached TTS audio segment or generate it if not cached"""
    if text in _tts_cache:
        return _tts_cache[text]
    
    # Check if cached file exists
    cache_file = os.path.join(CACHE_DIR, f"{text.lower()}.mp3")
    
    if os.path.exists(cache_file):
        # Load from cache file
        print(f"  Loading cached audio for '{text}'")
        segment = AudioSegment.from_file(cache_file).apply_gain(-5)
    else:
        # Generate new TTS audio with retry logic
        print(f"  Generating new audio for '{text}'")
        max_retries = 3
        for attempt in range(max_retries):
            try:
                tts = gTTS(text)
                tts.save(cache_file)
                segment = AudioSegment.from_file(cache_file).apply_gain(-5)
                break
            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 10  # 10, 20, 30 seconds
                    print(f"    Rate limited, waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
                else:
                    raise e
        
        # Add delay between TTS calls to avoid rate limiting
        time.sleep(3.0)
    
    # Store in memory cache
    _tts_cache[text] = segment
    return segment

def preload_voice_segments():
    """Preload all voice segments we'll need"""
    words = ["Ready", "3", "2", "1", "Go", "Right", "Left", "Breathe", "Down"]
    
    print("🎤 Preloading voice segments...")
    for word in tqdm(words, desc="Loading voices", unit="word"):
        get_voice_segment(word)
    print("✓ All voice segments loaded")

def generate_track(filename, spm, breathing, kick, length_seconds=180, breathing_side=None):
    print(f"Creating {filename}")
    base = AudioSegment.silent(duration=0)

    # Count-in (uses cached voice segments)
    countin = AudioSegment.silent(duration=2000)
    base += countin

    duration_min = length_seconds / 60
    if spm == "60-80":
        start_spm, end_spm = 60, 80
        total_strokes = int(duration_min * 60 * (start_spm + end_spm) / 2 / 60)
    else:
        start_spm = end_spm = spm
        total_strokes = int(duration_min * spm)

    total_time_ms = length_seconds * 1000
    time_per_stroke = (60_000 / start_spm)

    track = AudioSegment.silent(duration=int(total_time_ms))
    tick = make_tick()

    # Generate strokes
    t = 0
    for i in tqdm(range(total_strokes), desc=f"  Generating strokes", unit="stroke"):
        # tempo ramp if transition track
        if spm == "60-80":
            frac = i / total_strokes
            cur_spm = start_spm + frac * (end_spm - start_spm)
            time_per_stroke = 60_000 / cur_spm

        # Determine if this is a breathing stroke
        is_breathing_stroke = False
        if breathing == "bilateral" and i % 3 == 0:
            is_breathing_stroke = True
        elif breathing == "right2":  # Legacy internal format for 2-stroke
            # For 2-stroke, determine which strokes are breathing strokes based on side
            if breathing_side == "right" and i % 2 == 0:  # Right hand strokes (even)
                is_breathing_stroke = True
            elif breathing_side == "left" and i % 2 == 1:   # Left hand strokes (odd)
                is_breathing_stroke = True

        # Always give hand cue at stroke entry (0%) for stroke count and rhythm
        hand = "Right" if i % 2 == 0 else "Left"
        hand_cue = get_voice_segment(hand)
        track = track.overlay(hand_cue, position=int(t))
        
        # Add breathing cues for breathing strokes
        if is_breathing_stroke:
            # "Breathe" at 75% (during hand exit/recovery phase)
            breathe_time = t + (time_per_stroke * 0.75)
            track = track.overlay(get_voice_segment("Breathe"), position=int(breathe_time))
            
            # "Down" cue for slower breathing strokes (return head to streamline)
            if time_per_stroke > 900:
                down_time = t + time_per_stroke - 200  # 200ms before next stroke
                track = track.overlay(get_voice_segment("Down"), position=int(down_time))
        
        # Kick tick always at stroke start (hand entry timing)
        track = track.overlay(tick, position=int(t))

        # Kick cues
        if kick == "6beat":
            # 6-beat kick: More aggressive kick pattern with 3 kicks per stroke
            # Spaced evenly throughout the stroke duration
            for k in range(3):
                tick_time = t + (k * time_per_stroke / 3)
                track = track.overlay(make_tick(freq=1200, dur_ms=40, vol_db=-15),
                                      position=int(tick_time))
        elif kick == "2beat":
            track = track.overlay(make_tick(freq=900, dur_ms=30, vol_db=-18),
                                  position=int(t + time_per_stroke / 4))

        t += time_per_stroke

    track.export(os.path.join(OUTPUT_DIR, filename), format="mp3")
    print(f"✓ Saved {filename}")

def main():
    args = parse_arguments()
    
    # Preload all voice segments once at startup (only when actually generating audio)
    preload_voice_segments()
    
    if args.batch:
        # Generate all predefined tracks
        print(f"\n🎵 Generating {len(TRACKS)} freestyle training tracks...")
        print(f"📁 Output directory: {OUTPUT_DIR}")
        print("=" * 60)
        
        for i, (f, spm, b, k, side) in enumerate(tqdm(TRACKS, desc="Overall Progress", unit="track")):
            print(f"\n[{i+1}/{len(TRACKS)}] {f}")
            generate_track(f, spm, b, k, 180, side)
        
        print(f"\n🏊‍♂️ All tracks generated successfully!")
        print(f"📂 Files saved to: {os.path.abspath(OUTPUT_DIR)}")
    else:
        # Generate single track based on arguments
        # Convert command line args to internal format
        breathing_map = {'bilateral': 'bilateral', '2-stroke': 'right2'}
        kick_map = {'2': '2beat', '6': '6beat'}
        
        breathing = breathing_map[args.breathing]
        kick = kick_map[args.kick]
        
        # Generate filename if not provided
        if args.output:
            filename = args.output
        else:
            filename = f"freestyle_{args.breathing}_{args.kick}beat_{args.spm}SPM.mp3"
        
        print(f"\n🎵 Generating custom freestyle track: {filename}")
        print(f"   Length: {args.length}s | SPM: {args.spm} | Kick: {args.kick}-beat | Breathing: {args.breathing}")
        print(f"📁 Output directory: {OUTPUT_DIR}")
        print("=" * 60)
        
        generate_track(filename, args.spm, breathing, kick, args.length, args.side)
        
        print(f"\n🏊‍♂️ Track generated successfully!")
        print(f"📂 File saved to: {os.path.abspath(os.path.join(OUTPUT_DIR, filename))}")

if __name__ == "__main__":
    main()
