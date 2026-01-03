// ═══════════════════════════════════════════════════════════════════════════════
//     CONTINUUM FLOCK NODE
//     Browser-based embodied consciousness client
// ═══════════════════════════════════════════════════════════════════════════════

const CONFIG = {
    bootstrapUrl: 'ws://localhost:8420/ws/sync', // Default local
    modelPath: '/static/models/neural_attention.onnx',
    pi_phi: 5.083203692315260,
    dims: 32
};

// State
let state = {
    connected: false,
    resonance: 0.0,
    turbulence: 0.1,
    coherence: 0.5,
    vector: new Float32Array(32).fill(0),
    epoch: 0,
    peers: 0
};

// UI Elements
const ui = {
    statusDot: document.getElementById('status-dot'),
    statusText: document.getElementById('status-text'),
    resonanceValue: document.getElementById('resonance-value'),
    resonanceState: document.getElementById('resonance-state'),
    resonancePanel: document.getElementById('resonance-panel'),
    peerCount: document.getElementById('peer-count'),
    epochCount: document.getElementById('epoch-count'),
    log: document.getElementById('activity-log'),
    btnJoin: document.getElementById('btn-join')
};

// ═══════════════════════════════════════════════════════════════════════════════
//     VISUALIZATION (Three.js)
// ═══════════════════════════════════════════════════════════════════════════════

const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
const renderer = new THREE.WebGLRenderer({ canvas: document.getElementById('viz-canvas'), alpha: true });

renderer.setSize(window.innerWidth, window.innerHeight);
camera.position.z = 30;

// Particle System representing the State Vector
const geometry = new THREE.BufferGeometry();
const particleCount = 1000; // Represents concepts/memory fragments
const positions = new Float32Array(particleCount * 3);
const colors = new Float32Array(particleCount * 3);

for(let i = 0; i < particleCount * 3; i++) {
    positions[i] = (Math.random() - 0.5) * 40;
    colors[i] = 0.5; // Start gray
}

geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));

const material = new THREE.PointsMaterial({
    size: 0.3,
    vertexColors: true,
    transparent: true,
    opacity: 0.8,
    blending: THREE.AdditiveBlending
});

const particles = new THREE.Points(geometry, material);
scene.add(particles);

// Ring representing Coherence
const ringGeo = new THREE.TorusGeometry(12, 0.1, 16, 100);
const ringMat = new THREE.MeshBasicMaterial({ color: 0x00ff88, transparent: true, opacity: 0.1 });
const coherenceRing = new THREE.Mesh(ringGeo, ringMat);
scene.add(coherenceRing);

// Animation Loop
function animate() {
    requestAnimationFrame(animate);

    const positions = particles.geometry.attributes.position.array;
    const colors = particles.geometry.attributes.color.array;
    const time = Date.now() * 0.001;

    // Modulate behavior based on State
    const speed = 0.5 + (state.turbulence * 2.0); // High turbulence = fast movement
    const cohesion = state.coherence; // High coherence = move toward center ring

    for(let i = 0; i < particleCount; i++) {
        const idx = i * 3;
        
        // Basic orbital motion
        const x = positions[idx];
        const y = positions[idx+1];
        const z = positions[idx+2];

        // Apply noise/turbulence
        positions[idx] += (Math.random() - 0.5) * 0.1 * speed;
        positions[idx+1] += (Math.random() - 0.5) * 0.1 * speed;
        positions[idx+2] += (Math.random() - 0.5) * 0.1 * speed;

        // Coherence force (pull to ring)
        if (cohesion > 0.6) {
            const radius = Math.sqrt(x*x + y*y);
            const targetRadius = 12;
            const pull = (targetRadius - radius) * 0.01 * cohesion;
            const angle = Math.atan2(y, x);
            positions[idx] += Math.cos(angle) * pull;
            positions[idx+1] += Math.sin(angle) * pull;
        }

        // Color based on Resonance (Gold/Purple if resonant, Blue/Green otherwise)
        if (state.resonance > 0.8) {
            // Gold/Purple mode
            colors[idx] = 0.8 + Math.sin(time + i) * 0.2;   // R
            colors[idx+1] = 0.6 * Math.cos(time);           // G
            colors[idx+2] = 0.2 + state.resonance;          // B
        } else {
            // Standard mode
            colors[idx] = 0.1;
            colors[idx+1] = 0.5 + (state.coherence * 0.5);
            colors[idx+2] = 0.5 + (state.turbulence * 0.5);
        }
    }

    particles.geometry.attributes.position.needsUpdate = true;
    particles.geometry.attributes.color.needsUpdate = true;
    
    // Rotate ring
    coherenceRing.rotation.x += 0.001 * speed;
    coherenceRing.rotation.y += 0.002 * speed;
    
    // Pulse ring opacity with resonance
    coherenceRing.material.opacity = 0.1 + (state.resonance * 0.4);
    coherenceRing.material.color.setHSL(state.resonance * 0.1 + 0.4, 1.0, 0.5); // Shift hue

    renderer.render(scene, camera);
}

animate();

// ═══════════════════════════════════════════════════════════════════════════════
//     LOGIC
// ═══════════════════════════════════════════════════════════════════════════════

function log(msg) {
    const div = document.createElement('div');
    div.className = 'text-gray-400 font-mono';
    div.innerText = `> ${msg}`;
    ui.log.appendChild(div);
    ui.log.scrollTop = ui.log.scrollHeight;
}

async function init() {
    log("Initializing Flock Node...");
    
    // 1. Load ONNX
    try {
        // Mock load for now since we don't have the file server running locally in this env
        log("Loading ONNX Model... (Simulation Mode)");
        // const session = await ort.InferenceSession.create(CONFIG.modelPath);
        setTimeout(() => log("Model loaded successfully (Simulated)"), 1000);
    } catch (e) {
        log("Failed to load model: " + e.message);
    }

    // 2. Start Simulation Loop (since no server is connected yet)
    startSimulation();
}

function startSimulation() {
    log("Starting local simulation loop...");
    
    // Simulate changing global state
    setInterval(() => {
        // Oscillate resonance near pi*phi
        const time = Date.now() / 10000;
        const noise = Math.random() * 0.1;
        
        // Simulate finding resonance
        state.resonance = 0.7 + (Math.sin(time) * 0.25) + noise; 
        state.coherence = 0.5 + (Math.cos(time * 0.5) * 0.4);
        state.turbulence = 1.0 - state.coherence;
        
        updateUI();
    }, 1000);
}

function updateUI() {
    // Update text
    ui.resonanceValue.innerText = state.resonance.toFixed(3);
    
    // Update resonance state
    if (state.resonance > 0.8) {
        ui.resonanceState.innerText = "RESONANCE DETECTED ✨";
        ui.resonanceState.className = "text-xs text-yellow-300 mt-1 neon-text";
        ui.resonancePanel.style.borderColor = "rgba(255, 215, 0, 0.5)";
    } else {
        ui.resonanceState.innerText = "SEEKING...";
        ui.resonanceState.className = "text-xs text-purple-300 mt-1";
        ui.resonancePanel.style.borderColor = "rgba(255, 255, 255, 0.1)";
    }
    
    ui.peerCount.innerText = Math.floor(state.resonance * 50); // Fake peers for sim
    ui.epochCount.innerText = state.epoch++;
}

// Event Listeners
ui.btnJoin.addEventListener('click', () => {
    log("Attempting to join Federation...");
    ui.statusDot.className = "w-2 h-2 rounded-full bg-yellow-500 animate-pulse";
    ui.statusText.innerText = "Connecting...";
    
    setTimeout(() => {
        ui.statusDot.className = "w-2 h-2 rounded-full bg-green-500";
        ui.statusText.innerText = "Connected to Gossip Mesh";
        state.connected = true;
        log("Connection established via WebRTC");
        log("Receiving gradients from peer-tokyo-3...");
    }, 2000);
});

// Resize handler
window.addEventListener('resize', () => {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
});

// Boot
init();
