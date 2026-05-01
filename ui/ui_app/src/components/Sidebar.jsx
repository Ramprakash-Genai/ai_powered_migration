import { Avatar, Box, Button, Paper, Typography } from '@mui/material'
import AddRoundedIcon from '@mui/icons-material/AddRounded'

export default function Sidebar() {
  return (
    <Paper
      elevation={0}
      sx={{
        borderRadius: 3,
        p: 2,
        height: 'calc(100vh - 32px)',
        position: 'sticky',
        top: 16,
        background: 'rgba(255,255,255,0.75)',
        backdropFilter: 'blur(10px)',
        border: '1px solid rgba(0,0,0,0.06)',
        display: 'flex',
        flexDirection: 'column',
        gap: 2,
      }}
    >
      {/* Bot Header */}
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
        <Avatar
          src="/bot.png" // optional: you can add public/bot.png later
          alt="Bot Avatar"
          sx={{
            width: 42,
            height: 42,
            bgcolor: 'primary.main',
            fontWeight: 800,
          }}
        >
          AI
        </Avatar>

        <Box sx={{ minWidth: 0 }}>
          <Typography variant="subtitle1" sx={{ fontWeight: 800, lineHeight: 1.2 }}>
            AI Migration Assistant
          </Typography>
          <Typography variant="caption" sx={{ color: 'text.secondary' }}>
            Selenium + BDD → Playwright + BDD
          </Typography>
        </Box>
      </Box>

      {/* Only required now */}
      <Button
        variant="contained"
        startIcon={<AddRoundedIcon />}
        sx={{
          borderRadius: 2,
          textTransform: 'none',
          fontWeight: 700,
          py: 1.1,
        }}
        fullWidth
      >
        New Migration
      </Button>

      {/* Spacer (future items can come here later) */}
      <Box sx={{ flex: 1 }} />

      <Typography variant="caption" sx={{ color: 'text.secondary' }}>
        Step‑1 UI: Select source project style in the chat.
      </Typography>
    </Paper>
  )
}
