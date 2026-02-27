/**
 * NETEM Deep Vocab Tools - Database Layer
 * Using Dexie.js for IndexedDB management
 */

let db;
let dbInitPromise = null;

function initDB() {
    // Return existing promise if already initializing
    if (dbInitPromise) return dbInitPromise;

    dbInitPromise = new Promise(async (resolve, reject) => {
        try {
            // If db instance exists and is open, return it
            if (db && db.isOpen && db.isOpen()) {
                window.db = db;
                resolve(db);
                return;
            }
            
            // If db instance exists but is closed, try to open it
            if (db) {
                 window.db = db;
                 if (!db.isOpen()) {
                     try {
                        await db.open();
                     } catch(e) {
                        console.warn("Failed to re-open existing DB instance, creating new one...", e);
                        db = null; // Discard broken instance
                     }
                 }
                 if (db) {
                    resolve(db);
                    return;
                 }
            }

            // Initialize Dexie
            db = new Dexie("NetemVocabDB");

            // Define table schema
            // NOTE: When upgrading version, Dexie does NOT support changing primary key.
            // You must delete the old table and recreate it, or upgrade carefully.
            // Here we are incrementing version to force upgrade.
            db.version(6).stores({
                explanations: '[mode+query_key], mode, query_key, created_at',
                learning_progress: 'verb, stage, last_review, next_review, status',
                checkins: 'date',
                learn_batch: 'verb',
                verbs: 'word, frequency, pos, original_word' // Added verbs table for faster lookup, word is lowercase
            }).upgrade(tx => {
                // If we need to migrate data, do it here.
                // For now, since we are just ensuring schema consistency, no complex migration needed.
                // But if 'verbs' table PK changed from auto-increment to 'word', Dexie might complain.
                // To be safe, we can clear the table if it's causing issues, but upgrade() runs AFTER schema application attempt?
                // Actually upgrade() runs on old data before schema applied? No.
                // Dexie documentation says: "You cannot change primary key of an existing object store."
                // So if version 5 had a different PK for any of these, we are in trouble.
                // Version 5 defined: verbs: 'word, frequency...' which means PK is 'word'.
                // If previous version (implicit) had different schema, we might need to delete.
                
                // FORCE DELETE if we detect incompatible schema is not possible directly here easily without crashing first.
                // The best way to handle "Not yet support for changing primary key" is to increment version
                // and define null for the old table to delete it, then re-define it?
                // Or just clear the DB in init if we detect version mismatch?
            });

            // Handle DB errors globally
            db.on('versionchange', function(event) {
                event.target.close(); // Close db to allow upgrade
                console.warn("Database version changed, reloading page...");
                window.location.reload();
            });

            db.on('blocked', function () {
                console.warn('Database upgrade blocked - please close other tabs');
            });
            
            try {
                await db.open();
            } catch (err) {
                // Handle "Not yet support for changing primary key" error
                // This happens when we change schema incompatibly.
                // Solution: Delete the old DB and recreate.
                if (err.name === 'VersionError' || err.message.includes('primary key')) {
                    console.error("Database schema mismatch (Primary Key change detected). Deleting old DB...");
                    await Dexie.delete("NetemVocabDB");
                    // Re-init (recursive, but should pass now as DB is gone)
                    // We need to return a new promise or reset
                    db = new Dexie("NetemVocabDB");
                    db.version(6).stores({
                        explanations: '[mode+query_key], mode, query_key, created_at',
                        learning_progress: 'verb, stage, last_review, next_review, status',
                        checkins: 'date',
                        learn_batch: 'verb',
                        verbs: 'word, frequency, pos, original_word'
                    });
                    await db.open();
                } else {
                    throw err;
                }
            }
            
            window.db = db;
            resolve(db);
        } catch (e) {
            console.error("DB Init Failed:", e);
            db = null; // Reset global instance
            dbInitPromise = null; // Reset promise on failure to allow retry
            reject(e);
        }
    });

    return dbInitPromise;
}

// Auto-init on load
initDB().catch(e => console.error("Auto-init DB failed", e));

// Helper functions for database operations
const DB = {
    /**
     * Ensure DB is ready
     */
    async ensureDB() {
        if (!db || !db.isOpen()) {
            return await initDB();
        }
        return db;
    },

    /**
     * Get cached explanation
     */
    async getCachedResult(mode, queryKey) {
        try {
            await this.ensureDB();
            
            // Ensure table exists
            if (!db.explanations) {
                 console.error("DB Error: 'explanations' table missing. Re-initializing...");
                 // Force re-create instance
                 db = null; 
                 dbInitPromise = null;
                 await initDB();
                 if (!db.explanations) throw new Error("Failed to initialize explanations table");
            }
            
            const result = await db.explanations
                .where({ mode, query_key: queryKey })
                .first();
            return result || null;
        } catch (error) {
            console.error("DB error fetching cache:", error);
            // If error is "DatabaseClosedError", try to reopen
            if (error.name === 'DatabaseClosedError') {
                try {
                    dbInitPromise = null;
                    await initDB();
                    return await db.explanations.where({ mode, query_key: queryKey }).first() || null;
                } catch (retryError) {
                    console.error("Retry failed:", retryError);
                }
            }
            return null;
        }
    },

    /**
     * Save explanation to cache
     */
    async saveToCache(mode, queryKey, content, imageUrl = null) {
        try {
            await db.explanations.put({
                mode,
                query_key: queryKey,
                content,
                image_url: imageUrl,
                created_at: new Date().toISOString()
            });
        } catch (error) {
            console.error("DB error saving cache:", error);
        }
    },

    /**
     * Get all due verbs for review
     */
    async getDueVerbs() {
        const now = new Date().toISOString();
        try {
            return await db.learning_progress
                .filter(item => item.next_review <= now && item.status !== 'mastered')
                .toArray();
        } catch (error) {
            console.error("DB error fetching due verbs:", error);
            return [];
        }
    },

    /**
     * Update learning progress
     */
    async updateProgress(verb, stage, lastReview, nextReview, status, reviewCount) {
        try {
            // Normalize verb to lowercase to prevent duplicates (e.g. "Christian" vs "christian")
            const normalizedVerb = verb.toLowerCase();
            
            // Optional: Clean up any potential duplicate with different casing
            if (verb !== normalizedVerb) {
                // We try to delete the non-normalized version just in case
                // This is a "cleanup as we go" strategy
                try {
                    await db.learning_progress.delete(verb);
                } catch(e) { /* ignore if not exists */ }
            }

            await db.learning_progress.put({
                verb: normalizedVerb,
                stage,
                last_review: lastReview,
                next_review: nextReview,
                status,
                review_count: reviewCount
            });
        } catch (error) {
            console.error("DB error updating progress:", error);
        }
    },

    /**
     * Get checkins
     */
    async getCheckins() {
        return await db.checkins.toArray();
    },

    /**
     * Add checkin
     */
    async addCheckin(date) {
        await db.checkins.put({ date });
    },

    /**
     * Verbs table operations
     */
    async getVerbsCount() {
        if (!db.verbs) return 0;
        return await db.verbs.count();
    },

    async bulkAddVerbs(verbs) {
        if (!db.verbs) return;
        return await db.verbs.bulkPut(verbs);
    },

    async findVerb(word) {
        if (!db.verbs) return null;
        return await db.verbs.get(word.toLowerCase());
    },

    async getAllVerbs() {
        if (!db.verbs) return [];
        return await db.verbs.toArray();
    },

    /**
     * Batch operations
     */
    async getLearnBatch() {
        return await db.learn_batch.toArray();
    },

    async addToBatch(verb) {
        await db.learn_batch.put({ verb });
    },

    async removeFromBatch(verb) {
        await db.learn_batch.delete(verb);
    },

    async clearBatch() {
        await db.learn_batch.clear();
    }
};

window.DB = DB;
window.initDB = initDB;
