import React, { useState } from 'react';
import {
  Paper,
  Typography,
  List,
  ListItem,
  ListItemText,
  IconButton,
  TextField,
  Button,
  Box,
  CircularProgress,
  Alert,
} from '@mui/material';
import DeleteIcon from '@mui/icons-material/Delete';
import AddCircleOutlineIcon from '@mui/icons-material/AddCircleOutline';
import { useBotConfig } from '../hooks/useBotConfig';

const ConfigManager: React.FC = () => {
  const { config, error, loading, updateTrackedCoins } = useBotConfig();
  const [newCoin, setNewCoin] = useState('');

  const handleAddCoin = async () => {
    if (newCoin && config && !config.tracked_coins.includes(newCoin.toUpperCase())) {
      const updatedCoins = [...config.tracked_coins, newCoin.toUpperCase()];
      await updateTrackedCoins(updatedCoins);
      setNewCoin('');
    }
  };

  const handleRemoveCoin = async (coinToRemove: string) => {
    if (config) {
      const updatedCoins = config.tracked_coins.filter((c) => c !== coinToRemove);
      await updateTrackedCoins(updatedCoins);
    }
  };

  if (loading) {
    return <CircularProgress />;
  }

  if (error) {
    return <Alert severity="error">{error}</Alert>;
  }

  return (
    <Paper sx={{ p: 2 }}>
      <Typography variant="h6" gutterBottom>
        Tracked Coins
      </Typography>
      <List dense>
        {config?.tracked_coins.map((coin) => (
          <ListItem
            key={coin}
            secondaryAction={
              <IconButton edge="end" aria-label="delete" onClick={() => handleRemoveCoin(coin)}>
                <DeleteIcon />
              </IconButton>
            }
          >
            <ListItemText primary={coin} />
          </ListItem>
        ))}
      </List>
      <Box sx={{ display: 'flex', mt: 2 }}>
        <TextField
          label="New Coin (e.g., BTC)"
          variant="outlined"
          size="small"
          value={newCoin}
          onChange={(e) => setNewCoin(e.target.value)}
          sx={{ flexGrow: 1, mr: 1 }}
        />
        <Button
          variant="contained"
          onClick={handleAddCoin}
          startIcon={<AddCircleOutlineIcon />}
        >
          Add
        </Button>
      </Box>
    </Paper>
  );
};

export default ConfigManager;
