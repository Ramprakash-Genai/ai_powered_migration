import { useEffect, useMemo, useState } from 'react';
import {
    Box,
    Button,
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions,
    Typography,
    Divider,
    FormControl,
    MenuItem,
    Select,
    TextField,
    Alert,
    CircularProgress,
} from '@mui/material';
import { validateMigrationSetup } from '../api/projectMigrationSetup';

/**
 * Agent‑4 (Pre‑migration popup): Collect target stack + output path + new repo name.
 * Validates all fields on UI, then calls backend to validate path and repo name.
 */
export default function MigrationSetupDialog({
    open,
    onClose,
    sourceDetails,
    onValidated,
    onError,
    errorText,
}) {
    // Capability matrix (rule-based UI filtering)
    const OPTIONS = useMemo(
        () => ({
            java: {
                bdd: ['cucumber', 'gauge'],
                build: ['maven'],                // ✅ ONLY ONE
                runner: ['junit'],              // ✅ ONLY ONE
            },
            python: {
                bdd: ['pytest-bdd', 'behave'],
                build: ['pip'],                 // ✅ ONLY ONE
                runner: ['pytest'],             // ✅ ONLY ONE
            },
            csharp: {
                bdd: ['specflow', 'gauge'],
                build: ['dotnet'],              // ✅ ONLY ONE
                runner: ['dotnet test'],        // ✅ ONLY ONE
            },
        }),
        []
    );

    const [targetLanguage, setTargetLanguage] = useState('');
    const [targetBdd, setTargetBdd] = useState('');
    const [targetBuild, setTargetBuild] = useState('');
    const [targetRunner, setTargetRunner] = useState('');
    const [targetPath, setTargetPath] = useState('');
    const [newRepoName, setNewRepoName] = useState('');
    const [submitting, setSubmitting] = useState(false);
    const [loading, setLoading] = useState(false);

    // Reset dialog state when opened
    useEffect(() => {
        if (open) {
            setTargetLanguage('');
            setTargetBdd('');
            setTargetBuild('');
            setTargetRunner('');
            setTargetPath('');
            setNewRepoName('');
            onError?.('');
            setLoading(false);
        }
        else {
            setLoading(false);
            setSubmitting(false);
        }

    }, [open]);

    // Filtered dropdown lists based on selected language
    const languageOptions = [
        { value: 'java', label: 'Java (Playwright)' },
        { value: 'python', label: 'Python (Playwright)' },
        { value: 'csharp', label: 'C# (Playwright)' },
    ];

    const bddOptions = targetLanguage ? OPTIONS[targetLanguage]?.bdd || [] : [];
    const buildOptions = targetLanguage ? OPTIONS[targetLanguage]?.build || [] : [];
    const runnerOptions = targetLanguage ? OPTIONS[targetLanguage]?.runner || [] : [];

    // When language changes, clear dependent selections
    useEffect(() => {
        setTargetBdd('');

        if (targetLanguage) {
            const cfg = OPTIONS[targetLanguage];
            setTargetBuild(cfg?.build?.[0] || '');
            setTargetRunner(cfg?.runner?.[0] || '');
        } else {
            setTargetBuild('');
            setTargetRunner('');
        }
    }, [targetLanguage]);


    const allRequiredFilled =
        Boolean(targetLanguage) &&
        Boolean(targetBdd) &&
        Boolean(targetBuild) &&
        Boolean(targetRunner) &&
        Boolean(targetPath.trim()) &&
        Boolean(newRepoName.trim());

    const handleValidate = async () => {
        if (!allRequiredFilled) return;

        const payload = {
            target_language: targetLanguage,
            target_bdd: targetBdd,
            target_build_tool: targetBuild,
            target_runner: targetRunner,
            target_path: targetPath,
            repo_name: newRepoName,
        };

        try {
            setSubmitting(true);
            setLoading(true);

            await onValidated?.(payload);   // ✅ VERY IMPORTANT

        } catch (err) {
            console.error(err);
            onError?.('❌ Migration execution failed.');
        } finally {
            setLoading(false);
            setSubmitting(false);
        }
    };





    return (
        <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
            <DialogTitle sx={{ fontWeight: 800 }}>
                Select the correct technical details for Playwright Migration
            </DialogTitle>

            <DialogContent dividers>
                {/* Source summary */}
                {loading && (
                    <Box sx={{ display: 'flex', justifyContent: 'center', py: 2 }}>
                        <CircularProgress />
                    </Box>
                )}
                <Typography sx={{ fontWeight: 800, mb: 1 }}>
                    User Approved Existing Selenium Project details
                </Typography>

                <Box
                    sx={{
                        border: '1px solid rgba(0,0,0,0.08)',
                        borderRadius: 2,
                        p: 1.5,
                        mb: 2,
                        background: 'rgba(255,255,255,0.6)',
                    }}
                >
                    <Row label="Input Type" value={sourceDetails?.input_type} />
                    <Row label="Project / Report Name" value={sourceDetails?.name} />
                    {sourceDetails?.input_type === 'repository' ? (
                        <>
                            <Row label="Programming Language" value={sourceDetails?.language} />
                            <Row label="BDD Framework" value={sourceDetails?.bdd_framework} />
                            <Row label="Build Tool" value={sourceDetails?.build_tool} />
                            <Row label="Runner" value={sourceDetails?.runner} />
                        </>
                    ) : (
                        <>
                            <Row label="Report Type" value={sourceDetails?.report_type} />
                        </>
                    )}
                </Box>

                <Divider sx={{ mb: 2 }} />

                {/* Error */}
                {errorText ? <Alert severity="error" sx={{ mb: 2 }}>{errorText}</Alert> : null}

                {/* Target selection */}
                <Box sx={{ display: 'grid', gridTemplateColumns: '180px 1fr', gap: 1.25 }}>
                    <Typography sx={{ fontWeight: 700 }}>Programming Language</Typography>
                    <FormControl size="small" fullWidth>
                        <Select
                            value={targetLanguage}
                            displayEmpty
                            onChange={(e) => setTargetLanguage(e.target.value)}
                        >
                            <MenuItem value="" disabled>Select target language…</MenuItem>
                            {languageOptions.map((o) => (
                                <MenuItem key={o.value} value={o.value}>{o.label}</MenuItem>
                            ))}
                        </Select>
                    </FormControl>

                    <Typography sx={{ fontWeight: 700 }}>BDD Framework</Typography>
                    <FormControl size="small" fullWidth disabled={!targetLanguage}>
                        <Select
                            value={targetBdd}
                            displayEmpty
                            onChange={(e) => setTargetBdd(e.target.value)}
                        >
                            <MenuItem value="" disabled>Select BDD framework…</MenuItem>
                            {bddOptions.map((v) => (
                                <MenuItem key={v} value={v}>{v}</MenuItem>
                            ))}
                        </Select>
                    </FormControl>

                    <Typography sx={{ fontWeight: 700 }}>Build Tool</Typography>
                    <FormControl size="small" fullWidth disabled={!targetLanguage}>
                        <Select
                            value={targetBuild}
                            displayEmpty
                            onChange={(e) => setTargetBuild(e.target.value)}
                        >
                            <MenuItem value="" disabled>Select build tool…</MenuItem>
                            {buildOptions.map((v) => (
                                <MenuItem key={v} value={v}>{v}</MenuItem>
                            ))}
                        </Select>
                    </FormControl>

                    <Typography sx={{ fontWeight: 700 }}>Runner</Typography>
                    <FormControl size="small" fullWidth disabled={!targetLanguage}>
                        <Select
                            value={targetRunner}
                            displayEmpty
                            onChange={(e) => setTargetRunner(e.target.value)}
                        >
                            <MenuItem value="" disabled>Select runner…</MenuItem>
                            {runnerOptions.map((v) => (
                                <MenuItem key={v} value={v}>{v}</MenuItem>
                            ))}
                        </Select>
                    </FormControl>

                    <Typography sx={{ fontWeight: 700 }}>Absolute Path (target)</Typography>
                    <TextField
                        size="small"
                        value={targetPath}
                        onChange={(e) => setTargetPath(e.target.value)}
                        placeholder="C:/PlaywrightProjects"
                        fullWidth
                    />

                    <Typography sx={{ fontWeight: 700 }}>New Repository Name</Typography>
                    <TextField
                        size="small"
                        value={newRepoName}
                        onChange={(e) => setNewRepoName(e.target.value)}
                        placeholder="newproject"
                        fullWidth
                    />
                </Box>

                <Typography variant="caption" sx={{ color: 'text.secondary', display: 'block', mt: 1.5 }}>
                    Note: “I Approve to proceed for migration” will be enabled only after all fields are provided.
                </Typography>
            </DialogContent>

            <DialogActions>
                <Button onClick={onClose} sx={{ textTransform: 'none' }}>
                    Cancel
                </Button>

                <Button
                    variant="contained"
                    onClick={handleValidate}
                    disabled={!allRequiredFilled || submitting || loading}
                    sx={{ textTransform: 'none', fontWeight: 800 }}
                >
                    {loading ? 'Migrating…' : submitting ? 'Validating…' : 'I Approve to proceed for migration'}
                </Button>
            </DialogActions>
        </Dialog>
    );
}

function Row({ label, value }) {
    return (
        <Box sx={{ display: 'flex', justifyContent: 'space-between', gap: 2, mb: 0.5 }}>
            <Typography variant="body2" sx={{ fontWeight: 700 }}>{label}</Typography>
            <Typography variant="body2" sx={{ color: 'text.secondary', textAlign: 'right' }}>
                {String(value ?? '')}
            </Typography>
        </Box>
    );
}
