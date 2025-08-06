import React, { useState, useEffect } from "react";
import "./App.css";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function App() {
  const [activeTab, setActiveTab] = useState("dashboard");
  const [activeProductionTab, setActiveProductionTab] = useState("produits");
  const [activeHistoriqueTab, setActiveHistoriqueTab] = useState("ventes");
  const [dashboardStats, setDashboardStats] = useState({});
  const [produits, setProduits] = useState([]);
  const [fournisseurs, setFournisseurs] = useState([]);
  const [stocks, setStocks] = useState([]);
  const [mouvements, setMouvements] = useState([]);
  const [recettes, setRecettes] = useState([]);
  const [documentsOcr, setDocumentsOcr] = useState([]);
  const [loading, setLoading] = useState(false);

  // États pour les modals
  const [showProduitModal, setShowProduitModal] = useState(false);
  const [showFournisseurModal, setShowFournisseurModal] = useState(false);
  const [showMouvementModal, setShowMouvementModal] = useState(false);
  const [showRecetteModal, setShowRecetteModal] = useState(false);
  const [showOcrModal, setShowOcrModal] = useState(false);
  const [editingItem, setEditingItem] = useState(null);
  const [selectedRecette, setSelectedRecette] = useState(null);
  const [productionCapacity, setProductionCapacity] = useState(null);

  // États OCR
  const [ocrFile, setOcrFile] = useState(null);
  const [ocrPreview, setOcrPreview] = useState(null);
  const [ocrType, setOcrType] = useState("z_report");
  const [ocrResult, setOcrResult] = useState(null);
  const [processingOcr, setProcessingOcr] = useState(false);

  // Formulaires
  const [produitForm, setProduitForm] = useState({
    nom: "", description: "", categorie: "", unite: "", prix_achat: "", fournisseur_id: ""
  });
  const [fournisseurForm, setFournisseurForm] = useState({
    nom: "", contact: "", email: "", telephone: "", adresse: ""
  });
  const [mouvementForm, setMouvementForm] = useState({
    produit_id: "", type: "entree", quantite: "", reference: "", commentaire: ""
  });
  const [recetteForm, setRecetteForm] = useState({
    nom: "", description: "", categorie: "", portions: "", temps_preparation: "", 
    prix_vente: "", instructions: "", ingredients: []
  });
  const [ingredientForm, setIngredientForm] = useState({
    produit_id: "", quantite: "", unite: ""
  });

  // Charger les données initiales
  useEffect(() => {
    fetchDashboardStats();
    fetchProduits();
    fetchFournisseurs();
    fetchStocks();
    fetchMouvements();
    fetchRecettes();
    fetchDocumentsOcr();
  }, []);

  const fetchDashboardStats = async () => {
    try {
      const response = await axios.get(`${API}/dashboard/stats`);
      setDashboardStats(response.data);
    } catch (error) {
      console.error("Erreur lors du chargement des statistiques:", error);
    }
  };

  const fetchProduits = async () => {
    try {
      const response = await axios.get(`${API}/produits`);
      setProduits(response.data);
    } catch (error) {
      console.error("Erreur lors du chargement des produits:", error);
    }
  };

  const fetchFournisseurs = async () => {
    try {
      const response = await axios.get(`${API}/fournisseurs`);
      setFournisseurs(response.data);
    } catch (error) {
      console.error("Erreur lors du chargement des fournisseurs:", error);
    }
  };

  const fetchStocks = async () => {
    try {
      const response = await axios.get(`${API}/stocks`);
      setStocks(response.data);
    } catch (error) {
      console.error("Erreur lors du chargement des stocks:", error);
    }
  };

  const fetchMouvements = async () => {
    try {
      const response = await axios.get(`${API}/mouvements`);
      setMouvements(response.data.slice(0, 10)); // Derniers 10 mouvements
    } catch (error) {
      console.error("Erreur lors du chargement des mouvements:", error);
    }
  };

  const fetchRecettes = async () => {
    try {
      const response = await axios.get(`${API}/recettes`);
      setRecettes(response.data);
    } catch (error) {
      console.error("Erreur lors du chargement des recettes:", error);
    }
  };

  const fetchDocumentsOcr = async () => {
    try {
      const response = await axios.get(`${API}/ocr/documents`);
      setDocumentsOcr(response.data);
    } catch (error) {
      console.error("Erreur lors du chargement des documents OCR:", error);
    }
  };

  // Gestion des produits
  const handleProduitSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const formData = {
        ...produitForm,
        prix_achat: produitForm.prix_achat ? parseFloat(produitForm.prix_achat) : null
      };

      if (editingItem) {
        await axios.put(`${API}/produits/${editingItem.id}`, formData);
      } else {
        await axios.post(`${API}/produits`, formData);
      }

      setShowProduitModal(false);
      setProduitForm({ nom: "", description: "", categorie: "", unite: "", prix_achat: "", fournisseur_id: "" });
      setEditingItem(null);
      fetchProduits();
      fetchStocks();
      fetchDashboardStats();
    } catch (error) {
      console.error("Erreur lors de la sauvegarde du produit:", error);
      alert("Erreur lors de la sauvegarde");
    }
    setLoading(false);
  };

  // Gestion des fournisseurs
  const handleFournisseurSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      if (editingItem) {
        await axios.put(`${API}/fournisseurs/${editingItem.id}`, fournisseurForm);
      } else {
        await axios.post(`${API}/fournisseurs`, fournisseurForm);
      }

      setShowFournisseurModal(false);
      setFournisseurForm({ nom: "", contact: "", email: "", telephone: "", adresse: "" });
      setEditingItem(null);
      fetchFournisseurs();
      fetchDashboardStats();
    } catch (error) {
      console.error("Erreur lors de la sauvegarde du fournisseur:", error);
      alert("Erreur lors de la sauvegarde");
    }
    setLoading(false);
  };

  // Gestion des mouvements
  const handleMouvementSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const formData = {
        ...mouvementForm,
        quantite: parseFloat(mouvementForm.quantite)
      };

      await axios.post(`${API}/mouvements`, formData);
      setShowMouvementModal(false);
      setMouvementForm({ produit_id: "", type: "entree", quantite: "", reference: "", commentaire: "" });
      fetchMouvements();
      fetchStocks();
      fetchDashboardStats();
    } catch (error) {
      console.error("Erreur lors de la création du mouvement:", error);
      alert("Erreur lors de la sauvegarde");
    }
    setLoading(false);
  };

  // Gestion des recettes
  const handleRecetteSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const formData = {
        ...recetteForm,
        portions: parseInt(recetteForm.portions),
        temps_preparation: recetteForm.temps_preparation ? parseInt(recetteForm.temps_preparation) : null,
        prix_vente: recetteForm.prix_vente ? parseFloat(recetteForm.prix_vente) : null,
        ingredients: recetteForm.ingredients.map(ing => ({
          ...ing,
          quantite: parseFloat(ing.quantite)
        }))
      };

      if (editingItem) {
        await axios.put(`${API}/recettes/${editingItem.id}`, formData);
      } else {
        await axios.post(`${API}/recettes`, formData);
      }

      setShowRecetteModal(false);
      resetRecetteForm();
      setEditingItem(null);
      fetchRecettes();
    } catch (error) {
      console.error("Erreur lors de la sauvegarde de la recette:", error);
      alert("Erreur lors de la sauvegarde");
    }
    setLoading(false);
  };

  const resetRecetteForm = () => {
    setRecetteForm({
      nom: "", description: "", categorie: "", portions: "", temps_preparation: "", 
      prix_vente: "", instructions: "", ingredients: []
    });
    setIngredientForm({ produit_id: "", quantite: "", unite: "" });
  };

  const addIngredient = () => {
    if (ingredientForm.produit_id && ingredientForm.quantite) {
      const produit = produits.find(p => p.id === ingredientForm.produit_id);
      if (produit) {
        const newIngredient = {
          produit_id: ingredientForm.produit_id,
          produit_nom: produit.nom,
          quantite: parseFloat(ingredientForm.quantite),
          unite: ingredientForm.unite || produit.unite
        };
        
        setRecetteForm(prev => ({
          ...prev,
          ingredients: [...prev.ingredients, newIngredient]
        }));
        
        setIngredientForm({ produit_id: "", quantite: "", unite: "" });
      }
    }
  };

  const removeIngredient = (index) => {
    setRecetteForm(prev => ({
      ...prev,
      ingredients: prev.ingredients.filter((_, i) => i !== index)
    }));
  };

  // Calculer la capacité de production
  const calculateProductionCapacity = async (recetteId) => {
    try {
      const response = await axios.get(`${API}/recettes/${recetteId}/production-capacity`);
      setProductionCapacity(response.data);
      setSelectedRecette(recetteId);
    } catch (error) {
      console.error("Erreur lors du calcul de capacité:", error);
      alert("Erreur lors du calcul");
    }
  };

  // Fonction d'édition
  const handleEdit = (item, type) => {
    setEditingItem(item);
    if (type === "produit") {
      setProduitForm({
        nom: item.nom,
        description: item.description || "",
        categorie: item.categorie || "",
        unite: item.unite,
        prix_achat: item.prix_achat || "",
        fournisseur_id: item.fournisseur_id || ""
      });
      setShowProduitModal(true);
    } else if (type === "fournisseur") {
      setFournisseurForm({
        nom: item.nom,
        contact: item.contact || "",
        email: item.email || "",
        telephone: item.telephone || "",
        adresse: item.adresse || ""
      });
      setShowFournisseurModal(true);
    } else if (type === "recette") {
      setRecetteForm({
        nom: item.nom,
        description: item.description || "",
        categorie: item.categorie || "",
        portions: item.portions.toString(),
        temps_preparation: item.temps_preparation?.toString() || "",
        prix_vente: item.prix_vente?.toString() || "",
        instructions: item.instructions || "",
        ingredients: item.ingredients || []
      });
      setShowRecetteModal(true);
    }
  };

  // Fonction de suppression
  const handleDelete = async (id, type) => {
    if (!window.confirm("Êtes-vous sûr de vouloir supprimer cet élément ?")) return;

    try {
      if (type === "produit") {
        await axios.delete(`${API}/produits/${id}`);
        fetchProduits();
        fetchStocks();
      } else if (type === "fournisseur") {
        await axios.delete(`${API}/fournisseurs/${id}`);
        fetchFournisseurs();
      } else if (type === "recette") {
        await axios.delete(`${API}/recettes/${id}`);
        fetchRecettes();
      }
      fetchDashboardStats();
    } catch (error) {
      console.error(`Erreur lors de la suppression du ${type}:`, error);
      alert("Erreur lors de la suppression");
    }
  };

  // Export Excel
  const handleExport = async () => {
    try {
      const response = await axios.get(`${API}/export/stocks`, {
        responseType: 'blob'
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'stocks_export.xlsx');
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (error) {
      console.error("Erreur lors de l'export:", error);
      alert("Erreur lors de l'export");
    }
  };

  // Export Recettes Excel
  const handleExportRecettes = async () => {
    try {
      const response = await axios.get(`${API}/export/recettes`, {
        responseType: 'blob'
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'recettes_export.xlsx');
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (error) {
      console.error("Erreur lors de l'export des recettes:", error);
      alert("Erreur lors de l'export des recettes");
    }
  };

  // Calculer Coûts des Recettes
  const handleCalculerCouts = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API}/recettes/calculer-couts`);
      
      if (response.data.success) {
        alert(`Coûts calculés avec succès !\n\nRésumé:\n- ${response.data.recettes_calculees} recettes mises à jour\n- Coût moyen: ${response.data.cout_moyen}€\n- Marge moyenne: ${response.data.marge_moyenne}%`);
        fetchRecettes(); // Rafraîchir la liste
      } else {
        alert("Erreur lors du calcul des coûts");
      }
    } catch (error) {
      console.error("Erreur lors du calcul des coûts:", error);
      alert("Erreur lors du calcul des coûts");
    } finally {
      setLoading(false);
    }
  };

  // Import Excel
  const handleImport = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await axios.post(`${API}/import/stocks`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      
      alert(response.data.message);
      if (response.data.errors.length > 0) {
        console.warn("Erreurs d'import:", response.data.errors);
      }
      
      fetchStocks();
      fetchDashboardStats();
    } catch (error) {
      console.error("Erreur lors de l'import:", error);
      alert("Erreur lors de l'import");
    }
    
    event.target.value = '';
  };

  // Gestion Alertes Stocks
  const handleVoirAlertes = () => {
    const stocksCritiques = stocks.filter(stock => {
      const produit = produits.find(p => p.id === stock.produit_id);
      return stock.quantite_actuelle <= stock.quantite_min;
    });
    
    if (stocksCritiques.length === 0) {
      alert("✅ Aucun stock critique pour le moment !");
    } else {
      const message = `⚠️ STOCKS CRITIQUES (${stocksCritiques.length} produits):\n\n` +
        stocksCritiques.map(stock => {
          const produit = produits.find(p => p.id === stock.produit_id);
          const unite = getDisplayUnit(produit?.unite);
          return `• ${stock.produit_nom}: ${formatQuantity(stock.quantite_actuelle, unite)} (Min: ${formatQuantity(stock.quantite_min, unite)})`;
        }).join('\n');
      
      alert(message);
    }
  };

  // Analyse Produits
  const handleAnalyseProduits = () => {
    const stats = {
      totalProduits: produits.length,
      produitsAvecPrix: produits.filter(p => p.prix_achat).length,
      prixMoyen: produits.filter(p => p.prix_achat).reduce((sum, p) => sum + p.prix_achat, 0) / produits.filter(p => p.prix_achat).length || 0,
      categories: [...new Set(produits.map(p => p.categorie).filter(Boolean))],
      fournisseurs: [...new Set(produits.map(p => p.fournisseur_id).filter(Boolean))]
    };

    alert(`📊 ANALYSE PRODUITS:\n\n` +
      `📦 Total produits: ${stats.totalProduits}\n` +
      `💰 Produits avec prix: ${stats.produitsAvecPrix}\n` +
      `💰 Prix moyen: ${stats.prixMoyen.toFixed(2)}€\n` +
      `📁 Catégories: ${stats.categories.length} (${stats.categories.slice(0, 3).join(', ')}...)\n` +
      `🏪 Fournisseurs: ${stats.fournisseurs.length}`);
  };

  // Générer Étiquettes
  const handleGenererEtiquettes = () => {
    alert(`🏷️ GÉNÉRATION D'ÉTIQUETTES:\n\n` +
      `Cette fonctionnalité générera des étiquettes PDF\n` +
      `pour tous les produits sélectionnés.\n\n` +
      `Fonctionnalité en cours de développement.\n` +
      `Utilisez "📊 Rapport Stock" pour export Excel en attendant.`);
  };
  const handlePageInventaire = () => {
    // Cette fonction pourrait ouvrir une page dédiée inventaire
    // Pour l'instant, on affiche un résumé
    const totalProduits = stocks.length;
    const stocksCritiques = stocks.filter(stock => stock.quantite_actuelle <= stock.quantite_min).length;
    const valeurTotale = stocks.reduce((total, stock) => {
      const produit = produits.find(p => p.id === stock.produit_id);
      return total + (stock.quantite_actuelle * (produit?.prix_achat || 0));
    }, 0);

    alert(`📊 RÉSUMÉ INVENTAIRE:\n\n` +
      `📦 Produits total: ${totalProduits}\n` +
      `⚠️ Stocks critiques: ${stocksCritiques}\n` +
      `💰 Valeur totale: ${valeurTotale.toFixed(2)}€\n\n` +
      `Pour un inventaire détaillé, utilisez "📊 Rapport Stock" pour export Excel.`);
  };
  const handleImportRecettes = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await axios.post(`${API}/import/recettes`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      
      alert(response.data.message);
      if (response.data.errors.length > 0) {
        console.warn("Erreurs d'import:", response.data.errors);
      }
      
      fetchRecettes();
    } catch (error) {
      console.error("Erreur lors de l'import des recettes:", error);
      alert("Erreur lors de l'import des recettes");
    }
    
    event.target.value = '';
  };

  // Fonctions pour OCR
  const handleOcrFileSelect = (event) => {
    const file = event.target.files[0];
    if (file) {
      if (!file.type.startsWith('image/')) {
        alert('Veuillez sélectionner un fichier image');
        return;
      }
      
      setOcrFile(file);
      
      // Créer un aperçu
      const reader = new FileReader();
      reader.onload = (e) => {
        setOcrPreview(e.target.result);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleOcrUpload = async () => {
    if (!ocrFile) {
      alert('Veuillez sélectionner un fichier');
      return;
    }

    setProcessingOcr(true);
    
    try {
      const formData = new FormData();
      formData.append('file', ocrFile);
      formData.append('document_type', ocrType);

      const response = await axios.post(`${API}/ocr/upload-document?document_type=${ocrType}`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });

      setOcrResult(response.data);
      alert('Document traité avec succès !');
      fetchDocumentsOcr();
      
    } catch (error) {
      console.error('Erreur lors du traitement OCR:', error);
      alert(`Erreur: ${error.response?.data?.detail || 'Erreur lors du traitement'}`);
    } finally {
      setProcessingOcr(false);
    }
  };

  const handleProcessZReport = async (documentId) => {
    if (!window.confirm('Voulez-vous traiter ce rapport Z pour déduire automatiquement les stocks ?')) return;
    
    try {
      setLoading(true);
      const response = await axios.post(`${API}/ocr/process-z-report/${documentId}`);
      
      alert(response.data.message + 
            (response.data.warnings.length > 0 ? '\n\nAvertissements:\n' + response.data.warnings.join('\n') : ''));
      
      fetchDocumentsOcr();
      fetchStocks();
      fetchMouvements();
      fetchDashboardStats();
    } catch (error) {
      console.error('Erreur lors du traitement du rapport Z:', error);
      alert(`Erreur: ${error.response?.data?.detail || 'Erreur lors du traitement'}`);
    } finally {
      setLoading(false);
    }
  };

  const resetOcrModal = () => {
    setOcrFile(null);
    setOcrPreview(null);
    setOcrResult(null);
    setOcrType("z_report");
    setProcessingOcr(false);
  };

  // Fonction utilitaire pour formater les quantités
  const formatQuantity = (quantity, unit) => {
    if (quantity === undefined || quantity === null) return "0";
    
    // Si c'est un nombre entier ou très proche d'un entier
    if (quantity % 1 === 0) {
      return `${Math.round(quantity)} ${unit || ''}`.trim();
    }
    
    // Pour les décimales, limiter à 2 chiffres après la virgule
    if (quantity < 10) {
      return `${parseFloat(quantity.toFixed(2))} ${unit || ''}`.trim();
    } else {
      return `${parseFloat(quantity.toFixed(1))} ${unit || ''}`.trim();
    }
  };

  // Fonction pour obtenir l'unité d'affichage appropriée
  const getDisplayUnit = (unit) => {
    const unitMapping = {
      'kg': 'kg',
      'g': 'g',
      'L': 'L',
      'mL': 'mL',
      'cl': 'cL',
      'pièce': 'pcs',
      'paquet': 'pqts',
      'botte': 'bottes',
      'piece': 'pcs',
      'litre': 'L',
      'gramme': 'g',
      'kilogramme': 'kg'
    };
    
    return unitMapping[unit] || unit || 'unité';
  };

  return (
    <div className="container">
      {/* Header */}
      <div className="header">
        <h1>ResTop : Gestion de La Table d'Augustine</h1>
      </div>

      {/* Navigation */}
      <div className="nav-tabs">
        <button 
          className={`nav-tab ${activeTab === "dashboard" ? "active" : ""}`}
          onClick={() => setActiveTab("dashboard")}
        >
          📊 Dashboard
        </button>
        <button 
          className={`nav-tab ${activeTab === "ocr" ? "active" : ""}`}
          onClick={() => setActiveTab("ocr")}
        >
          📱 OCR
        </button>
        <button 
          className={`nav-tab ${activeTab === "stocks" ? "active" : ""}`}
          onClick={() => setActiveTab("stocks")}
        >
          📦 Gestion de Stocks
        </button>
        <button 
          className={`nav-tab ${activeTab === "production" ? "active" : ""}`}
          onClick={() => setActiveTab("production")}
        >
          🍳 Production
        </button>
        <button 
          className={`nav-tab ${activeTab === "historique" ? "active" : ""}`}
          onClick={() => setActiveTab("historique")}
        >
          📊 Historique
        </button>
      </div>

      {/* DASHBOARD */}
      <div id="dashboard" className={`wireframe-section ${activeTab === "dashboard" ? "active" : ""}`}>
        <div className="wireframe">
          <h2>📊 Dashboard Principal</h2>
          <div className="layout dashboard-layout">
            <div className="card stat-card">
              <div className="icon">💰</div>
              <div className="card-title">Chiffre d'Affaires</div>
              <div className="card-content">€15,420 ce mois</div>
            </div>
            <div className="card stat-card">
              <div className="icon">📦</div>
              <div className="card-title">Stock Critique</div>
              <div className="card-content">{dashboardStats.stocks_faibles || 0} produits</div>
            </div>
            <div className="card stat-card">
              <div className="icon">🍽️</div>
              <div className="card-title">Produits Total</div>
              <div className="card-content">{dashboardStats.total_produits || 0} produits</div>
            </div>
            
            <div className="card full-width">
              <div className="card-title">📈 Graphique des Ventes</div>
              <div className="card-content">Évolution du CA sur les 30 derniers jours</div>
            </div>
            
            <div className="card">
              <div className="card-title">⚠️ Alertes</div>
              <ul className="feature-list">
                <li>Stock tomates faible</li>
                <li>Livraison prévue 14h</li>
                <li>Nouvelle recette ajoutée</li>
              </ul>
            </div>
            
            <div className="card">
              <div className="card-title">📋 Tâches du Jour</div>
              <ul className="feature-list">
                <li>Inventaire cuisine</li>
                <li>Formation équipe</li>
                <li>Réunion fournisseur</li>
              </ul>
            </div>
            
            <div className="card">
              <div className="card-title">🔄 Activité Récente</div>
              <ul className="feature-list">
                {mouvements.slice(0, 3).map((mouvement, index) => (
                  <li key={index}>Stock {mouvement.produit_nom} mis à jour</li>
                ))}
                {mouvements.length === 0 && <li>Aucune activité récente</li>}
              </ul>
            </div>
          </div>
        </div>
      </div>

      {/* OCR */}
      <div id="ocr" className={`wireframe-section ${activeTab === "ocr" ? "active" : ""}`}>
        <div className="wireframe">
          <h2>📱 Module OCR - Numérisation Factures</h2>
          <div className="layout two-column">
            <div className="sidebar">
              <h3 style={{color: '#d4af37', marginBottom: '15px'}}>Actions</h3>
              <button className="button" onClick={() => setShowOcrModal(true)}>📷 Nouvelle Photo</button>
              <button className="button" onClick={() => setShowOcrModal(true)}>📁 Importer Fichier</button>
              <button className="button">🔄 Traitement Auto</button>
              <h4 style={{color: '#d4af37', margin: '20px 0 10px'}}>Historique</h4>
              <div style={{fontSize: '0.9rem'}}>
                {documentsOcr.slice(0, 3).map((doc, index) => (
                  <div key={index} style={{padding: '8px', margin: '5px 0', background: 'rgba(255,255,255,0.2)', borderRadius: '5px'}}>
                    {doc.nom_fichier}
                  </div>
                ))}
                {documentsOcr.length === 0 && (
                  <div style={{padding: '8px', margin: '5px 0', background: 'rgba(255,255,255,0.2)', borderRadius: '5px'}}>
                    Aucun document
                  </div>
                )}
              </div>
            </div>
            <div className="main-content">
              <input type="text" className="search-bar" placeholder="🔍 Rechercher une facture..."/>
              
              <div className="card">
                <div className="card-title">📄 Zone de Prévisualisation</div>
                <div style={{height: '200px', background: '#f8f7f4', border: '2px dashed #d4af37', borderRadius: '10px', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '15px 0'}}>
                  <span style={{color: '#4a5568'}}>Glissez votre facture ici ou cliquez pour sélectionner</span>
                </div>
              </div>
              
              <div className="table-mockup">
                <div className="table-header">Données Extraites</div>
                {documentsOcr.length > 0 && (
                  documentsOcr.slice(0, 3).map((doc, index) => (
                    <div key={index} className="table-row">
                      <span>Fournisseur: {doc.donnees_parsees?.fournisseur || 'Non identifié'} | Montant: {doc.donnees_parsees?.total_ca || 'N/A'}€</span>
                    </div>
                  ))
                )}
                {documentsOcr.length === 0 && (
                  <div className="table-row">
                    <span>Aucune donnée extraite</span>
                  </div>
                )}
              </div>
              
              <div style={{textAlign: 'center', marginTop: '20px'}}>
                <button className="button" onClick={() => setShowOcrModal(true)}>✅ Valider</button>
                <button className="button">✏️ Corriger</button>
                <button className="button">💾 Enregistrer</button>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* STOCKS */}
      <div id="stocks" className={`wireframe-section ${activeTab === "stocks" ? "active" : ""}`}>
        <div className="wireframe">
          <h2>📦 Gestion de Stocks</h2>
          <div className="layout">
            <div className="card full-width">
              <input type="text" className="search-bar" placeholder="🔍 Rechercher un produit..."/>
              <div style={{display: 'flex', justifyContent: 'center', gap: '10px', marginTop: '15px', flexWrap: 'wrap'}}>
                <button className="button" onClick={() => setShowProduitModal(true)}>➕ Nouveau Produit</button>
                <button className="button" onClick={handleExport}>📊 Rapport Stock</button>
                <button className="button" onClick={handleVoirAlertes}>⚠️ Alertes</button>
                <button className="button" onClick={handlePageInventaire}>📱 Inventaire</button>
              </div>
            </div>
            
            <div className="layout three-column">
              <div className="card stat-card">
                <div className="icon">📈</div>
                <div className="card-title">Stock Total</div>
                <div className="card-content">€12,450</div>
              </div>
              <div className="card stat-card">
                <div className="icon">⚠️</div>
                <div className="card-title">Produits Critiques</div>
                <div className="card-content">{dashboardStats.stocks_faibles || 0} produits</div>
              </div>
              <div className="card stat-card">
                <div className="icon">🔄</div>
                <div className="card-title">Rotation Stock</div>
                <div className="card-content">15 jours moy.</div>
              </div>
            </div>
            
            <div className="card full-width">
              <div className="card-title">📋 Liste des Produits</div>
              <div className="table-mockup">
                <div className="table-header">Produit | Quantité | Stock Min | Statut | Actions</div>
                {stocks.map((stock, index) => {
                  const isLowStock = stock.quantite_actuelle <= stock.quantite_min;
                  const produit = produits.find(p => p.id === stock.produit_id);
                  const unite = getDisplayUnit(produit?.unite);
                  
                  return (
                    <div key={index} className="table-row">
                      <span>
                        {produit?.categorie === 'légumes' ? '🍅' : produit?.categorie === 'épices' ? '🧄' : produit?.categorie === 'huiles' ? '🫒' : produit?.categorie === 'fromages' ? '🧀' : '📦'} {stock.produit_nom} | {formatQuantity(stock.quantite_actuelle, unite)} | {formatQuantity(stock.quantite_min, unite)} | {isLowStock ? '⚠️ Critique' : '✅ OK'}
                      </span>
                      <div>
                        <button className="button" style={{fontSize: '0.7rem', padding: '4px 8px'}} onClick={() => handleEdit(produit, 'produit')}>✏️ Éditer</button>
                        <button className="button" style={{fontSize: '0.7rem', padding: '4px 8px'}} onClick={() => setShowMouvementModal(true)}>🛒 Commander</button>
                      </div>
                    </div>
                  );
                })}
                {stocks.length === 0 && (
                  <div className="table-row">
                    <span>Aucun stock disponible</span>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* PRODUCTION */}
      <div id="production" className={`wireframe-section ${activeTab === "production" ? "active" : ""}`}>
        <div className="wireframe">
          <h2>🍳 Module Production</h2>
          
          {/* Sous-navigation Production */}
          <div className="sub-nav-tabs">
            <button 
              className="button" 
              onClick={() => setActiveProductionTab('produits')}
              style={{
                background: activeProductionTab === 'produits' ? 'linear-gradient(135deg, #2d5016, #4a7c59)' : 'linear-gradient(135deg, #d4af37, #f4d03f)',
                color: activeProductionTab === 'produits' ? '#f5f3f0' : '#2d5016'
              }}
            >
              🍽️ Produits
            </button>
            <button 
              className="button" 
              onClick={() => setActiveProductionTab('fournisseurs')}
              style={{
                background: activeProductionTab === 'fournisseurs' ? 'linear-gradient(135deg, #2d5016, #4a7c59)' : 'linear-gradient(135deg, #d4af37, #f4d03f)',
                color: activeProductionTab === 'fournisseurs' ? '#f5f3f0' : '#2d5016'
              }}
            >
              🚚 Fournisseurs
            </button>
            <button 
              className="button" 
              onClick={() => setActiveProductionTab('recettes')}
              style={{
                background: activeProductionTab === 'recettes' ? 'linear-gradient(135deg, #2d5016, #4a7c59)' : 'linear-gradient(135deg, #d4af37, #f4d03f)',
                color: activeProductionTab === 'recettes' ? '#f5f3f0' : '#2d5016'
              }}
            >
              📝 Recettes
            </button>
          </div>

          {/* PRODUITS */}
          <div className={`production-tab ${activeProductionTab === 'produits' ? 'active' : ''}`}>
            <div className="layout">
              <div className="card full-width">
                <div className="card-title">🍽️ Gestion des Produits</div>
                <input type="text" className="search-bar" placeholder="🔍 Rechercher un produit..."/>
                <div style={{textAlign: 'center', margin: '15px 0'}}>
                  <button className="button" onClick={() => setShowProduitModal(true)}>➕ Nouveau Produit</button>
                  <button className="button" onClick={handleAnalyseProduits}>📊 Analyse Produits</button>
                  <button className="button" onClick={handleGenererEtiquettes}>🏷️ Étiquettes</button>
                </div>
              </div>
              
              <div className="layout three-column">
                {produits.slice(0, 6).map((produit, index) => (
                  <div key={index} className="card">
                    <div className="icon">
                      {produit.categorie === 'entrée' ? '🥗' : 
                       produit.categorie === 'plat' ? '🍖' : 
                       produit.categorie === 'poisson' ? '🐟' : '🍽️'}
                    </div>
                    <div className="card-title">{produit.nom}</div>
                    <div className="card-content">
                      Prix: €{produit.prix_achat || 'N/A'}<br/>
                      {produit.description && `${produit.description.substring(0, 20)}...`}
                    </div>
                    <div style={{marginTop: '15px'}}>
                      <button className="button" style={{fontSize: '0.8rem', padding: '8px 16px'}} onClick={() => handleEdit(produit, 'produit')}>✏️ Éditer</button>
                      <button className="button" style={{fontSize: '0.8rem', padding: '8px 16px'}} onClick={() => handleDelete(produit.id, 'produit')}>🗑️ Suppr.</button>
                    </div>
                  </div>
                ))}
                {produits.length === 0 && (
                  <div className="card">
                    <div className="card-content">Aucun produit disponible</div>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* FOURNISSEURS */}
          <div className={`production-tab ${activeProductionTab === 'fournisseurs' ? 'active' : ''}`}>
            <div className="layout">
              <div className="card full-width">
                <div className="card-title">🚚 Gestion des Fournisseurs</div>
                <input type="text" className="search-bar" placeholder="🔍 Rechercher un fournisseur..."/>
                <div style={{textAlign: 'center', margin: '15px 0'}}>
                  <button className="button" onClick={() => setShowFournisseurModal(true)}>➕ Nouveau Fournisseur</button>
                  <button className="button">📞 Contacts</button>
                  <button className="button">📊 Performance</button>
                </div>
              </div>
              
              <div className="table-mockup">
                <div className="table-header">Fournisseur | Contact | Spécialité | Email | Actions</div>
                {fournisseurs.map((fournisseur, index) => (
                  <div key={index} className="table-row">
                    <span>
                      {fournisseur.nom.includes('Bio') ? '🌿' : 
                       fournisseur.nom.includes('Poissonnerie') ? '🐟' : 
                       fournisseur.nom.includes('Cave') ? '🍷' : 
                       fournisseur.nom.includes('Boulangerie') ? '🥖' : '🏪'} {fournisseur.nom} | {fournisseur.contact || fournisseur.telephone || 'N/A'} | {fournisseur.adresse?.split(',')[0] || 'Non spécifié'} | {fournisseur.email || 'N/A'}
                    </span>
                    <div>
                      <button className="button" style={{fontSize: '0.7rem', padding: '4px 8px'}} onClick={() => handleEdit(fournisseur, 'fournisseur')}>✏️ Éditer</button>
                      <button className="button" style={{fontSize: '0.7rem', padding: '4px 8px'}}>📞 Appeler</button>
                      <button className="button" style={{fontSize: '0.7rem', padding: '4px 8px'}}>📧 Email</button>
                    </div>
                  </div>
                ))}
                {fournisseurs.length === 0 && (
                  <div className="table-row">
                    <span>Aucun fournisseur disponible</span>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* RECETTES */}
          <div className={`production-tab ${activeProductionTab === 'recettes' ? 'active' : ''}`}>
            <div className="layout">
              <div className="card full-width">
                <div className="card-title">📝 Gestion des Recettes</div>
                <input type="text" className="search-bar" placeholder="🔍 Rechercher une recette..."/>
                <div style={{textAlign: 'center', margin: '15px 0'}}>
                  <button className="button" onClick={() => setShowRecetteModal(true)}>➕ Nouvelle Recette</button>
                  <button className="button" onClick={handleCalculerCouts} disabled={loading}>💰 Calculer Coûts</button>
                  <button className="button" onClick={handleExportRecettes}>📖 Export Excel</button>
                </div>
              </div>
              
              <div className="layout two-column">
                <div className="card">
                  <div className="card-title">📋 Liste des Recettes</div>
                  <div style={{maxHeight: '300px', overflowY: 'auto'}}>
                    {recettes.map((recette, index) => (
                      <div key={index} className="table-row">
                        <span>
                          {recette.categorie === 'entrée' ? '🥗' : 
                           recette.categorie === 'plat' ? '🍖' : 
                           recette.categorie === 'dessert' ? '🍰' : '🍽️'} {recette.nom} - {recette.ingredients?.length || 0} ingrédients
                        </span>
                        <div>
                          <button className="button" style={{fontSize: '0.7rem', padding: '4px 8px', margin: '2px'}} onClick={() => handleEdit(recette, 'recette')}>✏️ Éditer</button>
                          <button className="button" style={{fontSize: '0.7rem', padding: '4px 8px', margin: '2px'}} onClick={() => calculateProductionCapacity(recette.id)}>👁️ Voir</button>
                        </div>
                      </div>
                    ))}
                    {recettes.length === 0 && (
                      <div className="table-row">
                        <span>Aucune recette disponible</span>
                      </div>
                    )}
                  </div>
                </div>
                <div className="card">
                  <div className="card-title">📝 Recette Sélectionnée</div>
                  {selectedRecette && productionCapacity ? (
                    <div className="card-content">
                      <strong>Recette:</strong> {productionCapacity.recette_nom}<br/>
                      <strong>Portions possibles:</strong> {productionCapacity.portions_max}<br/>
                      <strong>Ingrédients:</strong><br/>
                      {productionCapacity.ingredients_status?.slice(0, 3).map((ingredient, idx) => (
                        <div key={idx}>• {ingredient.produit_nom}: {formatQuantity(ingredient.quantite_disponible, getDisplayUnit(ingredient.unite))}</div>
                      ))}
                      <br/>
                      <button className="button" style={{fontSize: '0.8rem'}} onClick={() => calculateProductionCapacity(selectedRecette)}>🔄 Actualiser</button>
                    </div>
                  ) : (
                    <div className="card-content">
                      Sélectionnez une recette pour voir les détails de production
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* HISTORIQUE */}
      <div id="historique" className={`wireframe-section ${activeTab === "historique" ? "active" : ""}`}>
        <div className="wireframe">
          <h2>📊 Gestion de l'Historique</h2>
          
          {/* Sous-navigation Historique */}
          <div className="sub-nav-tabs">
            <button 
              className="button" 
              onClick={() => setActiveHistoriqueTab('ventes')}
              style={{
                background: activeHistoriqueTab === 'ventes' ? 'linear-gradient(135deg, #2d5016, #4a7c59)' : 'linear-gradient(135deg, #d4af37, #f4d03f)',
                color: activeHistoriqueTab === 'ventes' ? '#f5f3f0' : '#2d5016'
              }}
            >
              💰 Ventes
            </button>
            <button 
              className="button" 
              onClick={() => setActiveHistoriqueTab('stocks')}
              style={{
                background: activeHistoriqueTab === 'stocks' ? 'linear-gradient(135deg, #2d5016, #4a7c59)' : 'linear-gradient(135deg, #d4af37, #f4d03f)',
                color: activeHistoriqueTab === 'stocks' ? '#f5f3f0' : '#2d5016'
              }}
            >
              📦 Mouvements Stock
            </button>
            <button 
              className="button" 
              onClick={() => setActiveHistoriqueTab('commandes')}
              style={{
                background: activeHistoriqueTab === 'commandes' ? 'linear-gradient(135deg, #2d5016, #4a7c59)' : 'linear-gradient(135deg, #d4af37, #f4d03f)',
                color: activeHistoriqueTab === 'commandes' ? '#f5f3f0' : '#2d5016'
              }}
            >
              🛒 Commandes
            </button>
            <button 
              className="button" 
              onClick={() => setActiveHistoriqueTab('factures')}
              style={{
                background: activeHistoriqueTab === 'factures' ? 'linear-gradient(135deg, #2d5016, #4a7c59)' : 'linear-gradient(135deg, #d4af37, #f4d03f)',
                color: activeHistoriqueTab === 'factures' ? '#f5f3f0' : '#2d5016'
              }}
            >
              📄 Factures
            </button>
            <button 
              className="button" 
              onClick={() => setActiveHistoriqueTab('modifications')}
              style={{
                background: activeHistoriqueTab === 'modifications' ? 'linear-gradient(135deg, #2d5016, #4a7c59)' : 'linear-gradient(135deg, #d4af37, #f4d03f)',
                color: activeHistoriqueTab === 'modifications' ? '#f5f3f0' : '#2d5016'
              }}
            >
              ✏️ Modifications
            </button>
          </div>

          {/* HISTORIQUE VENTES */}
          <div className={`historique-tab ${activeHistoriqueTab === 'ventes' ? 'active' : ''}`}>
            <div className="layout">
              <div className="card full-width">
                <div className="card-title">💰 Historique des Ventes</div>
                <div style={{display: 'flex', gap: '15px', alignItems: 'center', justifyContent: 'center', margin: '15px 0', flexWrap: 'wrap'}}>
                  <input type="date" className="search-bar" style={{width: 'auto', margin: 0}} defaultValue="2025-08-01"/>
                  <span style={{color: '#2d5016', fontWeight: 'bold'}}>à</span>
                  <input type="date" className="search-bar" style={{width: 'auto', margin: 0}} defaultValue="2025-08-05"/>
                  <button className="button">🔍 Filtrer</button>
                  <button className="button">📊 Exporter</button>
                </div>
              </div>
              
              <div className="layout three-column">
                <div className="card stat-card">
                  <div className="icon">💰</div>
                  <div className="card-title">CA Total Période</div>
                  <div className="card-content">€8,420.50</div>
                </div>
                <div className="card stat-card">
                  <div className="icon">🍽️</div>
                  <div className="card-title">Plats Vendus</div>
                  <div className="card-content">267 plats</div>
                </div>
                <div className="card stat-card">
                  <div className="icon">📈</div>
                  <div className="card-title">Ticket Moyen</div>
                  <div className="card-content">€31.50</div>
                </div>
              </div>
              
              <div className="card full-width">
                <div className="table-mockup">
                  <div className="table-header">Date | Heure | Plat | Quantité | Prix Unit. | Total</div>
                  {recettes.slice(0, 5).map((recette, index) => (
                    <div key={index} className="table-row">
                      <span>{new Date().toLocaleDateString('fr-FR')} | {String(12 + index).padStart(2, '0')}:30 | {recette.nom} | 1 | €{recette.prix_vente || '15.00'} | €{recette.prix_vente || '15.00'}</span>
                    </div>
                  ))}
                  {recettes.length === 0 && (
                    <div className="table-row">
                      <span>Aucune vente enregistrée</span>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* HISTORIQUE MOUVEMENTS STOCK */}
          <div className={`historique-tab ${activeHistoriqueTab === 'stocks' ? 'active' : ''}`}>
            <div className="layout">
              <div className="card full-width">
                <div className="card-title">📦 Historique des Mouvements de Stock</div>
                <div style={{display: 'flex', gap: '15px', alignItems: 'center', justifyContent: 'center', margin: '15px 0', flexWrap: 'wrap'}}>
                  <select className="search-bar" style={{width: 'auto', margin: 0}}>
                    <option>Tous les produits</option>
                    {produits.slice(0, 5).map((produit, index) => (
                      <option key={index}>{produit.nom}</option>
                    ))}
                  </select>
                  <select className="search-bar" style={{width: 'auto', margin: 0}}>
                    <option>Tous mouvements</option>
                    <option>➕ Entrée</option>
                    <option>➖ Sortie</option>
                    <option>🔄 Ajustement</option>
                  </select>
                  <button className="button">🔍 Filtrer</button>
                </div>
              </div>
              
              <div className="card full-width">
                <div className="table-mockup">
                  <div className="table-header">Date | Produit | Type | Quantité | Stock Avant | Stock Après | Motif</div>
                  {mouvements.slice(0, 5).map((mouvement, index) => {
                    const produit = produits.find(p => p.id === mouvement.produit_id);
                    const unite = getDisplayUnit(produit?.unite);
                    return (
                      <div key={index} className="table-row">
                        <span>
                          {new Date(mouvement.date).toLocaleDateString('fr-FR')} | {mouvement.produit_nom} | 
                          <span style={{
                            color: mouvement.type === 'entree' ? '#38a169' : mouvement.type === 'sortie' ? '#e53e3e' : '#d69e2e',
                            fontWeight: 'bold'
                          }}>
                            {mouvement.type === 'entree' ? '➕ Entrée' : mouvement.type === 'sortie' ? '➖ Sortie' : '🔄 Ajustement'}
                          </span> | 
                          {formatQuantity(Math.abs(mouvement.quantite), unite)} | - | - | {mouvement.commentaire || 'Mouvement standard'}
                        </span>
                      </div>
                    );
                  })}
                  {mouvements.length === 0 && (
                    <div className="table-row">
                      <span>Aucun mouvement enregistré</span>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* HISTORIQUE COMMANDES */}
          <div className={`historique-tab ${activeHistoriqueTab === 'commandes' ? 'active' : ''}`}>
            <div className="layout">
              <div className="card full-width">
                <div className="card-title">🛒 Historique des Commandes Fournisseurs</div>
                <div style={{display: 'flex', gap: '15px', alignItems: 'center', justifyContent: 'center', margin: '15px 0', flexWrap: 'wrap'}}>
                  <select className="search-bar" style={{width: 'auto', margin: 0}}>
                    <option>Tous les fournisseurs</option>
                    {fournisseurs.slice(0, 4).map((fournisseur, index) => (
                      <option key={index}>{fournisseur.nom}</option>
                    ))}
                  </select>
                  <select className="search-bar" style={{width: 'auto', margin: 0}}>
                    <option>Tous statuts</option>
                    <option>✅ Livrée</option>
                    <option>🚚 En cours</option>
                    <option>❌ Annulée</option>
                  </select>
                  <button className="button">🔍 Filtrer</button>
                </div>
              </div>
              
              <div className="card full-width">
                <div className="table-mockup">
                  <div className="table-header">N° Commande | Date | Fournisseur | Montant | Statut | Actions</div>
                  {fournisseurs.slice(0, 4).map((fournisseur, index) => (
                    <div key={index} className="table-row">
                      <span>
                        CMD-2025-{String(90 + index).padStart(3, '0')} | {new Date(Date.now() - index * 24 * 60 * 60 * 1000).toLocaleDateString('fr-FR')} | {fournisseur.nom} | €{(Math.random() * 500 + 100).toFixed(2)} | 
                        <span style={{color: '#38a169', fontWeight: 'bold'}}>✅ Livrée</span>
                      </span>
                      <button className="button" style={{fontSize: '0.7rem', padding: '4px 8px'}}>👁️ Détails</button>
                    </div>
                  ))}
                  {fournisseurs.length === 0 && (
                    <div className="table-row">
                      <span>Aucune commande enregistrée</span>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* HISTORIQUE FACTURES */}
          <div className={`historique-tab ${activeHistoriqueTab === 'factures' ? 'active' : ''}`}>
            <div className="layout">
              <div className="card full-width">
                <div className="card-title">📄 Historique des Factures OCR</div>
                <div style={{display: 'flex', gap: '15px', alignItems: 'center', justifyContent: 'center', margin: '15px 0', flexWrap: 'wrap'}}>
                  <input type="text" className="search-bar" placeholder="🔍 Rechercher par fournisseur..." style={{width: '300px', margin: 0}}/>
                  <select className="search-bar" style={{width: 'auto', margin: 0}}>
                    <option>Tous statuts</option>
                    <option>✅ Validée</option>
                    <option>⏳ En attente</option>
                    <option>❌ Rejetée</option>
                  </select>
                  <button className="button">🔍 Filtrer</button>
                </div>
              </div>
              
              <div className="card full-width">
                <div className="table-mockup">
                  <div className="table-header">Date Upload | Nom Fichier | Fournisseur | Montant | Statut | Actions</div>
                  {documentsOcr.slice(0, 4).map((doc, index) => (
                    <div key={index} className="table-row">
                      <span>
                        {new Date(doc.date_upload).toLocaleDateString('fr-FR')} | {doc.nom_fichier} | {doc.donnees_parsees?.fournisseur || 'Non identifié'} | €{doc.donnees_parsees?.total_ca || 'N/A'} | 
                        <span style={{color: '#38a169', fontWeight: 'bold'}}>✅ Validée</span>
                      </span>
                      <div>
                        <button className="button" style={{fontSize: '0.7rem', padding: '4px 8px'}}>👁️ Voir</button>
                        <button className="button" style={{fontSize: '0.7rem', padding: '4px 8px'}}>📄 PDF</button>
                      </div>
                    </div>
                  ))}
                  {documentsOcr.length === 0 && (
                    <div className="table-row">
                      <span>Aucune facture OCR traitée</span>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* HISTORIQUE MODIFICATIONS */}
          <div className={`historique-tab ${activeHistoriqueTab === 'modifications' ? 'active' : ''}`}>
            <div className="layout">
              <div className="card full-width">
                <div className="card-title">✏️ Historique des Modifications</div>
                <div style={{display: 'flex', gap: '15px', alignItems: 'center', justifyContent: 'center', margin: '15px 0', flexWrap: 'wrap'}}>
                  <select className="search-bar" style={{width: 'auto', margin: 0}}>
                    <option>Toutes les sections</option>
                    <option>🍽️ Produits</option>
                    <option>📝 Recettes</option>
                    <option>🚚 Fournisseurs</option>
                    <option>📦 Stock</option>
                  </select>
                  <select className="search-bar" style={{width: 'auto', margin: 0}}>
                    <option>Tous utilisateurs</option>
                    <option>Chef Antoine</option>
                    <option>Marie</option>
                    <option>Pierre</option>
                  </select>
                  <button className="button">🔍 Filtrer</button>
                </div>
              </div>
              
              <div className="card full-width">
                <div className="table-mockup">
                  <div className="table-header">Date/Heure | Utilisateur | Section | Élément | Action | Détails</div>
                  <div className="table-row">
                    <span>{new Date().toLocaleDateString('fr-FR')} 14:30 | Chef Antoine | <span style={{color: '#9f7aea', fontWeight: 'bold'}}>🍽️ Produits</span> | Salade Augustine | <span style={{color: '#3182ce'}}>Modification prix</span> | Prix mis à jour</span>
                  </div>
                  <div className="table-row">
                    <span>{new Date(Date.now() - 24*60*60*1000).toLocaleDateString('fr-FR')} 10:15 | Marie | <span style={{color: '#38a169', fontWeight: 'bold'}}>📝 Recettes</span> | Nouvelle recette | <span style={{color: '#38a169'}}>Ajout recette</span> | Recette créée</span>
                  </div>
                  <div className="table-row">
                    <span>{new Date(Date.now() - 2*24*60*60*1000).toLocaleDateString('fr-FR')} 16:45 | Pierre | <span style={{color: '#d69e2e', fontWeight: 'bold'}}>🚚 Fournisseurs</span> | Contact modifié | <span style={{color: '#3182ce'}}>Modification contact</span> | Coordonnées mises à jour</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Modal Produit */}
      {showProduitModal && (
        <div className="modal-overlay">
          <div className="modal-content">
            <h3 className="modal-header">
              {editingItem ? "Modifier le produit" : "Ajouter un produit"}
            </h3>
            <form onSubmit={handleProduitSubmit}>
              <div className="form-group">
                <label className="form-label">Nom du produit</label>
                <input
                  type="text"
                  className="form-input"
                  value={produitForm.nom}
                  onChange={(e) => setProduitForm({...produitForm, nom: e.target.value})}
                  required
                />
              </div>
              <div className="form-group">
                <label className="form-label">Description</label>
                <textarea
                  className="form-textarea"
                  value={produitForm.description}
                  onChange={(e) => setProduitForm({...produitForm, description: e.target.value})}
                />
              </div>
              <div className="form-group">
                <label className="form-label">Catégorie</label>
                <input
                  type="text"
                  className="form-input"
                  value={produitForm.categorie}
                  onChange={(e) => setProduitForm({...produitForm, categorie: e.target.value})}
                />
              </div>
              <div className="form-group">
                <label className="form-label">Unité</label>
                <select
                  className="form-select"
                  value={produitForm.unite}
                  onChange={(e) => setProduitForm({...produitForm, unite: e.target.value})}
                  required
                >
                  <option value="">Sélectionnez une unité</option>
                  <option value="kg">Kilogramme (kg)</option>
                  <option value="g">Gramme (g)</option>
                  <option value="L">Litre (L)</option>
                  <option value="mL">Millilitre (mL)</option>
                  <option value="pièce">Pièce</option>
                  <option value="paquet">Paquet</option>
                </select>
              </div>
              <div className="form-group">
                <label className="form-label">Prix d'achat (€)</label>
                <input
                  type="number"
                  step="0.01"
                  className="form-input"
                  value={produitForm.prix_achat}
                  onChange={(e) => setProduitForm({...produitForm, prix_achat: e.target.value})}
                />
              </div>
              <div className="form-group">
                <label className="form-label">Fournisseur</label>
                <select
                  className="form-select"
                  value={produitForm.fournisseur_id}
                  onChange={(e) => setProduitForm({...produitForm, fournisseur_id: e.target.value})}
                >
                  <option value="">Sélectionnez un fournisseur</option>
                  {fournisseurs.map((fournisseur) => (
                    <option key={fournisseur.id} value={fournisseur.id}>
                      {fournisseur.nom}
                    </option>
                  ))}
                </select>
              </div>
              <div className="button-group">
                <button
                  type="button"
                  className="button btn-cancel"
                  onClick={() => {
                    setShowProduitModal(false);
                    setEditingItem(null);
                    setProduitForm({ nom: "", description: "", categorie: "", unite: "", prix_achat: "", fournisseur_id: "" });
                  }}
                >
                  Annuler
                </button>
                <button
                  type="submit"
                  className="button btn-primary"
                  disabled={loading}
                >
                  {loading ? "Sauvegarde..." : (editingItem ? "Modifier" : "Ajouter")}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal Fournisseur */}
      {showFournisseurModal && (
        <div className="modal-overlay">
          <div className="modal-content">
            <h3 className="modal-header">
              {editingItem ? "Modifier le fournisseur" : "Ajouter un fournisseur"}
            </h3>
            <form onSubmit={handleFournisseurSubmit}>
              <div className="form-group">
                <label className="form-label">Nom du fournisseur</label>
                <input
                  type="text"
                  className="form-input"
                  value={fournisseurForm.nom}
                  onChange={(e) => setFournisseurForm({...fournisseurForm, nom: e.target.value})}
                  required
                />
              </div>
              <div className="form-group">
                <label className="form-label">Contact</label>
                <input
                  type="text"
                  className="form-input"
                  value={fournisseurForm.contact}
                  onChange={(e) => setFournisseurForm({...fournisseurForm, contact: e.target.value})}
                />
              </div>
              <div className="form-group">
                <label className="form-label">Email</label>
                <input
                  type="email"
                  className="form-input"
                  value={fournisseurForm.email}
                  onChange={(e) => setFournisseurForm({...fournisseurForm, email: e.target.value})}
                />
              </div>
              <div className="form-group">
                <label className="form-label">Téléphone</label>
                <input
                  type="tel"
                  className="form-input"
                  value={fournisseurForm.telephone}
                  onChange={(e) => setFournisseurForm({...fournisseurForm, telephone: e.target.value})}
                />
              </div>
              <div className="form-group">
                <label className="form-label">Adresse</label>
                <textarea
                  className="form-textarea"
                  value={fournisseurForm.adresse}
                  onChange={(e) => setFournisseurForm({...fournisseurForm, adresse: e.target.value})}
                />
              </div>
              <div className="button-group">
                <button
                  type="button"
                  className="button btn-cancel"
                  onClick={() => {
                    setShowFournisseurModal(false);
                    setEditingItem(null);
                    setFournisseurForm({ nom: "", contact: "", email: "", telephone: "", adresse: "" });
                  }}
                >
                  Annuler
                </button>
                <button
                  type="submit"
                  className="button btn-primary"
                  disabled={loading}
                >
                  {loading ? "Sauvegarde..." : (editingItem ? "Modifier" : "Ajouter")}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal Mouvement */}
      {showMouvementModal && (
        <div className="modal-overlay">
          <div className="modal-content">
            <h3 className="modal-header">Nouveau mouvement de stock</h3>
            <form onSubmit={handleMouvementSubmit}>
              <div className="form-group">
                <label className="form-label">Produit</label>
                <select
                  className="form-select"
                  value={mouvementForm.produit_id}
                  onChange={(e) => setMouvementForm({...mouvementForm, produit_id: e.target.value})}
                  required
                >
                  <option value="">Sélectionnez un produit</option>
                  {produits.map((produit) => (
                    <option key={produit.id} value={produit.id}>
                      {produit.nom}
                    </option>
                  ))}
                </select>
              </div>
              <div className="form-group">
                <label className="form-label">Type de mouvement</label>
                <select
                  className="form-select"
                  value={mouvementForm.type}
                  onChange={(e) => setMouvementForm({...mouvementForm, type: e.target.value})}
                  required
                >
                  <option value="entree">Entrée</option>
                  <option value="sortie">Sortie</option>
                  <option value="ajustement">Ajustement</option>
                </select>
              </div>
              <div className="form-group">
                <label className="form-label">Quantité</label>
                <input
                  type="number"
                  step="0.01"
                  className="form-input"
                  value={mouvementForm.quantite}
                  onChange={(e) => setMouvementForm({...mouvementForm, quantite: e.target.value})}
                  required
                />
              </div>
              <div className="form-group">
                <label className="form-label">Référence</label>
                <input
                  type="text"
                  className="form-input"
                  value={mouvementForm.reference}
                  onChange={(e) => setMouvementForm({...mouvementForm, reference: e.target.value})}
                />
              </div>
              <div className="form-group">
                <label className="form-label">Commentaire</label>
                <textarea
                  className="form-textarea"
                  value={mouvementForm.commentaire}
                  onChange={(e) => setMouvementForm({...mouvementForm, commentaire: e.target.value})}
                />
              </div>
              <div className="button-group">
                <button
                  type="button"
                  className="button btn-cancel"
                  onClick={() => {
                    setShowMouvementModal(false);
                    setMouvementForm({ produit_id: "", type: "entree", quantite: "", reference: "", commentaire: "" });
                  }}
                >
                  Annuler
                </button>
                <button
                  type="submit"
                  className="button btn-primary"
                  disabled={loading}
                >
                  {loading ? "Sauvegarde..." : "Créer"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal Recette */}
      {showRecetteModal && (
        <div className="modal-overlay">
          <div className="modal-content">
            <h3 className="modal-header">
              {editingItem ? "Modifier la recette" : "Ajouter une recette"}
            </h3>
            <form onSubmit={handleRecetteSubmit}>
              <div className="form-group">
                <label className="form-label">Nom de la recette</label>
                <input
                  type="text"
                  className="form-input"
                  value={recetteForm.nom}
                  onChange={(e) => setRecetteForm({...recetteForm, nom: e.target.value})}
                  required
                />
              </div>
              <div className="form-group">
                <label className="form-label">Description</label>
                <textarea
                  className="form-textarea"
                  value={recetteForm.description}
                  onChange={(e) => setRecetteForm({...recetteForm, description: e.target.value})}
                />
              </div>
              <div className="form-group">
                <label className="form-label">Catégorie</label>
                <select
                  className="form-select"
                  value={recetteForm.categorie}
                  onChange={(e) => setRecetteForm({...recetteForm, categorie: e.target.value})}
                >
                  <option value="">Sélectionnez une catégorie</option>
                  <option value="entrée">Entrée</option>
                  <option value="plat">Plat</option>
                  <option value="dessert">Dessert</option>
                </select>
              </div>
              <div className="form-group">
                <label className="form-label">Nombre de portions</label>
                <input
                  type="number"
                  className="form-input"
                  value={recetteForm.portions}
                  onChange={(e) => setRecetteForm({...recetteForm, portions: e.target.value})}
                  required
                />
              </div>
              <div className="form-group">
                <label className="form-label">Temps de préparation (minutes)</label>
                <input
                  type="number"
                  className="form-input"
                  value={recetteForm.temps_preparation}
                  onChange={(e) => setRecetteForm({...recetteForm, temps_preparation: e.target.value})}
                />
              </div>
              <div className="form-group">
                <label className="form-label">Prix de vente (€)</label>
                <input
                  type="number"
                  step="0.01"
                  className="form-input"
                  value={recetteForm.prix_vente}
                  onChange={(e) => setRecetteForm({...recetteForm, prix_vente: e.target.value})}
                />
              </div>

              {/* Gestion des ingrédients */}
              <div className="form-group">
                <label className="form-label">Ingrédients</label>
                
                {/* Liste des ingrédients actuels */}
                <div style={{marginBottom: '15px'}}>
                  {recetteForm.ingredients.map((ingredient, index) => (
                    <div key={index} style={{display: 'flex', alignItems: 'center', marginBottom: '8px', padding: '8px', background: '#f8f7f4', borderRadius: '5px'}}>
                      <span style={{flex: 1}}>
                        {ingredient.produit_nom} - {ingredient.quantite} {ingredient.unite}
                      </span>
                      <button
                        type="button"
                        className="button"
                        style={{fontSize: '0.7rem', padding: '4px 8px', background: '#e53e3e', color: 'white'}}
                        onClick={() => removeIngredient(index)}
                      >
                        ✕
                      </button>
                    </div>
                  ))}
                </div>

                {/* Formulaire d'ajout d'ingrédient */}
                <div style={{display: 'flex', gap: '10px', alignItems: 'end'}}>
                  <div style={{flex: 1}}>
                    <select
                      className="form-select"
                      value={ingredientForm.produit_id}
                      onChange={(e) => setIngredientForm({...ingredientForm, produit_id: e.target.value})}
                    >
                      <option value="">Sélectionnez un produit</option>
                      {produits.map((produit) => (
                        <option key={produit.id} value={produit.id}>
                          {produit.nom}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div style={{width: '100px'}}>
                    <input
                      type="number"
                      step="0.01"
                      className="form-input"
                      placeholder="Quantité"
                      value={ingredientForm.quantite}
                      onChange={(e) => setIngredientForm({...ingredientForm, quantite: e.target.value})}
                    />
                  </div>
                  <div style={{width: '80px'}}>
                    <input
                      type="text"
                      className="form-input"
                      placeholder="Unité"
                      value={ingredientForm.unite}
                      onChange={(e) => setIngredientForm({...ingredientForm, unite: e.target.value})}
                    />
                  </div>
                  <button
                    type="button"
                    className="button btn-primary"
                    onClick={addIngredient}
                    style={{minWidth: '80px'}}
                  >
                    Ajouter
                  </button>
                </div>
              </div>

              <div className="button-group">
                <button
                  type="button"
                  className="button btn-cancel"
                  onClick={() => {
                    setShowRecetteModal(false);
                    setEditingItem(null);
                    resetRecetteForm();
                  }}
                >
                  Annuler
                </button>
                <button
                  type="submit"
                  className="button btn-primary"
                  disabled={loading}
                >
                  {loading ? "Sauvegarde..." : (editingItem ? "Modifier" : "Ajouter")}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal OCR */}
      {showOcrModal && (
        <div className="modal-overlay">
          <div className="modal-content">
            <h3 className="modal-header">Upload Document OCR</h3>
            
            <div className="form-group">
              <label className="form-label">Type de document</label>
              <select
                className="form-select"
                value={ocrType}
                onChange={(e) => setOcrType(e.target.value)}
              >
                <option value="z_report">Rapport Z</option>
                <option value="facture_fournisseur">Facture Fournisseur</option>
              </select>
            </div>

            <div className="form-group">
              <label className="form-label">Fichier image</label>
              <input
                type="file"
                accept="image/*"
                className="form-input"
                onChange={handleOcrFileSelect}
              />
            </div>

            {ocrPreview && (
              <div className="form-group">
                <label className="form-label">Aperçu</label>
                <img
                  src={ocrPreview}
                  alt="Aperçu du document"
                  style={{maxWidth: '100%', maxHeight: '200px', objectFit: 'contain', border: '1px solid #ddd', borderRadius: '5px'}}
                />
              </div>
            )}

            {ocrResult && (
              <div className="form-group">
                <label className="form-label">Données extraites</label>
                <pre style={{background: '#f5f5f5', padding: '10px', borderRadius: '5px', fontSize: '0.8rem', maxHeight: '150px', overflow: 'auto'}}>
                  {JSON.stringify(ocrResult, null, 2)}
                </pre>
              </div>
            )}

            <div className="button-group">
              <button
                type="button"
                className="button btn-cancel"
                onClick={() => {
                  setShowOcrModal(false);
                  resetOcrModal();
                }}
              >
                Annuler
              </button>
              <button
                type="button"
                className="button btn-primary"
                onClick={handleOcrUpload}
                disabled={processingOcr || !ocrFile}
              >
                {processingOcr ? "Traitement..." : "Traiter"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;