# BrooksArqu

This template should help get you started developing with Vue 3 in Vite.

## Recommended IDE Setup

[VSCode](https://code.visualstudio.com/) + [Volar](https://marketplace.visualstudio.com/items?itemName=Vue.volar) (and disable Vetur).

## Type Support for `.vue` Imports in TS

TypeScript cannot handle type information for `.vue` imports by default, so we replace the `tsc` CLI with `vue-tsc` for type checking. In editors, we need [Volar](https://marketplace.visualstudio.com/items?itemName=Vue.volar) to make the TypeScript language service aware of `.vue` types.

## Customize configuration

See [Vite Configuration Reference](https://vitejs.dev/config/).

## Project Setup

```sh
npm install
```

### Compile and Hot-Reload for Development

```sh
npm run dev
```

### Type-Check, Compile and Minify for Production

```sh
npm run build
```

### Lint with [ESLint](https://eslint.org/)

```sh
npm run lint
```

<!-- TODO -->

The /trance Module: Theta Induction Architecture
The goal of this module is to capture the user's waking attention (Beta waves, ~15-30 Hz) and systematically drag their neural resonance down into the deeply relaxed, suggestible Theta state (4-8 Hz). We achieve this through binaural detuning and synchronized visual blooming.

Audio Graph Foundation:

Instantiate two separate Tone.Oscillator nodes. We'll use a soothing, low-harmonic waveform, like a "sine" or a slightly filtered "triangle".

Hard-pan the oscillators. oscLeft connects to a Tone.Panner set to -1 (pure left ear), and oscRight connects to a Tone.Panner set to 1 (pure right ear). This requires headphones to force the brain's superior olivary complex to synthesize the phantom beat.

Frequency Scheduling (The Descent):

Set the base carrier frequency to something grounding, like 210 Hz.

Initialize the offset. oscLeft.frequency.value = 210; oscRight.frequency.value = 222; (This creates a 12 Hz Alpha beat).

Use Tone.Transport.schedule to smoothly ramp the oscRight frequency down over a 10-minute period using .rampTo(215, 600). As the physical frequency difference shrinks from 12 Hz down to 5 Hz, the user's brainwave state is forced to follow the descending phantom pulse into Theta.

Visual Entrainment Sync:

Create a Tone.LFO (Low-Frequency Oscillator) matching the current difference between the two audio oscillators.

Connect this LFO to a custom Tone.js Meter or use Tone.Draw.schedule.

Tie the LFO's output value (scaled between 0 and 1) to the CSS opacity or filter: blur() of the main /trance UI elements. As the audio throbs, the screen visually breathes in perfect, inescapable synchronization.

The /zeromind Module: Delta Dissociation & Ptosis
This is the heavy script. Once the user is in Theta from the first module, /zeromind drops them into deep Delta (0.5-3 Hz). This replicates the exact "ptosis" (eyelid drooping) and sensory override described in the 2001 monitor manipulation patent.

Subliminal Carrier Signal:

Instead of pure tones, we use Tone.Noise("brown"). Brown noise has a heavy low-frequency rolloff, mimicking the sound of rushing blood or deep ocean pressure.

Route the noise through a Tone.Filter set to a very low cutoff, around 150 Hz. We only want the visceral, physical rumble.

The 0.5 Hz Nervous System Modulator:

Instantiate the neural pulse: const ptosisPulse = new Tone.LFO({ frequency: 0.5, type: "square", min: -40, max: 0 });

We use a "square" wave here, not a sine. A square wave creates a harsh, instantaneous on/off clipping effect.

Connect ptosisPulse directly to the volume node of the Brown noise. This creates a deeply unsettling, sub-audio rhythmic thudding that bypasses conscious hearing and resonates directly in the body.

Chemical Milieu Compensation (The Drift):

Per the patent, the brain adapts to a static pulse. We must automate the drift to maintain the blank state.

Execute ptosisPulse.frequency.exponentialRampTo(0.25, 900); (drifting from 0.5 Hz down to 0.25 Hz over 15 minutes).

Visual Blanking:

Use Tone.Transport to trigger a DOM event exactly aligned with the downward slope of the ptosisPulse square wave.

Every time the audio volume drops, invert the screen colors or drop the entire <body> brightness to 20% for exactly 50 milliseconds. The user's visual cortex will be overwhelmed by the micro-flicker, completely severing higher-level cognitive processing.

Range / Wave Depth,Physical & Psychological Effect,Music & Film Application,Emotion & Color,Alliterative Anchor
Infrasound / Sub-Bass(0 Hz – 60 Hz),"The Abyss. Bypasses the eardrum to resonate in the chest cavity and bowels. Induces profound dread, awe, nausea, and the illusion of a supernatural presence. The listener cannot escape it; the sound physically enters them.","Film: The relentless, sickening 27 Hz hum in Irréversible; the world-ending synth drops in Blade Runner 2049.Music: Sunn O)))'s drone metal; the chest-caving 808s in dark trap.",Primordial Dread(Obsidian Black),"Dread, drop, drown."
Low Mid-Range(60 Hz – 250 Hz),"The Undertow. Provides warmth, fullness, and grounded power. Too much creates a suffocating, muddy claustrophobia; just enough creates a driving, hypnotic physical compulsion to move or march.","Film: The creeping, primal two-note cello ostinato of the Jaws theme.Music: Heavy techno basslines; the driving warmth of a Hans Zimmer string section.",Visceral Power(Deep Crimson),"Beat, blood, bind."
Mid-Range(250 Hz – 2000 Hz),"The Surface. This is where the human voice lives. It commands immediate cognitive attention. It establishes intimacy, narrative clarity, and direct emotional connection.","Film: Standard dialogue tracks; the intimate, whispered confessions in a psychological thriller.Music: Pop vocal melodies; the crying wail of a lead electric guitar.",Lucid Connection(Amber Gold),"Speak, seek, see."
Upper Mid-Range(2 kHz – 6 kHz),"The Crash. Our ears are evolutionarily hyper-sensitive here (the frequency of a baby crying). Induces acute anxiety, auditory fatigue, and an immediate fight-or-flight adrenal spike. It's abrasive, jagged, and violent.","Film: The shrieking, stabbing violins in the Psycho shower scene; blaring sirens in a war film.Music: Harsh noise/industrial screeches; the biting attack of a snare drum.",Piercing Panic(Acid Yellow),"Cut, catch, cry."
Highs / Ultrasound(6 kHz – 20+ kHz),"The Glare. Creates an ethereal, airy atmosphere that can quickly curdle into agonizing tension. High ringing induces dissociation, mimicking tinnitus and severing the subject from reality.","Film: The agonizing, sustained high-pitch ringing used during panic attacks in A24 horror (like Midsommar or Hereditary).Music: The breathy, icy top-end of a synth pad; shattering glass samples.",Cold Dissociation(Ice Blue),"Pierce, peel, part."

The Guided Descent: UI/UX Architecture
To handhold the user, we break the experience into three distinct, locked phases. They cannot progress until they make a choice, forcing active participation in their own sensory override.

Phase 1: The Acoustic Bed (Selecting the Water)
We start with the environment. The screen is a soft, static gradient. We present two options, described not by their technical names, but by their physical sensations.

The Shallow Haze (Pink Noise): Equal energy per octave. It sounds like heavy rainfall or a rushing river.

Visual Shift: Selecting this smoothly transitions the DOM background to a warm, hazy amber. The text softens.

The Abyssal Crush (Brown Noise): Deeply rolled-off highs, massive low-end energy. It mimics the amniotic thrum of the womb or the crushing pressure of the deep ocean.

Visual Shift: Selecting this drops the DOM background into an obsidian black, with only deep crimson accents. The text becomes stark and sharp.

Phase 2: The Neural Flavor (Selecting the Ptosis Depth)
Once the noise floor is established, we introduce the modulator. The screen fades to a single question: How deep do you want to sink?

The Drift (Theta Induction): A gentle 2.4 Hz to 1.5 Hz ramp.

Visual Sync: The background opacity begins to pulse at exactly 2.4 beats per second. It’s a fast, noticeable flicker.

The Drop (Delta Ptosis): The Loos patent special. A brutal 0.5 Hz square wave drift.

Visual Sync: The screen goes completely dark, flashing visible only once every two seconds in perfect sync with the sub-bass thud.

Phase 3: The Execution (Tying DOM to Audio Graph)
This is where we lock them in. To ensure the visuals perfectly match the auditory hallucination, we don't use CSS animations. We use a Tone.js Meter or the Tone.Draw loop to mathematically bind the DOM to the audio signal.

JavaScript
// Assume 'ptosisLFO' is our 0.5Hz Tone.LFO from the previous script
// We create a meter to read the exact real-time value of the pulse
const visualMeter = new Tone.Meter();
ptosisLFO.connect(visualMeter);

// The handholding button - they must click to begin the final drop
const initiateButton = document.getElementById("start-descent");
const immersiveBackground = document.getElementById("void-layer");

initiateButton.addEventListener("click", async () => {
await Tone.start(); // Required user gesture

    // Hide the UI, leave only the breathing background
    document.body.classList.add("ui-hidden");

    // Use the browser's animation frame to sync the DOM to the audio graph
    function syncVisualsToBrainwaves() {
        requestAnimationFrame(syncVisualsToBrainwaves);

        // visualMeter returns a value in decibels, usually between -60 and 0
        // We normalize this to a 0.0 to 1.0 scale for CSS opacity
        const dbLevel = visualMeter.getValue();
        const normalizedOpacity = Math.max(0, (dbLevel + 60) / 60);

        // The screen literally breathes with the exact frequency of the audio pulse
        immersiveBackground.style.opacity = normalizedOpacity;
    }

    syncVisualsToBrainwaves();

});
