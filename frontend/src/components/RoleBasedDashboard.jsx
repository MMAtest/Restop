import React, { useState, useEffect } from 'react';
import axios from 'axios';
import DailySpecialMission from './DailySpecialMission';

const RoleBasedDashboard = ({ user, sessionId, onNavigateToPage, onCreateMission, activeDashboardTab, selectedDateRange }) => {
  const [missions, setMissions] = useState([]);
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(false);

  const API = process.env.REACT_APP_BACKEND_URL || import.meta.env.REACT_APP_BACKEND_URL;

  useEffect(() => {
    if (user?.id) {
      fetchMissionsAndNotifications();
    }
  }, [user]);

  useEffect(() => {
    const handleRefreshMissions = () => {
      fetchMissionsAndNotifications();
    };
    window.addEventListener('refreshMissions', handleRefreshMissions);
    return () => {
      window.removeEventListener('refreshMissions', handleRefreshMissions);
    };
  }, []);

  const fetchMissionsAndNotifications = async () => {
    try {
      setLoading(true);
      const missionsResponse = await axios.get(`${API}/api/missions/by-user/${user.id}`);
      setMissions(missionsResponse.data);
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
      alert('Mission marquee comme terminee ! Elle est en attente de validation.');
      fetchMissionsAndNotifications();
    } catch (error) {
      console.error('Erreur:', error);
      alert('Erreur lors de la mise a jour');
    }
  };

  const validateMission = async (missionId, notes = '') => {
    try {
      await axios.put(`${API}/api/missions/${missionId}?user_id=${user.id}`, {
        status: 'validee',
        validation_notes: notes
      });
      alert('Mission validee avec succes !');
      fetchMissionsAndNotifications();
    } catch (error) {
      console.error('Erreur:', error);
      alert('Erreur lors de la validation');
    }
  };

  const getStatusBadge = (status) => {
    const statusMap = {
      'en_cours': { text: 'En cours', color: '#2C4A3B', bg: '#E8F5EE' },
      'terminee_attente': { text: 'Attente validation', color: '#92400e', bg: '#FEF3C7' },
      'validee': { text: 'Validee', color: '#065f46', bg: '#D1FAE5' },
      'en_retard': { text: 'En retard', color: '#C85A32', bg: '#FEE2E2' },
      'annulee': { text: 'Annulee', color: '#6b7280', bg: '#F3F4F6' }
    };
    const style = statusMap[status] || statusMap['en_cours'];
    return (
      <span data-testid={`mission-status-${status}`} style={{
        padding: '3px 10px', borderRadius: '20px', fontSize: '11px',
        fontWeight: '600', color: style.color, background: style.bg,
        fontFamily: 'Manrope, sans-serif', letterSpacing: '0.2px'
      }}>
        {style.text}
      </span>
    );
  };

  const getPriorityBadge = (priority) => {
    const priorityMap = {
      'urgente': { text: 'URGENT', color: '#C85A32', bg: '#FEE2E2' },
      'haute': { text: 'Haute', color: '#ea580c', bg: '#FED7AA' },
      'normale': { text: 'Normale', color: '#2C4A3B', bg: '#E8F5EE' },
      'basse': { text: 'Basse', color: '#2563eb', bg: '#DBEAFE' }
    };
    const style = priorityMap[priority] || priorityMap['normale'];
    return (
      <span style={{
        padding: '2px 8px', borderRadius: '20px', fontSize: '10px',
        fontWeight: '700', color: style.color, background: style.bg,
        fontFamily: 'Manrope, sans-serif', textTransform: 'uppercase', letterSpacing: '0.5px'
      }}>
        {style.text}
      </span>
    );
  };

  const filterMissionsByDateRange = (missionsList, dateRange) => {
    if (!dateRange || !missionsList) return missionsList;
    return missionsList.filter(mission => {
      const missionDate = new Date(mission.assigned_date);
      const missionDateOnly = new Date(missionDate.getFullYear(), missionDate.getMonth(), missionDate.getDate());
      const startDateOnly = new Date(dateRange.startDate.getFullYear(), dateRange.startDate.getMonth(), dateRange.startDate.getDate());
      const endDateOnly = new Date(dateRange.endDate.getFullYear(), dateRange.endDate.getMonth(), dateRange.endDate.getDate());
      return missionDateOnly >= startDateOnly && missionDateOnly <= endDateOnly;
    });
  };

  const getFilteredMissions = () => {
    const now = new Date();
    const defaultStartDate = selectedDateRange ? selectedDateRange.startDate : new Date(now.getFullYear(), now.getMonth(), now.getDate(), 0, 0, 0);
    const defaultEndDate = selectedDateRange ? selectedDateRange.endDate : new Date(now.getFullYear(), now.getMonth(), now.getDate(), 23, 59, 59);
    const dateRange = { startDate: defaultStartDate, endDate: defaultEndDate, label: selectedDateRange?.label || "Aujourd'hui" };
    const missionsCreatedInPeriod = filterMissionsByDateRange(missions.created_by_me || [], dateRange);
    const missionsToValidateInPeriod = filterMissionsByDateRange(
      (missions.created_by_me || []).filter(m => m.status === 'terminee_attente'), dateRange
    );
    return { createdToday: missionsCreatedInPeriod, toValidateToday: missionsToValidateInPeriod, dateLabel: dateRange.label };
  };

  const missionsEnCours = missions.assigned_to_me?.filter(m => m.status === 'en_cours') || [];
  const missionsAValider = missions.created_by_me?.filter(m => m.status === 'terminee_attente') || [];

  const roleInfo = {
    super_admin: { greeting: 'Gerez votre equipe et supervisez les operations.', icon: 'M9 12.75 11.25 15 15 9.75' },
    patron: { greeting: 'Pilotez votre restaurant et suivez les performances.', icon: 'M9 12.75 11.25 15 15 9.75' },
    chef_cuisine: { greeting: 'Coordonnez votre equipe pour un service parfait.', icon: 'M15.362 5.214A8.252 8.252 0 0 1 12 21 8.25 8.25 0 0 1 6.038 7.047' },
    caissier: { greeting: 'Gerez les stocks et supervisez les livraisons.', icon: 'M2.25 18.75a60.07 60.07 0 0 1 15.797 2.101' },
    barman: { greeting: 'Preparez le bar et accueillez nos clients.', icon: 'M9.75 3.104v5.714a2.25 2.25 0 0 1-.659 1.591L5 14.5' },
    employe_cuisine: { greeting: 'Accomplissez vos taches avec soin pour une cuisine parfaite.', icon: 'M11.48 3.499a.562.562 0 0 1 1.04 0l2.125 5.111' }
  };
  const currentRole = roleInfo[user.role] || roleInfo['patron'];

  if (loading) {
    return (
      <div style={{textAlign: 'center', padding: '40px 20px'}}>
        <div style={{
          width: '32px', height: '32px', border: '3px solid #E5E5E0', borderTopColor: '#2C4A3B',
          borderRadius: '50%', animation: 'spin 0.8s linear infinite', margin: '0 auto 12px'
        }}/>
        <div style={{fontFamily: 'Manrope, sans-serif', fontSize: '13px', color: '#8C8C88', fontWeight: '600'}}>Chargement...</div>
        <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
      </div>
    );
  }

  return (
    <div data-testid="role-based-dashboard" style={{marginBottom: '20px'}}>
      {/* Mission obligatoire chef : Plat du jour & Menu enfant */}
      {(user.role === 'chef_cuisine' || user.role === 'patron' || user.role === 'super_admin') && (
        <DailySpecialMission currentUser={user} />
      )}
      {/* Welcome Banner */}
      {(user.role === 'super_admin' && activeDashboardTab === 'ventes') || (user.role !== 'super_admin') ? (
        <div data-testid="welcome-banner" style={{
          position: 'relative', borderRadius: '16px', overflow: 'hidden',
          marginBottom: '20px', height: '140px'
        }}>
          <div style={{
            position: 'absolute', inset: 0,
            background: 'linear-gradient(135deg, #2C4A3B 0%, #3E6B55 60%, #4E8C6F 100%)'
          }}/>
          <div style={{
            position: 'absolute', inset: 0,
            backgroundImage: 'radial-gradient(circle at 20% 50%, rgba(212,175,55,0.08) 0%, transparent 50%), radial-gradient(circle at 80% 30%, rgba(255,255,255,0.05) 0%, transparent 40%)'
          }}/>
          <div style={{
            position: 'relative', zIndex: 1, padding: '20px 24px',
            height: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'center'
          }}>
            <div style={{
              fontFamily: 'Cormorant Garamond, serif', fontSize: '11px', fontWeight: '600',
              color: 'rgba(212,175,55,0.9)', textTransform: 'uppercase', letterSpacing: '2px', marginBottom: '6px'
            }}>
              La Table d'Augustine
            </div>
            <div style={{
              fontFamily: 'Manrope, sans-serif', fontSize: '20px', fontWeight: '700',
              color: '#FFFFFF', letterSpacing: '-0.3px', marginBottom: '6px'
            }}>
              Bonjour, {user.full_name?.split('(')[0].trim() || user.username}
            </div>
            <div style={{
              fontFamily: 'Work Sans, sans-serif', fontSize: '13px',
              color: 'rgba(255,255,255,0.75)', lineHeight: '1.4'
            }}>
              {currentRole.greeting}
            </div>
            <div style={{
              fontFamily: 'Manrope, sans-serif', fontSize: '11px',
              color: 'rgba(255,255,255,0.5)', marginTop: '8px', fontWeight: '600',
              letterSpacing: '0.3px'
            }}>
              {new Date().toLocaleDateString('fr-FR', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' })}
            </div>
          </div>
        </div>
      ) : null}

      {/* Module 1 : Taches urgentes */}
      {missionsEnCours.length > 0 && (
        <div data-testid="urgent-missions" style={{
          background: '#FFFFFF', borderRadius: '16px', padding: '16px',
          marginBottom: '12px', border: '1px solid #E5E5E0',
          borderLeft: '4px solid #C85A32'
        }}>
          <div style={{
            fontFamily: 'Manrope, sans-serif', fontSize: '13px', fontWeight: '700',
            color: '#C85A32', marginBottom: '12px', textTransform: 'uppercase',
            letterSpacing: '0.5px'
          }}>
            Taches a effectuer ({missionsEnCours.length})
          </div>
          <div style={{display: 'grid', gap: '10px'}}>
            {missionsEnCours.map(mission => (
              <div key={mission.id} data-testid={`mission-card-${mission.id}`} style={{
                padding: '14px', background: '#FAFAF8', borderRadius: '12px',
                border: '1px solid #E5E5E0', transition: 'all 0.15s ease'
              }}>
                <div style={{
                  fontFamily: 'Manrope, sans-serif', fontSize: '14px', fontWeight: '600',
                  marginBottom: '4px', color: '#1C1C19'
                }}>
                  {mission.title}
                </div>
                <div style={{fontSize: '12px', color: '#8C8C88', marginBottom: '10px', lineHeight: '1.4'}}>
                  {mission.description}
                </div>
                <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '6px'}}>
                  <div style={{display: 'flex', gap: '6px', alignItems: 'center', flexWrap: 'wrap'}}>
                    {getPriorityBadge(mission.priority)}
                    {mission.due_date && (
                      <span style={{
                        fontSize: '10px', color: '#C85A32', fontWeight: '700',
                        padding: '2px 8px', background: '#FEF2F2', borderRadius: '20px',
                        fontFamily: 'Manrope, sans-serif'
                      }}>
                        {new Date(mission.due_date).toLocaleTimeString('fr-FR', {hour: '2-digit', minute: '2-digit'})}
                      </span>
                    )}
                    {mission.target_quantity && (
                      <span style={{
                        fontSize: '10px', color: '#92400e', fontWeight: '700',
                        padding: '2px 8px', background: '#FEF3C7', borderRadius: '20px',
                        fontFamily: 'Manrope, sans-serif'
                      }}>
                        {mission.target_quantity} {mission.target_unit}
                      </span>
                    )}
                  </div>
                  <button
                    data-testid={`complete-mission-${mission.id}`}
                    onClick={() => {
                      const notes = window.prompt('Details sur l\'accomplissement de la tache (obligatoire):');
                      if (notes && notes.trim()) { markMissionCompleted(mission.id, notes); }
                      else if (notes === '') { alert('Une note est obligatoire pour marquer la tache comme terminee.'); }
                    }}
                    style={{
                      fontSize: '12px', padding: '7px 16px', borderRadius: '20px',
                      background: '#2C4A3B', color: 'white', border: 'none',
                      cursor: 'pointer', fontWeight: '600', fontFamily: 'Manrope, sans-serif',
                      transition: 'all 0.2s ease', letterSpacing: '0.2px'
                    }}
                  >
                    Termine
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Module 2 : Taches recentes */}
      {missions.assigned_to_me?.filter(m => m.status === 'terminee_attente' || m.status === 'validee').length > 0 && (
        <div data-testid="recent-missions" style={{
          background: '#FFFFFF', borderRadius: '16px', padding: '16px',
          marginBottom: '12px', border: '1px solid #E5E5E0',
          borderLeft: '4px solid #2C4A3B'
        }}>
          <div style={{
            fontFamily: 'Manrope, sans-serif', fontSize: '13px', fontWeight: '700',
            color: '#2C4A3B', marginBottom: '12px', textTransform: 'uppercase',
            letterSpacing: '0.5px'
          }}>
            Taches recentes ({missions.assigned_to_me?.filter(m => m.status === 'terminee_attente' || m.status === 'validee').length || 0})
          </div>
          <div style={{display: 'grid', gap: '8px'}}>
            {missions.assigned_to_me?.filter(m => m.status === 'terminee_attente' || m.status === 'validee').slice(0, 4).map(mission => (
              <div key={mission.id} style={{
                padding: '12px 14px', background: '#FAFAF8', borderRadius: '10px',
                border: '1px solid #E5E5E0', display: 'flex',
                justifyContent: 'space-between', alignItems: 'center'
              }}>
                <div style={{flex: 1, minWidth: 0}}>
                  <div style={{fontFamily: 'Manrope, sans-serif', fontSize: '13px', fontWeight: '600', color: '#1C1C19', marginBottom: '2px'}}>
                    {mission.title}
                  </div>
                  <div style={{fontSize: '11px', color: '#8C8C88'}}>
                    {mission.completed_by_employee_date &&
                      `Termine le ${new Date(mission.completed_by_employee_date).toLocaleDateString('fr-FR')} a ${new Date(mission.completed_by_employee_date).toLocaleTimeString('fr-FR', {hour: '2-digit', minute: '2-digit'})}`
                    }
                  </div>
                  {mission.employee_notes && (
                    <div style={{fontSize: '11px', color: '#8C8C88', fontStyle: 'italic', marginTop: '2px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap'}}>
                      "{mission.employee_notes}"
                    </div>
                  )}
                </div>
                <div style={{marginLeft: '10px', flexShrink: 0}}>{getStatusBadge(mission.status)}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Module Validation */}
      {(user.role === 'super_admin' || user.role === 'patron' || user.role === 'chef_cuisine') && missionsAValider.length > 0 && (
        <div data-testid="missions-to-validate" style={{
          background: '#FFFFFF', borderRadius: '16px', padding: '16px',
          marginBottom: '12px', border: '1px solid #E5E5E0',
          borderLeft: '4px solid #D4AF37'
        }}>
          <div style={{
            fontFamily: 'Manrope, sans-serif', fontSize: '13px', fontWeight: '700',
            color: '#92400e', marginBottom: '12px', textTransform: 'uppercase',
            letterSpacing: '0.5px'
          }}>
            Missions a valider ({missionsAValider.length})
          </div>
          <div style={{display: 'grid', gap: '10px'}}>
            {missionsAValider.slice(0, 3).map(mission => (
              <div key={mission.id} style={{
                padding: '12px 14px', background: '#FAFAF8', borderRadius: '10px',
                border: '1px solid #E5E5E0', display: 'flex',
                justifyContent: 'space-between', alignItems: 'center', gap: '10px'
              }}>
                <div style={{flex: 1, minWidth: 0}}>
                  <div style={{fontFamily: 'Manrope, sans-serif', fontSize: '13px', fontWeight: '600', marginBottom: '3px', color: '#1C1C19'}}>
                    {mission.title}
                  </div>
                  <div style={{fontSize: '11px', color: '#D4AF37', fontWeight: '600', marginBottom: '2px'}}>
                    {mission.assigned_to_name}
                  </div>
                  <div style={{fontSize: '11px', color: '#8C8C88', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap'}}>
                    {mission.employee_notes || 'Pas de commentaire'}
                  </div>
                </div>
                <button
                  data-testid={`validate-mission-${mission.id}`}
                  onClick={() => validateMission(mission.id, 'Valide')}
                  style={{
                    fontSize: '12px', padding: '7px 14px', borderRadius: '20px',
                    background: '#2C4A3B', color: 'white', border: 'none',
                    cursor: 'pointer', fontWeight: '600', fontFamily: 'Manrope, sans-serif',
                    flexShrink: 0, transition: 'all 0.2s ease'
                  }}
                >
                  Valider
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Bouton Creer Mission + Listes */}
      {(user.role === 'super_admin' || user.role === 'patron' ||
        user.role === 'chef_cuisine' || user.role === 'caissier' ||
        user.role === 'barman' || user.role === 'employe_cuisine') && (
        <div data-testid="missions-section" style={{
          background: '#FFFFFF', borderRadius: '16px', padding: '16px',
          marginBottom: '12px', border: '1px solid #E5E5E0'
        }}>
          <button
            data-testid="create-mission-button"
            onClick={() => { if (onCreateMission) onCreateMission(); }}
            style={{
              width: '100%', padding: '14px 20px',
              background: '#2C4A3B', color: 'white', border: 'none',
              borderRadius: '12px', fontFamily: 'Manrope, sans-serif',
              fontSize: '14px', fontWeight: '700', cursor: 'pointer',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              gap: '8px', marginBottom: '16px', letterSpacing: '0.2px',
              transition: 'all 0.2s ease'
            }}
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
            Creer une Nouvelle Mission
          </button>

          {(() => {
            const filteredData = getFilteredMissions();
            return (
              <>
                <div style={{
                  fontFamily: 'Manrope, sans-serif', fontSize: '11px', fontWeight: '700',
                  color: '#8C8C88', textAlign: 'center', padding: '8px 12px',
                  background: '#F5F5F0', borderRadius: '8px', marginBottom: '14px',
                  textTransform: 'uppercase', letterSpacing: '0.8px'
                }}>
                  Missions - {filteredData.dateLabel}
                </div>

                {filteredData.createdToday.length > 0 && (
                  <div style={{marginBottom: '16px'}}>
                    <div style={{
                      fontFamily: 'Manrope, sans-serif', fontSize: '12px', fontWeight: '700',
                      color: '#5C5C58', marginBottom: '8px', textTransform: 'uppercase', letterSpacing: '0.5px'
                    }}>
                      Missions creees ({filteredData.createdToday.length})
                    </div>
                    <div style={{display: 'grid', gap: '6px'}}>
                      {filteredData.createdToday.map(mission => (
                        <div key={mission.id} style={{
                          padding: '10px 14px', background: '#FAFAF8', borderRadius: '10px',
                          border: '1px solid #E5E5E0', fontSize: '13px'
                        }}>
                          <div style={{fontFamily: 'Manrope, sans-serif', fontWeight: '600', marginBottom: '3px', color: '#1C1C19', fontSize: '13px'}}>
                            {mission.title}
                          </div>
                          <div style={{color: '#8C8C88', fontSize: '11px', display: 'flex', alignItems: 'center', gap: '6px', flexWrap: 'wrap'}}>
                            <span>{mission.assigned_to_name}</span>
                            <span style={{color: '#E5E5E0'}}>|</span>
                            {getStatusBadge(mission.status)}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {filteredData.toValidateToday.length > 0 && (
                  <div style={{marginBottom: '10px'}}>
                    <div style={{
                      fontFamily: 'Manrope, sans-serif', fontSize: '12px', fontWeight: '700',
                      color: '#5C5C58', marginBottom: '8px', textTransform: 'uppercase', letterSpacing: '0.5px'
                    }}>
                      A valider ({filteredData.toValidateToday.length})
                    </div>
                    <div style={{display: 'grid', gap: '6px'}}>
                      {filteredData.toValidateToday.map(mission => (
                        <div key={mission.id} style={{
                          padding: '12px 14px', background: '#FAFAF8', borderRadius: '10px',
                          border: '1px solid #E5E5E0', fontSize: '13px',
                          display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '8px'
                        }}>
                          <div style={{flex: 1, minWidth: 0}}>
                            <div style={{fontFamily: 'Manrope, sans-serif', fontWeight: '600', marginBottom: '2px', color: '#1C1C19', fontSize: '13px'}}>
                              {mission.title}
                            </div>
                            <div style={{color: '#D4AF37', fontSize: '11px', fontWeight: '600', marginBottom: '2px'}}>
                              {mission.assigned_to_name}
                            </div>
                            {mission.completed_by_employee_date && (
                              <div style={{color: '#8C8C88', fontSize: '10px'}}>
                                Termine le {new Date(mission.completed_by_employee_date).toLocaleDateString('fr-FR')} a {new Date(mission.completed_by_employee_date).toLocaleTimeString('fr-FR', {hour: '2-digit', minute: '2-digit'})}
                              </div>
                            )}
                            {mission.employee_notes && (
                              <div style={{color: '#8C8C88', fontSize: '10px', fontStyle: 'italic', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap'}}>
                                "{mission.employee_notes}"
                              </div>
                            )}
                          </div>
                          <button
                            onClick={() => validateMission(mission.id, `Valide par ${user.full_name?.split('(')[0].trim()}`)}
                            style={{
                              fontSize: '12px', padding: '7px 14px', borderRadius: '20px',
                              background: '#2C4A3B', color: 'white', border: 'none',
                              cursor: 'pointer', fontWeight: '600', fontFamily: 'Manrope, sans-serif',
                              flexShrink: 0
                            }}
                          >
                            Valider
                          </button>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {filteredData.createdToday.length === 0 && filteredData.toValidateToday.length === 0 && (
                  <div data-testid="no-missions-message" style={{
                    textAlign: 'center', padding: '24px', color: '#8C8C88',
                    background: '#F5F5F0', borderRadius: '12px'
                  }}>
                    <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#C8C8C4" strokeWidth="1.5" strokeLinecap="round" style={{margin: '0 auto 8px', display: 'block'}}>
                      <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/>
                    </svg>
                    <div style={{fontFamily: 'Manrope, sans-serif', fontSize: '13px', fontWeight: '600'}}>
                      Aucune mission pour {filteredData.dateLabel.toLowerCase()}
                    </div>
                  </div>
                )}
              </>
            );
          })()}
        </div>
      )}
    </div>
  );
};

export default RoleBasedDashboard;
