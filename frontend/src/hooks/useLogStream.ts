import { useState, useEffect, useRef } from 'react';

export const useLogStream = () => {
  const [logs, setLogs] = useState<string[]>([]);
  const [isConnected, setIsConnected] = useState<boolean>(false);
  const websocket = useRef<WebSocket | null>(null);

  useEffect(() => {
    // Use ws:// for http and wss:// for https
    const wsProtocol = window.location.protocol === 'https:-' ? 'wss' : 'ws';
    const wsUrl = process.env.REACT_APP_WS_URL || `${wsProtocol}://${window.location.hostname}:8080/ws/logs`;

    const connect = () => {
      websocket.current = new WebSocket(wsUrl);

      websocket.current.onopen = () => {
        console.log('WebSocket connected');
        setIsConnected(true);
        setLogs((prev) => [...prev, '-- WebSocket connection established --']);
      };

      websocket.current.onmessage = (event) => {
        setLogs((prev) => [...prev, event.data]);
      };

      websocket.current.onclose = () => {
        console.log('WebSocket disconnected');
        setIsConnected(false);
        setLogs((prev) => [...prev, '-- WebSocket connection lost. Attempting to reconnect... --']);
        // Attempt to reconnect after a delay
        setTimeout(connect, 5000);
      };

      websocket.current.onerror = (error) => {
        console.error('WebSocket error:', error);
        websocket.current?.close();
      };
    };

    connect();

    // Clean up the connection when the component unmounts
    return () => {
      if (websocket.current) {
        websocket.current.onclose = null; // prevent reconnect logic from firing on manual close
        websocket.current.close();
      }
    };
  }, []);

  return { logs, isConnected };
};
