import React, { useState } from 'react';
import axios from 'axios';
import { Link } from 'react-router-dom';
import { ArrowLeft, ArrowRight } from '@phosphor-icons/react';
import Brand from './restop/Brand';

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

  const handleDemo = async () => {
    setLoading(true);
    setError('');
    try {
      const response = await axios.post(API + '/api/auth/demo');
      const sessionId = response.data.session_id;
      axios.defaults.headers.common.Authorization = 'Bearer ' + sessionId;
      localStorage.setItem('user_session', JSON.stringify({
        user: response.data.user,
        session_id: sessionId,
        login_time: new Date().toISOString()
      }));
      onLoginSuccess(response.data.user, sessionId);
    } catch (e) {
      setError(e.response?.data?.detail || 'La démo est momentanément indisponible');
    } finally {
      setLoading(false);
    }
  };

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

  return <div className="rt-auth">
    <aside className="rt-auth-editorial"><img src="/images/restop-chef.webp" alt="" /><Link to="/" aria-label="Accueil Restop"><Brand light /></Link><div><h2>Moins de gestion.<br />Plus de cuisine.</h2><p>Retrouvez votre restaurant, vos produits et votre équipe dans un même espace.</p></div></aside>
    <main className="rt-auth-content"><div className="rt-auth-form"><Link className="rt-auth-return" to="/"><ArrowLeft size={16} />Retour à l’accueil</Link><h1>{mode === 'register' ? 'Créer votre espace' : 'Heureux de vous retrouver.'}</h1><p>{mode === 'register' ? 'Renseignez votre établissement pour commencer.' : 'Connectez-vous à votre espace Restop.'}</p>
      <form onSubmit={handleSubmit}>
        {mode === 'register' && <>
          <div><label htmlFor="restaurant_name">Nom du restaurant</label><input id="restaurant_name" value={form.restaurant_name} onChange={update('restaurant_name')} autoComplete="organization" required /></div>
          <div><label htmlFor="full_name">Votre nom</label><input id="full_name" value={form.full_name} onChange={update('full_name')} autoComplete="name" required /></div>
          <div><label htmlFor="email">Adresse e-mail</label><input id="email" type="email" value={form.email} onChange={update('email')} autoComplete="email" required /></div>
        </>}
        <div><label htmlFor="username">Nom d’utilisateur</label><input id="username" value={form.username} onChange={update('username')} autoComplete="username" required /></div>
        <div><label htmlFor="password">Mot de passe</label><input id="password" type="password" value={form.password} onChange={update('password')} minLength={mode === 'register' ? 8 : undefined} autoComplete={mode === 'register' ? 'new-password' : 'current-password'} required /></div>
        {error && <p className="rt-feedback" role="alert">{error}</p>}
        <button className="rt-button rt-peach" type="submit" disabled={loading}>{loading ? 'Chargement…' : mode === 'register' ? 'Créer mon espace' : 'Se connecter'}<ArrowRight size={18} /></button>
      </form>
      <button className="rt-auth-switch" onClick={() => {setMode(mode === 'login' ? 'register' : 'login');setError('');}}>{mode === 'login' ? 'Première connexion ? Créer un compte' : 'Déjà un compte ? Se connecter'}</button>
      {mode === 'login' && <button className="rt-button rt-outline" onClick={handleDemo} disabled={loading}>Explorer la démo commerciale<ArrowRight size={18} /></button>}
    </div></main>
  </div>;
};
export default LoginPage;
