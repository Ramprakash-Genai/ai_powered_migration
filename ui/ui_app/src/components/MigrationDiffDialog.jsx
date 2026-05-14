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
} from '@mui/material';

export default function MigrationDiffDialog({
    open,
    file,
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
                <Button onClick={onClose} sx={{ textTransform: 'none' }}>
                    Close
                </Button>

                <Button
                    variant="outlined"
                    color="error"
                    onClick={handleReject}
                    sx={{ textTransform: 'none', fontWeight: 800 }}
                >
                    Not approved
                </Button>

                <Button
                    variant="contained"
                    onClick={handleApprove}
                    sx={{ textTransform: 'none', fontWeight: 800 }}
                >
                    Approved
                </Button>
            </DialogActions>
        </Dialog>
    );
}