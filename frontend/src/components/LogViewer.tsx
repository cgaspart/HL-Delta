import React, { useEffect, useRef } from 'react';
import { Paper, Typography, Box, Chip } from '@mui/material';
import { useLogStream } from '../hooks/useLogStream';

const LogViewer: React.FC = () => {
  const { logs, isConnected } = useLogStream();
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Auto-scroll to the bottom
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [logs]);

  return (
    <Paper sx={{ p: 2, mt: 3, display: 'flex', flexDirection: 'column' }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
        <Typography variant="h6" gutterBottom component="div">
          Live Logs
        </Typography>
        <Chip 
          label={isConnected ? 'Connected' : 'Disconnected'} 
          color={isConnected ? 'success' : 'error'} 
          size="small"
        />
      </Box>
      <Paper 
        ref={scrollRef} 
        sx={{
          bgcolor: 'black',
          color: 'white',
          fontFamily: 'monospace',
          fontSize: '0.8rem',
          p: 2,
          height: '400px',
          overflowY: 'scroll',
          whiteSpace: 'pre-wrap',
          wordBreak: 'break-all',
        }}
      >
        {logs.map((log, index) => (
          <div key={index}>{log}</div>
        ))}
      </Paper>
    </Paper>
  );
};

export default LogViewer;
