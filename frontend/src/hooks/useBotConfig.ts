import { useState, useEffect, useCallback } from 'react';
import apiClient from '../api/client';
import { ApiResponse } from '../types';

interface BotConfig {
  tracked_coins: string[];
  [key: string]: any;
}

export const useBotConfig = () => {
  const [config, setConfig] = useState<BotConfig | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  const fetchConfig = useCallback(async () => {
    try {
      setLoading(true);
      const response = await apiClient.get<ApiResponse<{ config: BotConfig }>>('/config');
      if (response.data.success && response.data.data) {
        setConfig(response.data.data.config);
        setError(null);
      } else {
        setError(response.data.message || 'Failed to fetch config');
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'An unknown error occurred');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchConfig();
  }, [fetchConfig]);

  const updateTrackedCoins = async (coins: string[]) => {
    try {
      await apiClient.post('/config/update', { tracked_coins: coins });
      await fetchConfig(); // Refresh config after update
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to update config');
      throw err; // Re-throw to be caught in the component
    }
  };

  return { config, error, loading, refresh: fetchConfig, updateTrackedCoins };
};
