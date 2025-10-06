import React, { useState, useEffect } from 'react';
import axios from 'axios';

const RoleBasedDashboard = ({ user, sessionId, onNavigateToPage }) => {
  const [missions, setMissions] = useState([]);
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(false);

  const API = process.env.REACT_APP_BACKEND_URL || import.meta.env.REACT_APP_BACKEND_URL;

  useEffect(() => {
    if (user?.id) {
      fetchMissionsAndNotifications();
    }
  }, [user]);

  const fetchMissionsAndNotifications = async () => {
    try {
      setLoading(true);
      
      // Récupérer les missions de l'utilisateur
      const missionsResponse = await axios.get(`${API}/api/missions/by-user/${user.id}`);
      setMissions(missionsResponse.data);
      
      // Récupérer les notifications
      const notificationsResponse = await axios.get(`${API}/api/notifications/${user.id}`);
      setNotifications(notificationsResponse.data);
      
    } catch (error) {
      console.error('Erreur lors du chargement:', error);
    } finally {
      setLoading(false);
    }
  };

  const markMissionCompleted = async (missionId, notes = '') => {
    try {
      await axios.put(`${API}/api/missions/${missionId}?user_id=${user.id}`, {
        status: 'terminee_attente',
        employee_notes: notes
      });
      
      alert('✅ Mission marquée comme terminée !\nElle est maintenant en attente de validation.');
      fetchMissionsAndNotifications();
    } catch (error) {
      console.error('Erreur:', error);
      alert('❌ Erreur lors de la mise à jour');
    }
  };

  const validateMission = async (missionId, notes = '') => {
    try {
      await axios.put(`${API}/api/missions/${missionId}?user_id=${user.id}`, {
        status: 'validee',
        validation_notes: notes
      });
      
      alert('✅ Mission validée avec succès !');
      fetchMissionsAndNotifications();
    } catch (error) {
      console.error('Erreur:', error);
      alert('❌ Erreur lors de la validation');
    }
  };

  const getStatusBadge = (status) => {
    const statusMap = {
      'en_cours': { text: '🔄 En cours', color: '#2563eb', bg: '#dbeafe' },
      'terminee_attente': { text: '⏳ En attente validation', color: '#d97706', bg: '#fef3c7' },
      'validee': { text: '✅ Validée', color: '#059669', bg: '#dcfce7' },
      'en_retard': { text: '🚨 En retard', color: '#dc2626', bg: '#fee2e2' },
      'annulee': { text: '❌ Annulée', color: '#6b7280', bg: '#f3f4f6' }
    };
    
    const style = statusMap[status] || statusMap['en_cours'];
    return (
      <span style={{
        padding: '4px 8px',
        borderRadius: '12px',
        fontSize: '12px',
        fontWeight: '600',
        color: style.color,
        background: style.bg
      }}>
        {style.text}
      </span>
    );
  };

  const getPriorityBadge = (priority) => {
    const priorityMap = {
      'urgente': { text: '🚨 URGENT', color: '#dc2626', bg: '#fee2e2' },
      'haute': { text: '⚡ Haute', color: '#ea580c', bg: '#fed7aa' },
      'normale': { text: '📝 Normale', color: '#059669', bg: '#dcfce7' },
      'basse': { text: '🔵 Basse', color: '#2563eb', bg: '#dbeafe' }
    };
    
    const style = priorityMap[priority] || priorityMap['normale'];
    return (
      <span style={{
        padding: '2px 6px',
        borderRadius: '10px',
        fontSize: '11px',
        fontWeight: '600',
        color: style.color,
        background: style.bg
      }}>
        {style.text}
      </span>
    );
  };

  // Rendu compact intégré selon le rôle - Section missions visible sur la home
  const missionsEnCours = missions.assigned_to_me?.filter(m => m.status === 'en_cours') || [];
  const missionsAValider = missions.created_by_me?.filter(m => m.status === 'terminee_attente') || [];

  if (loading) {
    return (
      <div style={{textAlign: 'center', padding: '20px'}}>
        <div>🔄 Chargement des missions...</div>
      </div>
    );
  }

  return (
    <div style={{marginBottom: '20px'}}>
      {/* Missions personnelles prioritaires */}
      {missionsEnCours.length > 0 && (
        <div style={{
          background: 'linear-gradient(135deg, #fff7ed 0%, #fed7aa 100%)',
          borderRadius: '12px',
          padding: '16px',
          marginBottom: '16px',
          border: '2px solid #ea580c'
        }}>
          <div style={{fontSize: '16px', fontWeight: 'bold', color: '#c2410c', marginBottom: '12px'}}>
            🎯 Mes Tâches Urgentes ({missionsEnCours.length})
          </div>
          
          <div style={{display: 'grid', gap: '12px'}}>
            {missionsEnCours.slice(0, 2).map(mission => (
              <div key={mission.id} style={{
                padding: '12px',
                background: 'white',
                borderRadius: '8px',
                border: '1px solid #fdba74',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center'
              }}>
                <div>
                  <div style={{fontSize: '14px', fontWeight: '600', marginBottom: '4px'}}>
                    {mission.title}
                  </div>
                  <div style={{fontSize: '12px', color: '#ea580c', marginBottom: '6px'}}>
                    {mission.description.substring(0, 60)}...
                  </div>
                  {getPriorityBadge(mission.priority)}
                </div>
                <button 
                  onClick={() => {
                    const notes = window.prompt('Commentaires sur la tâche terminée:');
                    if (notes !== null) {
                      markMissionCompleted(mission.id, notes);
                    }
                  }}
                  style={{
                    fontSize: '12px',
                    padding: '6px 12px',
                    borderRadius: '6px',
                    background: '#ea580c',
                    color: 'white',
                    border: 'none',
                    cursor: 'pointer'
                  }}
                >
                  ✅ Fait
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Missions à valider (chef/patron) */}
      {(user.role === 'super_admin' || user.role === 'chef_cuisine') && missionsAValider.length > 0 && (
        <div style={{
          background: 'linear-gradient(135deg, #fef3c7 0%, #fbbf24 100%)',
          borderRadius: '12px',
          padding: '16px',
          marginBottom: '16px',
          border: '2px solid #d97706'
        }}>
          <div style={{fontSize: '16px', fontWeight: 'bold', color: '#92400e', marginBottom: '12px'}}>
            ⏳ Missions à Valider ({missionsAValider.length})
          </div>
          
          <div style={{display: 'grid', gap: '12px'}}>
            {missionsAValider.slice(0, 3).map(mission => (
              <div key={mission.id} style={{
                padding: '12px',
                background: 'white',
                borderRadius: '8px',
                border: '1px solid #fbbf24',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center'
              }}>
                <div>
                  <div style={{fontSize: '14px', fontWeight: '600', marginBottom: '4px'}}>
                    {mission.title}
                  </div>
                  <div style={{fontSize: '12px', color: '#d97706', marginBottom: '4px'}}>
                    👤 {mission.assigned_to_name}
                  </div>
                  <div style={{fontSize: '11px', color: '#92400e'}}>
                    📝 {mission.employee_notes || 'Pas de commentaire'}
                  </div>
                </div>
                <button 
                  onClick={() => validateMission(mission.id, 'Validé')}
                  style={{
                    fontSize: '12px',
                    padding: '6px 12px',
                    borderRadius: '6px',
                    background: '#10b981',
                    color: 'white',
                    border: 'none',
                    cursor: 'pointer'
                  }}
                >
                  ✅ Valider
                </button>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default RoleBasedDashboard;