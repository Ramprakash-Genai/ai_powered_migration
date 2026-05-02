import { Avatar, Box, Button, Paper, Typography } from '@mui/material'
import AddRoundedIcon from '@mui/icons-material/AddRounded'

export default function Sidebar() {
  return (
    <Paper
      elevation={0}
      sx={{
        borderRadius: 3,
        p: 1.75,
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
      {/* Header */}
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.25 }}>
        <Avatar
          src="/bot.png"
          alt="Bot Avatar"
          sx={{
            width: 36,
            height: 36,
            bgcolor: 'primary.main',
            fontWeight: 800,
            fontSize: 14,
            flexShrink: 0,
          }}
        >
          AI
        </Avatar>

        <Box>
          <Typography
            sx={{
              fontSize: 14,
              fontWeight: 800,
              lineHeight: 1.2,
            }}
          >
            AI Migration Assistant
          </Typography>          
        </Box>
      </Box>

      {/* New Migration Button */}
      <Button
        variant="contained"
        startIcon={<AddRoundedIcon fontSize="small" />}
        sx={{
          borderRadius: 2,
          textTransform: 'none',
          fontWeight: 600,
          py: 0.75,
          fontSize: 13,
        }}
        fullWidth
      >
        New Migration
      </Button>

      {/* Spacer */}
      <Box sx={{ flex: 1 }} />

      <Typography
        sx={{
          fontSize: 11,
          color: 'text.secondary',
          lineHeight: 1.3,
        }}
      >
        Step‑1 UI: Select source project style in the chat.
      </Typography>
    </Paper>
  )
}