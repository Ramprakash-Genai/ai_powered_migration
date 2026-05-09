// src/api/projectNormalization.js

import axios from 'axios';

//const API_BASE_URL = 'http://127.0.0.1:5000';
const API_BASE_URL = 'http://localhost:8000';

/**
 * Calls Agent-2: Project Normalization (NIM) backend API
 * Input: Project Detection output
 * Output: Normalized Intermediate Model (NIM)
 */
export async function buildProjectNormalization(detectionResult) {
    try {
        const res = await axios.post(
            `${API_BASE_URL}/api/project-normalization/build`,
            detectionResult,
            {
                headers: {
                    'Content-Type': 'application/json',
                },
                timeout: 20000,
            }
        );

        return res.data;
    } catch (error) {
        const message =
            error?.response?.data?.detail ||
            error?.message ||
            'Unknown error during project normalization';

        return {
            error: true,
            message,
        };
    }
}