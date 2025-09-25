import axios from 'axios';

const apiClient = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8080/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add a request interceptor to include the API key from environment variables
apiClient.interceptors.request.use(
  (config) => {
    const apiKey = process.env.REACT_APP_API_KEY;
    if (apiKey) {
      config.headers['X-API-KEY'] = apiKey;
    } else {
      // If the API key is missing, we can block the request or let it fail on the server
      console.warn('API key is not set in the environment variables.');
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

export default apiClient;