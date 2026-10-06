export function readSession() {
 try { const value=JSON.parse(localStorage.getItem('user_session') || 'null');return value?.session_id && value?.user ? value : null; }
 catch (_) { localStorage.removeItem('user_session');return null; }
}
export function clearSession() { localStorage.removeItem('user_session'); }
