import { Box, Button, Divider, Paper, Typography } from '@mui/material';

export default function MigrationOverview({ detectionResult, onConfirm, onReject }) {
    if (!detectionResult) return null;

    const {
        input_type,
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

            {/* Scrollable content */}
            <Box sx={{ flex: 1, minHeight: 0, overflowY: 'auto', pr: 1 }}>
                <InfoRow label="Input Type" value={input_type} />
                <InfoRow label="Project / Report Name" value={name || 'N/A'} />

                {input_type === 'repository' ? (
                    <>
                        <InfoRow label="Programming Language" value={language || 'N/A'} />
                        <InfoRow label="BDD Framework" value={bdd_framework || 'N/A'} />
                        <InfoRow label="Build Tool" value={build_tool || 'N/A'} />
                        <InfoRow label="Runner" value={runner || 'N/A'} />
                        <InfoRow label="Confidence" value={`${Math.round((confidence || 0) * 100)}%`} />
                    </>
                ) : (
                    <>
                        <InfoRow label="Report Type" value={report_type || 'unknown'} />
                        <InfoRow label="Steps Extracted" value={steps ? String(steps.length) : '0'} />
                        <InfoRow label="Screenshots Found" value={screenshots ? String(screenshots.length) : '0'} />
                        <InfoRow label="Confidence" value={`${Math.round((confidence || 0) * 100)}%`} />

                        {steps?.length ? (
                            <>
                                <Divider sx={{ my: 2 }} />
                                <Typography variant="subtitle2" sx={{ fontWeight: 800, mb: 1 }}>
                                    Steps (Preview)
                                </Typography>
                                <Box component="ul" sx={{ m: 0, pl: 2 }}>
                                    {steps.slice(0, 10).map((s, idx) => (
                                        <li key={idx}>
                                            <Typography variant="body2">{s}</Typography>
                                        </li>
                                    ))}
                                </Box>
                                {steps.length > 10 && (
                                    <Typography variant="caption" sx={{ color: 'text.secondary' }}>
                                        Showing first 10 steps…
                                    </Typography>
                                )}
                            </>
                        ) : null}
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

            {/* Action buttons always visible */}
            <Box sx={{ display: 'flex', gap: 1.5 }}>
                <Button
                    fullWidth
                    variant="contained"
                    sx={{ textTransform: 'none', fontWeight: 700 }}
                    onClick={onConfirm}
                >
                    Yes correct Go ahead for Migrate
                </Button>

                <Button
                    fullWidth
                    variant="outlined"
                    color="error"
                    sx={{ textTransform: 'none', fontWeight: 700 }}
                    onClick={onReject}
                >
                    No not correct don&apos;t Migrate
                </Button>
            </Box>
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
