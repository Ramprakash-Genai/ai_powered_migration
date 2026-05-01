import { useMemo, useState } from 'react';
import { Box, Paper, Typography, LinearProgress } from '@mui/material';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import Sidebar from '../components/Sidebar';
import MigrationChat from '../components/MigrationChat';
import MigrationOverview from '../components/MigrationOverview';

const STAGES = [
    'Select Source Style',
    'Confirm Target',
    'Parse Repo',
    'BDD Migration',
    'Locator Migration',
    'Script Generation',
    'Execution',
    'Review & Approve',
];

function humanStatus(status) {
    if (status === 'COMPLETED') return 'Completed';
    if (status === 'IN_PROGRESS') return 'In Progress';
    return 'Pending';
}

export default function MainLayout() {
    // ✅ 8-stage progress (unchanged conceptually)
    const [stageState, setStageState] = useState([
        'IN_PROGRESS',
        'PENDING',
        'PENDING',
        'PENDING',
        'PENDING',
        'PENDING',
        'PENDING',
        'PENDING',
    ]);

    // ✅ Detection result drives right panel visibility
    const [detectionResult, setDetectionResult] = useState(null);

    const progressPercent = useMemo(() => {
        const completed = stageState.filter((s) => s === 'COMPLETED').length;
        return Math.round((completed / STAGES.length) * 100);
    }, [stageState]);

    // Helpers to advance only first 4 steps for now:
    const markStageCompletedAndNextInProgress = (completedIndex, nextIndex) => {
        setStageState((prev) => {
            const updated = [...prev];
            updated[completedIndex] = 'COMPLETED';
            if (nextIndex != null && updated[nextIndex] !== 'COMPLETED') {
                updated[nextIndex] = 'IN_PROGRESS';
            }
            return updated;
        });
    };

    const setReviewStageInProgress = () => {
        setStageState((prev) => {
            const updated = [...prev];
            // Ensure stage 7 is in progress for review
            if (updated[7] !== 'COMPLETED') updated[7] = 'IN_PROGRESS';
            return updated;
        });
    };

    const handleDetectionComplete = (result) => {
        setDetectionResult(result);
        // We treat detection as: Parse Repo completed, move to Review stage
        // (You can refine mapping later; for now it enables right panel + review gate)
        markStageCompletedAndNextInProgress(2, 7);
        setReviewStageInProgress();
    };

    const handleUserConfirms = () => {
        // User approval completes Review stage
        setStageState((prev) => {
            const updated = [...prev];
            updated[7] = 'COMPLETED';
            return updated;
        });
        // Next agent will start later
        alert('Approved. Next agent will be triggered in the next implementation step.');
    };

    const handleUserRejects = () => {
        alert('Rejected. Flow will be reworked (next step: ask for correction / restart).');
    };

    return (
        <Box
            sx={{
                minHeight: '100vh',
                display: 'grid',
                gridTemplateColumns: detectionResult ? '280px 1fr 420px' : '280px 1fr',
                gap: 2,
                p: 2,
            }}
        >
            {/* LEFT */}
            <Sidebar />

            {/* CENTER */}
            <Box
                sx={{
                    display: 'flex',
                    flexDirection: 'column',
                    height: 'calc(100vh - 32px)',
                    gap: 2,
                    minWidth: 0,
                }}
            >
                {/* PROGRESS (fixed) */}
                <Paper
                    elevation={0}
                    sx={{
                        p: 2,
                        borderRadius: 3,
                        background: 'rgba(255,255,255,0.75)',
                        backdropFilter: 'blur(10px)',
                        border: '1px solid rgba(0,0,0,0.06)',
                        flexShrink: 0,
                    }}
                >
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                        <Typography fontWeight={700}>Migration Progress</Typography>
                        <Typography fontWeight={600}>{progressPercent}%</Typography>
                    </Box>

                    <LinearProgress
                        variant="determinate"
                        value={progressPercent}
                        sx={{
                            height: 8,
                            borderRadius: 5,
                            mb: 3,
                            backgroundColor: '#e0e0e0',
                            '& .MuiLinearProgress-bar': { backgroundColor: '#1976d2' },
                        }}
                    />

                    <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                        {STAGES.map((label, index) => {
                            const status = stageState[index];
                            const isCompleted = status === 'COMPLETED';
                            const isInProgress = status === 'IN_PROGRESS';

                            return (
                                <Box
                                    key={label}
                                    sx={{
                                        display: 'flex',
                                        flexDirection: 'column',
                                        alignItems: 'center',
                                        flex: 1,
                                        position: 'relative',
                                        minWidth: 0,
                                    }}
                                >
                                    {index !== 0 && (
                                        <Box
                                            sx={{
                                                position: 'absolute',
                                                top: 14,
                                                left: '-50%',
                                                width: '100%',
                                                height: 2,
                                                backgroundColor: stageState[index - 1] === 'COMPLETED' ? '#1976d2' : '#cfcfcf',
                                                zIndex: 0,
                                            }}
                                        />
                                    )}

                                    <Box
                                        sx={{
                                            width: 28,
                                            height: 28,
                                            borderRadius: '50%',
                                            display: 'flex',
                                            alignItems: 'center',
                                            justifyContent: 'center',
                                            backgroundColor: isCompleted ? '#4caf50' : isInProgress ? '#1976d2' : '#bdbdbd',
                                            color: '#fff',
                                            zIndex: 1,
                                        }}
                                    >
                                        {isCompleted && <CheckCircleIcon sx={{ fontSize: 18 }} />}
                                    </Box>

                                    <Typography
                                        sx={{
                                            mt: 1,
                                            fontSize: 12,
                                            fontWeight: isInProgress ? 700 : 500,
                                            color: isInProgress ? 'primary.main' : 'text.secondary',
                                            textAlign: 'center',
                                            px: 0.5,
                                            whiteSpace: 'nowrap',
                                            overflow: 'hidden',
                                            textOverflow: 'ellipsis',
                                            maxWidth: '100%',
                                        }}
                                    >
                                        {label}
                                    </Typography>

                                    <Typography variant="caption" sx={{ color: 'text.secondary', mt: 0.5 }}>
                                        {humanStatus(status)}
                                    </Typography>
                                </Box>
                            );
                        })}
                    </Box>
                </Paper>

                {/* CHAT (takes remaining height, scroll-safe) */}
                <Box sx={{ flex: 1, minHeight: 0 }}>
                    <MigrationChat
                        onStageAdvance={(stageIndexDone, stageIndexNext) =>
                            markStageCompletedAndNextInProgress(stageIndexDone, stageIndexNext)
                        }
                        onDetectionComplete={handleDetectionComplete}
                    />
                </Box>
            </Box>

            {/* RIGHT (only after detection completes) */}
            {detectionResult && (
                <MigrationOverview
                    detectionResult={detectionResult}
                    onConfirm={handleUserConfirms}
                    onReject={handleUserRejects}
                />
            )}
        </Box>
    );
}
