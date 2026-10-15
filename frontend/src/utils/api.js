import axios from 'axios';
import { readSession } from './session';

export const BACKEND_URL = (process.env.REACT_APP_BACKEND_URL || '').replace(/\/$/, '');
export const API = `${BACKEND_URL}/api`;
axios.defaults.timeout = 25000;

export async function apiFetch(input, init = {}) {
 const url = typeof input === 'string' ? input : input.url;
 const headers = new Headers(init.headers || (typeof input !== 'string' ? input.headers : undefined));
 const session = readSession();
 // Same-origin /api calls must also carry the session (when no backend URL is set).
 // Never attach credentials to unrelated external URLs.
 const target = new URL(url, window.location.origin);
 const configured = new URL(BACKEND_URL || window.location.origin, window.location.origin);
 if (session && target.origin === configured.origin && target.pathname.startsWith('/api/')) {
  headers.set('Authorization', `Bearer ${session.session_id}`);
 }
 const controller = new AbortController();
 const timer = setTimeout(() => controller.abort(), 25000);
 try {
  const response = await fetch(input, {...init,headers,signal:init.signal || controller.signal});
  return response;
 } finally { clearTimeout(timer); }
}
export async function responseJson(response) {
 const data = await response.json();
 if (!response.ok) throw new Error(data.detail || data.message || `Erreur HTTP ${response.status}`);
 return data;
}
