import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

/**
 * Agent‑4 Setup Validation:
 * Validate target path + repo name + selected stack.
 * No migration happens here yet.
 */
export async function validateMigrationSetup(payload) {
    try {
        const res = await axios.post(
            `${API_BASE_URL}/api/project-migration-setup/validate`,
            payload,
            { headers: { 'Content-Type': 'application/json' }, timeout: 20000 }
        );
        return res.data;
    } catch (err) {
        return {
            error: true,
            message:
                err?.response?.data?.detail ||
                err?.message ||
                'Unknown error during migration setup validation',
        };
    }
}