// Single place for runtime configuration. Set these in .env.local (see ../.env.example).
const stripTrailingSlash = (url) => url.replace(/\/+$/, '');

export const BACKEND_URL = stripTrailingSlash(
  import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000'
);

// Optional external events feed. When unset, the map uses built-in sample events.
export const EVENTS_API_URL = import.meta.env.VITE_EVENTS_API_URL || '';
