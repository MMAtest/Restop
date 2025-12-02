import React, { useState, useEffect } from 'react';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const InvoiceValidationModal = ({ documentId, onClose, onSuccess, produitsList }) => {
  const [loading, setLoading] = useState(true);
  const [analysis, setAnalysis] = useState(null);
  const [error, setError] = useState(null);
  const [items, setItems] = useState([]);
  
  // Charger l'analyse au montage
  useEffect(() => {
    const fetchAnalysis = async () => {
      try {
        const response = await axios.post(`${API}/ocr/analyze-facture/${documentId}`);
        setAnalysis(response.data);
        
        // Initialiser les items avec des valeurs par défaut pour l'édition
        const initializedItems = response.data.items.map(item => ({
          ...item,
          // Si déjà matché, on garde l'ID, sinon vide (pour sélecteur)
          selected_product_id: item.status === 'matched' ? item.product_id : '', 
          final_name: item.product_name || item.ocr_name,
          final_qty: item.ocr_qty,
          final_unit: item.ocr_unit,
          batch_number: '',
          dlc: ''
        }));
        setItems(initializedItems);
        setLoading(false);
      } catch (err) {
        console.error("Erreur analyse:", err);
        setError("Impossible d'analyser la facture. Vérifiez que c'est bien une facture fournisseur.");
        setLoading(false);
      }
    };
    
    if (documentId) {
      fetchAnalysis();
    }
  }, [documentId]);

  const handleItemChange = (index, field, value) => {
    const newItems = [...items];
    newItems[index] = { ...newItems[index], [field]: value };
    
    // Si on change le produit sélectionné, on met à jour le nom final pour affichage
    if (field === 'selected_product_id') {
        const prod = produitsList.find(p => p.id === value);
        if (prod) {
            newItems[index].final_name = prod.nom;
            newItems[index].final_unit = prod.unite;
        } else if (value === "") {
            // Si on désélectionne (création), on remet le nom OCR
            newItems[index].final_name = newItems[index].ocr_name;
        }
    }
    
    setItems(newItems);
  };

  const handleValidate = async () => {
    if (!window.confirm("Confirmez-vous l'import de ces produits en stock ?")) return;
    
    setLoading(true);
    try {
      const payload = {
        document_id: documentId,
        supplier_id: analysis.supplier_id,
        supplier_name: analysis.supplier_name,
        create_supplier: analysis.is_new_supplier,
        items: items.map(item => ({
            ...item,
            // S'assurer que les champs vides sont null
            dlc: item.dlc || null,
            batch_number: item.batch_number || null
        }))
      };
      
      const response = await axios.post(`${API}/ocr/confirm-import`, payload);
      alert(`✅ Import réussi !\n${response.data.stats.stock_entries} entrées de stock créées.\n${response.data.stats.batches_created} lots créés.`);
      onSuccess();
      onClose();
    } catch (err) {
      console.error("Erreur validation:", err);
      alert("Erreur lors de la validation: " + (err.response?.data?.detail || err.message));
      setLoading(false);
    }
  };

  if (loading) return (
    <div className="modal-overlay">
      <div className="modal-content">
        <div style={{textAlign: 'center', padding: '40px'}}>
          <div style={{fontSize: '40px', marginBottom: '20px'}}>🤖</div>
          <h3>Analyse intelligente en cours...</h3>
          <p>Je lis la facture et cherche les correspondances...</p>
        </div>
      </div>
    </div>
  );

  if (error) return (
    <div className="modal-overlay">
      <div className="modal-content">
        <div style={{textAlign: 'center', padding: '20px'}}>
          <div style={{color: 'red', fontSize: '40px', marginBottom: '10px'}}>⚠️</div>
          <h3>Erreur</h3>
          <p>{error}</p>
          <button className="button secondary" onClick={onClose} style={{marginTop: '20px'}}>Fermer</button>
        </div>
      </div>
    </div>
  );

  return (
    <div className="modal-overlay">
      <div className="modal-content large" style={{maxWidth: '900px', width: '95%'}}>
        <div className="modal-header" style={{borderBottom: '1px solid #eee', paddingBottom: '15px', marginBottom: '15px'}}>
          <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
            <h3>📝 Validation Facture - {analysis.supplier_name}</h3>
            <button className="modal-close" onClick={onClose} style={{background: 'none', border: 'none', fontSize: '24px', cursor: 'pointer'}}>×</button>
          </div>
          <div style={{fontSize: '14px', color: '#666', marginTop: '5px'}}>
            Date: {analysis.facture_date} • N°: {analysis.numero_facture}
            {analysis.is_new_supplier && <span style={{marginLeft: '10px', color: '#f59e0b', fontWeight: 'bold'}}>⚠️ Nouveau fournisseur détecté</span>}
          </div>
        </div>

        <div className="modal-body" style={{maxHeight: '60vh', overflowY: 'auto'}}>
          <table style={{width: '100%', borderCollapse: 'collapse', fontSize: '13px'}}>
            <thead style={{background: '#f8f9fa', position: 'sticky', top: 0, zIndex: 1}}>
              <tr>
                <th style={{padding: '10px', textAlign: 'left'}}>Produit Lu (OCR)</th>
                <th style={{padding: '10px', textAlign: 'left'}}>Correspondance Stock</th>
                <th style={{padding: '10px', textAlign: 'center', width: '80px'}}>Qté</th>
                <th style={{padding: '10px', textAlign: 'left', width: '130px'}}>DLC 📅</th>
                <th style={{padding: '10px', textAlign: 'left', width: '120px'}}>Lot 📦</th>
                <th style={{padding: '10px', textAlign: 'right'}}>Prix</th>
              </tr>
            </thead>
            <tbody>
              {items.map((item, index) => (
                <tr key={index} style={{borderBottom: '1px solid #eee', background: item.selected_product_id ? 'white' : '#fff7ed'}}>
                  <td style={{padding: '10px'}}>
                    <div style={{fontWeight: 'bold'}}>{item.ocr_name}</div>
                    <div style={{fontSize: '11px', color: '#666'}}>{item.ocr_unit}</div>
                  </td>
                  <td style={{padding: '10px'}}>
                    <select 
                      style={{
                        width: '100%', 
                        padding: '6px', 
                        borderRadius: '4px',
                        border: item.selected_product_id ? '1px solid #ddd' : '2px solid #f59e0b',
                        backgroundColor: item.selected_product_id ? 'white' : '#fff7ed'
                      }}
                      value={item.selected_product_id}
                      onChange={(e) => handleItemChange(index, 'selected_product_id', e.target.value)}
                    >
                      <option value="">➕ Créer nouveau produit</option>
                      {produitsList.map(p => (
                        <option key={p.id} value={p.id}>
                          {p.nom} ({p.unite})
                        </option>
                      ))}
                    </select>
                    {!item.selected_product_id && (
                        <input 
                            type="text"
                            value={item.final_name}
                            onChange={(e) => handleItemChange(index, 'final_name', e.target.value)}
                            placeholder="Nom du nouveau produit"
                            style={{width: '100%', marginTop: '5px', padding: '4px', fontSize: '12px', border: '1px solid #f59e0b'}}
                        />
                    )}
                  </td>
                  <td style={{padding: '10px'}}>
                    <input 
                      type="number" 
                      style={{width: '60px', padding: '4px', textAlign: 'center'}}
                      value={item.final_qty}
                      onChange={(e) => handleItemChange(index, 'final_qty', parseFloat(e.target.value))}
                    />
                  </td>
                  <td style={{padding: '10px'}}>
                    <input 
                      type="date" 
                      style={{width: '100%', padding: '4px', border: '1px solid #3b82f6', borderRadius: '4px'}}
                      value={item.dlc}
                      onChange={(e) => handleItemChange(index, 'dlc', e.target.value)}
                    />
                  </td>
                  <td style={{padding: '10px'}}>
                    <input 
                      type="text" 
                      placeholder="Auto"
                      style={{width: '100%', padding: '4px'}}
                      value={item.batch_number}
                      onChange={(e) => handleItemChange(index, 'batch_number', e.target.value)}
                    />
                  </td>
                  <td style={{padding: '10px', textAlign: 'right'}}>
                    {item.ocr_price}€
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="modal-footer" style={{borderTop: '1px solid #eee', paddingTop: '15px', marginTop: '15px', display: 'flex', justifyContent: 'flex-end', gap: '10px'}}>
          <button className="button secondary" onClick={onClose}>Annuler</button>
          <button className="button success" onClick={handleValidate}>✅ Valider et Intégrer au Stock</button>
        </div>
      </div>
    </div>
  );
};

export default InvoiceValidationModal;
