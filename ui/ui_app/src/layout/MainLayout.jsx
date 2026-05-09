import { useMemo, useState } from 'react';
import {
    Box,
    Paper,
    Typography,
    LinearProgress,
    Stepper,
    Step,
    StepLabel,
    StepConnector,
} from '@mui/material';
import { styled } from '@mui/material/styles';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import Sidebar from '../components/Sidebar';
import MigrationChat from '../components/MigrationChat';
import MigrationOverview from '../components/MigrationOverview';
import { buildProjectNormalization } from '../api/project_normalization';
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

const ProgressConnector = styled(StepConnector)(() => ({
    [`& .MuiStepConnector-line`]: {
        borderColor: '#cfcfcf',
        borderTopWidth: 2,
        borderRadius: 1,
    },
    [`&.Mui-active .MuiStepConnector-line`]: {
        borderColor: '#1976d2',
    },
    [`&.Mui-completed .MuiStepConnector-line`]: {
        borderColor: '#1976d2',
    },
}));

function ProgressStepIcon(props) {
    const { active, completed, className } = props;

    if (completed) {
        return (
            <Box
                className={className}
                sx={{
                    width: 28,
                    height: 28,
                    borderRadius: '50%',
                    backgroundColor: '#4caf50',
                    color: '#fff',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                }}
            >
                <CheckCircleIcon sx={{ fontSize: 18 }} />
            </Box>
        );
    }

    if (active) {
        return (
            <Box
                className={className}
                sx={{
                    width: 28,
                    height: 28,
                    borderRadius: '50%',
                    backgroundColor: '#1976d2',
                }}
            />
        );
    }

    return (
        <Box
            className={className}
            sx={{
                width: 28,
                height: 28,
                borderRadius: '50%',
                backgroundColor: '#bdbdbd',
            }}
        />
    );
}

export default function MainLayout() {
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

    const [detectionResult, setDetectionResult] = useState(null);
    const [chatResetKey, setChatResetKey] = useState(0);

    const progressPercent = useMemo(() => {
        const completed = stageState.filter((s) => s === 'COMPLETED').length;
        return Math.round((completed / STAGES.length) * 100);
    }, [stageState]);

    const activeStep = useMemo(() => {
        const idx = stageState.findIndex((s) => s === 'IN_PROGRESS');
        if (idx !== -1) return idx;
        const completedCount = stageState.filter((s) => s === 'COMPLETED').length;
        return Math.min(completedCount, STAGES.length - 1);
    }, [stageState]);

    const resetFlow = () => {
        setDetectionResult(null);
        setStageState([
            'IN_PROGRESS',
            'PENDING',
            'PENDING',
            'PENDING',
            'PENDING',
            'PENDING',
            'PENDING',
            'PENDING',
        ]);
        // ✅ Force MigrationChat remount
        setChatResetKey(prev => prev + 1);
    };
    const [normalizedContext, setNormalizedContext] = useState(null);
    const handleProceedToNormalization = async () => {
        if (!detectionResult) return;
        try {
            const norm = await buildProjectNormalization(detectionResult);
            if (norm?.error) {
                console.error(norm.message);
                return;
            }
            // ✅ Store normalized output
            setNormalizedContext(norm);
            console.log('✅ Project Normalization completed silently', norm);
        } catch (e) {
            console.error('❌ Normalization failed', e);
        }
    };


    return (
        <Box
            sx={{
                minHeight: '100vh',
                display: 'grid',
                gridTemplateColumns: detectionResult
                    ? '180px minmax(640px, 2fr) minmax(380px, 1fr)'
                    : '180px 1fr',
                gap: 2,
                p: 2,
                overflowX: 'hidden',
            }}
        >
            <Sidebar />

            <Box
                sx={{
                    display: 'flex',
                    flexDirection: 'column',
                    height: 'calc(100vh - 32px)',
                    gap: 2,
                    minWidth: 0,
                }}
            >
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
                            mb: 2,
                            backgroundColor: '#e0e0e0',
                            '& .MuiLinearProgress-bar': { backgroundColor: '#1976d2' },
                        }}
                    />

                    <Stepper
                        alternativeLabel
                        activeStep={activeStep}
                        connector={<ProgressConnector />}
                        sx={{
                            pt: 1,
                            pb: 0,
                            '& .MuiStepLabel-label': {
                                fontSize: 12,
                                lineHeight: 1.2,
                                wordBreak: 'break-word',
                                textAlign: 'center',
                            },
                            '& .MuiStepLabel-label.Mui-active': {
                                color: '#1976d2',
                                fontWeight: 700,
                            },
                            '& .MuiStepLabel-label.Mui-completed': {
                                color: '#2e7d32',
                                fontWeight: 600,
                            },
                        }}
                    >
                        {STAGES.map((label, index) => {
                            const status = stageState[index];
                            const isCompleted = status === 'COMPLETED';

                            return (
                                <Step key={label} completed={isCompleted}>
                                    <StepLabel StepIconComponent={ProgressStepIcon}>
                                        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
                                            <Typography
                                                sx={{
                                                    fontSize: 12,
                                                    fontWeight: status === 'IN_PROGRESS' ? 700 : 500,
                                                    color: status === 'IN_PROGRESS' ? '#1976d2' : 'text.secondary',
                                                }}
                                            >
                                                {label}
                                            </Typography>
                                            <Typography sx={{ fontSize: 11, color: 'text.secondary' }}>
                                                {humanStatus(status)}
                                            </Typography>
                                        </Box>
                                    </StepLabel>
                                </Step>
                            );
                        })}
                    </Stepper>
                </Paper>

                <Box sx={{ flex: 1, minHeight: 0 }}>
                    <MigrationChat
                        key={chatResetKey}
                        onDetectionComplete={setDetectionResult}
                    />
                </Box>
            </Box>

            {detectionResult && (
                <Box sx={{ height: 'calc(100vh - 32px)' }}>
                    <MigrationOverview
                        detectionResult={detectionResult}
                        onUpdateDetection={setDetectionResult}
                        onResetFlow={resetFlow}
                        onProceedToNormalization={handleProceedToNormalization}
                    />
                </Box>
            )}
        </Box>
    );
}
