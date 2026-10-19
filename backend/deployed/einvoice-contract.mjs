// DIGIGROUPE E-Facture draft contract v1.
// IMPORTANT: this is an internal preflight, NOT a Factur-X file or legal transmission.
// Mirrored byte-for-byte in Restop until a versioned shared package is published.
export const CONTRACT_VERSION = 'digigroupe.einvoice.draft.v1';
const asObject = (v) => v !== null && typeof v === 'object' && !Array.isArray(v) ? v : {};
const trim = (v, max = 250) => typeof v === 'string' ? v.trim().slice(0, max) : '';
const validDate = (v) => {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(v)) return false;
  const dt = new Date(v + 'T00:00:00Z');
  return !Number.isNaN(dt.getTime()) && dt.toISOString().slice(0, 10) === v;
};
const cents = (value) => {
  const s = typeof value === 'number' && Number.isFinite(value) ? String(value) : value;
  if (typeof s !== 'string' || !/^(0|[1-9]\d{0,9})(\.\d{1,2})?$/.test(s)) return null;
  const [whole, fraction = ''] = s.split('.');
  const amount = Number(whole) * 100 + Number(fraction.padEnd(2, '0'));
  return Number.isSafeInteger(amount) ? amount : null;
};
const euro = (value) => Number((value / 100).toFixed(2));
function party(data, prefix, errors) {
  const p = asObject(data);
  const name = trim(p.name, 180);
  const siret = trim(p.siret, 14);
  if (!name) errors.push(prefix + '.name_required');
  if (!/^\d{14}$/.test(siret)) errors.push(prefix + '.siret_14_digits_required');
  return {name, siret};
}
export function providerCapabilities() {
  return {
    version: CONTRACT_VERSION,
    providerPreference: 'tiime',
    status: 'PREVIEW_ONLY',
    apiConnected: false,
    regulatoryDelivery: false,
    invoiceReception: false,
    autoSendEnabled: false,
    paidApiEnabled: false,
    formats: ['JSON_PREVIEW'],
    note: 'No Factur-X/UBL/CII generation or legally valid delivery is performed by this module.'
  };
}
export function validateDraft(value) {
  const input = asObject(value), errors = [];
  const documentType = trim(input.documentType, 20) || 'invoice';
  if (!['invoice', 'credit_note'].includes(documentType)) errors.push('documentType_invalid');
  const number = trim(input.number, 80);
  if (!number) errors.push('number_required');
  const issueDate = trim(input.issueDate, 10);
  if (!validDate(issueDate)) errors.push('issueDate_invalid');
  if (input.currency !== 'EUR') errors.push('currency_must_be_EUR');
  const seller = party(input.seller, 'seller', errors);
  const buyer = party(input.buyer, 'buyer', errors);
  const rawLines = Array.isArray(input.lines) ? input.lines : [];
  if (rawLines.length === 0 || rawLines.length > 100) errors.push('lines_count_invalid');
  let totalNet = 0, totalVat = 0;
  const lines = [];
  for (const [i, item] of rawLines.slice(0, 100).entries()) {
    const line = asObject(item), title = trim(line.description, 250);
    const quantity = Number(line.quantity);
    const price = cents(line.unitPriceExclTax);
    const vatRate = Number(line.vatRate);
    if (!title) errors.push('lines.' + i + '.description_required');
    if (typeof line.quantity !== 'number' || !Number.isFinite(quantity) || quantity <= 0 || quantity > 100000 || Math.round(quantity * 10000) !== quantity * 10000)
      errors.push('lines.' + i + '.quantity_invalid');
    if (price === null) errors.push('lines.' + i + '.unitPriceExclTax_invalid');
    if (typeof line.vatRate !== 'number' || !Number.isFinite(vatRate) || vatRate < 0 || vatRate > 100 || Math.round(vatRate * 100) !== vatRate * 100)
      errors.push('lines.' + i + '.vatRate_invalid');
    if (title && price !== null && Number.isFinite(quantity) && quantity > 0 && Number.isFinite(vatRate) && vatRate >= 0 && vatRate <= 100) {
      const net = Math.round(price * quantity);
      const tax = Math.round(net * vatRate / 100);
      totalNet += net; totalVat += tax;
      lines.push({description: title, quantity, unitPriceExclTax: euro(price), vatRate, net: euro(net), vat: euro(tax)});
    }
  }
  if (!Number.isSafeInteger(totalNet) || !Number.isSafeInteger(totalVat) || totalNet > 1e12) errors.push('totals_out_of_range');
  if (errors.length) return {ok: false, version: CONTRACT_VERSION, errors};
  return {
    ok: true, version: CONTRACT_VERSION, errors: [],
    preview: {
      documentType, number, issueDate, currency: 'EUR', seller, buyer, lines,
      totals: {net: euro(totalNet), vat: euro(totalVat), gross: euro(totalNet + totalVat)},
      regulatoryStatus: 'NOT_TRANSMITTED', provider: 'tiime', exportFormat: 'JSON_PREVIEW_ONLY'
    },
    notice: 'Internal preview. Does not produce a Factur-X, UBL, CII, e-reporting file or tax-compliant invoice.'
  };
}
