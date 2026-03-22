const stars = []; const STAR_COUNT = 400; class Star { constructor(canvas) { this.reset(canvas); }
reset(canvas) { this.x = (Math.random() - 0.5) * canvas.width * 2; this.y = (Math.random() - 0.5) *
canvas.height * 2; this.z = canvas.width; // Start far away this.px = 0; this.py = 0; // Previous
positions for "streak" effect } update(speed, canvas) { this.px = this.x / (this.z / canvas.width);
this.py = this.y / (this.z / canvas.width); this.z -= speed; // Move toward camera if (this.z < 1)
this.reset(canvas); } } // Inside your Vue Component or Store const scheduleDeepenSequence = () => {
const loop = new Tone.Loop((time) => { // 1. Audio: Trigger a deep sub-bass drop
subBass.triggerAttackRelease("E1", "8n", time); // 2. Visuals: DEFERRED CALLBACK // This will run on
the requestAnimationFrame closest to 'time' Tone.Draw.schedule(() => { tunnelPulseStrength.value =
1.0; // Trigger a visual flash/lunge }, time);
}, "2n").start(0); }; const renderTunnel = () => { const ctx = canvasRef.value.getContext('2d');
const { width, height } = canvasRef.value; // Fade previous frame slightly for "motion blur"
ctx.fillStyle = "rgba(0, 0, 0, 0.15)"; ctx.fillRect(0, 0, width, height); // Speed increases when
the audio 'pulse' happens const currentSpeed = 5 + (tunnelPulseStrength.value * 20); // Decay the
pulse strength over time tunnelPulseStrength.value *= 0.9; ctx.strokeStyle = `white`;
ctx.beginPath(); stars.forEach(star => { star.update(currentSpeed, canvasRef.value); // Project 3D
coordinates to 2D const x2d = star.x / (star.z / width) + width / 2; const y2d = star.y / (star.z /
height) + height / 2; if (star.px !== 0) { ctx.moveTo(star.px + width / 2, star.py + height / 2);
ctx.lineTo(x2d, y2d); } }); ctx.stroke(); requestAnimationFrame(renderTunnel); };
