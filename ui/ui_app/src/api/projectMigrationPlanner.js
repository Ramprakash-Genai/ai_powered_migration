import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

export async function buildMigrationPlan(normalizedContext) {
    try {
        const res = await axios.post(
            `${API_BASE_URL}/api/project-migration-planner/plan`,
            normalizedContext,
            {
                headers: { 'Content-Type': 'application/json' },
                timeout: 20000,
            }
        );
        return res.data;
    } catch (err) {
        return {
            error: true,
            message:
                err?.response?.data?.detail ||
                err?.message ||
                'Migration planning failed',
        };
    }
}