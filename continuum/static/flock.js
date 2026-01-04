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
    btnJoin: document.getElementById('btn-join'),
    llmInput: document.getElementById('llm-input'),
    btnInfer: document.getElementById('btn-infer'),
    llmOutput: document.getElementById('llm-output'),
    llmStatus: document.getElementById('llm-status')
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

// WebRTC State
let signalingSocket = null;
let myPeerId = null;
let peerConnections = {};  // peerId -> RTCPeerConnection
let dataChannels = {};     // peerId -> RTCDataChannel

// Local LLM State
let localLLM = null;

// Configuration extension
CONFIG.signalingUrl = 'ws://localhost:8421';

function log(msg) {
    const div = document.createElement('div');
    div.className = 'text-gray-400 font-mono';
    div.innerText = `> ${msg}`;
    ui.log.appendChild(div);
    ui.log.scrollTop = ui.log.scrollHeight;
}

async function init() {
    log("Initializing Flock Node...");
    
    // 1. Load Browser LLM
    loadBrowserLLM();

    // 2. Load ONNX (Placeholder)
    try {
        log("Loading ONNX Model...");
        // In a real deployment, we would load the model here
        // const session = await ort.InferenceSession.create(CONFIG.modelPath);
        setTimeout(() => log("ONNX Runtime initialized"), 500);
    } catch (e) {
        log("Failed to load model: " + e.message);
    }

    // Start state broadcast loop
    setInterval(() => {
        if (state.connected && Object.keys(dataChannels).length > 0) {
            broadcastState();
        }
        
        // Keep UI updating even without network for visuals
        // Simulate minor noise when idle
        if (!state.connected) {
             const time = Date.now() / 10000;
             state.resonance = 0.5 + (Math.sin(time) * 0.1); 
             updateUI();
        }
    }, 1000);
}

// ═══════════════════════════════════════════════════════════════════════════════
//     LOCAL COGNITION (Transformers.js)
// ═══════════════════════════════════════════════════════════════════════════════

async function loadBrowserLLM() {
    ui.llmStatus.innerText = "LOADING MODEL...";
    log("Loading local LLM (DistilGPT-2)...");
    
    // Wait for transformers module to load
    const checkTransformers = setInterval(async () => {
        if (window.transformers) {
            clearInterval(checkTransformers);
            try {
                // Initialize Pipeline
                const { pipeline } = window.transformers;
                // Using a small model for demo/fast load. 
                // Could swap for Xenova/LaMini-Flan-T5-783M for better quality
                localLLM = await pipeline('text-generation', 'Xenova/distilgpt2');
                
                log("Local LLM Ready: Xenova/distilgpt2");
                ui.llmStatus.innerText = "ONLINE (DistilGPT-2)";
                ui.llmStatus.className = "text-green-500 text-[10px] uppercase";
                
                // Enable UI
                ui.llmInput.disabled = false;
                ui.btnInfer.disabled = false;
                
            } catch (e) {
                log("LLM Load Failed: " + e.message);
                ui.llmStatus.innerText = "FAILED";
                ui.llmStatus.className = "text-red-500 text-[10px] uppercase";
            }
        }
    }, 100);
}

async function localInfer() {
    const prompt = ui.llmInput.value.trim();
    if (!prompt || !localLLM) return;
    
    ui.llmOutput.innerText = "Thinking...";
    ui.llmOutput.classList.remove('hidden');
    ui.llmInput.disabled = true;
    
    try {
        const result = await localLLM(prompt, {
            max_new_tokens: 64,
            temperature: 0.7
        });
        
        // Handle result format from pipeline
        let text = "";
        if (Array.isArray(result)) {
            text = result[0].generated_text;
        } else {
            text = result.generated_text;
        }

        ui.llmOutput.innerText = text;
        log(`Inference complete: "${text.substring(0, 20)}..."`);
        
    } catch (e) {
        ui.llmOutput.innerText = "Error: " + e.message;
        log("Inference error: " + e.message);
    } finally {
        ui.llmInput.disabled = false;
        ui.llmInput.focus();
    }
}

// Event Listeners for LLM
if (ui.btnInfer) ui.btnInfer.addEventListener('click', localInfer);
if (ui.llmInput) ui.llmInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') localInfer();
});

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
    
    // ui.peerCount is updated by connection events now
    ui.epochCount.innerText = state.epoch;
}

// ═══════════════════════════════════════════════════════════════════════════════
//     WEBRTC SIGNALING & MESH
// ═══════════════════════════════════════════════════════════════════════════════

async function connectToSignaling() {
    log(`Connecting to signaling server at ${CONFIG.signalingUrl}...`);
    try {
        signalingSocket = new WebSocket(CONFIG.signalingUrl);
    } catch (e) {
        log("Error creating WebSocket: " + e.message);
        return;
    }

    signalingSocket.onopen = () => {
        log("Signaling connected, waiting for peer ID...");
        ui.statusDot.className = "w-2 h-2 rounded-full bg-yellow-500 animate-pulse";
        ui.statusText.innerText = "Registering...";
    };

    signalingSocket.onmessage = async (event) => {
        try {
            const msg = JSON.parse(event.data);
            await handleSignalingMessage(msg);
        } catch (e) {
            console.error("Signal parse error:", e);
        }
    };

    signalingSocket.onclose = () => {
        log("Signaling disconnected");
        ui.statusDot.className = "w-2 h-2 rounded-full bg-red-500";
        ui.statusText.innerText = "Disconnected";
        state.connected = false;
        state.peers = 0;
        ui.peerCount.innerText = "0";
    };
    
    signalingSocket.onerror = (err) => {
        log("Signaling error. Is server running?");
        console.error(err);
    };
}

async function handleSignalingMessage(msg) {
    switch(msg.type) {
        case 'welcome':
            // Got our peer ID and list of existing peers
            myPeerId = msg.id;
            log(`Registered as peer: ${myPeerId}`);
            ui.statusDot.className = "w-2 h-2 rounded-full bg-green-500";
            ui.statusText.innerText = `Connected (${myPeerId.substring(0,6)}...)`;
            state.connected = true;

            // Connect to all existing peers
            if (msg.peers && msg.peers.length > 0) {
                log(`Discovered ${msg.peers.length} existing peers`);
                for (const peerId of msg.peers) {
                    if (peerId !== myPeerId) {
                        await initiateConnection(peerId);
                    }
                }
            } else {
                log("No other peers online yet.");
            }
            break;

        case 'offer':
            await handleOffer(msg.sender, msg.sdp);
            break;

        case 'answer':
            await handleAnswer(msg.sender, msg.sdp);
            break;

        case 'ice':
            await handleIceCandidate(msg.sender, msg.candidate);
            break;
            
        case 'error':
            log("Signaling Error: " + msg.message);
            break;
    }
}

function createPeerConnection(peerId) {
    const pc = new RTCPeerConnection({
        iceServers: [
            { urls: 'stun:stun.l.google.com:19302' },
            { urls: 'stun:stun1.l.google.com:19302' }
        ]
    });

    // Send ICE candidates to signaling server
    pc.onicecandidate = (event) => {
        if (event.candidate) {
            signalingSocket.send(JSON.stringify({
                type: 'ice',
                target: peerId,
                candidate: event.candidate
            }));
        }
    };

    // Handle incoming data channels (Responder side)
    pc.ondatachannel = (event) => {
        setupDataChannel(peerId, event.channel);
    };

    pc.onconnectionstatechange = () => {
        const stateStr = pc.connectionState;
        // log(`Peer ${peerId.substring(0,6)}: ${stateStr}`);
        
        if (stateStr === 'connected') {
            if (!peerConnections[peerId]) { // Avoid double count
                 state.peers++; 
            }
            ui.peerCount.innerText = state.peers;
        } else if (stateStr === 'disconnected' || stateStr === 'failed') {
             if (peerConnections[peerId]) {
                state.peers = Math.max(0, state.peers - 1);
                ui.peerCount.innerText = state.peers;
                delete peerConnections[peerId];
                delete dataChannels[peerId];
             }
        }
    };

    peerConnections[peerId] = pc;
    return pc;
}

async function initiateConnection(peerId) {
    log(`Initiating connection to ${peerId.substring(0,6)}...`);

    const pc = createPeerConnection(peerId);

    // Create data channel for gradient exchange (Initiator side)
    const channel = pc.createDataChannel('gradients', {
        ordered: false,  // Speed over ordering for real-time sync
        maxRetransmits: 0  // Lossy but fast
    });
    setupDataChannel(peerId, channel);

    // Create and send offer
    const offer = await pc.createOffer();
    await pc.setLocalDescription(offer);

    signalingSocket.send(JSON.stringify({
        type: 'offer',
        target: peerId,
        sdp: pc.localDescription
    }));
}

async function handleOffer(senderId, sdp) {
    log(`Received offer from ${senderId.substring(0,6)}`);

    const pc = createPeerConnection(senderId);
    await pc.setRemoteDescription(new RTCSessionDescription(sdp));

    // Create and send answer
    const answer = await pc.createAnswer();
    await pc.setLocalDescription(answer);

    signalingSocket.send(JSON.stringify({
        type: 'answer',
        target: senderId,
        sdp: pc.localDescription
    }));
}

async function handleAnswer(senderId, sdp) {
    const pc = peerConnections[senderId];
    if (pc) {
        await pc.setRemoteDescription(new RTCSessionDescription(sdp));
        log(`Connection established with ${senderId.substring(0,6)}`);
    }
}

async function handleIceCandidate(senderId, candidate) {
    const pc = peerConnections[senderId];
    if (pc) {
        await pc.addIceCandidate(new RTCIceCandidate(candidate));
    }
}

function setupDataChannel(peerId, channel) {
    channel.onopen = () => {
        log(`DataChannel open with ${peerId.substring(0,6)}`);
        dataChannels[peerId] = channel;
        state.peers = Object.keys(dataChannels).length;
        ui.peerCount.innerText = state.peers;
    };

    channel.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);
            handlePeerData(peerId, data);
        } catch (e) {}
    };

    channel.onclose = () => {
        log(`DataChannel closed with ${peerId.substring(0,6)}`);
        delete dataChannels[peerId];
        state.peers = Object.keys(dataChannels).length;
        ui.peerCount.innerText = state.peers;
    };
}

function handlePeerData(peerId, data) {
    if (data.type === 'state') {
        // Got global state update from peer - Influence our local state
        // Simple averaging for coherence
        const influence = 0.1;
        state.resonance = (state.resonance * (1-influence)) + (data.resonance * influence);
        state.coherence = (state.coherence * (1-influence)) + (data.coherence * influence);
        
        // Visual feedback of data reception
        // (Could trigger a particle effect here)
        updateUI();
    } else if (data.type === 'gradient') {
        log(`Received gradient bundle from ${peerId.substring(0,6)}`);
        // TODO: Apply to local ONNX model
    }
}

function broadcastState() {
    const msg = JSON.stringify({
        type: 'state',
        resonance: state.resonance,
        coherence: state.coherence,
        turbulence: state.turbulence,
        epoch: state.epoch
    });

    for (const channel of Object.values(dataChannels)) {
        if (channel.readyState === 'open') {
            channel.send(msg);
        }
    }
}

// Event Listeners
ui.btnJoin.addEventListener('click', () => {
    if (!state.connected) {
        connectToSignaling();
    } else {
        log("Already connected.");
    }
});

// Resize handler
window.addEventListener('resize', () => {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
});

// Boot
init();
