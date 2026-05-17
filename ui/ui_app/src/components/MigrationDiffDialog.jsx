import { useEffect, useState } from 'react';
import {
    Box,
    Button,
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions,
    Typography,
    Divider,
    TextField,
    Alert,
    Backdrop,
    CircularProgress,
} from '@mui/material';

export default function MigrationDiffDialog({
    open,
    file,
    loading,
    onClose,
    onApprove,
    onReject,
}) {
    const [comment, setComment] = useState('');
    const [err, setErr] = useState('');

    useEffect(() => {
        if (open) {
            setComment('');
            setErr('');
        }
    }, [open]);

    const handleApprove = () => {
        setErr('');
        onApprove?.(file?.path);
    };

    const handleReject = () => {
        if (!comment.trim()) {
            setErr('Comment is mandatory when you choose Not approved.');
            return;
        }
        setErr('');
        onReject?.(file?.path, comment.trim());
    };

    return (
        <Dialog open={open} onClose={onClose} maxWidth="lg" fullWidth>
            <DialogTitle sx={{ fontWeight: 800 }}>
                Verify Difference — {file?.path || ''}
            </DialogTitle>

            <DialogContent dividers sx={{ minHeight: 380 }}>
                <Backdrop
                    open={Boolean(loading)}

                    sx={{
                        color: '#fff',
                        backgroundColor: 'rgba(0,0,0,0.4)',
                        zIndex: (theme) => theme.zIndex.modal + 1
                    }}

                >
                    <CircularProgress color="inherit" />
                </Backdrop>
                {err ? <Alert severity="error" sx={{ mb: 2 }}>{err}</Alert> : null}

                <Typography variant="body2" sx={{ color: 'text.secondary', mb: 1 }}>
                    Compare the existing Selenium file vs migrated Playwright file and approve or reject.
                </Typography>

                <Divider sx={{ mb: 2 }} />

                {/* Side-by-side compare */}
                <Box
                    sx={{
                        display: 'grid',
                        gridTemplateColumns: '1fr 1fr',
                        gap: 2,
                        alignItems: 'start',
                    }}
                >
                    <Box
                        sx={{
                            border: '1px solid rgba(0,0,0,0.08)',
                            borderRadius: 2,
                            p: 1.5,
                            overflow: 'auto',
                            maxHeight: 320,
                            background: 'rgba(255,255,255,0.7)',
                        }}
                    >
                        <Typography fontWeight={800} sx={{ mb: 0.5 }}>
                            Selenium (Original)
                        </Typography>
                        <Typography variant="caption" sx={{ color: 'text.secondary', mb: 1 }}>
                            {file?.source_path || 'Source file path not available'}
                        </Typography>
                        <pre style={{ margin: 0, whiteSpace: 'pre', overflowX: 'auto' }}>
                            {file?.original || ''}
                        </pre>
                    </Box>

                    <Box
                        sx={{
                            border: '1px solid rgba(0,0,0,0.08)',
                            borderRadius: 2,
                            p: 1.5,
                            overflow: 'auto',
                            maxHeight: 320,
                            background: 'rgba(255,255,255,0.7)',
                        }}
                    >
                        <Typography fontWeight={800} sx={{ mb: 0.5 }}>
                            Playwright (Migrated)
                        </Typography>
                        <Typography variant="caption" sx={{ color: 'text.secondary', mb: 1 }}>
                            {file?.target_path || 'Target file path not available'}
                        </Typography>
                        <pre style={{ margin: 0, whiteSpace: 'pre', overflowX: 'auto' }}>
                            {file?.migrated || ''}
                        </pre>
                    </Box>
                </Box>

                <Divider sx={{ my: 2 }} />

                {/* Comment (mandatory only for reject) */}
                {/* ✅ Model justification (for repair / deny case) */}
                {file?.justification && (
                    <Alert
                        severity={file?.decision === 'DENIED' ? 'error' : 'info'}
                        sx={{ mb: 2 }}
                    >
                        {file.justification}
                    </Alert>
                )}
                <TextField
                    fullWidth
                    multiline
                    minRows={3}
                    label="Comment (mandatory if Not approved)"
                    placeholder="Explain what is wrong in migrated code (example: locator strategy incorrect, missing assertion, etc.)"
                    value={comment}
                    onChange={(e) => setComment(e.target.value)}
                />
            </DialogContent>

            <DialogActions>
                <Button onClick={onClose} disabled={loading} sx={{ textTransform: 'none' }}>
                    Close
                </Button>

                {/* ✅ Hide actions if model DENIED the user */}
                {file && (
                    <>
                        <Button
                            variant="outlined"
                            color="error"
                            onClick={handleReject} disabled={loading}
                            sx={{ textTransform: 'none', fontWeight: 800 }}
                        >
                            Not approved
                        </Button>

                        <Button
                            variant="contained"
                            onClick={handleApprove} disabled={loading}
                            sx={{ textTransform: 'none', fontWeight: 800 }}
                        >
                            Approved
                        </Button>
                    </>
                )}
            </DialogActions>
        </Dialog>
    );
}