import React, { useEffect, useState } from 'react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function HistoriqueZPage() {
  const [rapports, setRapports] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchRapports();
  }, []);

  const fetchRapports = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API}/rapports_z`);
      setRapports(response.data);
      setError(null);
    } catch (err) {
      console.error('Erreur lors du chargement des rapports Z:', err);
      setError('Erreur lors du chargement des rapports');
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('fr-FR', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  const formatMoney = (amount) => {
    return new Intl.NumberFormat('fr-FR', {
      style: 'currency',
      currency: 'EUR'
    }).format(amount);
  };

  if (loading) {
    return (
      <div className="wireframe">
        <h2>📊 Historique des Rapports Z</h2>
        <div className="card">
          <div className="card-content">Chargement des rapports...</div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="wireframe">
        <h2>📊 Historique des Rapports Z</h2>
        <div className="card">
          <div className="card-content error">{error}</div>
        </div>
      </div>
    );
  }

  return (
    <div className="wireframe">
      <h2>📊 Historique des Rapports Z</h2>
      
      <div className="layout">
        <div className="card full-width">
          <div className="card-title">📋 Liste des Rapports Z</div>
          
          {rapports.length === 0 ? (
            <div className="card-content">
              Aucun rapport Z enregistré pour le moment.
            </div>
          ) : (
            <div className="table-mockup">
              <div className="table-header">Date | CA Total | Nombre de Plats | Actions</div>
              {rapports.map((rapport) => (
                <div key={rapport.id} className="table-row">
                  <span>
                    <strong>📅 {formatDate(rapport.date)}</strong> | 
                    <strong>💰 {formatMoney(rapport.ca_total)}</strong> | 
                    <strong>🍽️ {rapport.produits ? rapport.produits.length : 0} plats</strong>
                  </span>
                  <div>
                    <button 
                      className="button" 
                      style={{fontSize: '0.7rem', padding: '4px 8px'}}
                      onClick={() => {
                        const details = `📊 DÉTAILS RAPPORT Z\n\n` +
                          `📅 Date: ${formatDate(rapport.date)}\n` +
                          `💰 CA Total: ${formatMoney(rapport.ca_total)}\n` +
                          `🍽️ Plats vendus: ${rapport.produits ? rapport.produits.length : 0}\n\n`;
                        
                        let platsList = '';
                        if (rapport.produits && rapport.produits.length > 0) {
                          platsList = 'TOP PLATS VENDUS:\n';
                          rapport.produits.slice(0, 10).forEach((plat, i) => {
                            platsList += `${i + 1}. ${plat.quantite || 1}x ${plat.nom}\n`;
                          });
                        }
                        
                        alert(details + platsList);
                      }}
                    >
                      👁️ Détails
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
          
          <div style={{textAlign: 'center', marginTop: '20px'}}>
            <button className="button" onClick={fetchRapports}>
              🔄 Actualiser
            </button>
            <button className="button">
              📊 Exporter Excel
            </button>
          </div>
        </div>
        
        {rapports.length > 0 && (
          <div className="layout three-column">
            <div className="card stat-card">
              <div className="icon">💰</div>
              <div className="card-title">CA Moyen</div>
              <div className="card-content">
                {formatMoney(rapports.reduce((sum, r) => sum + r.ca_total, 0) / rapports.length)}
              </div>
            </div>
            <div className="card stat-card">
              <div className="icon">📊</div>
              <div className="card-title">Total Rapports</div>
              <div className="card-content">{rapports.length} rapports</div>
            </div>
            <div className="card stat-card">
              <div className="icon">📅</div>
              <div className="card-title">Dernier Rapport</div>
              <div className="card-content">
                {rapports.length > 0 ? formatDate(rapports[0].date) : 'N/A'}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}