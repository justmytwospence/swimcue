from gtts import gTTS
from pydub import AudioSegment
from pydub.generators import Sine, WhiteNoise
from tqdm import tqdm
import os, argparse, time

def parse_arguments():
    parser = argparse.ArgumentParser(description='Generate freestyle swimming training audio cues')
    parser.add_argument('-l', '--length', type=int, default=120, 
                       help='Length of track in seconds (default: 120, excluding count-in)')
    parser.add_argument('-s', '--spm', type=int, default=65,
                       help='Strokes per minute (SPM) (default: 65, optimal for intermediate swimmers)')
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
    ("freestyle_bilateral_2beat_65SPM.mp3", 65, "bilateral", "2beat", None),
    ("freestyle_bilateral_6beat_65SPM.mp3", 65, "bilateral", "6beat", None),
    ("freestyle_2stroke_2beat_65SPM.mp3", 65, "right2", "2beat", "right"),
    ("freestyle_2stroke_6beat_65SPM.mp3", 65, "right2", "6beat", "right"),
]

OUTPUT_DIR = "freestyle_mp3s"
CACHE_DIR = "tts_cache"
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(CACHE_DIR, exist_ok=True)

# Cache for TTS audio segments
_tts_cache = {}

def make_tick(freq=800, dur_ms=40, vol_db=-18):
    return Sine(freq).to_audio_segment(duration=dur_ms).apply_gain(vol_db)

def make_breathing_sound(duration_ms=400):
    """Create a realistic swimming breathing sound - inhale"""
    # Use white noise as the primary texture (sounds like air rushing)
    # Layer with subtle low frequencies for body/depth
    
    inhale = WhiteNoise().to_audio_segment(duration=duration_ms)
    
    # Add subtle low-end body (not dominant, just adds warmth)
    low_freq = Sine(200).to_audio_segment(duration=duration_ms).apply_gain(-25)
    inhale = inhale.overlay(low_freq)
    
    # Natural inhale envelope - smooth crescendo and decrescendo
    attack_dur = int(duration_ms * 0.3)
    decay_dur = int(duration_ms * 0.4)
    
    # Smooth, organic transitions
    inhale = inhale.fade_in(attack_dur).fade_out(decay_dur)
    
    inhale = inhale.apply_gain(-9)  # Softer, natural level
    return inhale

def make_exhale_sound(duration_ms=2000):
    """Create continuous underwater exhale/bubbles"""
    # Underwater bubbles - white noise dominated with subtle low-end
    
    exhale = WhiteNoise().to_audio_segment(duration=duration_ms)
    
    # Add subtle underwater rumble
    low_freq = Sine(150).to_audio_segment(duration=duration_ms).apply_gain(-28)
    exhale = exhale.overlay(low_freq)
    
    # Very gradual fadeout (air depleting naturally)
    exhale = exhale.fade_out(int(duration_ms * 0.7))
    
    # Gentle start (smooth transition from inhale)
    exhale = exhale.fade_in(int(duration_ms * 0.15))
    
    exhale = exhale.apply_gain(-19)  # Very subtle background
    return exhale

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
    words = ["bilateral breathing", "two stroke breathing", "two beat kick", "six beat kick", "3", "2", "1", "Go", "Pull"]
    
    print("🎤 Preloading voice segments...")
    for word in tqdm(words, desc="Loading voices", unit="word"):
        get_voice_segment(word)
    print("✓ All voice segments loaded")

def generate_track(filename, spm, breathing, kick, length_seconds=180, breathing_side=None):
    print(f"Creating {filename}")
    base = AudioSegment.silent(duration=0)

    # Build announcement describing the track
    # Convert internal format to readable description
    breathing_name = "bilateral breathing" if breathing == "bilateral" else "two stroke breathing"
    kick_name = "two beat kick" if kick == "2beat" else "six beat kick"
    
    # Count-in with track description: "[Breathing], [Kick], 3, 2, 1"
    # Quick countdown for immediate push-off
    countin = AudioSegment.silent(duration=300)
    countin += get_voice_segment(breathing_name)
    countin += AudioSegment.silent(duration=400)
    countin += get_voice_segment(kick_name)
    countin += AudioSegment.silent(duration=500)
    countin += get_voice_segment("3")
    countin += AudioSegment.silent(duration=250)  # Rapid countdown
    countin += get_voice_segment("2")
    countin += AudioSegment.silent(duration=250)
    countin += get_voice_segment("1")
    countin += AudioSegment.silent(duration=250)  # Push off right after "1"
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

    # PUSH-OFF EXHALE: Simulate initial underwater exhale during streamline glide
    # After push-off, swimmer exhales during the underwater glide and breakout
    # Duration: approximately 2-3 stroke cycles worth of time
    initial_exhale_duration = int(time_per_stroke * 2.5)  # ~2.5 seconds at 65 SPM
    initial_exhale = make_exhale_sound(duration_ms=initial_exhale_duration)
    track = track.overlay(initial_exhale, position=0)

    # Generate strokes
    t = 0
    for i in tqdm(range(total_strokes), desc=f"  Generating strokes", unit="stroke"):
        # tempo ramp if transition track
        if spm == "60-80":
            frac = i / total_strokes
            cur_spm = start_spm + frac * (end_spm - start_spm)
            time_per_stroke = 60_000 / cur_spm

        # Determine if this is a breathing stroke
        # IMPORTANT: Skip breathing on first few strokes after push-off
        # Swimmer is in streamlined glide, breaking out, establishing rhythm
        # First breath should be on stroke 6 (bilateral) or stroke 4 (2-stroke)
        is_breathing_stroke = False
        
        if breathing == "bilateral":
            # Bilateral: breathe every 3rd stroke, but skip first two cycles (strokes 0-5)
            # First breath on stroke 6 - allows full breakout and rhythm establishment
            # Then continues: 9, 12, 15, etc. (every 3rd stroke)
            if i >= 6 and i % 3 == 0:
                is_breathing_stroke = True
        elif breathing == "right2":  # Legacy internal format for 2-stroke
            # For 2-stroke, breathe every 2nd stroke, but skip first two strokes (0,1,2,3)
            # First breath on stroke 4 - shorter breakout since breathing more frequently
            # Then continues: 6, 8, 10, etc. (every 2nd stroke)
            if i >= 4 and i % 2 == 0:
                is_breathing_stroke = True

        # Give pull cue at the catch/early pull phase (30%) - this is when power application begins
        # BUT: Skip pull cues during initial breakout (first 3 strokes)
        # Swimmer is still establishing position and rhythm from push-off
        if i >= 3:  # Start pull cues from stroke 3 onward
            pull_cue_time = t + (time_per_stroke * 0.30)
            pull_cue = get_voice_segment("Pull")
            track = track.overlay(pull_cue, position=int(pull_cue_time))
        
        # Add breathing cues for breathing strokes
        if is_breathing_stroke:
            # FREESTYLE BREATHING BIOMECHANICS:
            # 0% = Hand entry (catch) - head still down
            # 0-30% = Early pull phase - head begins rotation as body rotates
            # 30-45% = Mid-pull to hand exit - head rotated to side, MOUTH CLEARS WATER
            # 45-50% = Hand exit begins - INHALE WINDOW OPENS
            # 50-70% = Arm recovery - INHALE OCCURS (head fully rotated)
            # 70-80% = Late recovery - head begins returning, INHALE ENDS
            # 80-95% = Hand extends forward - head returns to neutral
            # 95-100% = Hand entry position - head down, streamlined
            
            # INHALE TIMING AND DURATION:
            # Window: 45-80% of stroke cycle (35% window = plenty of time)
            # Start inhale at 50% (mid-recovery, mouth fully clear, stable position)
            # 
            # Duration strategy that balances physiology with pace:
            # - Base duration: 450ms (comfortable, full breath for technique work)
            # - Scales down only for high-tempo swimming where necessary
            # - Never shorter than 300ms (physiological lower limit for effective breathing)
            # - At 65 SPM (923ms/stroke): 450ms = comfortable training breathing
            # - At 80 SPM (750ms/stroke): 400ms = still comfortable
            # - At 90 SPM (667ms/stroke): 350ms = race pace breathing
            # 
            # This ensures technique work feels natural while still being realistic at faster tempos
            
            inhale_start_pct = 0.50  # Start at mid-recovery when mouth is fully clear
            inhale_time = t + (time_per_stroke * inhale_start_pct)
            
            # Calculate comfortable inhale duration that scales appropriately with tempo
            # Formula: Start at 450ms, scale down gradually for faster swimming
            # Only becomes noticeably shorter above 75 SPM
            base_inhale = 450  # Comfortable base duration in ms
            current_spm = cur_spm if spm == "60-80" else start_spm
            
            # Scale factor: reduces duration only when SPM exceeds 75
            # At 65 SPM: scale ≈ 1.0 → 450ms (comfortable)
            # At 80 SPM: scale ≈ 0.89 → 400ms (still comfortable)
            # At 90 SPM: scale ≈ 0.78 → 350ms (race pace)
            scale_factor = max(0.67, min(1.0, (75 / current_spm)))
            inhale_duration = int(base_inhale * scale_factor)
            
            # Absolute physiological limits
            inhale_duration = min(600, max(300, inhale_duration))
            
            inhale_sound = make_breathing_sound(duration_ms=inhale_duration)
            track = track.overlay(inhale_sound, position=int(inhale_time))
            
            # Continuous exhale from after inhale until NEXT breath
            # Calculate time until next breathing stroke
            if breathing == "bilateral":
                strokes_until_next_breath = 3
            else:  # 2-stroke
                strokes_until_next_breath = 2
            
            exhale_start = inhale_time + inhale_duration
            exhale_duration = int(time_per_stroke * strokes_until_next_breath - inhale_duration - 100)
            exhale_sound = make_exhale_sound(duration_ms=max(500, exhale_duration))
            track = track.overlay(exhale_sound, position=int(exhale_start))
        
        # Kick cues - CRITICAL: Kicks must be coordinated with body rotation and opposite arm
        if kick == "6beat":
            # 6-beat kick: 3 kicks per arm stroke = 6 kicks per full stroke cycle
            # Continuous propulsion with emphasis on power-phase kicks
            # Kick timing optimized for body rotation:
            # - Kick 1 at 0% (hand entry) - moderate, coordinates with rotation initiation
            # - Kick 2 at 30% (pull phase) - POWER kick, peak hip rotation and propulsion
            # - Kick 3 at 65% (recovery) - moderate, maintains momentum
            kick_timings = [0.0, 0.30, 0.65]  # Percentages of stroke cycle
            kick_volumes = [-17, -14, -17]    # dB: moderate, POWER, moderate
            
            for k, (timing, vol) in enumerate(zip(kick_timings, kick_volumes)):
                tick_time = t + (time_per_stroke * timing)
                # Kick duration scales with tempo: faster = snappier kicks
                kick_dur = max(30, min(50, int(60_000 / (3 * start_spm if spm != "60-80" else cur_spm))))
                track = track.overlay(make_tick(freq=1200, dur_ms=kick_dur, vol_db=vol),
                                      position=int(tick_time))
        elif kick == "2beat":
            # 2-beat kick: TWO kicks per arm stroke = 2 kicks per full stroke cycle
            # First kick: downbeat with THIS arm's pull (opposite leg kicks down)
            # Second kick: subtle upbeat during recovery
            # Driven by hip rotation, emphasizing power generation on the downbeat
            # 
            # Kick 1 at 30% (pull phase) - DOWNBEAT when hip rotation is maximal, opposite leg drives down
            # Kick 2 at 70% (late recovery) - upbeat, subtler, maintains rhythm
            kick_timings = [0.30, 0.70]  # Percentages of stroke cycle
            kick_volumes = [-15, -19]    # dB: POWER downbeat, subtle upbeat
            
            for timing, vol in zip(kick_timings, kick_volumes):
                kick_time = t + (time_per_stroke * timing)
                # Kick duration scales with tempo: faster swimming = quicker, snappier kicks
                kick_dur = max(25, min(40, int(60_000 / (2 * start_spm if spm != "60-80" else cur_spm))))
                track = track.overlay(make_tick(freq=900, dur_ms=kick_dur, vol_db=vol),
                                      position=int(kick_time))

        t += time_per_stroke

    # Combine count-in with the main track
    final_track = base + track
    final_track.export(os.path.join(OUTPUT_DIR, filename), format="mp3")
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
