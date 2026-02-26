/**
 * NETEM Deep Vocab Tools - Ebbinghaus Logic
 * Memory review stages and intervals (in minutes)
 */

const EBBINGHAUS_STAGES = [
    5,      // Stage 1: 5 minutes
    30,     // Stage 2: 30 minutes
    720,    // Stage 3: 12 hours
    1440,   // Stage 4: 1 day
    2880,   // Stage 5: 2 days
    5760,   // Stage 6: 4 days
    10080,  // Stage 7: 7 days
    21600,  // Stage 8: 15 days
    43200   // Stage 9: 30 days
];

const Ebbinghaus = {
    /**
     * Record a review result and calculate the next stage
     */
    async recordReview(verb, result) {
        // Fetch current progress from DB
        const progress = await window.db.learning_progress.get(verb);
        
        const now = new Date();
        let stage = 0;
        let reviewCount = 0;
        
        if (progress) {
            stage = progress.stage;
            reviewCount = progress.review_count;
        }
        
        let newStage = 0;
        if (result === 'remembered') {
            // Advance to next stage
            newStage = Math.min(stage + 1, EBBINGHAUS_STAGES.length);
        } else {
            // Reset to stage 0 if forgotten
            newStage = 0;
        }
        
        // Calculate next review time
        let nextReview;
        if (newStage === 0) {
            nextReview = new Date(now.getTime() + EBBINGHAUS_STAGES[0] * 60000);
        } else if (newStage <= EBBINGHAUS_STAGES.length) {
            nextReview = new Date(now.getTime() + EBBINGHAUS_STAGES[newStage - 1] * 60000);
        } else {
            // Mastered (Stage 9) - Set to 30 days later
            nextReview = new Date(now.getTime() + 30 * 24 * 60 * 60 * 1000);
        }
        
        const status = newStage < EBBINGHAUS_STAGES.length ? 'learning' : 'mastered';
        
        await DB.updateProgress(
            verb, 
            newStage, 
            now.toISOString(), 
            nextReview.toISOString(), 
            status, 
            reviewCount + 1
        );
        
        return {
            status: 'success',
            new_stage: newStage,
            next_review: nextReview.toISOString()
        };
    },

    /**
     * Mark a verb as mastered
     */
    async markMastered(verb) {
        const now = new Date();
        const stage = EBBINGHAUS_STAGES.length; // Stage 9
        const nextReview = new Date(now.getTime() + 365 * 24 * 60 * 60 * 1000); // 1 year later
        const status = 'mastered';
        
        await DB.updateProgress(
            verb, 
            stage, 
            now.toISOString(), 
            nextReview.toISOString(), 
            'mastered', 
            1
        );
        
        return {
            status: 'success',
            new_stage: stage
        };
    },

    /**
     * Get all due verbs for review
     */
    async getDueVerbs() {
        return await DB.getDueVerbs();
    }
};

window.Ebbinghaus = Ebbinghaus;
