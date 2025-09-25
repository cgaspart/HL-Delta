import React from 'react';
import {
  Grid,
  AppBar,
  Toolbar,
  Typography,
  Container,
  CssBaseline,
  Box,
  Paper,
  CircularProgress,
  Alert,
} from '@mui/material';
import StatusOverview from '../components/StatusOverview';
import PositionsTable from '../components/PositionsTable';
import ConfigManager from '../components/ConfigManager';
import LogViewer from '../components/LogViewer';
import { useBotStatus } from '../hooks/useBotStatus';

const Dashboard: React.FC = () => {
  const { status, error, loading } = useBotStatus();

  return (
    <Box sx={{ display: 'flex' }}>
      <CssBaseline />
      <AppBar position="fixed">
        <Toolbar>
          <Typography variant="h6" noWrap component="div">
            Delta Bot Dashboard
          </Typography>
        </Toolbar>
      </AppBar>
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          bgcolor: 'background.default',
          p: 3,
          marginTop: '64px',
        }}
      >
        <Container maxWidth="xl">
          <Grid container spacing={3}>
            <Grid size={{ xs: 12 }}>
              <StatusOverview />
            </Grid>
            <Grid size={{ xs: 12, lg: 8 }}>
              <Paper sx={{ p: 2, display: 'flex', flexDirection: 'column' }}>
                <Typography variant="h6" gutterBottom>
                  Current Positions
                </Typography>
                {loading && !status ? (
                  <CircularProgress />
                ) : error ? (
                  <Alert severity="error">{error}</Alert>
                ) : status ? (
                  <PositionsTable positions={status.positions} />
                ) : (
                  <Typography>No data available.</Typography>
                )}
              </Paper>
            </Grid>
            <Grid size={{ xs: 12, lg: 4 }}>
              <ConfigManager />
            </Grid>
            <Grid size={{ xs: 12}}>
              <LogViewer />
            </Grid>
          </Grid>
        </Container>
      </Box>
    </Box>
  );
};

export default Dashboard;
