const getApiUrl = (): string => {
  if (import.meta.env.VITE_API_URL) {
    return import.meta.env.VITE_API_URL;
  }
  if (typeof window !== 'undefined') {
    const hostname = window.location.hostname;
    // On deployed hosts (e.g. Vercel), use relative /api/v1 to route to serverless API
    if (hostname && hostname !== 'localhost' && hostname !== '127.0.0.1') {
      return '/api/v1';
    }
    return `http://${hostname}:8000/api/v1`;
  }
  return 'http://127.0.0.1:8000/api/v1';
};

export const ENV = {
  API_URL: getApiUrl(),
  APP_NAME: 'Enermax CRM',
  VERSION: '0.2.0 (Phase 2 Core)',
};
