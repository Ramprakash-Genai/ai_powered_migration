import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

/**
 * Calls backend Project Detection API
 * POST /api/project-detection
 *
 * @param {Object} params
 * @param {string} params.userProjectStyle - java-selenium-bdd | python-selenium-bdd | csharp-selenium-bdd (intent)
 * @param {string} params.inputType - repository | html_report
 * @param {string} params.inputPath - absolute path to folder/file
 */
export async function detectProject({ userProjectStyle, inputType, inputPath }) {
    const payload = {
        user_project_style: userProjectStyle,
        input_type: inputType,
        input_path: inputPath,
    };

    const res = await axios.post(`${API_BASE_URL}/api/project-detection`, payload, {
        headers: { 'Content-Type': 'application/json' },
    });

    return res.data;
}
