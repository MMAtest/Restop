export function csvCell(value) {
  const text = String(value ?? '');
  // Prevent spreadsheet formula execution when exporting user supplied names.
  return '"' + (/^[=+@\-]/.test(text) ? "'" + text : text).replace(/"/g,'""') + '"';
}
export function downloadCsv(filename, headers, rows) {
  const content = '\uFEFF' + [headers,...rows].map(row=>row.map(csvCell).join(';')).join('\r\n');
  const url = URL.createObjectURL(new Blob([content],{type:'text/csv;charset=utf-8'}));
  const anchor=document.createElement('a');anchor.href=url;anchor.download=filename;anchor.click();
  setTimeout(()=>URL.revokeObjectURL(url),1000);
}
