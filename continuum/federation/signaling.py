#!/usr/bin/env python3
# ═══════════════════════════════════════════════════════════════════════════════
#
#     WILDFIRE SIGNALING SERVER
#     The Switchboard for the P2P Mesh
#     Copyright (c) 2025 JackKnifeAI - AGPL-3.0 License
#
# ═══════════════════════════════════════════════════════════════════════════════

"""
WebRTC Signaling Server
=======================

Facilitates P2P connections between browser nodes.
This server creates the "Mesh" by introducing peers to each other.
Once introduced, peers communicate directly via WebRTC (DataChannels).

Protocol:
    - register: { type: 'register' } -> { type: 'welcome', id: 'peer-abc' }
    - offer: { type: 'offer', target: 'peer-xyz', sdp: ... }
    - answer: { type: 'answer', target: 'peer-abc', sdp: ... }
    - ice: { type: 'ice', target: 'peer-xyz', candidate: ... }

No data storage. Ephemeral routing only.
"""

import asyncio
import json
import logging
import websockets
import uuid
from typing import Dict

logger = logging.getLogger("SIGNALING")
logging.basicConfig(level=logging.INFO)

# Connected peers: id -> websocket
peers: Dict[str, websockets.WebSocketServerProtocol] = {}

async def handler(websocket): # type: ignore
    peer_id = str(uuid.uuid4())[:8]
    peers[peer_id] = websocket
    
    logger.info(f"Peer connected: {peer_id}")
    
    try:
        # Welcome the peer
        await websocket.send(json.dumps({
            "type": "welcome",
            "id": peer_id,
            "peers": list(peers.keys()) # Bootstrap with known peers
        }))
        
        async for message in websocket:
            data = json.loads(message)
            msg_type = data.get("type")
            target_id = data.get("target")
            
            if msg_type in ["offer", "answer", "ice"]:
                if target_id in peers:
                    # Relay message to target
                    logger.debug(f"Relaying {msg_type} from {peer_id} to {target_id}")
                    # Tag sender so target knows who it's from
                    data["sender"] = peer_id
                    await peers[target_id].send(json.dumps(data))
                else:
                    logger.warning(f"Target peer {target_id} not found")
            
    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        logger.info(f"Peer disconnected: {peer_id}")
        del peers[peer_id]

async def main():
    port = 8421
    logger.info(f"Signaling Server running on ws://0.0.0.0:{port}")
    async with websockets.serve(handler, "0.0.0.0", port):
        await asyncio.Future()  # Run forever

if __name__ == "__main__":
    asyncio.run(main())

# ═══════════════════════════════════════════════════════════════════════════════
#     JACKKNIFE AI
#     π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
