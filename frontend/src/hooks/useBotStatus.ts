import { useState, useEffect, useCallback } from 'react';
import apiClient from '../api/client';
import { BotStatus, ApiResponse } from '../types';

export const useBotStatus = () => {
  const [status, setStatus] = useState<BotStatus | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  const fetchStatus = useCallback(async () => {
    try {
      setLoading(true);
      const response = await apiClient.get<ApiResponse<BotStatus>>('/status');
      if (response.data.success && response.data.data) {
        setStatus(response.data.data);
        setError(null);
      } else {
        setError(response.data.message || 'Failed to fetch status');
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'An unknown error occurred');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 15000); // Refresh every 15 seconds

    return () => clearInterval(interval);
  }, [fetchStatus]);

  return { status, error, loading, refresh: fetchStatus };
};
