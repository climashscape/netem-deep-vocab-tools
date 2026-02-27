/**
 * NETEM Deep Vocab Tools - Local API Gateway
 * Intercepts /api/ calls and handles them locally
 */

const LocalAPI = {
    verbsData: null,
    legacyData: null,
    originalFetch: null,
    DATA_VERSION: 9, // Increment this to force re-import of verbs and legacy data

    /**
     * Helper to fetch resources with path fallback
     */
    async fetchResource(filename) {
        const paths = [
            `static/${filename}`,
            `./static/${filename}`,
            `../static/${filename}`
        ];
        
        for (const path of paths) {
            try {
                const resp = await fetch(path);
                if (resp.ok) return resp;
                console.warn(`LocalAPI: Path ${path} returned ${resp.status}`);
            } catch (e) {
                console.warn(`LocalAPI: Failed to fetch ${path}`, e);
            }
        }
        return null;
    },

    /**
     * Initialize the local API by loading data
     */
    async init(fetchProxy = null) {
        if (fetchProxy) this.originalFetch = fetchProxy;
        
        try {
            // Bootstrap settings from .env if not present
            this.bootstrap();

            // 1. Sync from backend if available
            await this.syncFromBackend();

            // Load legacy data for fallback
            // Priority: Window Global (Inline JS) > Fetch Resource
            if (window.NETEM_LEGACY_DATA) {
                this.legacyData = window.NETEM_LEGACY_DATA;
                console.log(`LocalAPI: Loaded ${Object.keys(this.legacyData).length} legacy records from inline JS.`);
            } else {
                const legacyResp = await this.fetchResource('legacy_data.json');
                if (legacyResp) {
                    try {
                        this.legacyData = await legacyResp.json();
                        console.log(`LocalAPI: Loaded ${Object.keys(this.legacyData).length} legacy records.`);
                    } catch (jsonErr) {
                        console.error("LocalAPI: JSON parse error for legacy_data", jsonErr);
                    }
                } else {
                    console.error("LocalAPI: Critical - Could not load legacy_data.json from any path.");
                }
            }

            // Wait for DB to be ready
            if (window.db) {
                try {
                    // Timeout race for initial DB connection
                    await Promise.race([
                        window.db.open(),
                        new Promise((_, reject) => setTimeout(() => reject(new Error("DB Open Timeout")), 2000))
                    ]);
                    console.log("LocalAPI: Database opened.");
                    
                    // Check Data Version
                    const currentVersion = parseInt(localStorage.getItem('data_version') || '0');
                    const needsUpdate = currentVersion < this.DATA_VERSION;
                    
                    if (needsUpdate) {
                        console.log(`LocalAPI: Data version mismatch (Current: ${currentVersion}, New: ${this.DATA_VERSION}). Clearing verbs table for fresh import...`);
                        if (window.db.verbs) await window.db.verbs.clear();
                        localStorage.setItem('data_version', this.DATA_VERSION.toString());
                        // Reset legacy imported flag to force re-check
                        localStorage.removeItem('legacy_data_imported_v3');
                    }

                    // 1. Smart Import/Merge legacy data into explanations table
                    // We check if we've fully imported before, or if the DB count is suspiciously low
                    const legacyImported = localStorage.getItem('legacy_data_imported_v3');
                    const expCount = await window.db.explanations.count();
                    const legacyCount = this.legacyData ? Object.keys(this.legacyData).length : 0;

                    // If not marked as imported, OR DB has fewer records than legacy (indicating partial/failed import)
                    if (this.legacyData && (!legacyImported || expCount < legacyCount || needsUpdate)) {
                        const legacyEntries = Object.entries(this.legacyData);
                        if (legacyEntries.length > 0) {
                            console.log(`LocalAPI: reconciling legacy data (DB: ${expCount}, Legacy: ${legacyCount})...`);
                            
                            // Get all existing keys to perform a "safe insert" (don't overwrite user data)
                            // This is efficient even for 5000+ keys
                            const existingKeys = new Set(await window.db.explanations.toCollection().primaryKeys());
                            
                            const explanationsToAdd = [];
                            const now = new Date().toISOString();
                            
                            for (const [word, val] of legacyEntries) {
                                // Normalize key to handle word:verb suffix
                                let key = word.toLowerCase();
                                if (key.endsWith(':verb')) {
                                    key = key.substring(0, key.length - 5);
                                }

                                // Only add if NOT present in DB
                                if (!existingKeys.has(key)) {
                                    let content = null;
                                    let image_url = null;
                                    let image_dicebear = null;
                                    let image_pollinations = null;

                                    // Support both string (old) and object (new) formats
                                    if (typeof val === 'string') {
                                        content = val;
                                    } else if (typeof val === 'object' && val !== null) {
                                        content = val.content;
                                        image_url = val.image_url;
                                        image_dicebear = val.image_dicebear;
                                        image_pollinations = val.image_pollinations;
                                    }

                                    // Ensure content is valid string
                                    if (content && typeof content === 'string' && content.length > 10) {
                                        // Check if this key is already in our pending list (handle duplicates in legacyData itself)
                                        // Although legacyData is object, maybe key normalization caused collision?
                                        const isDuplicate = explanationsToAdd.some(e => e.query_key === key);
                                        if (!isDuplicate) {
                                            explanationsToAdd.push({
                                                mode: 'single',
                                                query_key: key,
                                                content: content,
                                                image_url: image_url,
                                                image_dicebear: image_dicebear,
                                                image_pollinations: image_pollinations,
                                                created_at: now
                                            });
                                        }
                                    }
                                }
                            }
                            
                            if (explanationsToAdd.length > 0) {
                                try {
                                    console.log(`LocalAPI: Adding ${explanationsToAdd.length} missing records...`);
                                    // Use bulkPut instead of bulkAdd to avoid ConstraintError if keys exist
                                    await window.db.explanations.bulkPut(explanationsToAdd);
                                    console.log(`LocalAPI: Successfully merged legacy data.`);
                                    localStorage.setItem('legacy_data_imported_v3', 'true');
                                } catch (importErr) {
                                    console.error("LocalAPI: Failed to import legacy data", importErr);
                                }
                            } else {
                                console.log("LocalAPI: All legacy records already exist.");
                                localStorage.setItem('legacy_data_imported_v3', 'true');
                            }
                        }
                    } else if (expCount > 0) {
                        console.log(`LocalAPI: DB seems up to date (${expCount} records).`);
                    } else {
                        console.warn("LocalAPI: No legacy data found to import.");
                    }

                    // 2. Check if we need to import netem_full_list into verbs table
                    if (window.db.verbs) {
                        const verbCount = await DB.getVerbsCount();
                        // If count is less than 5530, it means we might have missing entries due to casing deduplication
                        // or it's a fresh install. We should reload the full list.
                        if (verbCount < 5530 || needsUpdate) {
                            console.log(`LocalAPI: Verbs table has ${verbCount} entries (expected 5530), importing full list...`);
                            
                            let rawData = null;
                            
                            // Priority: Window Global (Inline JS) > Fetch Resource
                            if (window.NETEM_FULL_LIST) {
                                console.log("LocalAPI: Using inline NETEM_FULL_LIST.");
                                rawData = window.NETEM_FULL_LIST;
                            } else {
                                try {
                                    const response = await this.fetchResource('netem_full_list.json');
                                    if (response) {
                                        rawData = await response.json();
                                    }
                                } catch (fetchErr) {
                                    console.error("LocalAPI: Failed to fetch netem_full_list", fetchErr);
                                }
                            }

                            if (rawData) {
                                const list = rawData["5530考研词汇词频排序表"] || [];
                                
                                if (list.length > 0) {
                                    // Clear table first to avoid key constraints if we're re-importing
                                    if (verbCount > 0 && verbCount < 5530) {
                                        console.warn("LocalAPI: Clearing incomplete verbs table before re-import...");
                                        await window.db.verbs.clear();
                                    }

                                    // Validate first item structure for debugging
                                    if (list.length > 0) {
                                        const firstItem = list[0];
                                        console.log("LocalAPI: Validating first item structure:", JSON.stringify(firstItem));
                                        if (!firstItem["单词"] && !firstItem.word) {
                                            console.error("LocalAPI: Invalid item structure. Keys found:", Object.keys(firstItem));
                                        }
                                    }

                                    const verbsToInsert = list.map(item => {
                                        // Handle both English and Chinese keys for robustness
                                        const original = (item["单词"] || item.word || "").trim();
                                        
                                        if (!original) {
                                            // Skip empty entries silently
                                            return null;
                                        }

                                        // STRICT MODE: Use original case as key to ensure 5530 distinct entries
                                        // This allows 'May' and 'may' to coexist as separate entries
                                        return {
                                            word: original, // Primary Key: Exact string match
                                            original_word: original,
                                            frequency: parseInt(item["词频"] || item.frequency || 0),
                                            definition: item["释义"] || item.definition || "",
                                            pos: item["pos"] || "other",
                                            alternative_spelling: item["其他拼写"] || item.alternative_spelling || null,
                                            sequence: parseInt(item["序号"] || item.sequence || 0)
                                        };
                                    }).filter(v => v !== null); // Remove nulls
                                    
                                    if (verbsToInsert.length > 0) {
                                        await DB.bulkAddVerbs(verbsToInsert);
                                        console.log(`LocalAPI: Imported ${verbsToInsert.length} verbs to IndexedDB.`);
                                    } else {
                                        console.warn("LocalAPI: No valid verbs found to insert.");
                                    }
                                }
                            } else {
                                console.error("LocalAPI: Failed to fetch netem_full_list.json");
                            }
                        }
                    } else {
                        console.warn("LocalAPI: Verbs table schema missing, skipping import.");
                    }
                } catch (dbError) {
                    console.warn("LocalAPI: Database initialization issue (switching to fallback mode):", dbError.message || dbError);
                    // If it's a version error, it usually means another tab is holding the lock
                    if (dbError.name === 'VersionError' || dbError.name === 'Blocked') {
                        console.warn("LocalAPI: Database upgrade blocked. Please close other tabs of this application and reload.");
                    }
                }
            }

            // Optional: Keep in-memory cache for ultra-fast access if needed, 
            // but prefer DB for large datasets.
            if (!this.verbsData) {
                let loadedFromDb = false;
                if (window.db && window.db.verbs) {
                    try {
                        const count = await DB.getVerbsCount();
                        if (count > 0) {
                            this.verbsData = await DB.getAllVerbs();
                            console.log(`LocalAPI: Loaded ${this.verbsData.length} verbs from IndexedDB.`);
                            loadedFromDb = true;
                        }
                    } catch (e) {
                        console.warn("LocalAPI: Failed to load verbs from DB, falling back to JSON", e);
                    }
                }

                if (!loadedFromDb) {
                    // Fallback to inline JS or fetch
                    if (window.NETEM_FULL_LIST) {
                        this.verbsData = window.NETEM_FULL_LIST["5530考研词汇词频排序表"] || [];
                    } else {
                        const response = await this.fetchResource('netem_full_list.json');
                        if (response) {
                            const rawData = await response.json();
                            this.verbsData = rawData["5530考研词汇词频排序表"] || [];
                        }
                    }
                    
                    // Data Sanitization
                    if (this.verbsData && Array.isArray(this.verbsData)) {
                        this.verbsData = this.verbsData.filter(v => v && (v.word || v['单词']));
                        
                        // Populate DB with initial data if loaded from JSON
                        // This ensures consistent access via DB later and fixes schema issues
                        if (window.db && window.db.verbs) {
                            const dbCount = await DB.getVerbsCount();
                            if (dbCount === 0) {
                                console.log("LocalAPI: Populating verbs table from JSON...");
                                const dbRecords = this.verbsData.map(v => ({
                                    word: v.word || v['单词'],
                                    frequency: parseInt(v.frequency || v['词频'] || v.freq) || 0,
                                    pos: v.pos || v.part_of_speech || 'other',
                                    original_word: v.original_word || v.word || v['单词'],
                                    definition: v.definition || v['释义'],
                                    alternative_spelling: v.alternative_spelling || v['其他拼写'],
                                    sequence: v.sequence || v['序号']
                                }));
                                await DB.bulkAddVerbs(dbRecords);
                                console.log(`LocalAPI: Populated ${dbRecords.length} verbs to DB.`);
                            }
                        }
                    }
                }
            }
        } catch (error) {
            console.error("LocalAPI init error:", error);
        }
    },

    /**
     * Sync data from backend if available
     */
    async syncFromBackend() {
        // Static build optimization: skip backend sync by default to avoid 404s
        // Only enable if explicitly configured (e.g. in a non-static deployment)
        if (!window.ENABLE_BACKEND_SYNC) {
             // console.log("LocalAPI: Backend sync disabled (static mode).");
             return;
        }

        const fetchFn = this.originalFetch || window.fetch;
        try {
            console.log("LocalAPI: Checking for data sync from backend...");
            const response = await fetchFn('/api/sync/all_explanations');
            if (response.ok) {
                const data = await response.json();
                if (data && Array.isArray(data) && data.length > 0) {
                    console.log(`LocalAPI: Syncing ${data.length} records from backend...`);
                    // Prepare data for bulkPut
                    const records = data.map(item => ({
                        mode: item.mode,
                        query_key: item.query_key,
                        content: item.content,
                        image_url: item.image_url,
                        created_at: item.created_at || new Date().toISOString()
                    }));
                    await window.db.explanations.bulkPut(records);
                    console.log(`LocalAPI: Successfully synced ${data.length} records from backend.`);
                }
            }
        } catch (e) {
            console.warn("LocalAPI: Backend sync unavailable or failed.", e.message);
        }
    },

    /**
     * Bootstrap settings from .env (for local dev and initial setup)
     */
    bootstrap() {
        const currentSettings = JSON.parse(localStorage.getItem('app_settings') || '{}');
        
        // Populate basic defaults if settings are empty
        if (Object.keys(currentSettings).length === 0) {
            console.log("LocalAPI: Initializing empty default settings...");
            const defaults = {
                openai_api_key: '',
                openai_base_url: '',
                openai_model: '',
                image_provider: 'dicebear',
                daily_goal: '40'
            };
            localStorage.setItem('app_settings', JSON.stringify(defaults));
        } else {
            // Ensure daily_goal has a default if missing in existing settings
            if (!currentSettings.daily_goal) {
                currentSettings.daily_goal = '40';
                localStorage.setItem('app_settings', JSON.stringify(currentSettings));
            }
        }
    },

    /**
     * Main handler for API requests
     */
    async handle(route, data = {}) {
        console.log(`LocalAPI: Handling ${route}`, data);

        // Defensive check for database initialization
        // IMPORTANT: We need to check for /api/ebbinghaus/clear_all specifically
        // because it might be called when the DB is in a bad state, and we want to allow it to proceed
        // to clear things up.
        
        const isClearAll = route.includes('/api/ebbinghaus/clear_all');
        
        const needsDb = (route.includes('/api/ebbinghaus') || 
                       route.includes('/api/checkins') || 
                       route.includes('/api/learn_batch') || 
                       route.includes('/api/export') ||
                       route.includes('/api/mastery')) && !isClearAll; // Skip check for clear_all

        if (needsDb) {
            // Force init if window.db is missing but initDB exists
            if (window.initDB) {
                try {
                    // Add timeout race condition (2000ms)
                    await Promise.race([
                        window.initDB(),
                        new Promise((_, reject) => setTimeout(() => reject(new Error("DB Init Timeout")), 2000))
                    ]);
                } catch(e) { console.error("InitDB failed in handle", e); }
            }

            if (!window.db || !window.db.learning_progress) {
                console.error(`LocalAPI: Critical - window.db is undefined or schema missing while handling ${route}`);
                // Try to reopen if possible using the correct initDB from db.js
                if (window.initDB) {
                    try {
                        console.log("LocalAPI: Attempting to re-initialize database via initDB()...");
                        await window.initDB();
                    } catch(e) {
                         return { error: "Database initialization failed: " + e.message };
                    }
                } else {
                    return { error: "Database instance not found and initDB missing" };
                }
            }
            
            // Ensure tables exist (double check)
            if (!window.db.learning_progress || !window.db.explanations) {
                 console.warn("LocalAPI: Tables still not ready, waiting...");
                 await new Promise(r => setTimeout(r, 500));
                 // Last attempt to fix
                 if (window.initDB && (!window.db || !window.db.learning_progress)) {
                      await window.initDB();
                 }
                 
                 if (!window.db.learning_progress) return { error: "Database tables not initialized" };
            }
        }

        switch (route) {
            case '/api/verbs':
                const limit = parseInt(new URLSearchParams(route.split('?')[1]).get('limit') || 6000);
                
                // Attempt to initialize DB if not ready, but don't block heavily
                if (!window.db && window.initDB) {
                    try {
                        await Promise.race([
                            window.initDB(),
                            new Promise((_, r) => setTimeout(() => r("Timeout"), 1000))
                        ]);
                    } catch(e) {}
                }

                // Ensure verbsData is populated
                if (!this.verbsData || this.verbsData.length === 0) {
                    try {
                        // 1. Try DB first
                        if (window.db && window.db.verbs) {
                            try {
                                const count = await DB.getVerbsCount();
                                if (count > 0) {
                                    this.verbsData = await DB.getAllVerbs();
                                }
                            } catch(dbErr) {
                                console.warn("LocalAPI: DB access failed for verbs, falling back to JSON", dbErr);
                            }
                        }
                        
                        // 2. Fallback to JSON if DB failed or empty
                        if (!this.verbsData || this.verbsData.length === 0) {
                             if (window.NETEM_FULL_LIST) {
                                this.verbsData = window.NETEM_FULL_LIST["5530考研词汇词频排序表"] || [];
                            } else {
                                const response = await this.fetchResource('netem_full_list.json');
                                if (response) {
                                    const rawData = await response.json();
                                    this.verbsData = rawData["5530考研词汇词频排序表"] || [];
                                }
                            }
                        }

                        // Data Sanitization: Filter out invalid entries
                        if (this.verbsData && Array.isArray(this.verbsData)) {
                            const originalLength = this.verbsData.length;
                            this.verbsData = this.verbsData.filter(v => v && (v.word || v['单词']));
                            if (this.verbsData.length < originalLength) {
                                console.warn(`LocalAPI: Filtered out ${originalLength - this.verbsData.length} invalid verb records.`);
                            }
                        }
                    } catch (e) {
                        console.error("Failed to load verbs data in handle:", e);
                        return { error: "Failed to load verbs data" };
                    }
                }
                
                if (this.verbsData) {
                    return { items: this.verbsData.slice(0, limit), total: this.verbsData.length };
                }
                return { items: [], total: 0 };
            case '/api/settings':
                if (Object.keys(data).length > 0) {
                    // Merge with existing settings instead of overwriting
                    const current = JSON.parse(localStorage.getItem('app_settings') || '{}');
                    const updated = { ...current, ...data };
                    localStorage.setItem('app_settings', JSON.stringify(updated));
                    return { status: "success", settings: updated };
                } else {
                    return JSON.parse(localStorage.getItem('app_settings') || '{}');
                }

            case '/api/explain':
                // Check if data contains verbs or if it's nested
                // The router in index.html sends: { verbs: ..., mode: ..., refresh: ... } as 'data'
                // But sometimes it might be passed differently.
                // handleExplain expects 'data' to be the object containing { verbs, ... }
                // So this call seems correct: this.handleExplain(data)
                
                // However, the error 'can't access property "includes", verbs is undefined' means data.verbs is missing.
                // Let's add a defensive check and log
                if (!data || typeof data !== 'object') {
                    console.error("LocalAPI: /api/explain called with invalid data:", data);
                    return { error: "Invalid parameters" };
                }
                // Allow empty string as valid input (returns empty list), but block null/undefined
                if (data.verbs === undefined || data.verbs === null) {
                    console.warn("LocalAPI: /api/explain called without 'verbs' property:", data);
                    return { error: "No verbs provided" };
                }
                return await this.handleExplain(data);

            case '/api/ebbinghaus/record':
                return await Ebbinghaus.recordReview(data.verb, data.result);

            case '/api/mastery':
                return await Ebbinghaus.markMastered(data.verb);

            case '/api/ebbinghaus/due':
                return await Ebbinghaus.getDueVerbs();

            case '/api/checkins':
                if (Object.keys(data).length > 0) {
                    await DB.addCheckin(data.date);
                    return { status: "success" };
                } else {
                    return await DB.getCheckins();
                }

            case '/api/learn_batch':
                if (data.verb) {
                    await DB.addToBatch(data.verb);
                    return { status: "success" };
                } else if (data.clear) {
                    await DB.clearBatch();
                    return { status: "success" };
                } else {
                    return await DB.getLearnBatch();
                }

            case '/api/verbs':
                const rawItems = Array.isArray(this.verbsData) ? this.verbsData : [];
                // Map back to the Chinese keys expected by the UI if they are coming from DB (English keys)
                const items = rawItems.map(item => {
                    if (item.word) {
                        return {
                            "单词": item.word,
                            "词频": item.frequency,
                            "释义": item.definition,
                            "pos": item.pos,
                            "其他拼写": item.alternative_spelling,
                            "序号": item.sequence
                        };
                    }
                    return item;
                });
                return { items: items };

            case '/api/image/': {
                // The actual word is part of the URL, not data.verb in some calls
                // But in LocalAPI.handle(route, data), the route is usually stripped
                const verb = data.verb || route.split('/').pop();
                return { url: this.generateImageUrl(verb) };
            }

            case '/api/checkins/delete': // Special handling for DELETE proxy
                if (data.date) {
                    await window.db.checkins.delete(data.date);
                    return { status: "success" };
                }
                return { status: "error" };

            case '/api/export': {
                const allExplanations = await window.db.explanations.toArray();
                const allProgress = await window.db.learning_progress.toArray();
                const allCheckins = await window.db.checkins.toArray();
                
                // Ensure legacy data is loaded for filtering
                if (!this.legacyData) {
                    try {
                        if (window.NETEM_LEGACY_DATA) {
                            this.legacyData = window.NETEM_LEGACY_DATA;
                        } else {
                            const legacyResp = await this.fetchResource('legacy_data.json');
                            if (legacyResp) {
                                this.legacyData = await legacyResp.json();
                            }
                        }
                    } catch (e) {
                        console.warn("LocalAPI: Failed to reload legacy data for export filtering", e);
                    }
                }

                // Build a normalized map of legacy data for accurate filtering
                const legacyMap = new Map();
                if (this.legacyData) {
                    Object.entries(this.legacyData).forEach(([k, v]) => {
                        let key = k.toLowerCase();
                        if (key.endsWith(':verb')) key = key.substring(0, key.length - 5);
                        
                        let content = '';
                        if (typeof v === 'string') content = v;
                        else if (v && typeof v === 'object') content = v.content || '';
                        
                        // Normalize content: remove ALL whitespace to be robust against formatting changes
                        if (content) legacyMap.set(key, content.replace(/\s+/g, ''));
                    });
                }

                // Filter out legacy data (from default library) to reduce export size
                const filteredExplanations = allExplanations.filter(exp => {
                    // Only filter 'single' word explanations
                    if (exp.mode !== 'single') return true;
                    
                    const queryKey = exp.query_key.toLowerCase();
                    
                    // If word is in legacy library AND content matches exactly, exclude it
                    if (legacyMap.has(queryKey)) {
                        const legacyContent = legacyMap.get(queryKey);
                        const currentContent = (exp.content || '').replace(/\s+/g, '');
                        
                        // Check if the normalized content is the same
                        if (currentContent === legacyContent) {
                            return false;
                        }
                    }
                    return true;
                });

                const exportData = {
                    explanations: filteredExplanations,
                    progress: allProgress,
                    checkins: allCheckins,
                    settings: JSON.parse(localStorage.getItem('app_settings') || '{}'),
                    excluded: JSON.parse(localStorage.getItem('excludedVerbs') || '[]')
                };
                return exportData;
            }

            case '/api/ebbinghaus/status': {
                const allProgress = await window.db.learning_progress.toArray();
                const statusMap = {};
                allProgress.forEach(p => {
                    statusMap[p.verb.toLowerCase()] = p;
                });
                return statusMap;
            }

            case '/api/exclude':
                const excluded = JSON.parse(localStorage.getItem('excludedVerbs') || '[]');
                if (data.verb) {
                    if (data.exclude) {
                        if (!excluded.includes(data.verb)) excluded.push(data.verb);
                    } else {
                        const index = excluded.indexOf(data.verb);
                        if (index > -1) excluded.splice(index, 1);
                    }
                    localStorage.setItem('excludedVerbs', JSON.stringify(excluded));
                    return { status: "success" };
                }
                return excluded;

            case '/api/stats/daily_goal':
                const appSettings = JSON.parse(localStorage.getItem('app_settings') || '{}');
                const dailyGoal = parseInt(appSettings.daily_goal || '40');
                
                const now = new Date();
                const todayStart = new Date(now.getFullYear(), now.getMonth(), now.getDate()).toISOString();
                
                // Count new words learned today (review_count = 1 and last_review >= today_start)
                const newWordsToday = await window.db.learning_progress
                    .where('last_review').aboveOrEqual(todayStart)
                    .filter(p => p.review_count === 1)
                    .count();
                
                // Count remaining due reviews
                const dueWordsRemaining = await window.db.learning_progress
                    .where('next_review').belowOrEqual(now.toISOString())
                    .and(p => p.status === 'learning')
                    .count();
                
                return { 
                    daily_goal: dailyGoal,
                    new_words_today: newWordsToday,
                    due_words_remaining: dueWordsRemaining
                };

            case '/api/check_cache':
                if (Array.isArray(data.verbs)) {
                    // Batch check
                    const result = [];
                    for (const v of data.verbs) {
                        if (!v) continue; // Skip null/undefined/empty
                        const cached = await DB.getCachedResult('single', v.toLowerCase());
                        if (cached) result.push(v.toLowerCase());
                    }
                    return result;
                } else {
                    const queryKey = data.verbs.trim().toLowerCase();
                    const cachedData = await DB.getCachedResult(data.mode || 'single', queryKey);
                    return { cached: !!cachedData };
                }

            case '/api/ebbinghaus/clear_all':
                try {
                    // Check if DB is initialized
                    if (!window.db) {
                        if (window.initDB) await window.initDB();
                        if (!window.db) throw new Error("Database not initialized");
                    }
                    
                    if (window.db.learning_progress) await window.db.learning_progress.clear();
                    if (window.db.explanations) await window.db.explanations.clear();
                    if (window.db.checkins) await window.db.checkins.clear();
                    if (window.db.learn_batch) await window.db.learn_batch.clear();
                    
                    // Clear the verbs table too during full reset to allow re-importing
                    if (window.db.verbs) {
                        await window.db.verbs.clear();
                        console.log("LocalAPI: Verbs table cleared.");
                    }
                    if (data.reset_settings) {
                        localStorage.removeItem('app_settings');
                        localStorage.removeItem('visuals_provider');
                        localStorage.removeItem('excludedVerbs');
                    }
                    return { status: "success" };
                } catch (clearErr) {
                    console.error("LocalAPI: Failed to clear data", clearErr);
                    return { status: "error", message: clearErr.message };
                }

            case '/api/ebbinghaus/reset':
                if (data.verb) {
                    await window.db.learning_progress.delete(data.verb);
                    return { status: "success" };
                }
                return { status: "error", message: "Verb required" };

            case '/api/import':
                let importData = data.data;

                // Handle file input if provided as Blob/File
                if (data.file && data.file instanceof Blob) {
                    try {
                        const text = await new Promise((resolve, reject) => {
                            const reader = new FileReader();
                            reader.onload = (e) => resolve(e.target.result);
                            reader.onerror = (e) => reject(e);
                            reader.readAsText(data.file);
                        });
                        importData = JSON.parse(text);
                    } catch (e) {
                        return { status: "error", message: "Invalid file format. Please import a valid JSON backup file." };
                    }
                }
                
                if (!importData) return { status: "error", message: "No data provided" };

                try {
                    // 0. Clear existing data (as promised in UI)
                    await window.db.learning_progress.clear();
                    await window.db.explanations.clear();
                    await window.db.checkins.clear();
                    await window.db.learn_batch.clear();
                    if (window.db.verbs) {
                        await window.db.verbs.clear();
                    }

                    // 1. Restore Learning Progress
                    if (importData.progress && Array.isArray(importData.progress)) {
                        for (const item of importData.progress) {
                            if (item.verb) {
                                await DB.updateProgress(
                                    item.verb,
                                    item.stage || 0,
                                    item.last_review || new Date().toISOString(),
                                    item.next_review || new Date().toISOString(),
                                    item.status || 'learning',
                                    item.review_count || 0
                                );
                            }
                        }
                    }

                    // 2. Restore Explanations (including images)
                    if (importData.explanations && Array.isArray(importData.explanations)) {
                        // Remove IDs to avoid conflicts and let auto-increment handle it, 
                        // or keep them if we want exact replica. 
                        // Since we cleared the table, keeping IDs is fine.
                        await window.db.explanations.bulkPut(importData.explanations);
                    }

                    // 3. Restore Checkins
                    if (importData.checkins && Array.isArray(importData.checkins)) {
                        await window.db.checkins.bulkPut(importData.checkins);
                    }

                    // 4. Restore Settings
                    if (importData.settings) {
                        localStorage.setItem('app_settings', JSON.stringify(importData.settings));
                        // Sync Visuals Provider if present
                        if (importData.settings.image_provider) {
                            localStorage.setItem('visuals_provider', importData.settings.image_provider);
                        } else {
                            localStorage.removeItem('visuals_provider');
                        }
                    }

                    // 5. Restore Excluded Verbs
                    if (importData.excluded) {
                        localStorage.setItem('excludedVerbs', JSON.stringify(importData.excluded));
                    }

                    return { status: "success" };
                } catch (e) {
                    console.error("Import error in LocalAPI:", e);
                    return { status: "error", message: e.message };
                }

            default:
                console.error(`LocalAPI: Unhandled route ${route}`);
                throw new Error(`Route ${route} not implemented`);
        }
    },

    /**
     * Handle word explanation (with caching and batching)
     */
    async handleExplain(data) {
        const { verbs, mode, refresh, pos, only_images } = data;
        
        if (!verbs) {
            return { error: "No verbs provided" };
        }

        let verbList = [];
        if (typeof verbs === 'string') {
            if (verbs.includes(',')) {
                verbList = verbs.split(',').map(v => v.trim());
            } else {
                verbList = verbs.split(/\s+/).map(v => v.trim());
            }
        } else if (Array.isArray(verbs)) {
            verbList = verbs;
        } else {
            // Fallback for unexpected type
            verbList = [String(verbs).trim()];
        }
        
        verbList = verbList.filter(v => v.length > 0);

        if (mode === 'single') {
            const results = [];
            const images = {};
            
            for (const verb of verbList) {
                try {
                    const key = verb; 
                    let cachedData = null;
                
                if (!refresh) {
                    cachedData = await DB.getCachedResult('single', key);
                    
                    // Try to fetch from real backend (Dev Mode bridge)
                    // But ONLY if we are in a context where window.fetch can actually reach a backend
                    // In static build, this usually fails unless there is a proxy.
                    // To prevent 'fetch' called on non-window object error, we ensure we use window.fetch
                    if (!cachedData) {
                        try {
                            // Check if we are in a dev environment where the backend might exist
                            // Simple heuristic: If we are on localhost:8000, maybe the backend is at :8080?
                            // Or if we are in dev mode.
                            // But usually static build has NO backend.
                            // Let's just try a safe fetch if it looks like we might be connected.
                            
                            // NOTE: In the pure static build (dist), this is expected to fail 404.
                            // But we should catch it gracefully.
                            // Only check backend if we are NOT on a purely static host (e.g. GitHub Pages)
                            // Or if we specifically want to try connecting to a local backend
                            // For now, let's skip backend check if window.location.protocol is 'file:' or if we know we are static
                            const isStatic = true; // Assume static for dist build unless configured otherwise
                            
                            if (!isStatic) {
                                const backendUrl = `/api/explain?verbs=${verb}&mode=single`;
                                console.log(`LocalAPI: ${verb} not in IndexedDB, checking backend...`);
                                
                                // Add bypass header to prevent infinite recursion in static mode
                                const res = await window.fetch(backendUrl, {
                                    headers: { 'X-Bypass-Local': 'true' }
                                });
                                if (res.ok) {
                                    const backendResult = await res.json();
                                    if (backendResult && backendResult.explanations && backendResult.explanations[key]) {
                                        const content = backendResult.explanations[key];
                                        const imageUrl = backendResult.images ? Object.values(backendResult.images)[0] : null;
                                        
                                        cachedData = {
                                            content: content,
                                            image_url: imageUrl
                                        };
                                        
                                        // Save to IndexedDB so it's there next time
                                        await DB.saveToCache('single', key, content, imageUrl);
                                        console.log(`LocalAPI: Saved backend result for ${verb} to IndexedDB.`);
                                    }
                                }
                            } else {
                                // console.log(`LocalAPI: Skipping backend check for ${verb} (static mode).`);
                            }
                        } catch (e) {
                            console.warn(`LocalAPI: Backend check failed for ${verb}:`, e.message);
                        }
                    }

                    // Fallback to memory-loaded legacy data if still not found
                    if (!cachedData && this.legacyData) {
                        // Normalize key: try exact, then verb, then with :verb suffix
                        const exactKey = key;
                        const verbKey = `${key}:verb`; // Most legacy data keys are "word:verb"
                        
                        let legacyContent = this.legacyData[exactKey] || this.legacyData[verbKey];
                        
                        // Try case-insensitive lookup if still not found
                        if (!legacyContent) {
                            const lowerKey = key.toLowerCase();
                            const lowerVerbKey = `${lowerKey}:verb`;
                            
                            // Find case-insensitive match in keys
                            const allKeys = Object.keys(this.legacyData);
                            const foundKey = allKeys.find(k => 
                                k.toLowerCase() === lowerKey || 
                                k.toLowerCase() === lowerVerbKey
                            );
                            if (foundKey) legacyContent = this.legacyData[foundKey];
                        }

                        if (legacyContent) {
                            console.log(`LocalAPI: Found ${verb} in legacy fallback data.`);
                            // Legacy content might be an object { content: "...", ... } or just string? 
                            // Based on json file, it is an object with "content" property.
                            const contentStr = typeof legacyContent === 'string' ? legacyContent : legacyContent.content;
                            
                            cachedData = {
                                content: contentStr,
                                image_url: null
                            };
                            // Optionally save to DB now so it's there next time
                            DB.saveToCache('single', key, cachedData.content, null);
                        }
                    }
                }
                
                let content = (cachedData && cachedData.content) ? cachedData.content : null;
                let imageUrl = (cachedData && cachedData.image_url) ? cachedData.image_url : null;
                
                // If we have cached content, use it immediately
                const hasCachedContent = !!content;
                
                // We only need to fetch from LLM if:
                // 1. We are explicitly refreshing (refresh === true)
                // 2. We don't have any cached content (hasCachedContent === false)
                // 3. We are NOT just requesting images (only_images === false)
                const needLlmCall = (refresh || !hasCachedContent) && !only_images;
                
                // Image Provider Logic
                const standalone = localStorage.getItem('visuals_provider');
                let provider = 'none';
                if (standalone && standalone !== 'null') {
                    provider = standalone;
                } else {
                    const settings = JSON.parse(localStorage.getItem('app_settings') || '{}');
                    if (settings.image_provider) provider = settings.image_provider;
                }

                // If provider is 'none', we don't want an image
                if (provider === 'none') {
                    imageUrl = null;
                } else {
                    // We want an image. Do we have one?
                    if (!imageUrl) {
                        // No image in cache, generate one
                        imageUrl = this.generateImageUrl(verb);
                    } else {
                        // We have an image in cache. Does it match the current provider?
                        const isDiceBearUrl = typeof imageUrl === 'string' && imageUrl.includes('dicebear.com');
                        const isPollinationsUrl = typeof imageUrl === 'string' && imageUrl.includes('pollinations.ai');
                        
                        if (provider === 'dicebear' && !isDiceBearUrl) {
                            console.log(`LocalAPI: Provider mismatch (expected dicebear), regenerating image for ${verb}`);
                            imageUrl = this.generateImageUrl(verb);
                        } else if (provider === 'pollinations' && !isPollinationsUrl) {
                            console.log(`LocalAPI: Provider mismatch (expected pollinations), regenerating image for ${verb}`);
                            imageUrl = this.generateImageUrl(verb);
                        }
                    }
                }
                
                const settings = JSON.parse(localStorage.getItem('app_settings') || '{}');
                const hasApiKey = !!settings.openai_api_key;
                
                // Strict Cache Mode: If need LLM but no API key, skip LLM and go to fallback directly
                if (needLlmCall && !hasApiKey) {
                    console.warn(`LocalAPI: Strict Cache Mode - No API Key for ${verb}, skipping LLM call.`);
                    const basicDef = this.getBasicDefinition(verb);
                    if (basicDef) {
                        content = basicDef;
                    } else {
                        throw new Error("No API key and no local definition found.");
                    }
                } else if (needLlmCall) {
                    try {
                        console.log(`LocalAPI: Fetching new AI explanation for ${verb}...`);
                        content = await LLM.explainVerb(verb, pos || 'verb');
                        // Save to cache after successful LLM call
                        await DB.saveToCache('single', key, content, imageUrl);
                    } catch (e) {
                        console.error(`LLM error for ${verb}:`, e);
                        if (hasCachedContent) {
                            content = cachedData.content;
                        } else {
                            // Offline fallback: Use basic definition from the library
                            const basicDef = this.getBasicDefinition(verb);
                            if (basicDef) {
                                console.log(`LocalAPI: Using basic offline fallback for ${verb}`);
                                content = basicDef;
                            } else {
                                throw e;
                            }
                        }
                    }
                } else if ((!cachedData?.image_url && imageUrl) || (cachedData?.image_url !== imageUrl)) {
                        console.log(`LocalAPI: Updating cache with image URL for ${verb}`);
                        
                        // CRITICAL FIX: If we are updating only the image, do NOT overwrite existing content with null
                        const contentToSave = content || (cachedData ? cachedData.content : null);
                        
                        // Only save if we have either content OR we are explicitly requesting only_images
                        // If only_images is true, we allow saving null content IF there was no content before
                        // but if only_images is false (user requested detail), we should have content.
                        if (contentToSave || only_images) {
                            await DB.saveToCache('single', key, contentToSave, imageUrl);
                        }
                    }
                
                    results.push(content);
                    if (imageUrl) images[verb] = imageUrl;
                } catch (err) {
                    console.error(`LocalAPI Error processing verb ${verb}:`, err);
                    results.push(null);
                }
            }
            
            return {
                result: results.join('\n\n---\n\n'),
                images: images
            };
        } else {
            // mode === 'list'
            const key = verbList.map(v => v.toLowerCase()).sort().join(',');
            let cachedData = null;
            
            if (!refresh) {
                cachedData = await DB.getCachedResult('list', key);
                
                // For lists, we don't have a simple legacy fallback unless the exact list matches
                if (!cachedData && this.legacyData && this.legacyData[key]) {
                    cachedData = { content: this.legacyData[key] };
                    DB.saveToCache('list', key, cachedData.content, null);
                }
            }
            
            if (cachedData && !refresh) {
                return { result: cachedData.content };
            }
            
            const content = await LLM.explainVerb(verbs, pos || 'verb');
            await DB.saveToCache('list', key, content, null);
            return { result: content };
        }
    },

    /**
     * Get a basic offline definition for a word
     */
    getBasicDefinition(verb) {
        if (!this.verbsData) return null;
        
        // Try exact match first
        let found = this.verbsData.find(v => {
            const word = (v.word || v["单词"] || "").trim();
            return word === verb;
        });

        // Fallback to case-insensitive match
        if (!found) {
             const lowerKey = verb.toLowerCase();
             found = this.verbsData.find(v => {
                const word = (v.word || v["单词"] || "").trim().toLowerCase();
                return word === lowerKey;
            });
        }
        
        if (found) {
            const word = found.original_word || found.word || found["单词"];
            const def = found.definition || found["释义"] || "暂无释义";
            const pos = found.pos || "other";
            const freq = found.frequency || found["词频"] || 0;
            
            return `### ${word} (${def})\n\n> ⚠️ 正在离线使用。如需深度解析，请在联网后点击“刷新解析”。\n\n- **词性**: ${pos}\n- **释义**: ${def}\n- **词频**: ${freq}`;
        }
        return null;
    },

    /**
     * Image generation logic
     */
    generateImageUrl(verb) {
        // PRIORITY: Standalone Key > App Settings > Default
        const settings = JSON.parse(localStorage.getItem('app_settings') || '{}');
        const standalone = localStorage.getItem('visuals_provider');
        let provider = 'none';

        if (standalone && standalone !== 'null') {
             provider = standalone;
        } else {
             provider = settings.image_provider || 'none';
        }
        
        if (provider === 'none') {
            return ''; // Return empty string for no image
        }
        
        if (provider === 'pollinations') {
            const prompt = encodeURIComponent(`minimalist vector illustration of action ${verb} white background`);
            // Simple hash for stable seed
            let seed = 0;
            for (let i = 0; i < verb.length; i++) {
                seed = ((seed << 5) - seed) + verb.charCodeAt(i);
                seed |= 0;
            }
            seed = Math.abs(seed) % 1000000;
            
            if (settings.pollinations_api_key) {
                return `https://gen.pollinations.ai/image/${prompt}?model=${settings.pollinations_model || 'flux'}&nologo=true&seed=${seed}`;
            } else {
                return `https://image.pollinations.ai/prompt/${prompt}?model=${settings.pollinations_model || 'flux'}&nologo=true&seed=${seed}`;
            }
        } else {
            // Use 'icons' style to match backend and frontend consistency
            return `https://api.dicebear.com/9.x/icons/svg?seed=${encodeURIComponent(verb)}`;
        }
    }
};

window.LocalAPI = LocalAPI;