import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

export async function detectProject({ userProjectStyle, inputType, inputPath }) {
    const payload = {
        user_project_style: userProjectStyle,
        input_type: inputType,
        input_path: inputPath,
    };

    const res = await axios.post(`${API_BASE_URL}/api/project-detection`, payload, {
        headers: { 'Content-Type': 'application/json' },
    });

    // ✅ Ensure detection result always carries input_path for later override validation
    return {
        ...res.data,
        input_path: inputPath,
        input_type: inputType,
        user_project_style: userProjectStyle,
    };
}

export async function overrideProjectDetection({
    inputType,
    inputPath,
    userProjectStyle,
    currentDetection,
    userCorrection,
}) {
    const payload = {
        input_type: inputType,
        input_path: inputPath || currentDetection?.input_path,
        user_project_style: userProjectStyle,
        current_detection: currentDetection,
        user_correction: userCorrection,
    };

    try {
        // ✅ IMPORTANT:
        // validateStatus prevents Axios from throwing on non-2xx
        const res = await axios.post(
            `${API_BASE_URL}/api/project-detection/override`,
            payload,
            {
                headers: { 'Content-Type': 'application/json' },
                validateStatus: () => true,
                timeout: 15000,
            }
        );

        // If backend returned nothing usable
        if (!res || typeof res.data === 'undefined' || res.data === null) {
            return {
                decision: 'rejected',
                updated_detection: currentDetection,
                validation_source: 'rule',
                evidence: ['❌ Technical issue: Empty response from backend override API.'],
                _http_status: res?.status,
            };
        }

        // Attach status for debugging if needed (harmless)
        if (typeof res.data === 'object' && res.data !== null && !res.data._http_status) {
            res.data._http_status = res.status;
        }

        // If backend returns FastAPI error shape { detail: ... } instead of decision
        if (typeof res.data === 'object' && res.data !== null && !res.data.decision) {
            return {
                decision: 'rejected',
                updated_detection: currentDetection,
                validation_source: 'rule',
                evidence: [
                    '❌ Technical issue: Backend did not return a decision field.',
                    `Details: ${JSON.stringify(res.data).slice(0, 250)}`,
                ],
                _http_status: res.status,
            };
        }

        return res.data;
    } catch (err) {
        // ✅ This is the key: NEVER throw; return deterministic response
        const msg =
            err?.message ||
            err?.toString?.() ||
            'Unknown client-side error while calling override API';

        return {
            decision: 'rejected',
            updated_detection: currentDetection,
            validation_source: 'rule',
            evidence: [`❌ Technical issue while validating override: ${msg}`],
        };
    }
}