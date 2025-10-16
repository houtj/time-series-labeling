/**
 * Production environment configuration
 * Uses relative URLs to work with nginx proxy
 */
export const environment = {
  production: true,
  apiUrl: '/api',
  wsUrl: `${location.protocol === 'https:' ? 'wss:' : 'ws:'}//${location.host}/ws`
};

