import React from 'react';
import {
  Card,
  CardContent,
  Typography,
  Grid,
  Chip,
  CircularProgress,
  Alert,
  Button,
  Box,
} from '@mui/material';
import PowerSettingsNewIcon from '@mui/icons-material/PowerSettingsNew';
import PlayCircleOutlineIcon from '@mui/icons-material/PlayCircleOutline';
import { useBotStatus } from '../hooks/useBotStatus';
import apiClient from '../api/client';

const StatusOverview: React.FC = () => {
  const { status, error, loading, refresh } = useBotStatus();

  const handleStart = async () => {
    try {
      await apiClient.post('/bot/start');
      refresh();
    } catch (err) {
      console.error('Failed to start bot', err);
    }
  };

  const handleStop = async () => {
    try {
      await apiClient.post('/bot/stop');
      refresh();
    } catch (err) {
      console.error('Failed to stop bot', err);
    }
  };

  const handleShutdown = async () => {
    if (window.confirm('Are you sure you want to shut down the entire backend? This will stop the bot and the API server.')) {
      try {
        // We don't need to wait for a response, as the server will be shutting down.
        apiClient.post('/bot/shutdown');
        alert('Shutdown signal sent to backend. You may need to refresh the page later.');
      } catch (err) {
        // This part may not even be reached if the server shuts down immediately.
        console.error('Failed to send shutdown signal', err);
      }
    }
  };

  if (loading && !status) {
    return <CircularProgress />;
  }

  if (error) {
    return <Alert severity="error">{error}</Alert>;
  }

  if (!status) {
    return <Typography>No status data available.</Typography>;
  }

  return (
    <Card sx={{ mb: 3 }}>
      <CardContent>
        <Grid container spacing={2} alignItems="center">
          <Grid size={{ xs: 12, lg: 4 }}>
            <Typography variant="h5" component="div">
              Account Value
            </Typography>
            <Typography variant="h4">
              ${status.account.total_value.toFixed(2)}
            </Typography>
          </Grid>
          <Grid size={{ xs: 12, md: 4 }}>
            <Typography color="text.secondary">Bot Status</Typography>
            <Chip
              icon={status.running ? <PlayCircleOutlineIcon /> : <PowerSettingsNewIcon />}
              label={status.running ? 'Running' : 'Stopped'}
              color={status.running ? 'success' : 'error'}
              sx={{ mt: 1 }}
            />
          </Grid>
          <Grid size={{ xs: 12, md: 4 }} sx={{ textAlign: 'right' }}>
            <Box>
              <Button
                variant="contained"
                color="success"
                onClick={handleStart}
                disabled={status.running}
                sx={{ mr: 1 }}
              >
                Start
              </Button>
              <Button
                variant="contained"
                color="error"
                onClick={handleStop}
                disabled={!status.running}
                sx={{ mr: 1 }}
              >
                Stop
              </Button>
              <Button
                variant="outlined"
                color="error"
                onClick={handleShutdown}
              >
                Shutdown Backend
              </Button>
            </Box>
          </Grid>
        </Grid>
      </CardContent>
    </Card>
  );
};

export default StatusOverview;
