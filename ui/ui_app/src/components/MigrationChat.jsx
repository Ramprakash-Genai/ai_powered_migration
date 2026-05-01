import { useMemo, useRef, useState } from 'react';
import {
  Avatar,
  Box,
  Divider,
  FormControl,
  MenuItem,
  Paper,
  Select,
  Typography,
  TextField,
  IconButton,
  Tooltip,
  Button,
  CircularProgress,
} from '@mui/material';
import SendRoundedIcon from '@mui/icons-material/SendRounded';
import SmartToyOutlinedIcon from '@mui/icons-material/SmartToyOutlined';
import { detectProject } from '../api/projectDetection';

export default function MigrationChat({ onStageAdvance, onDetectionComplete }) {
  const sourceOptions = useMemo(
    () => [
      { value: 'java-selenium-bdd', label: 'Java - Selenium - BDD style' },
      { value: 'python-selenium-bdd', label: 'Python - Selenium - BDD style' },
      { value: 'csharp-selenium-bdd', label: 'C# - Selenium - BDD style' },
    ],
    []
  );

  const inputTypeOptions = useMemo(
    () => [
      { value: 'repository', label: 'Upload full Repository (Folder Path)' },
      { value: 'html_report', label: 'Upload Test report HTML file (File Path)' },
    ],
    []
  );

  // Conversation state
  const [step, setStep] = useState(1);

  // Collected values
  const [selectedSource, setSelectedSource] = useState('');
  const [selectedInputType, setSelectedInputType] = useState('');
  const [inputPath, setInputPath] = useState('');

  // UI state
  const [loading, setLoading] = useState(false);

  // Messages
  const [messages, setMessages] = useState([
    { id: 'bot-1', from: 'bot', type: 'step1' },
  ]);

  const scrollRef = useRef(null);

  const scrollToBottom = () => {
    requestAnimationFrame(() => {
      if (scrollRef.current) {
        scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
      }
    });
  };

  const appendMessages = (newMsgs) => {
    setMessages((prev) => [...prev, ...newMsgs]);
    scrollToBottom();
  };

  // -------- Step handlers --------

  const handleSourceSelect = (value) => {
    setSelectedSource(value);
    const label = sourceOptions.find((o) => o.value === value)?.label || value;

    appendMessages([
      { id: `user-${Date.now()}`, from: 'user', text: `I have selected the project style as: ${label}` },
      { id: `bot-${Date.now()}`, from: 'bot', type: 'step2' },
    ]);

    // Stage 0 complete -> stage 1 in progress
    onStageAdvance?.(0, 1);
    setStep(2);
  };

  const handleInputTypeSelect = (value) => {
    setSelectedInputType(value);
    const label = inputTypeOptions.find((o) => o.value === value)?.label || value;

    appendMessages([
      { id: `user-${Date.now()}`, from: 'user', text: `I have selected the input type as: ${label}` },
      { id: `bot-${Date.now()}`, from: 'bot', type: 'step3' },
    ]);

    // Stage 1 complete -> stage 2 in progress (Parse Repo stage)
    onStageAdvance?.(1, 2);
    setStep(3);
  };

  const handleValidateAndDetect = async () => {
    if (!selectedSource || !selectedInputType || !inputPath) return;

    appendMessages([
      { id: `user-${Date.now()}`, from: 'user', text: `Input path provided: ${inputPath}` },
      { id: `bot-${Date.now()}`, from: 'bot', type: 'loading' },
    ]);

    setLoading(true);
    scrollToBottom();

    try {
      const result = await detectProject({
        userProjectStyle: selectedSource,
        inputType: selectedInputType,
        inputPath,
      });

      // Remove loading bubble and add completion bubble
      setMessages((prev) => prev.filter((m) => m.type !== 'loading'));
      appendMessages([
        {
          id: `bot-${Date.now()}-done`,
          from: 'bot',
          text: `Project detection completed successfully. Please review the Migration Overview panel on the right and confirm.`,
        },
      ]);

      // Mark Parse Repo completed -> Review & Approve stage will be handled in MainLayout when result set
      onStageAdvance?.(2, 7);

      onDetectionComplete?.(result);
      setStep(4);
    } catch (e) {
      setMessages((prev) => prev.filter((m) => m.type !== 'loading'));
      appendMessages([
        {
          id: `bot-${Date.now()}-err`,
          from: 'bot',
          text: `❌ Project detection failed. Please check backend is running (http://localhost:8000/health) and try again.`,
        },
      ]);
    } finally {
      setLoading(false);
      scrollToBottom();
    }
  };

  // -------- Render --------

  return (
    <Paper
      elevation={0}
      sx={{
        borderRadius: 3,
        background: 'rgba(255,255,255,0.75)',
        backdropFilter: 'blur(10px)',
        border: '1px solid rgba(0,0,0,0.06)',
        overflow: 'hidden',
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
      }}
    >
      {/* Header */}
      <Box sx={{ px: 2, py: 1.5, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Avatar sx={{ bgcolor: 'primary.main', width: 34, height: 34 }}>
            <SmartToyOutlinedIcon fontSize="small" />
          </Avatar>
          <Box>
            <Typography variant="subtitle1" sx={{ fontWeight: 800, lineHeight: 1.2 }}>
              Migration Assistant
            </Typography>
            <Typography variant="caption" sx={{ color: 'text.secondary' }}>
              Your AI companion for test migration
            </Typography>
          </Box>
        </Box>
      </Box>

      <Divider />

      {/* Messages */}
      <Box
        ref={scrollRef}
        sx={{
          p: 2,
          flex: 1,
          minHeight: 0,
          overflowY: 'auto',
          display: 'flex',
          flexDirection: 'column',
          gap: 1.5,
        }}
      >
        {messages.map((m) => (
          <MessageBubble
            key={m.id}
            message={m}
            step={step}
            selectedSource={selectedSource}
            sourceOptions={sourceOptions}
            selectedInputType={selectedInputType}
            inputTypeOptions={inputTypeOptions}
            inputPath={inputPath}
            setInputPath={setInputPath}
            loading={loading}
            onSourceSelect={handleSourceSelect}
            onInputTypeSelect={handleInputTypeSelect}
            onValidateAndDetect={handleValidateAndDetect}
          />
        ))}
      </Box>

      <Divider />

      {/* Bottom input area (disabled - since interaction is via controls inside bot bubbles) */}
      <Box sx={{ p: 1.5, display: 'flex', gap: 1 }}>
        <TextField fullWidth size="small" placeholder="Use the options above to proceed step-by-step…" disabled />
        <Tooltip title="Send (disabled in guided flow)">
          <span>
            <IconButton disabled>
              <SendRoundedIcon />
            </IconButton>
          </span>
        </Tooltip>
      </Box>
    </Paper>
  );
}

function MessageBubble({
  message,
  step,
  selectedSource,
  sourceOptions,
  selectedInputType,
  inputTypeOptions,
  inputPath,
  setInputPath,
  loading,
  onSourceSelect,
  onInputTypeSelect,
  onValidateAndDetect,
}) {
  const isUser = message.from === 'user';

  return (
    <Box
      sx={{
        display: 'flex',
        justifyContent: isUser ? 'flex-end' : 'flex-start',
        alignItems: 'flex-end',
        gap: 1,
      }}
    >
      {!isUser && (
        <Avatar src="/bot.png" alt="Bot" sx={{ width: 30, height: 30, bgcolor: 'primary.main' }}>
          AI
        </Avatar>
      )}

      <Paper
        elevation={0}
        sx={{
          px: 1.6,
          py: 1.2,
          maxWidth: '72%',
          borderRadius: 2.5,
          borderTopLeftRadius: isUser ? 16 : 6,
          borderTopRightRadius: isUser ? 6 : 16,
          bgcolor: isUser ? 'rgba(25,118,210,0.10)' : 'rgba(255,255,255,0.9)',
          border: '1px solid rgba(0,0,0,0.06)',
        }}
      >
        {/* Step bubbles */}
        {message.type === 'step1' ? (
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
            <Typography variant="body2" sx={{ fontWeight: 700 }}>
              Hey User, Welcome to Migration Assistant Chatbot !
            </Typography>

            <Typography variant="body2" sx={{ color: 'text.secondary' }}>
              The assistant helps you migrate from Java / Python / C# based Selenium + BDD project
              to any of Java / Python / C# Playwright + BDD.
            </Typography>

            <Typography variant="body2" sx={{ mt: 1 }}>
              Please select your <b>current project style</b> from the dropdown below:
            </Typography>

            <FormControl size="small" sx={{ mt: 0.5, width: 340, maxWidth: '100%' }}>
              <Select
                value={selectedSource}
                displayEmpty
                onChange={(e) => onSourceSelect(e.target.value)}
              >
                <MenuItem value="" disabled>
                  Select source project style…
                </MenuItem>
                {sourceOptions.map((opt) => (
                  <MenuItem key={opt.value} value={opt.value}>
                    {opt.label}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            <Typography variant="caption" sx={{ color: 'text.secondary' }}>
              Step‑1 • Select source project style
            </Typography>
          </Box>
        ) : message.type === 'step2' ? (
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
            <Typography variant="body2" sx={{ fontWeight: 700 }}>
              Please select your input type for migration:
            </Typography>

            <FormControl size="small" sx={{ mt: 0.5, width: 380, maxWidth: '100%' }}>
              <Select
                value={selectedInputType}
                displayEmpty
                onChange={(e) => onInputTypeSelect(e.target.value)}
              >
                <MenuItem value="" disabled>
                  Select input type…
                </MenuItem>
                {inputTypeOptions.map((opt) => (
                  <MenuItem key={opt.value} value={opt.value}>
                    {opt.label}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            <Typography variant="caption" sx={{ color: 'text.secondary' }}>
              Step‑2 • Choose repository folder path OR HTML report file path
            </Typography>
          </Box>
        ) : message.type === 'step3' ? (
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
            <Typography variant="body2" sx={{ fontWeight: 700 }}>
              Please provide the absolute {selectedInputType === 'html_report' ? 'HTML file path' : 'folder path'}:
            </Typography>

            <TextField
              size="small"
              value={inputPath}
              onChange={(e) => setInputPath(e.target.value)}
              placeholder={selectedInputType === 'html_report' ? 'C:/Reports/report.html' : 'C:/Projects/MyRepo'}
              sx={{ mt: 0.5, width: 420, maxWidth: '100%' }}
            />

            <Box sx={{ display: 'flex', justifyContent: 'flex-end', mt: 0.5 }}>
              <Button
                variant="contained"
                size="small"
                sx={{ textTransform: 'none', fontWeight: 700 }}
                disabled={!inputPath || loading}
                onClick={onValidateAndDetect}
              >
                Validate & Detect
              </Button>
            </Box>

            <Typography variant="caption" sx={{ color: 'text.secondary' }}>
              Step‑3 • Provide path, then run Project Detection Agent
            </Typography>
          </Box>
        ) : message.type === 'loading' ? (
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <CircularProgress size={16} />
            <Typography variant="body2" sx={{ fontWeight: 700 }}>
              Validating and identifying your input… please wait
            </Typography>
          </Box>
        ) : (
          <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>
            {message.text}
          </Typography>
        )}
      </Paper>

      {isUser && (
        <Avatar alt="User" sx={{ width: 30, height: 30, bgcolor: 'grey.700', fontWeight: 800 }}>
          U
        </Avatar>
      )}
    </Box>
  );
}