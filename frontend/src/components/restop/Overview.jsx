import React from 'react';
import { ArrowRight, Package, UploadSimple, ShoppingCart, CheckCircle } from '@phosphor-icons/react';

export const previewStocks = [
  { image: 'restop-tomatoes.webp', produit_id: 'tomate', produit_nom: 'Tomates fraîches', quantite_actuelle: 8, quantite_min: 20, unite: 'kg' },
  { image: 'restop-mozzarella.webp', produit_id: 'mozza', produit_nom: 'Mozzarella di bufala', quantite_actuelle: 1.5, quantite_min: 5, unite: 'kg' },
  { image: 'restop-basil.webp', produit_id: 'basilic', produit_nom: 'Basilic frais', quantite_actuelle: 200, quantite_min: 1000, unite: 'g' },
];

export default function Overview({ stocks = [], documents = [], user, onStocks, onStockAlerts, onImport, onPurchases, loading = false, error = '', onRetry, preview = false }) {
  const Heading = preview ? 'h2' : 'h1';
  const lowStocks = stocks.filter(s => Number(s.quantite_actuelle) <= Number(s.quantite_min));
  const pending = documents.filter(d => !['validated', 'valide', 'validé', 'traite', 'processed'].includes(d.statut || d.status));
  const firstName = (user?.full_name || 'à vous').split(' ')[0];
  return <section className="rt-overview" aria-labelledby={preview ? 'preview-title' : 'overview-title'}>
    <div className="rt-page-heading">
      <div><p className="rt-eyebrow">Votre restaurant, aujourd’hui</p><Heading id={preview ? 'preview-title' : 'overview-title'}>Bonjour {firstName},<br /><span>voici vos priorités du jour.</span></Heading></div>
      {onImport && <button className="rt-button rt-peach" onClick={onImport}><UploadSimple size={20} />Importer une facture</button>}
    </div>
    {error ? <div className="rt-feedback" role="alert">{error} <button className="rt-text-link" onClick={onRetry}>Réessayer</button></div> : loading ? <p role="status" className="rt-empty">Chargement de vos données…</p> : <>
      <div className="rt-summary">
        <button onClick={onPurchases} className="rt-summary-item"><span className="rt-icon-circle"><ShoppingCart size={25} /></span><span><span className="rt-summary-label">Documents à vérifier</span><strong>{preview ? 2 : pending.length}</strong><small>avant validation</small></span><ArrowRight size={18} /></button>
        <button onClick={onStockAlerts || onStocks} className="rt-summary-item"><span className="rt-icon-circle"><Package size={25} /></span><span><span className="rt-summary-label">Produits à surveiller</span><strong>{lowStocks.length}</strong><small>sous le seuil de stock</small></span><ArrowRight size={18} /></button>
      </div>
      <div className="rt-section-heading"><h2>Produits à surveiller</h2><button className="rt-text-link" onClick={onStocks}>Voir tous les stocks <ArrowRight size={18} /></button></div>
      {lowStocks.length ? <div className="rt-table-scroll"><table className="rt-stock-table"><thead><tr><th>Produit</th><th>Stock actuel</th><th>Seuil d’alerte</th><th>Statut</th></tr></thead><tbody>{lowStocks.slice(0, 6).map((s, i) => <tr key={s.produit_id || i}><td><span className="rt-product-cell">{preview && s.image ? <img src={`/images/${s.image}`} alt="" width="44" height="44" loading="lazy" /> : <Package size={21} weight="light" />}<span>{s.produit_nom || s.nom || 'Produit sans nom'}</span></span></td><td>{Number(s.quantite_actuelle || 0).toLocaleString('fr-FR')} {s.unite || ''}</td><td>{Number(s.quantite_min || 0).toLocaleString('fr-FR')} {s.unite || ''}</td><td><span className={`rt-status${Number(s.quantite_actuelle) <= 0 ? ' rt-status-danger' : ''}`}>{Number(s.quantite_actuelle) <= 0 ? 'Rupture' : 'Stock faible'}</span></td></tr>)}</tbody></table></div> : <div className="rt-empty"><CheckCircle size={28} /><h3>{stocks.length ? 'Vos stocks sont au-dessus des seuils.' : 'Votre suivi de stock commence ici.'}</h3><p>{stocks.length ? 'Retrouvez les quantités et les mouvements dans Stocks.' : 'Ajoutez vos produits pour retrouver ici ceux qui nécessitent votre attention.'}</p><button className="rt-text-link" onClick={onStocks}>Ouvrir les stocks <ArrowRight /></button></div>}
    </>}
  </section>;
}
