import { useMemo, useState } from 'react';
import {
    Box,
    Button,
    Divider,
    Paper,
    Typography,
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions,
    FormControl,
    MenuItem,
    Select,
    TextField,
} from '@mui/material';
import { overrideProjectDetection } from '../api/projectDetection';

export default function MigrationOverview({
    detectionResult,
    onUpdateDetection,
    onResetFlow,
}) {
    if (!detectionResult) return null;

    const {
        input_type,
        input_path,
        user_project_style,
        name,
        language,
        bdd_framework,
        build_tool,
        runner,
        confidence,
        report_type,
        steps,
        screenshots,
        evidence,
    } = detectionResult;

    const [open, setOpen] = useState(false);
    const [reason, setReason] = useState('');
    const [correctedLanguage, setCorrectedLanguage] = useState('unknown');
    const [correctedFramework, setCorrectedFramework] = useState('');
    const [correctedBuildTool, setCorrectedBuildTool] = useState('');
    const [correctedRunner, setCorrectedRunner] = useState('');
    const [decisionMsg, setDecisionMsg] = useState(null);
    const [needHardResetConfirm, setNeedHardResetConfirm] = useState(false);

    const repoMode = input_type === 'repository';
    const htmlMode = input_type === 'html_report';

    const displayedConfidence = `${Math.round((confidence || 0) * 100)}%`;

    const openDialog = () => {
        setDecisionMsg(null);
        setNeedHardResetConfirm(false);
        setReason('');
        setCorrectedLanguage('unknown');
        setCorrectedFramework('');
        setCorrectedBuildTool('');
        setCorrectedRunner('');
        setOpen(true);
    };

    const closeDialog = () => setOpen(false);

    const handleConfirmOverride = async () => {
        // ✅ Frontend guard: repository correction requires language selection
        if (repoMode && correctedLanguage === 'unknown') {
            setDecisionMsg('❌ Please select the correct Programming Language to proceed.');
            return;
        }
        const userCorrection = repoMode
            ? {
                corrected_language: correctedLanguage,
                corrected_bdd_framework: correctedFramework || null,
                corrected_build_tool: correctedBuildTool || null,
                corrected_runner: correctedRunner || null,
                reason: reason || null,
            }
            : {
                reason: reason || null,
            };
        // ✅ If user selected SAME details as detected, treat as CONFIRMATION (not correction)
        if (repoMode) {
            const isSameAsDetected =
                correctedLanguage === (detectionResult.language || 'unknown') &&
                (!correctedFramework || correctedFramework === (detectionResult.bdd_framework || 'unknown')) &&
                (!correctedBuildTool || correctedBuildTool === (detectionResult.build_tool || 'unknown')) &&
                (!correctedRunner || correctedRunner === (detectionResult.runner || 'unknown'));

            if (isSameAsDetected) {
                const updated = {
                    ...detectionResult,
                    evidence: [
                        '✅ User confirmation matches with Originally detected repository details.',
                        ...(Array.isArray(detectionResult.evidence) ? detectionResult.evidence : []),
                    ],
                };

                setDecisionMsg('✅ Your confirmation matches the detected repository details.');
                setNeedHardResetConfirm(false);

                // ✅ Update Migration Overview so evidence reflects confirmation
                onUpdateDetection?.(updated);

                closeDialog();
                return;
            }

        }

        try {
            const res = await overrideProjectDetection({
                inputType: input_type,
                inputPath: input_path,
                userProjectStyle: user_project_style,
                currentDetection: detectionResult,
                userCorrection,
            });

            if (res.decision === 'accepted') {
                const updated = res.updated_detection;

                // ✅ Check if user merely CONFIRMED the same detected values
                const isSameAsDetected =
                    updated?.language === detectionResult.language &&
                    updated?.bdd_framework === detectionResult.bdd_framework &&
                    updated?.build_tool === detectionResult.build_tool &&
                    updated?.runner === detectionResult.runner;

                if (isSameAsDetected) {
                    setDecisionMsg('✅ Your confirmation matches the detected repository details.');
                } else {
                    setDecisionMsg('✅ You are correct. Identification updated based on your clarification.');
                }

                setNeedHardResetConfirm(false);
                onUpdateDetection?.(updated);
                closeDialog();
            } else {
                setDecisionMsg(
                    '❌ Originally detected repository details do not match the details you provided. Unable to move forward.'
                );
                setNeedHardResetConfirm(true);

                // ✅ IMPORTANT: merge backend conflict evidence into overview
                const updated = {
                    ...(res.updated_detection || detectionResult),
                    evidence: Array.isArray(res.evidence) && res.evidence.length
                        ? res.evidence
                        : [
                            '❌ Conflict detected between originally detected repository details and user-provided information.',
                            ...(detectionResult.evidence || []),
                        ],
                };

                onUpdateDetection?.(updated);
                closeDialog();
            }
        } catch (e) {
            // With the API patch, this should be rare. Still handle safely.
            const msg =
                e?.message ||
                e?.toString?.() ||
                'Unknown technical error while validating override';

            setDecisionMsg(`❌ Technical error while validating override: ${msg}`);
            setNeedHardResetConfirm(true);

            // Keep detected details visible and ask user to restart
            const updated = { ...detectionResult };
            const ev = Array.isArray(updated.evidence) ? [...updated.evidence] : [];
            ev.unshift(`❌ Technical error while validating override: ${msg}`);
            updated.evidence = ev;
            onUpdateDetection?.(updated);

            closeDialog();
        }
    };

    const handleHardReset = () => {
        // reset full flow to step-1
        onResetFlow?.();
    };

    return (
        <Paper
            elevation={0}
            sx={{
                borderRadius: 3,
                p: 2,
                height: 'calc(100vh - 32px)',
                display: 'flex',
                flexDirection: 'column',
                border: '1px solid rgba(0,0,0,0.06)',
                background: 'rgba(255,255,255,0.75)',
                backdropFilter: 'blur(10px)',
                overflow: 'hidden',
            }}
        >
            <Typography variant="h6" sx={{ fontWeight: 800 }}>
                Migration Overview
            </Typography>

            <Typography variant="body2" sx={{ mt: 0.5, color: 'text.secondary' }}>
                Please review the identified current project setup below and confirm.
            </Typography>

            <Divider sx={{ my: 2 }} />

            <Box sx={{ flex: 1, minHeight: 0, overflowY: 'auto', pr: 1 }}>
                <InfoRow label="Input Type" value={input_type} />
                <InfoRow label="Project / Report Name" value={name || 'N/A'} />

                {repoMode ? (
                    <>
                        <InfoRow label="Programming Language" value={language || 'N/A'} />
                        <InfoRow label="BDD Framework" value={bdd_framework || 'N/A'} />
                        <InfoRow label="Build Tool" value={build_tool || 'N/A'} />
                        <InfoRow label="Runner" value={runner || 'N/A'} />
                        <InfoRow label="Confidence" value={displayedConfidence} />
                    </>
                ) : (
                    <>
                        <InfoRow label="Report Type" value={report_type || 'unknown'} />
                        <InfoRow label="Steps Extracted" value={steps ? String(steps.length) : '0'} />
                        <InfoRow label="Screenshots Found" value={screenshots ? String(screenshots.length) : '0'} />
                        <InfoRow label="Confidence" value={displayedConfidence} />
                    </>
                )}

                {evidence?.length ? (
                    <>
                        <Divider sx={{ my: 2 }} />
                        <Typography variant="subtitle2" sx={{ fontWeight: 800, mb: 1 }}>
                            Evidence
                        </Typography>
                        <Box component="ul" sx={{ m: 0, pl: 2 }}>
                            {evidence.map((ev, idx) => (
                                <li key={idx}>
                                    <Typography variant="body2">{ev}</Typography>
                                </li>
                            ))}
                        </Box>
                    </>
                ) : null}
            </Box>

            <Divider sx={{ my: 2 }} />

            {!needHardResetConfirm && (
                <Box sx={{ display: 'flex', gap: 1.5 }}>
                    {!(repoMode && detectionResult.intent_mismatch) && (
                        <Button
                            fullWidth
                            variant="contained"
                            sx={{ textTransform: 'none', fontWeight: 700 }}
                            onClick={() => alert('Yes confirmed. Next agent integration will be implemented next.')}
                        >
                            Yes correct Go ahead for Migrate
                        </Button>
                    )}

                    <Button
                        fullWidth
                        variant="outlined"
                        color="error"
                        sx={{ textTransform: 'none', fontWeight: 700 }}
                        onClick={repoMode && detectionResult.intent_mismatch ? handleHardReset : openDialog}
                    >
                        No not correct don&apos;t Migrate
                    </Button>
                </Box>
            )}

            {/* If rejected, enforce hard reset */}
            {needHardResetConfirm && (
                <Box sx={{ mt: 1.5 }}>
                    <Button
                        fullWidth
                        variant="contained"
                        color="error"
                        sx={{ textTransform: 'none', fontWeight: 800 }}
                        onClick={handleHardReset}
                    >
                        Confirm (Restart from Step‑1)
                    </Button>
                </Box>
            )}

            {/* Popup Dialog */}
            <Dialog open={open} onClose={closeDialog} maxWidth="sm" fullWidth>
                <DialogTitle>Please justify what is wrong with current identification</DialogTitle>

                <DialogContent dividers>
                    <Typography variant="body2" sx={{ color: 'text.secondary', mb: 2 }}>
                        Review the detected values below and provide your correction.
                    </Typography>

                    {/* Read-only snapshot */}
                    <Box sx={{ mb: 2 }}>
                        <InfoRow label="Input Type" value={input_type} />
                        <InfoRow label="Project / Report Name" value={name || 'N/A'} />
                        {repoMode ? (
                            <>
                                <InfoRow label="Programming Language" value={language || 'N/A'} />
                                <InfoRow label="BDD Framework" value={bdd_framework || 'N/A'} />
                                <InfoRow label="Build Tool" value={build_tool || 'N/A'} />
                                <InfoRow label="Runner" value={runner || 'N/A'} />
                            </>
                        ) : (
                            <>
                                <InfoRow label="Report Type" value={report_type || 'unknown'} />
                                <InfoRow label="Steps Extracted" value={steps ? String(steps.length) : '0'} />
                                <InfoRow label="Screenshots Found" value={screenshots ? String(screenshots.length) : '0'} />
                            </>
                        )}
                    </Box>

                    {/* Correction form */}
                    {repoMode ? (
                        <>
                            <Typography variant="subtitle2" sx={{ fontWeight: 800, mb: 1 }}>
                                Your Correction (Repository)
                            </Typography>

                            <FormControl fullWidth size="small" sx={{ mb: 1.5 }}>
                                <Select value={correctedLanguage} onChange={(e) => setCorrectedLanguage(e.target.value)}>
                                    <MenuItem value="unknown">Select Correct Language…</MenuItem>
                                    <MenuItem value="java">Java</MenuItem>
                                    <MenuItem value="python">Python</MenuItem>
                                    <MenuItem value="csharp">C#</MenuItem>
                                </Select>
                            </FormControl>

                            <TextField
                                fullWidth
                                size="small"
                                label="Correct BDD Framework (optional)"
                                value={correctedFramework}
                                onChange={(e) => setCorrectedFramework(e.target.value)}
                                sx={{ mb: 1.5 }}
                            />

                            <TextField
                                fullWidth
                                size="small"
                                label="Correct Build Tool (optional)"
                                value={correctedBuildTool}
                                onChange={(e) => setCorrectedBuildTool(e.target.value)}
                                sx={{ mb: 1.5 }}
                            />

                            <TextField
                                fullWidth
                                size="small"
                                label="Correct Runner (optional)"
                                value={correctedRunner}
                                onChange={(e) => setCorrectedRunner(e.target.value)}
                                sx={{ mb: 1.5 }}
                            />
                        </>
                    ) : (
                        <>
                            <Typography variant="subtitle2" sx={{ fontWeight: 800, mb: 1 }}>
                                Your Confirmation (HTML Report)
                            </Typography>
                            <Typography variant="body2" sx={{ color: 'text.secondary', mb: 1.5 }}>
                                HTML reports do not contain reliable language/build metadata. Your confirmation will be used.
                            </Typography>
                        </>
                    )}

                    <TextField
                        fullWidth
                        size="small"
                        label="Reason (optional)"
                        value={reason}
                        onChange={(e) => setReason(e.target.value)}
                        inputProps={{ maxLength: 200 }}
                    />

                    {decisionMsg && (
                        <Typography sx={{ mt: 2, fontWeight: 700 }}>
                            {decisionMsg}
                        </Typography>
                    )}
                </DialogContent>

                <DialogActions>
                    <Button onClick={closeDialog}>Cancel</Button>
                    <Button variant="contained" onClick={handleConfirmOverride}>
                        Confirm
                    </Button>
                </DialogActions>
            </Dialog>
        </Paper>
    );
}

function InfoRow({ label, value }) {
    return (
        <Box sx={{ display: 'flex', justifyContent: 'space-between', gap: 2, mb: 1 }}>
            <Typography variant="body2" sx={{ fontWeight: 700 }}>
                {label}
            </Typography>
            <Typography variant="body2" sx={{ color: 'text.secondary', textAlign: 'right' }}>
                {value}
            </Typography>
        </Box>
    );
}
