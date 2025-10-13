import React, { useState, useEffect } from 'react';
import axios from 'axios';

const RoleBasedDashboard = ({ user, sessionId, onNavigateToPage, onCreateMission, activeDashboardTab }) => {
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
      {/* Message de bienvenue personnalisé selon le rôle */}
      <div style={{
        background: 'linear-gradient(135deg, #059669 0%, #10b981 100%)',
        borderRadius: '12px',
        padding: '20px',
        marginBottom: '20px',
        color: 'white',
        textAlign: 'center'
      }}>
        <div style={{fontSize: '24px', marginBottom: '8px'}}>
          {user.role === 'super_admin' && '👑'}
          {user.role === 'chef_cuisine' && '👨‍🍳'}  
          {user.role === 'caissier' && '💰'}
          {user.role === 'barman' && '🍹'}
          {user.role === 'employe_cuisine' && '🥘'}
        </div>
        
        <div style={{fontSize: '18px', fontWeight: 'bold', marginBottom: '8px'}}>
          Bonjour {user.full_name?.split('(')[0].trim() || user.username} !
        </div>
        
        <div style={{fontSize: '14px', opacity: 0.9}}>
          {user.role === 'super_admin' && 
            `🌟 Excellente journée ! Gérez votre équipe et supervisez les opérations de La Table d'Augustine.`
          }
          {user.role === 'chef_cuisine' && 
            `🔥 Prêt pour un nouveau service ! Coordonnez votre équipe et assurez-vous que tout est parfait.`
          }
          {user.role === 'caissier' && 
            `💪 À vous de jouer ! Gérez les stocks et supervisez les livraisons pour un service impeccable.`
          }
          {user.role === 'barman' && 
            `🎯 C'est parti ! Préparez le bar et assurez-vous que tout soit prêt pour accueillir nos clients.`
          }
          {user.role === 'employe_cuisine' && 
            `⭐ Nouvelle journée, nouvelles missions ! Accomplissez vos tâches avec soin pour une cuisine parfaite.`
          }
        </div>
        
        <div style={{fontSize: '12px', opacity: 0.8, marginTop: '8px'}}>
          📅 {new Date().toLocaleDateString('fr-FR', {
            weekday: 'long', 
            day: 'numeric', 
            month: 'long',
            year: 'numeric'
          })}
        </div>
      </div>

      {/* Module 1 : Tâches urgentes à effectuer aujourd'hui */}
      {missionsEnCours.length > 0 && (
        <div style={{
          background: 'linear-gradient(135deg, #fff7ed 0%, #fed7aa 100%)',
          borderRadius: '12px',
          padding: '16px',
          marginBottom: '16px',
          border: '2px solid #ea580c'
        }}>
          <div style={{fontSize: '16px', fontWeight: 'bold', color: '#c2410c', marginBottom: '12px'}}>
            🎯 Tâches à Effectuer Aujourd'hui ({missionsEnCours.length})
          </div>
          
          <div style={{display: 'grid', gap: '12px'}}>
            {missionsEnCours.map(mission => (
              <div key={mission.id} style={{
                padding: '14px',
                background: 'white',
                borderRadius: '8px',
                border: '1px solid #fdba74'
              }}>
                <div style={{fontSize: '15px', fontWeight: '600', marginBottom: '6px', color: '#c2410c'}}>
                  {mission.title}
                </div>
                <div style={{fontSize: '13px', color: '#ea580c', marginBottom: '8px'}}>
                  {mission.description}
                </div>
                
                <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
                  <div style={{display: 'flex', gap: '8px', alignItems: 'center'}}>
                    {getPriorityBadge(mission.priority)}
                    {mission.due_date && (
                      <span style={{
                        fontSize: '11px',
                        color: '#dc2626', 
                        fontWeight: '600',
                        padding: '2px 6px',
                        background: '#fee2e2',
                        borderRadius: '4px'
                      }}>
                        ⏰ {new Date(mission.due_date).toLocaleTimeString('fr-FR', {hour: '2-digit', minute: '2-digit'})}
                      </span>
                    )}
                    {mission.target_quantity && (
                      <span style={{
                        fontSize: '11px',
                        color: '#92400e',
                        fontWeight: '600',
                        padding: '2px 6px',
                        background: '#fdba74',
                        borderRadius: '4px'
                      }}>
                        🎯 {mission.target_quantity} {mission.target_unit}
                      </span>
                    )}
                  </div>
                  
                  <button 
                    onClick={() => {
                      const notes = window.prompt('Détails sur l\'accomplissement de la tâche (obligatoire):');
                      if (notes && notes.trim()) {
                        markMissionCompleted(mission.id, notes);
                      } else if (notes === '') {
                        alert('❌ Une note est obligatoire pour marquer la tâche comme terminée.');
                      }
                    }}
                    style={{
                      fontSize: '13px',
                      padding: '8px 16px',
                      borderRadius: '6px',
                      background: '#ea580c',
                      color: 'white',
                      border: 'none',
                      cursor: 'pointer',
                      fontWeight: '600'
                    }}
                  >
                    ✅ Terminé
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Module 2 : Tâches en cours ou déjà effectuées (en attente validation) */}
      {missions.assigned_to_me?.filter(m => m.status === 'terminee_attente' || m.status === 'validee').length > 0 && (
        <div style={{
          background: 'linear-gradient(135deg, #f0fdf4 0%, #bbf7d0 100%)',
          borderRadius: '12px',
          padding: '16px',
          marginBottom: '16px',
          border: '2px solid #10b981'
        }}>
          <div style={{fontSize: '16px', fontWeight: 'bold', color: '#065f46', marginBottom: '12px'}}>
            📊 Mes Tâches Récentes ({missions.assigned_to_me?.filter(m => m.status === 'terminee_attente' || m.status === 'validee').length || 0})
          </div>
          
          <div style={{display: 'grid', gap: '10px'}}>
            {missions.assigned_to_me?.filter(m => m.status === 'terminee_attente' || m.status === 'validee').slice(0, 4).map(mission => (
              <div key={mission.id} style={{
                padding: '12px',
                background: 'white',
                borderRadius: '6px',
                border: '1px solid #bbf7d0',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center'
              }}>
                <div>
                  <div style={{fontSize: '14px', fontWeight: '600', marginBottom: '3px', color: '#065f46'}}>
                    {mission.title}
                  </div>
                  <div style={{fontSize: '11px', color: '#10b981'}}>
                    {mission.completed_by_employee_date && 
                      `Terminé le ${new Date(mission.completed_by_employee_date).toLocaleDateString('fr-FR')} à ${new Date(mission.completed_by_employee_date).toLocaleTimeString('fr-FR', {hour: '2-digit', minute: '2-digit'})}`
                    }
                  </div>
                  {mission.employee_notes && (
                    <div style={{fontSize: '11px', color: '#059669', fontStyle: 'italic'}}>
                      💬 "{mission.employee_notes}"
                    </div>
                  )}
                </div>
                
                <div>
                  {getStatusBadge(mission.status)}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Module pour Chef/Patron : Missions à valider */}
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

      {/* Bouton Créer Mission pour Chef, Patron ET Caissier */}
      {(user.role === 'super_admin' || user.role === 'chef_cuisine' || user.role === 'caissier') && (
        <div style={{
          background: 'white',
          borderRadius: '12px',
          padding: '16px',
          marginBottom: '16px',
          border: '1px solid #e5e7eb'
        }}>
          <button
            onClick={() => {
              if (onCreateMission) {
                onCreateMission();
              }
            }}
            style={{
              width: '100%',
              padding: '14px 20px',
              background: 'linear-gradient(135deg, #3b82f6 0%, #1e40af 100%)',
              color: 'white',
              border: 'none',
              borderRadius: '8px',
              fontSize: '16px',
              fontWeight: '600',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '8px'
            }}
          >
            ➕ Créer une Nouvelle Mission
          </button>
        </div>
      )}
    </div>
  );
};

export default RoleBasedDashboard;