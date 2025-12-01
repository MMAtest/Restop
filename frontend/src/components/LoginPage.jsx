import React, { useState } from 'react';
import axios from 'axios';

const LoginPage = ({ onLoginSuccess }) => {
  const [loginForm, setLoginForm] = useState({
    username: '',
    password: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const API = process.env.REACT_APP_BACKEND_URL || import.meta.env.REACT_APP_BACKEND_URL;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = await axios.post(`${API}/api/auth/login`, loginForm);
      
      if (response.data.success) {
        // Stocker les données de session
        localStorage.setItem('user_session', JSON.stringify({
          user: response.data.user,
          session_id: response.data.session_id,
          login_time: new Date().toISOString()
        }));
        
        // Appeler la fonction de succès
        onLoginSuccess(response.data.user, response.data.session_id);
      } else {
        setError(response.data.message);
      }
    } catch (error) {
      console.error('Erreur de connexion:', error);
      setError(error.response?.data?.message || 'Erreur de connexion');
    } finally {
      setLoading(false);
    }
  };

  const handleTestLogin = (username) => {
    setLoginForm({
      username: username,
      password: 'password123'
    });
  };

  return (
    <div style={{
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #059669 0%, #10b981 50%, #34d399 100%)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '20px'
    }}>
      <div style={{
        background: 'white',
        borderRadius: '16px',
        padding: '40px',
        maxWidth: '480px',
        width: '100%',
        boxShadow: '0 20px 40px rgba(0,0,0,0.1)'
      }}>
        {/* Header */}
        <div style={{textAlign: 'center', marginBottom: '32px'}}>
          <div style={{fontSize: '32px', marginBottom: '8px'}}>🍽️</div>
          <h1 style={{
            fontSize: '24px',
            fontWeight: 'bold',
            color: '#059669',
            marginBottom: '4px'
          }}>
            ResTop
          </h1>
          <p style={{
            fontSize: '16px',
            color: '#6b7280',
            marginBottom: '0'
          }}>
            La Table d'Augustine
          </p>
        </div>

        {/* Formulaire de connexion */}
        <form onSubmit={handleSubmit}>
          <div style={{marginBottom: '20px'}}>
            <label style={{
              display: 'block',
              fontSize: '14px',
              fontWeight: '600',
              color: '#374151',
              marginBottom: '8px'
            }}>
              Nom d'utilisateur
            </label>
            <input
              type="text"
              value={loginForm.username}
              onChange={(e) => setLoginForm({...loginForm, username: e.target.value})}
              style={{
                width: '100%',
                padding: '12px 16px',
                border: '2px solid #e5e7eb',
                borderRadius: '8px',
                fontSize: '16px',
                outline: 'none',
                transition: 'border-color 0.3s',
                boxSizing: 'border-box'
              }}
              placeholder="Entrez votre nom d'utilisateur"
              required
              onFocus={(e) => e.target.style.borderColor = '#10b981'}
              onBlur={(e) => e.target.style.borderColor = '#e5e7eb'}
            />
          </div>

          <div style={{marginBottom: '24px'}}>
            <label style={{
              display: 'block',
              fontSize: '14px',
              fontWeight: '600',
              color: '#374151',
              marginBottom: '8px'
            }}>
              Mot de passe
            </label>
            <input
              type="password"
              value={loginForm.password}
              onChange={(e) => setLoginForm({...loginForm, password: e.target.value})}
              style={{
                width: '100%',
                padding: '12px 16px',
                border: '2px solid #e5e7eb',
                borderRadius: '8px',
                fontSize: '16px',
                outline: 'none',
                transition: 'border-color 0.3s',
                boxSizing: 'border-box'
              }}
              placeholder="Entrez votre mot de passe"
              required
              onFocus={(e) => e.target.style.borderColor = '#10b981'}
              onBlur={(e) => e.target.style.borderColor = '#e5e7eb'}
            />
          </div>

          {/* Affichage des erreurs */}
          {error && (
            <div style={{
              padding: '12px 16px',
              background: '#fee2e2',
              border: '1px solid #fecaca',
              borderRadius: '8px',
              color: '#dc2626',
              fontSize: '14px',
              marginBottom: '20px'
            }}>
              ❌ {error}
            </div>
          )}

          {/* Bouton de connexion */}
          <button
            type="submit"
            disabled={loading}
            style={{
              width: '100%',
              padding: '14px 20px',
              background: loading ? '#9ca3af' : '#10b981',
              color: 'white',
              border: 'none',
              borderRadius: '8px',
              fontSize: '16px',
              fontWeight: '600',
              cursor: loading ? 'not-allowed' : 'pointer',
              transition: 'background-color 0.3s'
            }}
            onMouseEnter={(e) => {
              if (!loading) e.target.style.background = '#059669';
            }}
            onMouseLeave={(e) => {
              if (!loading) e.target.style.background = '#10b981';
            }}
          >
            {loading ? '🔄 Connexion...' : '🔑 Se connecter'}
          </button>
        </form>

        {/* Comptes de test - MASQUÉS EN PRODUCTION */}
        {process.env.NODE_ENV === 'development' && (
        <div style={{marginTop: '32px', padding: '20px', background: '#f9fafb', borderRadius: '8px'}}>
          <h3 style={{
            fontSize: '16px',
            fontWeight: '600',
            color: '#374151',
            marginBottom: '16px',
            textAlign: 'center'
          }}>
            🧪 Comptes de test disponibles
          </h3>
          
          <div style={{display: 'grid', gap: '8px'}}>
            {[
              { username: 'skander_admin', role: '👤 Super Admin', color: '#7c3aed' },
              { username: 'patron_test', role: '👑 Patron', color: '#dc2626' },
              { username: 'chef_test', role: '👨‍🍳 Chef de Cuisine', color: '#059669' },
              { username: 'souschef_test', role: '👨‍🍳 Sous-Chef', color: '#16a34a' },
              { username: 'caisse_test', role: '💰 Responsable Caisse', color: '#2563eb' },
              { username: 'barman_test', role: '🍹 Barman', color: '#7c3aed' },
              { username: 'cuisine_test', role: '🥘 Employé Cuisine', color: '#ea580c' }
            ].map((account, index) => (
              <button
                key={index}
                onClick={() => handleTestLogin(account.username)}
                style={{
                  padding: '8px 12px',
                  background: 'white',
                  border: `2px solid ${account.color}`,
                  borderRadius: '6px',
                  cursor: 'pointer',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  fontSize: '13px',
                  transition: 'all 0.3s'
                }}
                onMouseEnter={(e) => {
                  e.target.style.background = account.color;
                  e.target.style.color = 'white';
                }}
                onMouseLeave={(e) => {
                  e.target.style.background = 'white';
                  e.target.style.color = '#374151';
                }}
              >
                <span style={{fontWeight: '600'}}>{account.role}</span>
                <span style={{fontSize: '11px', opacity: '0.8'}}>{account.username}</span>
              </button>
            ))}
          </div>
          
          <div style={{
            textAlign: 'center',
            fontSize: '12px',
            color: '#6b7280',
            marginTop: '12px'
          }}>
            💡 Mot de passe : <code style={{background: '#e5e7eb', padding: '2px 4px', borderRadius: '3px'}}>password123</code>
          </div>
        </div>
        )}
      </div>
    </div>
  );
};

export default LoginPage;