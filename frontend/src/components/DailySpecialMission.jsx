import React, { useState, useEffect } from 'react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

/**
 * Mission Chef : Définir le Plat du Jour + Menu Enfant pour la journée.
 * S'affiche en haut du dashboard chef/patron tant que la mission n'est pas complétée.
 *
 * Permet de :
 *   - Sélectionner une recette existante
 *   - OU créer une nouvelle recette à la volée (qui sera persistée + définie comme spécial du jour)
 */
export default function DailySpecialMission({ currentUser, onCompleted }) {
  const [status, setStatus] = useState(null);
  const [todayConfig, setTodayConfig] = useState(null);
  const [recettes, setRecettes] = useState([]);
  const [showModal, setShowModal] = useState(false);
  const [loading, setLoading] = useState(false);

  const [platSelected, setPlatSelected] = useState('');
  const [menuSelected, setMenuSelected] = useState('');
  const [createMode, setCreateMode] = useState({ plat: false, menu: false });
  const [newRecipe, setNewRecipe] = useState({
    plat: { nom: '', categorie: 'Plat', prix_vente: '' },
    menu: { nom: '', categorie: 'Plat', prix_vente: '' },
  });

  const fetchStatus = async () => {
    try {
      const [s, t] = await Promise.all([
        axios.get(`${API}/daily-specials/mission-status/today`),
        axios.get(`${API}/daily-specials/today`),
      ]);
      setStatus(s.data);
      setTodayConfig(t.data);
      setPlatSelected(t.data.plat_du_jour?.recette_id || '');
      setMenuSelected(t.data.menu_enfant?.recette_id || '');
    } catch (err) {
      console.error('Status fetch failed:', err);
    }
  };

  const fetchRecettes = async () => {
    try {
      const r = await axios.get(`${API}/recettes`);
      setRecettes(r.data.filter(x => !x.archived));
    } catch (err) {
      console.error('Recettes fetch failed:', err);
    }
  };

  useEffect(() => {
    fetchStatus();
    fetchRecettes();
  }, []);

  const handleOpen = () => {
    setShowModal(true);
  };

  const createRecipe = async (target) => {
    const data = newRecipe[target];
    if (!data.nom.trim()) {
      alert('Le nom de la recette est requis');
      return null;
    }
    try {
      const r = await axios.post(`${API}/recettes`, {
        nom: data.nom.trim(),
        categorie: data.categorie,
        portions: 1,
        prix_vente: parseFloat(data.prix_vente) || 0,
        ingredients: [],
        description: target === 'plat' ? 'Plat du jour créé via mission chef' : 'Menu enfant créé via mission chef',
      });
      await fetchRecettes();
      return r.data;
    } catch (err) {
      alert(`Erreur création recette : ${err.response?.data?.detail || err.message}`);
      return null;
    }
  };

  const handleSubmit = async () => {
    setLoading(true);
    try {
      let platRef = null;
      let menuRef = null;

      // Plat du jour
      if (createMode.plat) {
        const created = await createRecipe('plat');
        if (!created) { setLoading(false); return; }
        platRef = { recette_id: created.id, recette_nom: created.nom };
      } else if (platSelected) {
        const r = recettes.find(x => x.id === platSelected);
        platRef = { recette_id: platSelected, recette_nom: r?.nom };
      }

      // Menu enfant
      if (createMode.menu) {
        const created = await createRecipe('menu');
        if (!created) { setLoading(false); return; }
        menuRef = { recette_id: created.id, recette_nom: created.nom };
      } else if (menuSelected) {
        const r = recettes.find(x => x.id === menuSelected);
        menuRef = { recette_id: menuSelected, recette_nom: r?.nom };
      }

      if (!platRef && !menuRef) {
        alert('Veuillez définir au moins le plat du jour ou le menu enfant');
        setLoading(false);
        return;
      }

      await axios.post(`${API}/daily-specials/today`, {
        plat_du_jour: platRef,
        menu_enfant: menuRef,
        set_by_user_id: currentUser?.id,
        set_by_user_nom: currentUser?.username || currentUser?.nom,
      });

      await fetchStatus();
      setShowModal(false);
      setCreateMode({ plat: false, menu: false });
      if (onCompleted) onCompleted();
    } catch (err) {
      alert(`Erreur : ${err.response?.data?.detail || err.message}`);
    } finally {
      setLoading(false);
    }
  };

  if (!status) return null;

  const isComplete = status.is_complete;
  const nbMissing = status.missing_fields?.length || 0;

  return (
    <>
      {/* Bandeau toujours visible (en haut du dashboard) */}
      <div
        className="daily-special-mission"
        data-testid="daily-special-mission-banner"
        style={{
          background: isComplete
            ? 'linear-gradient(135deg, #10b981, #059669)'
            : 'linear-gradient(135deg, #f59e0b, #d97706)',
          color: 'white',
          padding: '16px 20px',
          borderRadius: '12px',
          marginBottom: '20px',
          display: 'flex',
          flexWrap: 'wrap',
          justifyContent: 'space-between',
          alignItems: 'center',
          gap: '12px',
          boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
        }}
      >
        <div style={{ flex: 1, minWidth: '250px' }}>
          {isComplete ? (
            <>
              <div style={{ fontSize: '15px', fontWeight: 'bold', marginBottom: '4px' }}>
                ✅ Mission du jour complétée
              </div>
              <div style={{ fontSize: '13px', opacity: 0.95 }}>
                🍽️ Plat du jour : <strong>{todayConfig?.plat_du_jour?.recette_nom || 'Non défini'}</strong>
                {' • '}
                👶 Menu enfant : <strong>{todayConfig?.menu_enfant?.recette_nom || 'Non défini'}</strong>
              </div>
            </>
          ) : (
            <>
              <div style={{ fontSize: '15px', fontWeight: 'bold', marginBottom: '4px' }}>
                ⚠️ Mission obligatoire — {nbMissing === 2 ? 'Plat du jour & Menu enfant' : status.missing_fields[0] === 'plat_du_jour' ? 'Plat du jour' : 'Menu enfant'} à définir
              </div>
              <div style={{ fontSize: '13px', opacity: 0.95 }}>
                Sans cette config, le décrément stock sera incomplet pour le service du jour.
              </div>
            </>
          )}
        </div>
        <button
          onClick={handleOpen}
          data-testid="daily-special-open-btn"
          style={{
            background: 'rgba(255,255,255,0.95)',
            color: isComplete ? '#059669' : '#d97706',
            border: 'none',
            padding: '10px 20px',
            borderRadius: '8px',
            fontWeight: 'bold',
            cursor: 'pointer',
            fontSize: '14px',
          }}
        >
          {isComplete ? '✏️ Modifier' : '⚡ Définir maintenant'}
        </button>
      </div>

      {/* Modal */}
      {showModal && (
        <div
          style={{
            position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.6)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            zIndex: 9999, padding: '20px',
          }}
          onClick={(e) => { if (e.target === e.currentTarget) setShowModal(false); }}
        >
          <div
            style={{
              background: 'white', borderRadius: '16px', padding: '24px',
              maxWidth: '600px', width: '100%', maxHeight: '90vh', overflowY: 'auto',
            }}
          >
            <h2 style={{ marginTop: 0, color: '#2C4A3B' }}>
              📋 Mission du jour — Plat du jour & Menu enfant
            </h2>
            <p style={{ color: '#6b7280', fontSize: '14px', marginBottom: '20px' }}>
              Définissez ce que sera servi aujourd'hui. Vous pouvez sélectionner une recette existante ou en créer une nouvelle.
            </p>

            {/* PLAT DU JOUR */}
            <div style={{ marginBottom: '24px', padding: '16px', background: '#f9fafb', borderRadius: '10px' }}>
              <h3 style={{ margin: '0 0 12px 0', color: '#2C4A3B' }}>🍽️ Plat du jour</h3>
              {!createMode.plat ? (
                <>
                  <select
                    value={platSelected}
                    onChange={(e) => setPlatSelected(e.target.value)}
                    data-testid="daily-plat-select"
                    style={{ width: '100%', padding: '8px', borderRadius: '6px', border: '1px solid #d1d5db' }}
                  >
                    <option value="">— Sélectionner une recette —</option>
                    {recettes
                      .sort((a, b) => a.nom.localeCompare(b.nom))
                      .map(r => (
                        <option key={r.id} value={r.id}>
                          {r.nom} {r.prix_vente ? `(${r.prix_vente}€)` : ''}
                        </option>
                      ))}
                  </select>
                  <button
                    onClick={() => setCreateMode({ ...createMode, plat: true })}
                    data-testid="daily-plat-create-toggle"
                    style={{ marginTop: '8px', background: 'transparent', border: '1px dashed #9ca3af',
                      padding: '6px 12px', borderRadius: '6px', cursor: 'pointer', fontSize: '13px' }}
                  >
                    ➕ ou créer une nouvelle recette
                  </button>
                </>
              ) : (
                <div style={{ display: 'grid', gap: '8px' }}>
                  <input
                    placeholder="Nom du plat (ex: Filet de loup à la sauce vierge)"
                    value={newRecipe.plat.nom}
                    onChange={(e) => setNewRecipe({ ...newRecipe, plat: { ...newRecipe.plat, nom: e.target.value } })}
                    data-testid="daily-plat-new-nom"
                    style={{ padding: '8px', borderRadius: '6px', border: '1px solid #d1d5db' }}
                  />
                  <div style={{ display: 'flex', gap: '8px' }}>
                    <select
                      value={newRecipe.plat.categorie}
                      onChange={(e) => setNewRecipe({ ...newRecipe, plat: { ...newRecipe.plat, categorie: e.target.value } })}
                      style={{ flex: 1, padding: '8px', borderRadius: '6px', border: '1px solid #d1d5db' }}
                    >
                      <option value="Plat">Plat</option>
                      <option value="Entrée">Entrée</option>
                      <option value="Dessert">Dessert</option>
                      <option value="Autres">Autres</option>
                    </select>
                    <input
                      type="number" step="0.5" placeholder="Prix vente (€)"
                      value={newRecipe.plat.prix_vente}
                      onChange={(e) => setNewRecipe({ ...newRecipe, plat: { ...newRecipe.plat, prix_vente: e.target.value } })}
                      data-testid="daily-plat-new-prix"
                      style={{ flex: 1, padding: '8px', borderRadius: '6px', border: '1px solid #d1d5db' }}
                    />
                  </div>
                  <button
                    onClick={() => setCreateMode({ ...createMode, plat: false })}
                    style={{ background: 'transparent', border: 'none', padding: '4px', cursor: 'pointer',
                      color: '#6b7280', fontSize: '13px', textAlign: 'left' }}
                  >
                    ← Choisir une existante à la place
                  </button>
                </div>
              )}
            </div>

            {/* MENU ENFANT */}
            <div style={{ marginBottom: '24px', padding: '16px', background: '#f9fafb', borderRadius: '10px' }}>
              <h3 style={{ margin: '0 0 12px 0', color: '#2C4A3B' }}>👶 Menu enfant</h3>
              {!createMode.menu ? (
                <>
                  <select
                    value={menuSelected}
                    onChange={(e) => setMenuSelected(e.target.value)}
                    data-testid="daily-menu-select"
                    style={{ width: '100%', padding: '8px', borderRadius: '6px', border: '1px solid #d1d5db' }}
                  >
                    <option value="">— Sélectionner une recette —</option>
                    {recettes
                      .sort((a, b) => a.nom.localeCompare(b.nom))
                      .map(r => (
                        <option key={r.id} value={r.id}>
                          {r.nom} {r.prix_vente ? `(${r.prix_vente}€)` : ''}
                        </option>
                      ))}
                  </select>
                  <button
                    onClick={() => setCreateMode({ ...createMode, menu: true })}
                    data-testid="daily-menu-create-toggle"
                    style={{ marginTop: '8px', background: 'transparent', border: '1px dashed #9ca3af',
                      padding: '6px 12px', borderRadius: '6px', cursor: 'pointer', fontSize: '13px' }}
                  >
                    ➕ ou créer une nouvelle recette
                  </button>
                </>
              ) : (
                <div style={{ display: 'grid', gap: '8px' }}>
                  <input
                    placeholder="Nom du menu (ex: Steak haché frites)"
                    value={newRecipe.menu.nom}
                    onChange={(e) => setNewRecipe({ ...newRecipe, menu: { ...newRecipe.menu, nom: e.target.value } })}
                    data-testid="daily-menu-new-nom"
                    style={{ padding: '8px', borderRadius: '6px', border: '1px solid #d1d5db' }}
                  />
                  <input
                    type="number" step="0.5" placeholder="Prix vente (€)"
                    value={newRecipe.menu.prix_vente}
                    onChange={(e) => setNewRecipe({ ...newRecipe, menu: { ...newRecipe.menu, prix_vente: e.target.value } })}
                    data-testid="daily-menu-new-prix"
                    style={{ padding: '8px', borderRadius: '6px', border: '1px solid #d1d5db' }}
                  />
                  <button
                    onClick={() => setCreateMode({ ...createMode, menu: false })}
                    style={{ background: 'transparent', border: 'none', padding: '4px', cursor: 'pointer',
                      color: '#6b7280', fontSize: '13px', textAlign: 'left' }}
                  >
                    ← Choisir une existante à la place
                  </button>
                </div>
              )}
            </div>

            {/* Boutons */}
            <div style={{ display: 'flex', gap: '8px', justifyContent: 'flex-end' }}>
              <button
                onClick={() => setShowModal(false)}
                style={{ background: '#e5e7eb', border: 'none', padding: '10px 20px',
                  borderRadius: '8px', cursor: 'pointer', fontWeight: '500' }}
              >
                Annuler
              </button>
              <button
                onClick={handleSubmit}
                disabled={loading}
                data-testid="daily-special-submit-btn"
                style={{ background: '#10b981', color: 'white', border: 'none',
                  padding: '10px 20px', borderRadius: '8px', cursor: 'pointer', fontWeight: 'bold' }}
              >
                {loading ? '⏳ Sauvegarde...' : '✅ Valider la mission'}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
