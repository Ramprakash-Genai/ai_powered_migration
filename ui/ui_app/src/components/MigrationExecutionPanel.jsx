import { Box, Typography, Radio, Divider } from '@mui/material';

export default function MigrationExecutionPanel({
    files = [],
    selectedFile,
    onSelectFile,
}) {
    return (
        <Box sx={{ mt: 1 }}>
            <Typography fontWeight={800}>Migration Review (Agent‑4)</Typography>
            <Divider sx={{ my: 1 }} />

            {files.map((file) => (
                <Box key={file.path} sx={{ display: 'flex', alignItems: 'center', mb: 0.5 }}>
                    <Radio
                        disabled={file.status !== 'PENDING'}
                        checked={selectedFile === file.path}
                        onChange={() => onSelectFile?.(file.path)}
                    />
                    <Typography component="span" sx={{ fontSize: 14, whiteSpace: 'nowrap' }}>
                        {file.path}
                    </Typography>


                    {/* Small status badge */}
                    <Typography
                        component="span"
                        sx={{
                            ml: 1,
                            fontSize: 12,
                            color:
                                file.status === 'APPROVED'
                                    ? 'success.main'
                                    : file.status === 'REJECTED'
                                        ? 'error.main'
                                        : 'text.secondary',
                            fontWeight: 700,
                        }}
                    >
                        {file.status === 'PENDING'
                            ? '(Pending)'
                            : file.status === 'APPROVED'
                                ? '(Approved)'
                                : '(Rejected)'}
                    </Typography>
                </Box>
            ))}
        </Box>
    );
}