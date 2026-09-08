import React, { useState, useEffect } from 'react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

/**
 * Composant d'upload du fichier "sales-analysis" L'Addition
 * - Upload Excel
 * - Preview (auto-mappés / à mapper / ignorés)
 * - Mapping interactif des nouveaux items
 * - Application du décrément stock
 */
export default function SalesUploader({ onApplied }) {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [preview, setPreview] = useState(null);
  const [recettes, setRecettes] = useState([]);
  const [produits, setProduits] = useState([]);
  const [activeTab, setActiveTab] = useState('mapped');
  const [error, setError] = useState(null);

  useEffect(() => {
    // Charger recettes et produits pour les dropdowns
    Promise.all([
      axios.get(`${API}/recettes`),
      axios.get(`${API}/produits`),
    ]).then(([r, p]) => {
      setRecettes(r.data.filter(x => !x.archived));
      setProduits(p.data.filter(x => !x.archived));
    }).catch(() => {});
  }, []);

  const handleFileChange = (e) => {
    setFile(e.target.files?.[0] || null);
    setPreview(null);
    setError(null);
  };

  const handlePreview = async () => {
    if (!file) return;
    setLoading(true);
    setError(null);
    try {
      const fd = new FormData();
      fd.append('file', file);
      const r = await axios.post(`${API}/sales/preview`, fd, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      setPreview(r.data);
      setActiveTab(r.data.items_unmapped.length > 0 ? 'unmapped' : 'mapped');
    } catch (err) {
      setError(err.response?.data?.detail || err.message);
    } finally {
      setLoading(false);
    }
  };

  const updateUnmappedItem = (idx, updates) => {
    setPreview(prev => {
      const newUnmapped = [...prev.items_unmapped];
      newUnmapped[idx] = { ...newUnmapped[idx], ...updates };
      return { ...prev, items_unmapped: newUnmapped };
    });
  };

  // Sauvegarder un mapping pour réutilisation future
  const saveMapping = async (item) => {
    if (!item.mapping_type) return;
    try {
      await axios.post(`${API}/sales/mappings`, {
        caisse_nom: item.caisse_nom,
        type: item.mapping_type,
        cible_id: item.cible_id || null,
      });
      return true;
    } catch (err) {
      console.error('Save mapping failed:', err);
      return false;
    }
  };

  const handleApply = async () => {
    if (!preview) return;
    // Vérifier qu'aucun item unmapped n'est resté sans mapping_type
    const stillUnmapped = preview.items_unmapped.filter(i => !i.mapping_type);
    if (stillUnmapped.length > 0) {
      if (!window.confirm(
        `⚠️ ${stillUnmapped.length} produit(s) ne sont pas mappés et seront IGNORÉS pour le décrément stock.\n\n` +
        stillUnmapped.map(i => `  • ${i.caisse_nom} (${i.quantite}x)`).join('\n') +
        '\n\nContinuer quand même ?'
      )) return;
    }
    if (!window.confirm(
      `Appliquer le décrément stock pour ${preview.nb_lignes} produits vendus (${preview.total_ca}€) ?\n\n` +
      `Cette action est définitive (mais l'historique est gardé).`
    )) return;

    setLoading(true);
    try {
      // 1. Sauvegarder tous les nouveaux mappings (pour les prochaines fois)
      const newlyMapped = preview.items_unmapped.filter(i => i.mapping_type);
      await Promise.all(newlyMapped.map(saveMapping));

      // 2. Construire la liste finale d'items à appliquer
      const allItems = [
        ...preview.items_mapped,
        ...preview.items_unmapped.filter(i => i.mapping_type),
        ...preview.items_ignored,
      ];

      // 3. Appliquer
      const r = await axios.post(`${API}/sales/apply`, {
        date_vente: preview.date_vente,
        items: allItems,
      });

      const stats = r.data.stats;
      alert(
        `✅ Import appliqué !\n\n` +
        `CA total: ${r.data.ca_total}€\n` +
        `Quantité: ${r.data.qty_total}\n\n` +
        `Décrément stock :\n` +
        `  • Recettes traitées: ${stats.recettes_decrementees}\n` +
        `  • Produits directs : ${stats.produits_decrementes}\n` +
        `  • Items ignorés    : ${stats.items_ignored}\n` +
        (stats.warnings > 0 ? `  ⚠️ Warnings: ${stats.warnings}\n` : '') +
        `\nUn rapport Z a été créé.`
      );

      setPreview(null);
      setFile(null);
      if (onApplied) onApplied();
    } catch (err) {
      setError(err.response?.data?.detail || err.message);
    } finally {
      setLoading(false);
    }
  };

  // Rendu d'une ligne d'item dans le tableau
  const renderItem = (item, idx, mode = 'mapped') => {
    const isUnmapped = mode === 'unmapped';
    return (
      <tr key={`${mode}-${idx}-${item.caisse_nom}`} style={{ borderBottom: '1px solid var(--color-border)' }}>
        <td style={{ padding: '8px', fontWeight: '500' }}>
          {item.pattern_match && '🐟 '}
          {item.caisse_nom}
          {item.auto_converted && item.weight_grams && (
            <div style={{ fontSize: '11px', color: '#0891b2', marginTop: '2px', fontStyle: 'italic' }}>
              ⚖️ {item.weight_grams}g vendus → converti en {item.quantite} service(s)
            </div>
          )}
        </td>
        <td style={{ padding: '8px', textAlign: 'center', fontWeight: 'bold' }}>{item.quantite}</td>
        <td style={{ padding: '8px', textAlign: 'right' }}>{item.ca_ttc}€</td>
        {isUnmapped ? (
          <>
            <td style={{ padding: '8px' }}>
              <select
                value={item.mapping_type || ''}
                onChange={(e) => updateUnmappedItem(idx, { mapping_type: e.target.value || null, cible_id: null, cible_nom: null })}
                data-testid={`mapping-type-${idx}`}
                style={{ width: '100%', padding: '4px' }}
              >
                <option value="">— Choisir —</option>
                <option value="recette">🍽️ Recette</option>
                <option value="produit_direct">🍷 Produit (boisson)</option>
                <option value="ignore">🚫 Ignorer (pas de stock)</option>
              </select>
            </td>
            <td style={{ padding: '8px' }}>
              {item.mapping_type === 'recette' && (
                <select
                  value={item.cible_id || ''}
                  onChange={(e) => {
                    const r = recettes.find(x => x.id === e.target.value);
                    updateUnmappedItem(idx, { cible_id: e.target.value, cible_nom: r?.nom });
                  }}
                  data-testid={`mapping-target-${idx}`}
                  style={{ width: '100%', padding: '4px' }}
                >
                  <option value="">— Choisir une recette —</option>
                  {recettes.sort((a, b) => a.nom.localeCompare(b.nom)).map(r => (
                    <option key={r.id} value={r.id}>{r.nom}</option>
                  ))}
                </select>
              )}
              {item.mapping_type === 'produit_direct' && (
                <select
                  value={item.cible_id || ''}
                  onChange={(e) => {
                    const p = produits.find(x => x.id === e.target.value);
                    updateUnmappedItem(idx, { cible_id: e.target.value, cible_nom: p?.nom });
                  }}
                  data-testid={`mapping-target-${idx}`}
                  style={{ width: '100%', padding: '4px' }}
                >
                  <option value="">— Choisir un produit —</option>
                  {produits.sort((a, b) => a.nom.localeCompare(b.nom)).map(p => (
                    <option key={p.id} value={p.id}>{p.nom} {p.sous_categorie ? `(${p.sous_categorie})` : ''}</option>
                  ))}
                </select>
              )}
              {item.mapping_type === 'ignore' && (
                <span style={{ color: 'var(--color-text-muted)', fontStyle: 'italic' }}>Sera ignoré</span>
              )}
            </td>
          </>
        ) : (
          <td colSpan="2" style={{ padding: '8px', color: 'var(--color-text-secondary)' }}>
            {item.mapping_type === 'recette' && '🍽️ '}
            {item.mapping_type === 'produit_direct' && '🍷 '}
            {item.mapping_type === 'ignore' && '🚫 '}
            {item.cible_nom || (item.mapping_type === 'ignore' ? 'Pas de décrément' : '—')}
          </td>
        )}
      </tr>
    );
  };

  return (
    <div className="sales-uploader" style={{
      background: 'var(--color-background-card)',
      border: '1px solid var(--color-border)',
      borderRadius: '12px',
      padding: '20px',
      marginBottom: '20px'
    }}>
      <h3 style={{ marginTop: 0, color: 'var(--color-primary)' }}>
        📊 Import des ventes journalières (sales-analysis L'Addition)
      </h3>
      <p style={{ color: 'var(--color-text-secondary)', fontSize: '14px', marginBottom: '15px' }}>
        Uploadez le fichier Excel "sales-analysis" exporté depuis L'Addition pour décrémenter automatiquement le stock.
      </p>

      {!preview && (
        <div style={{ display: 'flex', gap: '10px', alignItems: 'center', flexWrap: 'wrap' }}>
          <input
            type="file"
            accept=".xlsx,.xls"
            onChange={handleFileChange}
            data-testid="sales-file-input"
            style={{ flex: 1, minWidth: '250px' }}
          />
          <button
            className="button"
            onClick={handlePreview}
            disabled={!file || loading}
            data-testid="sales-preview-btn"
            style={{ background: 'var(--color-primary)' }}
          >
            {loading ? '⏳ Analyse...' : '🔍 Prévisualiser'}
          </button>
        </div>
      )}

      {error && (
        <div style={{
          background: '#fee', border: '1px solid #f99',
          padding: '10px', borderRadius: '6px', marginTop: '10px', color: '#c00'
        }}>
          ❌ {error}
        </div>
      )}

      {preview && (
        <div style={{ marginTop: '15px' }}>
          {/* Résumé */}
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
            gap: '10px',
            marginBottom: '20px'
          }}>
            <div className="stat-card">
              <div style={{ fontSize: '12px', color: 'var(--color-text-secondary)' }}>Date</div>
              <div style={{ fontSize: '18px', fontWeight: 'bold' }}>{preview.date_vente}</div>
            </div>
            <div className="stat-card">
              <div style={{ fontSize: '12px', color: 'var(--color-text-secondary)' }}>CA total</div>
              <div style={{ fontSize: '18px', fontWeight: 'bold', color: 'var(--color-primary)' }}>
                {preview.total_ca}€
              </div>
            </div>
            <div className="stat-card">
              <div style={{ fontSize: '12px', color: 'var(--color-text-secondary)' }}>Quantités</div>
              <div style={{ fontSize: '18px', fontWeight: 'bold' }}>{preview.total_qty}</div>
            </div>
            <div className="stat-card">
              <div style={{ fontSize: '12px', color: 'var(--color-text-secondary)' }}>Lignes</div>
              <div style={{ fontSize: '18px', fontWeight: 'bold' }}>{preview.nb_lignes}</div>
            </div>
          </div>

          {/* Tabs */}
          <div style={{ display: 'flex', gap: '5px', marginBottom: '15px', flexWrap: 'wrap' }}>
            <button
              className="button small"
              onClick={() => setActiveTab('mapped')}
              data-testid="sales-tab-mapped"
              style={{
                background: activeTab === 'mapped' ? '#10b981' : 'var(--color-background-card-light)',
                color: activeTab === 'mapped' ? 'white' : 'var(--color-text-primary)'
              }}
            >
              ✅ Auto-mappés ({preview.items_mapped.length})
            </button>
            <button
              className="button small"
              onClick={() => setActiveTab('unmapped')}
              data-testid="sales-tab-unmapped"
              style={{
                background: activeTab === 'unmapped' ? '#f59e0b' : 'var(--color-background-card-light)',
                color: activeTab === 'unmapped' ? 'white' : 'var(--color-text-primary)'
              }}
            >
              🟡 À mapper ({preview.items_unmapped.length})
            </button>
            <button
              className="button small"
              onClick={() => setActiveTab('ignored')}
              data-testid="sales-tab-ignored"
              style={{
                background: activeTab === 'ignored' ? '#6b7280' : 'var(--color-background-card-light)',
                color: activeTab === 'ignored' ? 'white' : 'var(--color-text-primary)'
              }}
            >
              🚫 Ignorés ({preview.items_ignored.length})
            </button>
          </div>

          {/* Tableau */}
          <div style={{ maxHeight: '500px', overflowY: 'auto', border: '1px solid var(--color-border)', borderRadius: '8px' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '14px' }}>
              <thead style={{ position: 'sticky', top: 0, background: 'var(--color-background-card-light)', zIndex: 1 }}>
                <tr>
                  <th style={{ padding: '10px', textAlign: 'left' }}>Produit caisse</th>
                  <th style={{ padding: '10px', textAlign: 'center', width: '60px' }}>Qty</th>
                  <th style={{ padding: '10px', textAlign: 'right', width: '80px' }}>CA</th>
                  {activeTab === 'unmapped' ? (
                    <>
                      <th style={{ padding: '10px', textAlign: 'left', width: '160px' }}>Type</th>
                      <th style={{ padding: '10px', textAlign: 'left', width: '300px' }}>Cible</th>
                    </>
                  ) : (
                    <th style={{ padding: '10px', textAlign: 'left' }} colSpan="2">Mappé sur</th>
                  )}
                </tr>
              </thead>
              <tbody>
                {activeTab === 'mapped' && preview.items_mapped
                  .sort((a, b) => b.quantite - a.quantite)
                  .map((it, i) => renderItem(it, i, 'mapped'))}
                {activeTab === 'unmapped' && preview.items_unmapped
                  .sort((a, b) => b.quantite - a.quantite)
                  .map((it, i) => renderItem(it, i, 'unmapped'))}
                {activeTab === 'ignored' && preview.items_ignored
                  .sort((a, b) => b.quantite - a.quantite)
                  .map((it, i) => renderItem(it, i, 'ignored'))}
                {((activeTab === 'mapped' && preview.items_mapped.length === 0) ||
                  (activeTab === 'unmapped' && preview.items_unmapped.length === 0) ||
                  (activeTab === 'ignored' && preview.items_ignored.length === 0)) && (
                  <tr>
                    <td colSpan="5" style={{ padding: '30px', textAlign: 'center', color: 'var(--color-text-muted)' }}>
                      Aucun item dans cet onglet
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>

          {/* Boutons d'action */}
          <div style={{ display: 'flex', gap: '10px', marginTop: '20px', justifyContent: 'flex-end', flexWrap: 'wrap' }}>
            <button
              className="button secondary"
              onClick={() => { setPreview(null); setFile(null); }}
              data-testid="sales-cancel-btn"
            >
              ❌ Annuler
            </button>
            <button
              className="button"
              onClick={handleApply}
              disabled={loading}
              data-testid="sales-apply-btn"
              style={{ background: '#10b981', color: 'white', fontWeight: 'bold' }}
            >
              {loading ? '⏳ Application...' : '✅ Appliquer le décrément stock'}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
