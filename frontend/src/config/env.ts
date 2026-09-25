const host = typeof window !== 'undefined' && window.location.hostname ? window.location.hostname : '127.0.0.1';

export const ENV = {
  API_URL: import.meta.env.VITE_API_URL || `http://${host}:8000/api/v1`,
  APP_NAME: 'Enermax CRM',
  VERSION: '0.2.0 (Phase 2 Core)',
};
