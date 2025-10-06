import React, { useState, useEffect } from 'react';
import axios from 'axios';

const RoleBasedDashboard = ({ user, sessionId }) => {
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

  // Interface spécifique selon le rôle
  const renderRoleSpecificContent = () => {
    switch (user.role) {
      case 'super_admin': // PATRON
        return (
          <div>
            <div style={{display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '20px', marginBottom: '24px'}}>
              {/* Missions assignées à moi */}
              <div style={{background: 'white', borderRadius: '12px', padding: '20px', border: '1px solid #e5e7eb'}}>
                <h3 style={{fontSize: '18px', fontWeight: 'bold', color: '#dc2626', marginBottom: '16px'}}>
                  👑 Mes Missions ({missions.assigned_to_me?.length || 0})
                </h3>
                {missions.assigned_to_me?.length > 0 ? (
                  missions.assigned_to_me.slice(0, 3).map(mission => (
                    <div key={mission.id} style={{
                      padding: '12px',
                      background: '#fef2f2',
                      borderRadius: '8px',
                      marginBottom: '8px',
                      border: '1px solid #fecaca'
                    }}>
                      <div style={{fontSize: '14px', fontWeight: '600', marginBottom: '4px'}}>
                        {mission.title}
                      </div>
                      <div style={{display: 'flex', gap: '8px', marginBottom: '6px'}}>
                        {getStatusBadge(mission.status)}
                        {getPriorityBadge(mission.priority)}
                      </div>
                    </div>
                  ))
                ) : (
                  <div style={{textAlign: 'center', color: '#6b7280', fontSize: '14px'}}>
                    Aucune mission assignée
                  </div>
                )}
              </div>

              {/* Missions que j'ai créées */}
              <div style={{background: 'white', borderRadius: '12px', padding: '20px', border: '1px solid #e5e7eb'}}>
                <h3 style={{fontSize: '18px', fontWeight: 'bold', color: '#059669', marginBottom: '16px'}}>
                  📋 Missions Données ({missions.created_by_me?.length || 0})
                </h3>
                {missions.created_by_me?.length > 0 ? (
                  missions.created_by_me.slice(0, 3).map(mission => (
                    <div key={mission.id} style={{
                      padding: '12px',
                      background: '#f0fdf4',
                      borderRadius: '8px',
                      marginBottom: '8px',
                      border: '1px solid #bbf7d0'
                    }}>
                      <div style={{fontSize: '14px', fontWeight: '600', marginBottom: '4px'}}>
                        {mission.title}
                      </div>
                      <div style={{fontSize: '12px', color: '#059669', marginBottom: '4px'}}>
                        👤 {mission.assigned_to_name}
                      </div>
                      <div style={{display: 'flex', gap: '8px'}}>
                        {getStatusBadge(mission.status)}
                        {mission.status === 'terminee_attente' && (
                          <button 
                            onClick={() => validateMission(mission.id, 'Validé par le patron')}
                            style={{
                              fontSize: '10px',
                              padding: '2px 6px',
                              borderRadius: '4px',
                              background: '#10b981',
                              color: 'white',
                              border: 'none',
                              cursor: 'pointer'
                            }}
                          >
                            ✅ Valider
                          </button>
                        )}
                      </div>
                    </div>
                  ))
                ) : (
                  <div style={{textAlign: 'center', color: '#6b7280', fontSize: '14px'}}>
                    Aucune mission créée
                  </div>
                )}
              </div>
            </div>

            {/* Analytics pour le patron */}
            <div style={{background: 'white', borderRadius: '12px', padding: '20px', border: '1px solid #e5e7eb'}}>
              <h3 style={{fontSize: '18px', fontWeight: 'bold', color: '#374151', marginBottom: '16px'}}>
                📊 Vue d'ensemble de l'équipe
              </h3>
              <div style={{display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))', gap: '12px'}}>
                <div style={{textAlign: 'center', padding: '12px', background: '#fef3c7', borderRadius: '8px'}}>
                  <div style={{fontSize: '20px', fontWeight: 'bold', color: '#d97706'}}>
                    {missions.created_by_me?.filter(m => m.status === 'terminee_attente').length || 0}
                  </div>
                  <div style={{fontSize: '12px', color: '#92400e'}}>À valider</div>
                </div>
                <div style={{textAlign: 'center', padding: '12px', background: '#dcfce7', borderRadius: '8px'}}>
                  <div style={{fontSize: '20px', fontWeight: 'bold', color: '#059669'}}>
                    {missions.created_by_me?.filter(m => m.status === 'validee').length || 0}
                  </div>
                  <div style={{fontSize: '12px', color: '#065f46'}}>Validées</div>
                </div>
                <div style={{textAlign: 'center', padding: '12px', background: '#dbeafe', borderRadius: '8px'}}>
                  <div style={{fontSize: '20px', fontWeight: 'bold', color: '#2563eb'}}>
                    {missions.created_by_me?.filter(m => m.status === 'en_cours').length || 0}
                  </div>
                  <div style={{fontSize: '12px', color: '#1e40af'}}>En cours</div>
                </div>
              </div>
            </div>
          </div>
        );

      case 'chef_cuisine': // CHEF DE CUISINE - ACCÈS LIMITÉ
        return (
          <div>
            {/* Message d'information sur les restrictions */}
            <div style={{
              background: '#eff6ff',
              border: '1px solid #93c5fd',
              borderRadius: '8px',
              padding: '12px',
              marginBottom: '20px',
              fontSize: '14px',
              color: '#1e40af'
            }}>
              👨‍🍳 <strong>Interface Chef de Cuisine</strong> - Accès aux missions, production et stocks. 
              Pas d'accès aux analytics business et OCR tickets Z.
            </div>

            <div style={{display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '20px', marginBottom: '24px'}}>
              {/* Mes tâches prioritaires */}
              <div style={{background: 'white', borderRadius: '12px', padding: '20px', border: '1px solid #e5e7eb'}}>
                <h3 style={{fontSize: '18px', fontWeight: 'bold', color: '#059669', marginBottom: '16px'}}>
                  📋 Mes Tâches ({missions.assigned_to_me?.filter(m => m.status === 'en_cours').length || 0})
                </h3>
                {missions.assigned_to_me?.filter(m => m.status === 'en_cours').slice(0, 4).map(mission => (
                  <div key={mission.id} style={{
                    padding: '12px',
                    background: '#f0fdf4',
                    borderRadius: '8px',
                    marginBottom: '10px',
                    border: '1px solid #bbf7d0'
                  }}>
                    <div style={{fontSize: '14px', fontWeight: '600', marginBottom: '6px'}}>
                      {mission.title}
                    </div>
                    <div style={{fontSize: '12px', color: '#059669', marginBottom: '8px'}}>
                      {mission.description}
                    </div>
                    <div style={{display: 'flex', gap: '8px', justifyContent: 'space-between', alignItems: 'center'}}>
                      {getPriorityBadge(mission.priority)}
                      <button 
                        onClick={() => {
                          const notes = window.prompt('Notes (optionnel):');
                          if (notes !== null) {
                            markMissionCompleted(mission.id, notes);
                          }
                        }}
                        style={{
                          fontSize: '11px',
                          padding: '4px 8px',
                          borderRadius: '4px',
                          background: '#10b981',
                          color: 'white',
                          border: 'none',
                          cursor: 'pointer'
                        }}
                      >
                        ✅ Terminé
                      </button>
                    </div>
                  </div>
                )) || (
                  <div style={{textAlign: 'center', color: '#6b7280', fontSize: '14px'}}>
                    Aucune tâche en cours
                  </div>
                )}
              </div>

              {/* Gestion de l'équipe cuisine */}
              <div style={{background: 'white', borderRadius: '12px', padding: '20px', border: '1px solid #e5e7eb'}}>
                <h3 style={{fontSize: '18px', fontWeight: 'bold', color: '#ea580c', marginBottom: '16px'}}>
                  👥 Équipe Cuisine ({missions.created_by_me?.length || 0})
                </h3>
                {missions.created_by_me?.slice(0, 4).map(mission => (
                  <div key={mission.id} style={{
                    padding: '12px',
                    background: mission.status === 'terminee_attente' ? '#fef3c7' : '#f8fafc',
                    borderRadius: '8px',
                    marginBottom: '10px',
                    border: `1px solid ${mission.status === 'terminee_attente' ? '#fbbf24' : '#e2e8f0'}`
                  }}>
                    <div style={{fontSize: '13px', fontWeight: '600', marginBottom: '4px'}}>
                      👤 {mission.assigned_to_name}
                    </div>
                    <div style={{fontSize: '12px', marginBottom: '6px'}}>
                      {mission.title}
                    </div>
                    <div style={{display: 'flex', gap: '8px', justifyContent: 'space-between', alignItems: 'center'}}>
                      {getStatusBadge(mission.status)}
                      {mission.status === 'terminee_attente' && (
                        <button 
                          onClick={() => validateMission(mission.id, 'Validé par le chef')}
                          style={{
                            fontSize: '10px',
                            padding: '3px 6px',
                            borderRadius: '4px',
                            background: '#10b981',
                            color: 'white',
                            border: 'none',
                            cursor: 'pointer'
                          }}
                        >
                          ✅ Valider
                        </button>
                      )}
                    </div>
                  </div>
                )) || (
                  <div style={{textAlign: 'center', color: '#6b7280', fontSize: '14px'}}>
                    Aucune mission donnée
                  </div>
                )}
              </div>
            </div>

            {/* Accès limité aux fonctions production/stock */}
            <div style={{background: 'white', borderRadius: '12px', padding: '20px', border: '1px solid #e5e7eb'}}>
              <h3 style={{fontSize: '18px', fontWeight: 'bold', color: '#1f2937', marginBottom: '16px'}}>
                🔧 Accès Autorisés - Chef de Cuisine
              </h3>
              
              <div style={{display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '12px'}}>
                {[
                  { icon: '🥘', label: 'Productions', desc: 'Gestion recettes', color: '#059669' },
                  { icon: '📦', label: 'Stocks', desc: 'Gestion inventaire', color: '#2563eb' },
                  { icon: '🔪', label: 'Préparations', desc: 'Découpes & mise en place', color: '#ea580c' },
                  { icon: '🚚', label: 'Fournisseurs', desc: 'Contacts & livraisons', color: '#7c3aed' },
                  { icon: '🛒', label: 'Commandes', desc: 'Suivi des commandes', color: '#dc2626' },
                  { icon: '👥', label: 'Équipe', desc: 'Missions cuisiniers', color: '#059669' }
                ].map((access, index) => (
                  <div key={index} style={{
                    padding: '12px',
                    background: '#f9fafb',
                    borderRadius: '6px',
                    border: '1px solid #e5e7eb',
                    textAlign: 'center'
                  }}>
                    <div style={{fontSize: '24px', marginBottom: '4px'}}>{access.icon}</div>
                    <div style={{fontSize: '12px', fontWeight: '600', color: access.color, marginBottom: '2px'}}>
                      {access.label}
                    </div>
                    <div style={{fontSize: '10px', color: '#6b7280'}}>
                      {access.desc}
                    </div>
                  </div>
                ))}
              </div>
              
              {/* Restrictions explicites */}
              <div style={{
                marginTop: '16px',
                padding: '12px',
                background: '#fef2f2',
                borderRadius: '6px',
                border: '1px solid #fecaca'
              }}>
                <div style={{fontSize: '12px', color: '#dc2626', fontWeight: '600', marginBottom: '4px'}}>
                  🚫 Accès restreints :
                </div>
                <div style={{fontSize: '11px', color: '#991b1b'}}>
                  • Analytics & chiffres d'affaires • OCR Tickets Z • Gestion utilisateurs • Vue business complète
                </div>
              </div>
            </div>
          </div>
        );

      case 'barman': // BARMAN
        return (
          <div>
            <div style={{background: 'white', borderRadius: '12px', padding: '20px', border: '1px solid #e5e7eb', marginBottom: '20px'}}>
              <h3 style={{fontSize: '18px', fontWeight: 'bold', color: '#7c3aed', marginBottom: '16px'}}>
                🍹 Mes Tâches Bar ({missions.assigned_to_me?.filter(m => m.status === 'en_cours').length || 0})
              </h3>
              {missions.assigned_to_me?.filter(m => m.status === 'en_cours').map(mission => (
                <div key={mission.id} style={{
                  padding: '16px',
                  background: '#faf5ff',
                  borderRadius: '8px',
                  marginBottom: '12px',
                  border: '1px solid #d8b4fe'
                }}>
                  <div style={{fontSize: '16px', fontWeight: '600', marginBottom: '8px'}}>
                    {mission.title}
                  </div>
                  <div style={{fontSize: '14px', color: '#6b46c1', marginBottom: '10px'}}>
                    {mission.description}
                  </div>
                  <div style={{display: 'flex', gap: '10px', justifyContent: 'space-between', alignItems: 'center'}}>
                    {getPriorityBadge(mission.priority)}
                    <button 
                      onClick={() => {
                        const notes = window.prompt('Commentaires sur la tâche terminée:');
                        if (notes !== null) {
                          markMissionCompleted(mission.id, notes);
                        }
                      }}
                      style={{
                        fontSize: '14px',
                        padding: '8px 16px',
                        borderRadius: '6px',
                        background: '#7c3aed',
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
              )) || (
                <div style={{textAlign: 'center', padding: '40px', color: '#6b7280'}}>
                  <div style={{fontSize: '48px', marginBottom: '12px'}}>🍹</div>
                  <div>Aucune tâche en cours</div>
                  <div style={{fontSize: '14px'}}>Profitez d'un moment de calme !</div>
                </div>
              )}
            </div>
          </div>
        );

      case 'caissier': // RESPONSABLE CAISSE  
        return (
          <div>
            <div style={{background: 'white', borderRadius: '12px', padding: '20px', border: '1px solid #e5e7eb'}}>
              <h3 style={{fontSize: '18px', fontWeight: 'bold', color: '#2563eb', marginBottom: '16px'}}>
                💰 Todo List - Caisse ({missions.assigned_to_me?.filter(m => m.status === 'en_cours').length || 0})
              </h3>
              {missions.assigned_to_me?.filter(m => m.status === 'en_cours').map(mission => (
                <div key={mission.id} style={{
                  padding: '16px',
                  background: '#eff6ff',
                  borderRadius: '8px',
                  marginBottom: '12px',
                  border: '1px solid #93c5fd'
                }}>
                  <div style={{fontSize: '16px', fontWeight: '600', marginBottom: '8px'}}>
                    {mission.title}
                  </div>
                  <div style={{fontSize: '14px', color: '#1e40af', marginBottom: '10px'}}>
                    {mission.description}
                  </div>
                  <div style={{display: 'flex', gap: '10px', justifyContent: 'space-between', alignItems: 'center'}}>
                    <div style={{display: 'flex', gap: '8px'}}>
                      {getPriorityBadge(mission.priority)}
                      {mission.due_date && (
                        <span style={{fontSize: '11px', color: '#6b7280'}}>
                          ⏰ {new Date(mission.due_date).toLocaleTimeString('fr-FR', {hour: '2-digit', minute: '2-digit'})}
                        </span>
                      )}
                    </div>
                    <button 
                      onClick={() => markMissionCompleted(mission.id, '')}
                      style={{
                        fontSize: '14px',
                        padding: '8px 16px',
                        borderRadius: '6px',
                        background: '#2563eb',
                        color: 'white',
                        border: 'none',
                        cursor: 'pointer',
                        fontWeight: '600'
                      }}
                    >
                      ✅ Fait
                    </button>
                  </div>
                </div>
              )) || (
                <div style={{textAlign: 'center', padding: '40px', color: '#6b7280'}}>
                  <div style={{fontSize: '48px', marginBottom: '12px'}}>💰</div>
                  <div>Aucune tâche en cours</div>
                </div>
              )}
            </div>
          </div>
        );

      case 'gerant': // EMPLOYÉ CUISINE
        return (
          <div>
            <div style={{background: 'white', borderRadius: '12px', padding: '20px', border: '1px solid #e5e7eb'}}>
              <h3 style={{fontSize: '20px', fontWeight: 'bold', color: '#ea580c', marginBottom: '20px'}}>
                🥘 Mes Tâches de Cuisine ({missions.assigned_to_me?.filter(m => m.status === 'en_cours').length || 0})
              </h3>
              
              {missions.assigned_to_me?.filter(m => m.status === 'en_cours').length > 0 ? (
                missions.assigned_to_me.filter(m => m.status === 'en_cours').map(mission => (
                  <div key={mission.id} style={{
                    padding: '20px',
                    background: '#fff7ed',
                    borderRadius: '10px',
                    marginBottom: '16px',
                    border: '2px solid #fed7aa'
                  }}>
                    <div style={{fontSize: '18px', fontWeight: 'bold', marginBottom: '10px', color: '#c2410c'}}>
                      {mission.title}
                    </div>
                    <div style={{fontSize: '15px', color: '#ea580c', marginBottom: '12px', lineHeight: '1.4'}}>
                      {mission.description}
                    </div>
                    
                    {mission.target_quantity && (
                      <div style={{
                        padding: '8px 12px',
                        background: '#fdba74',
                        borderRadius: '6px',
                        fontSize: '14px',
                        color: '#9a3412',
                        marginBottom: '12px',
                        fontWeight: '600'
                      }}>
                        🎯 Objectif: {mission.target_quantity} {mission.target_unit}
                      </div>
                    )}
                    
                    <div style={{display: 'flex', gap: '12px', justifyContent: 'space-between', alignItems: 'center'}}>
                      <div style={{display: 'flex', gap: '8px'}}>
                        {getPriorityBadge(mission.priority)}
                        {mission.due_date && (
                          <span style={{
                            fontSize: '12px', 
                            color: '#dc2626',
                            fontWeight: '600',
                            padding: '2px 6px',
                            background: '#fee2e2',
                            borderRadius: '4px'
                          }}>
                            ⏰ À faire avant {new Date(mission.due_date).toLocaleTimeString('fr-FR', {hour: '2-digit', minute: '2-digit'})}
                          </span>
                        )}
                      </div>
                      <button 
                        onClick={() => {
                          const notes = window.prompt('Détails sur l\'accomplissement de la tâche:');
                          if (notes !== null) {
                            markMissionCompleted(mission.id, notes);
                          }
                        }}
                        style={{
                          fontSize: '16px',
                          padding: '10px 20px',
                          borderRadius: '8px',
                          background: '#ea580c',
                          color: 'white',
                          border: 'none',
                          cursor: 'pointer',
                          fontWeight: 'bold'
                        }}
                      >
                        ✅ Terminée !
                      </button>
                    </div>
                  </div>
                ))
              ) : (
                <div style={{textAlign: 'center', padding: '60px', color: '#6b7280'}}>
                  <div style={{fontSize: '64px', marginBottom: '16px'}}>🥘</div>
                  <div style={{fontSize: '18px', fontWeight: '600', marginBottom: '8px'}}>Aucune tâche en cours</div>
                  <div style={{fontSize: '16px'}}>Excellent travail ! Vous êtes à jour.</div>
                </div>
              )}

              {/* Missions terminées récentes */}
              {missions.assigned_to_me?.filter(m => m.status === 'terminee_attente' || m.status === 'validee').length > 0 && (
                <div style={{marginTop: '20px', padding: '16px', background: '#f3f4f6', borderRadius: '8px'}}>
                  <h4 style={{fontSize: '14px', fontWeight: '600', color: '#374151', marginBottom: '10px'}}>
                    📊 Missions récentes terminées
                  </h4>
                  {missions.assigned_to_me.filter(m => m.status === 'terminee_attente' || m.status === 'validee').slice(0, 3).map(mission => (
                    <div key={mission.id} style={{fontSize: '12px', color: '#6b7280', marginBottom: '4px'}}>
                      • {mission.title} - {getStatusBadge(mission.status)}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        );

      default:
        return (
          <div style={{textAlign: 'center', padding: '40px'}}>
            <div style={{fontSize: '48px', marginBottom: '16px'}}>🔒</div>
            <div style={{fontSize: '18px', fontWeight: 'bold', marginBottom: '8px'}}>
              Interface en cours de développement
            </div>
            <div style={{color: '#6b7280'}}>
              Rôle: {user.role}
            </div>
          </div>
        );
    }
  };

  if (loading) {
    return (
      <div style={{textAlign: 'center', padding: '40px'}}>
        <div style={{fontSize: '32px', marginBottom: '16px'}}>🔄</div>
        <div>Chargement des missions...</div>
      </div>
    );
  }

  return (
    <div style={{padding: '20px', background: '#f9fafb', minHeight: '100vh'}}>
      {/* Header utilisateur */}
      <div style={{
        background: 'white',
        borderRadius: '12px',
        padding: '20px',
        marginBottom: '24px',
        border: '1px solid #e5e7eb',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center'
      }}>
        <div>
          <h1 style={{fontSize: '24px', fontWeight: 'bold', color: '#059669', marginBottom: '4px'}}>
            Bonjour {user.full_name} !
          </h1>
          <p style={{fontSize: '14px', color: '#6b7280', margin: '0'}}>
            Connecté en tant que {user.role} • {new Date().toLocaleDateString('fr-FR', {
              weekday: 'long', year: 'numeric', month: 'long', day: 'numeric'
            })}
          </p>
        </div>
        
        {/* Notifications */}
        <div style={{display: 'flex', alignItems: 'center', gap: '12px'}}>
          <div style={{position: 'relative'}}>
            <button style={{
              background: notifications.filter(n => !n.read).length > 0 ? '#dc2626' : '#6b7280',
              color: 'white',
              border: 'none',
              borderRadius: '20px',
              padding: '8px 12px',
              fontSize: '14px',
              cursor: 'pointer'
            }}>
              🔔 {notifications.filter(n => !n.read).length}
            </button>
          </div>
          
          <button
            onClick={() => {
              localStorage.removeItem('user_session');
              window.location.reload();
            }}
            style={{
              background: '#dc2626',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              padding: '8px 16px',
              fontSize: '14px',
              cursor: 'pointer'
            }}
          >
            🚪 Déconnexion
          </button>
        </div>
      </div>

      {/* Contenu spécifique au rôle */}
      {renderRoleSpecificContent()}
    </div>
  );
};

export default RoleBasedDashboard;