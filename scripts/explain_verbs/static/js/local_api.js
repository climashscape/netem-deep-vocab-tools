/**
 * NETEM Deep Vocab Tools - Local API Gateway
 * Intercepts /api/ calls and handles them locally
 */

const LocalAPI = {
    verbsData: null,
    legacyData: null,
    originalFetch: null,

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
            try {
                const legacyResp = await fetch('static/legacy_data.json');
                if (legacyResp.ok) {
                    this.legacyData = await legacyResp.json();
                    console.log(`LocalAPI: Loaded ${Object.keys(this.legacyData).length} legacy records.`);
                }
            } catch (e) {
                console.warn("LocalAPI: Could not load legacy_data.json", e);
            }

            // Wait for DB to be ready
            if (window.db) {
                try {
                    await window.db.open();
                    console.log("LocalAPI: Database opened.");
                    
                    // 1. Check if we need to import legacy data into explanations table
                    const expCount = await window.db.explanations.count();
                    // If table is empty AND we have legacy data, import it.
                    // IMPORTANT: We must wait for this import to finish before proceeding,
                    // otherwise subsequent loads might think the DB is empty.
                    if (expCount === 0 && this.legacyData && Object.keys(this.legacyData).length > 0) {
                        console.log("LocalAPI: Explanations table is empty, importing legacy data...");
                        const explanations = [];
                        const now = new Date().toISOString();
                        
                        for (const [word, content] of Object.entries(this.legacyData)) {
                            // Ensure content is valid string
                            if (content && typeof content === 'string' && content.length > 10) {
                                explanations.push({
                                    mode: 'single',
                                    query_key: word.toLowerCase(),
                                    content: content,
                                    created_at: now
                                });
                            }
                        }
                        
                        if (explanations.length > 0) {
                            try {
                                await window.db.explanations.bulkPut(explanations);
                                console.log(`LocalAPI: Imported ${explanations.length} legacy records to explanations.`);
                            } catch (importErr) {
                                console.error("LocalAPI: Failed to import legacy data", importErr);
                            }
                        }
                    } else if (expCount > 0) {
                        console.log(`LocalAPI: DB has ${expCount} records, skipping legacy import.`);
                    } else {
                        console.warn("LocalAPI: No legacy data found to import.");
                    }

                    // 2. Check if we need to import netem_full_list into verbs table
                    if (window.db.verbs) {
                        const verbCount = await DB.getVerbsCount();
                        // If count is less than 5530, it means we might have missing entries due to casing deduplication
                        // or it's a fresh install. We should reload the full list.
                        if (verbCount < 5530) {
                            console.log(`LocalAPI: Verbs table has ${verbCount} entries (expected ~5530), importing full list...`);
                            const response = await fetch('static/netem_full_list.json');
                            if (response.ok) {
                                const rawData = await response.json();
                                const list = rawData["5530考研词汇词频排序表"] || [];
                                
                                if (list.length > 0) {
                                    const verbsToInsert = list.map(item => ({
                                        word: (item["单词"] || "").trim().toLowerCase(), // Lowercase key for lookup
                                        original_word: (item["单词"] || "").trim(), // Preserve original case
                                        frequency: item["词频"] || 0,
                                        definition: item["释义"] || "",
                                        pos: item["pos"] || "other",
                                        alternative_spelling: item["其他拼写"] || null,
                                        sequence: item["序号"] || 0
                                    }));
                                    
                                    await DB.bulkAddVerbs(verbsToInsert);
                                    console.log(`LocalAPI: Imported ${verbsToInsert.length} verbs to IndexedDB.`);
                                }
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
                    // Fallback to fetch if DB import failed or is taking too long
                    const response = await fetch('static/netem_full_list.json');
                    if (response.ok) {
                        const rawData = await response.json();
                        this.verbsData = rawData["5530考研词汇词频排序表"] || [];
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
                daily_goal: '20'
            };
            localStorage.setItem('app_settings', JSON.stringify(defaults));
        }
    },

    /**
     * Main handler for API requests
     */
    async handle(route, data = {}) {
        console.log(`LocalAPI: Handling ${route}`, data);

        // Defensive check for database initialization
        const needsDb = route.includes('/api/ebbinghaus') || 
                       route.includes('/api/checkins') || 
                       route.includes('/api/learn_batch') || 
                       route.includes('/api/export') ||
                       route.includes('/api/mastery');

        if (needsDb && !window.db) {
            console.error(`LocalAPI: Critical - window.db is undefined while handling ${route}`);
            return { error: "Database instance not found" };
        }

        switch (route) {
            case '/api/settings':
                if (Object.keys(data).length > 0) {
                    localStorage.setItem('app_settings', JSON.stringify(data));
                    return { status: "success", settings: data };
                } else {
                    return JSON.parse(localStorage.getItem('app_settings') || '{}');
                }

            case '/api/explain':
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
                
                // Filter out legacy data (from default library) to reduce export size
                const filteredExplanations = allExplanations.filter(exp => {
                    // Only filter 'single' word explanations
                    if (exp.mode !== 'single') return true;
                    
                    const queryKey = exp.query_key.toLowerCase();
                    
                    // If word is in legacy library AND content matches exactly, exclude it
                    if (this.legacyData && this.legacyData[queryKey]) {
                        // Check if the content is the same as the legacy version
                        // This allows user-updated explanations (refresh) to still be exported
                        if (this.legacyData[queryKey] === exp.content) {
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
                const dailyGoal = parseInt(appSettings.daily_goal || '20');
                
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
                await window.db.learning_progress.clear();
                await window.db.explanations.clear();
                await window.db.checkins.clear();
                await window.db.learn_batch.clear();
                // Clear the verbs table too during full reset to allow re-importing
                if (window.db.verbs) {
                    await window.db.verbs.clear();
                    console.log("LocalAPI: Verbs table cleared.");
                }
                if (data.reset_settings) {
                    localStorage.removeItem('app_settings');
                    localStorage.removeItem('excludedVerbs');
                }
                return { status: "success" };

            case '/api/ebbinghaus/reset':
                if (data.verb) {
                    await window.db.learning_progress.delete(data.verb);
                    return { status: "success" };
                }
                return { status: "error", message: "Verb required" };

            case '/api/import':
                const importData = data.data;
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
        
        let verbList = [];
        if (verbs.includes(',')) {
            verbList = verbs.split(',').map(v => v.trim());
        } else {
            verbList = verbs.split(/\s+/).map(v => v.trim());
        }
        verbList = verbList.filter(v => v.length > 0);

        if (mode === 'single') {
            const results = [];
            const images = {};
            
            for (const verb of verbList) {
                const key = verb.toLowerCase();
                let cachedData = null;
                
                if (!refresh) {
                    cachedData = await DB.getCachedResult('single', key);
                    
                    // NEW: Fallback to backend if not in IndexedDB
                    if (!cachedData && this.originalFetch) {
                        try {
                            console.log(`LocalAPI: ${verb} not in IndexedDB, checking backend...`);
                            const response = await this.originalFetch('/api/explain', {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify({ verbs: verb, mode: 'single', refresh: false })
                            });
                            if (response.ok) {
                                const backendResult = await response.json();
                                if (backendResult && backendResult.result) {
                                    // Extract first content and first image
                                    const content = backendResult.result;
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
                        } catch (e) {
                            console.warn(`LocalAPI: Backend check failed for ${verb}:`, e.message);
                        }
                    }

                    // Fallback to memory-loaded legacy data if still not found
                    if (!cachedData && this.legacyData && this.legacyData[key]) {
                        console.log(`LocalAPI: Found ${verb} in legacy fallback data.`);
                        cachedData = {
                            content: this.legacyData[key],
                            image_url: null
                        };
                        // Optionally save to DB now so it's there next time
                        DB.saveToCache('single', key, cachedData.content, null);
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
                
                // If we don't have an image URL in cache, generate one (this is local and fast)
                if (!imageUrl) {
                    imageUrl = this.generateImageUrl(verb);
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
                } else if (!cachedData?.image_url && imageUrl) {
                    // Case A: only_images is true, so we just want to save/update the image
                    // Case B: We already had content but no image_url in cache
                    console.log(`LocalAPI: Updating cache with image URL for ${verb}`);
                    // Use existing content if any, otherwise save with null content (to be filled later by analyzeVerbs)
                    await DB.saveToCache('single', key, content, imageUrl);
                }
                
                results.push(content);
                if (imageUrl) images[verb] = imageUrl;
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
        const key = verb.toLowerCase();
        
        // Find in in-memory cache
        const found = this.verbsData.find(v => {
            const word = (v.word || v["单词"] || "").toLowerCase();
            return word === key;
        });
        
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
        const settings = JSON.parse(localStorage.getItem('app_settings') || '{}');
        const provider = settings.image_provider || 'dicebear';
        
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
            return `https://api.dicebear.com/9.x/icons/svg?seed=${encodeURIComponent(verb)}`;
        }
    }
};

window.LocalAPI = LocalAPI;
