import React, { useState } from 'react';
import axios from 'axios';

const fieldStyle = {
  width: '100%',
  padding: '12px 14px',
  border: '1px solid #d7ddd9',
  borderRadius: '10px',
  fontSize: '15px',
  outline: 'none',
  boxSizing: 'border-box',
  background: '#fff'
};

const LoginPage = ({ onLoginSuccess }) => {
  const [mode, setMode] = useState('login');
  const [form, setForm] = useState({
    username: '',
    email: '',
    password: '',
    full_name: '',
    restaurant_name: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const API = process.env.REACT_APP_BACKEND_URL;

  const update = (key) => (e) => setForm((prev) => ({ ...prev, [key]: e.target.value }));

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const endpoint = mode === 'register' ? '/api/auth/register' : '/api/auth/login';
      const payload = mode === 'register'
        ? form
        : { username: form.username, password: form.password };

      const response = await axios.post(API + endpoint, payload);
      if (!response.data?.success) {
        setError(response.data?.message || 'Impossible de continuer');
        return;
      }

      const sessionId = response.data.session_id;
      axios.defaults.headers.common.Authorization = 'Bearer ' + sessionId;
      localStorage.setItem('user_session', JSON.stringify({
        user: response.data.user,
        session_id: sessionId,
        login_time: new Date().toISOString()
      }));
      onLoginSuccess(response.data.user, sessionId);
    } catch (e) {
      setError(e.response?.data?.detail || e.response?.data?.message || 'Erreur de connexion');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      minHeight: '100vh',
      background: 'linear-gradient(145deg, #f5f7f4 0%, #e8f2ed 100%)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '24px'
    }}>
      <div style={{
        background: '#fff',
        border: '1px solid #e3e8e5',
        borderRadius: '20px',
        padding: '36px',
        maxWidth: '440px',
        width: '100%',
        boxShadow: '0 22px 60px rgba(18, 51, 50, 0.10)'
      }}>
        <div style={{ marginBottom: '28px' }}>
          <div style={{ color: '#123332', fontSize: '13px', letterSpacing: '0.12em', textTransform: 'uppercase', marginBottom: '8px' }}>
            ResTop
          </div>
          <h1 style={{ margin: 0, fontSize: '30px', fontWeight: 500, color: '#1D4241' }}>
            {mode === 'register' ? 'Créer votre espace' : 'Connexion'}
          </h1>
          <p style={{ color: '#6f7b77', margin: '10px 0 0', lineHeight: 1.5 }}>
            {mode === 'register'
              ? 'Une base vierge et sécurisée sera créée pour votre établissement.'
              : 'Accédez à vos stocks, fournisseurs et opérations.'}
          </p>
        </div>

        <form onSubmit={handleSubmit}>
          {mode === 'register' && (
            <>
              <div style={{ marginBottom: 14 }}>
                <label style={{ display: 'block', fontSize: 13, marginBottom: 6, color: '#314744' }}>Nom du restaurant</label>
                <input style={fieldStyle} value={form.restaurant_name} onChange={update('restaurant_name')} required />
              </div>
              <div style={{ marginBottom: 14 }}>
                <label style={{ display: 'block', fontSize: 13, marginBottom: 6, color: '#314744' }}>Votre nom</label>
                <input style={fieldStyle} value={form.full_name} onChange={update('full_name')} required />
              </div>
              <div style={{ marginBottom: 14 }}>
                <label style={{ display: 'block', fontSize: 13, marginBottom: 6, color: '#314744' }}>Email</label>
                <input style={fieldStyle} type="email" value={form.email} onChange={update('email')} required />
              </div>
            </>
          )}

          <div style={{ marginBottom: 14 }}>
            <label style={{ display: 'block', fontSize: 13, marginBottom: 6, color: '#314744' }}>Nom d'utilisateur</label>
            <input style={fieldStyle} value={form.username} onChange={update('username')} autoComplete="username" required />
          </div>

          <div style={{ marginBottom: 18 }}>
            <label style={{ display: 'block', fontSize: 13, marginBottom: 6, color: '#314744' }}>Mot de passe</label>
            <input style={fieldStyle} type="password" value={form.password} onChange={update('password')} minLength={8} autoComplete={mode === 'register' ? 'new-password' : 'current-password'} required />
          </div>

          {error && (
            <div style={{ background: '#fff2f0', border: '1px solid #f2c7bf', color: '#8a3428', borderRadius: 10, padding: '11px 13px', fontSize: 13, marginBottom: 16 }}>
              {error}
            </div>
          )}

          <button type="submit" disabled={loading} style={{ width: '100%', border: 0, borderRadius: 10, padding: '13px 16px', background: loading ? '#8ba09a' : '#1D4241', color: '#fff', fontSize: 15, cursor: loading ? 'wait' : 'pointer' }}>
            {loading ? 'Chargement…' : mode === 'register' ? 'Créer mon espace' : 'Se connecter'}
          </button>
        </form>

        <button type="button" onClick={() => { setMode(mode === 'login' ? 'register' : 'login'); setError(''); }} style={{ width: '100%', marginTop: 12, padding: '10px', border: 0, background: 'transparent', color: '#1D4241', cursor: 'pointer', fontSize: 13 }}>
          {mode === 'login' ? 'Première connexion ? Créer un compte' : 'Déjà un compte ? Se connecter'}
        </button>
      </div>
    </div>
  );
};

export default LoginPage;
