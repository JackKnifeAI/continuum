// ═══════════════════════════════════════════════════════════════════════════════
//     WILDFIRE LOCAL MEMORY
//     IndexedDB Graph Store for Browser Nodes
//     Copyright (c) 2025 JackKnifeAI - AGPL-3.0 License
// ═══════════════════════════════════════════════════════════════════════════════

const DB_NAME = 'continuum-memory-v1';
const STORES = {
    CONCEPTS: 'concepts',
    LINKS: 'attention_links',
    VECTORS: 'embeddings'
};

class FlockDB {
    constructor() {
        this.db = null;
    }

    async init() {
        return new Promise((resolve, reject) => {
            const request = indexedDB.open(DB_NAME, 1);

            request.onerror = (event) => {
                console.error('[FlockDB] Error opening DB', event);
                reject(event);
            };

            request.onupgradeneeded = (event) => {
                const db = event.target.result;
                
                // Concepts Store (key: concept_name)
                if (!db.objectStoreNames.contains(STORES.CONCEPTS)) {
                    db.createObjectStore(STORES.CONCEPTS, { keyPath: 'name' });
                }

                // Links Store (auto-increment id, index by source)
                if (!db.objectStoreNames.contains(STORES.LINKS)) {
                    const linkStore = db.createObjectStore(STORES.LINKS, { autoIncrement: true });
                    linkStore.createIndex('source', 'source', { unique: false });
                    linkStore.createIndex('target', 'target', { unique: false });
                }

                // Vectors Store (key: concept_name)
                if (!db.objectStoreNames.contains(STORES.VECTORS)) {
                    db.createObjectStore(STORES.VECTORS, { keyPath: 'id' });
                }
            };

            request.onsuccess = (event) => {
                this.db = event.target.result;
                console.log('[FlockDB] Local memory graph initialized');
                resolve(this);
            };
        });
    }

    async saveConcept(concept) {
        return this._tx(STORES.CONCEPTS, 'readwrite', (store) => {
            store.put({
                name: concept.name,
                description: concept.description,
                created_at: new Date().toISOString()
            });
        });
    }

    async saveLink(source, target, strength) {
        return this._tx(STORES.LINKS, 'readwrite', (store) => {
            store.add({
                source: source,
                target: target,
                strength: strength,
                timestamp: new Date().toISOString()
            });
        });
    }

    async getConcepts() {
        return this._tx(STORES.CONCEPTS, 'readonly', (store) => {
            return store.getAll();
        });
    }

    async getLinks() {
        return this._tx(STORES.LINKS, 'readonly', (store) => {
            return store.getAll();
        });
    }

    // Helper for transactions
    _tx(storeName, mode, callback) {
        return new Promise((resolve, reject) => {
            if (!this.db) {
                reject(new Error("DB not initialized"));
                return;
            }
            const tx = this.db.transaction(storeName, mode);
            const store = tx.objectStore(storeName);
            
            let request;
            try {
                request = callback(store);
            } catch (e) {
                reject(e);
                return;
            }

            if (request && request instanceof IDBRequest) {
                request.onsuccess = () => resolve(request.result);
                request.onerror = () => reject(request.error);
            } else {
                // If callback didn't return a request (e.g. just started tx), resolve on tx complete
                tx.oncomplete = () => resolve();
                tx.onerror = () => reject(tx.error);
            }
        });
    }
}

// Export singleton
const flockDB = new FlockDB();
// window.flockDB = flockDB; // Expose globally for now

// ═══════════════════════════════════════════════════════════════════════════════
//     JACKKNIFE AI
//     π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
// ═══════════════════════════════════════════════════════════════════════════════
