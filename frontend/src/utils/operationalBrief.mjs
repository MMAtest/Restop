/** Deterministic operational priorities from persisted restaurant data.
 * No estimated savings are presented as achieved financial results.
 */
const number = value => Number.isFinite(Number(value)) ? Number(value) : 0;
const eur = value => number(value).toLocaleString('fr-FR', { style: 'currency', currency: 'EUR', maximumFractionDigits: 2 });

export function pendingSupplierInvoices(documents = []) {
  return (Array.isArray(documents) ? documents : []).filter(document =>
    document.type_document === 'facture_fournisseur' &&
    !['integre', 'validé', 'valide', 'validated', 'rejected', 'rejete', 'annule'].includes(
      String(document.statut || document.status || '').toLowerCase()
    )
  );
}

export function buildOperationalBrief(alerts = {}, documents = [], today = new Date()) {
  const actions = [];
  const list = key => Array.isArray(alerts?.[key]) ? alerts[key] : [];
  const add = (kind, priority, title, detail, action, label, key) => actions.push({
    id: `${kind}-${key}`, kind, priority, title, detail, action, label,
  });

  list('expiring_products').forEach((entry, index) => {
    const days = Number(entry.days_to_expiry);
    if (!Number.isFinite(days)) return;
    const when = days < 0 ? 'DLC dépassée' : days === 0 ? 'DLC aujourd’hui' : days === 1 ? 'DLC demain' : `DLC dans ${Math.floor(days)} jours`;
    add('dlc', days <= 2 ? 0 : 3, entry.product_name || 'Produit à contrôler',
      `${when} · ${number(entry.quantity).toLocaleString('fr-FR')} unités déclarées · Vérifier le lot et la traçabilité`,
      'stocks', 'Consulter les stocks', entry.batch_id || index);
  });

  list('low_stock_items').forEach((entry, index) => {
    const current = number(entry.current_quantity);
    const shortage = Math.max(0, number(entry.minimum_quantity) - current);
    add('stock', current <= 0 ? 1 : 4, entry.product_name || 'Stock à réapprovisionner',
      `${current.toLocaleString('fr-FR')} en stock · ${shortage.toLocaleString('fr-FR')} manquant(s) jusqu’au seuil minimum`,
      'stocks', 'Vérifier le stock', index);
  });

  list('price_anomalies').forEach((entry, index) => {
    const actual = number(entry.actual_price);
    const reference = number(entry.reference_price);
    if (reference <= 0 || actual <= reference) return;
    const delta = actual - reference;
    const pct = (delta / reference) * 100;
    add('price', 2, entry.product_name || 'Prix fournisseur à vérifier',
      `Hausse de ${pct.toLocaleString('fr-FR', {maximumFractionDigits: 1})} % (${eur(delta)} par unité de prix) · ${entry.supplier_name || 'Fournisseur non renseigné'}`,
      'factures', 'Contrôler la facture', index);
  });

  const pending = pendingSupplierInvoices(documents);
  if (pending.length) {
    add('invoice', 3, `${pending.length} facture${pending.length > 1 ? 's' : ''} à valider`,
      'Vérifiez les lignes OCR et leur correspondance avant l’entrée en stock.',
      'factures', 'Examiner les factures', 'pending');
  }

  list('unused_stock').forEach((entry, index) => {
    const qty = number(entry.quantity);
    if (qty <= 0) return;
    add('unused', 5, entry.product_name || 'Produit immobilisé',
      `${qty.toLocaleString('fr-FR')} en stock · aucun mouvement enregistré depuis ${Math.max(0, number(entry.days_unused))} jours`,
      'stocks', 'Examiner le stock', index);
  });

  actions.sort((a, b) => a.priority - b.priority || a.title.localeCompare(b.title, 'fr'));
  return {
    actions,
    urgentCount: actions.filter(a => a.priority <= 2).length,
    pendingInvoiceCount: pending.length,
    date: today.toLocaleDateString('fr-FR', {day:'numeric',month:'long',year:'numeric'}),
  };
}
