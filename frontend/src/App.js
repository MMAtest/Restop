import React, { useState, useEffect } from "react";
import "./App.css";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function App() {
  const [activeTab, setActiveTab] = useState("dashboard");
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

  // Import Recettes Excel
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
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center">
              <h1 className="text-2xl font-bold text-gray-900">🍽️ Gestion des Stocks Restaurant</h1>
            </div>
            <div className="flex space-x-2">
              <button
                onClick={handleExport}
                className="bg-green-600 text-white px-4 py-2 rounded-md hover:bg-green-700 transition-colors"
              >
                📊 Exporter Excel
              </button>
              <label className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 transition-colors cursor-pointer">
                📁 Importer Excel
                <input type="file" accept=".xlsx,.xls" onChange={handleImport} className="hidden" />
              </label>
            </div>
          </div>
        </div>
      </header>

      {/* Navigation */}
      <nav className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex space-x-8">
            {[
              { id: "dashboard", label: "📊 Tableau de bord" },
              { id: "stocks", label: "📦 Stocks" },
              { id: "produits", label: "🥘 Produits" },
              { id: "fournisseurs", label: "🏪 Fournisseurs" },
              { id: "recettes", label: "👨‍🍳 Recettes" },
              { id: "ocr", label: "📱 OCR Documents" },
              { id: "mouvements", label: "📋 Mouvements" }
            ].map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`py-3 px-1 border-b-2 font-medium text-sm ${
                  activeTab === tab.id
                    ? "border-blue-500 text-blue-600"
                    : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>
        </div>
      </nav>

      {/* Contenu principal */}
      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        
        {/* Dashboard */}
        {activeTab === "dashboard" && (
          <div className="px-4 py-6 sm:px-0">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
              <div className="bg-white overflow-hidden shadow rounded-lg">
                <div className="p-5">
                  <div className="flex items-center">
                    <div className="flex-shrink-0">
                      <span className="text-2xl">🥘</span>
                    </div>
                    <div className="ml-5 w-0 flex-1">
                      <dl>
                        <dt className="text-sm font-medium text-gray-500 truncate">Total Produits</dt>
                        <dd className="text-lg font-medium text-gray-900">{dashboardStats.total_produits || 0}</dd>
                      </dl>
                    </div>
                  </div>
                </div>
              </div>

              <div className="bg-white overflow-hidden shadow rounded-lg">
                <div className="p-5">
                  <div className="flex items-center">
                    <div className="flex-shrink-0">
                      <span className="text-2xl">🏪</span>
                    </div>
                    <div className="ml-5 w-0 flex-1">
                      <dl>
                        <dt className="text-sm font-medium text-gray-500 truncate">Fournisseurs</dt>
                        <dd className="text-lg font-medium text-gray-900">{dashboardStats.total_fournisseurs || 0}</dd>
                      </dl>
                    </div>
                  </div>
                </div>
              </div>

              <div className="bg-white overflow-hidden shadow rounded-lg">
                <div className="p-5">
                  <div className="flex items-center">
                    <div className="flex-shrink-0">
                      <span className="text-2xl">⚠️</span>
                    </div>
                    <div className="ml-5 w-0 flex-1">
                      <dl>
                        <dt className="text-sm font-medium text-gray-500 truncate">Stocks Faibles</dt>
                        <dd className="text-lg font-medium text-red-600">{dashboardStats.stocks_faibles || 0}</dd>
                      </dl>
                    </div>
                  </div>
                </div>
              </div>

              <div className="bg-white overflow-hidden shadow rounded-lg">
                <div className="p-5">
                  <div className="flex items-center">
                    <div className="flex-shrink-0">
                      <span className="text-2xl">🔄</span>
                    </div>
                    <div className="ml-5 w-0 flex-1">
                      <dl>
                        <dt className="text-sm font-medium text-gray-500 truncate">Stocks Récents</dt>
                        <dd className="text-lg font-medium text-green-600">{dashboardStats.stocks_recents || 0}</dd>
                      </dl>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Derniers mouvements */}
            <div className="bg-white shadow rounded-lg">
              <div className="px-4 py-5 sm:p-6">
                <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">Derniers Mouvements</h3>
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Produit</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Type</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Quantité</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Date</th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {mouvements.map((mouvement) => (
                        <tr key={mouvement.id}>
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                            {mouvement.produit_nom || "Produit inconnu"}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                              mouvement.type === 'entree' ? 'bg-green-100 text-green-800' :
                              mouvement.type === 'sortie' ? 'bg-red-100 text-red-800' :
                              'bg-blue-100 text-blue-800'
                            }`}>
                              {mouvement.type}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            {mouvement.quantite}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                            {new Date(mouvement.date).toLocaleDateString('fr-FR')}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Stocks */}
        {activeTab === "stocks" && (
          <div className="px-4 py-6 sm:px-0">
            <div className="sm:flex sm:items-center mb-6">
              <div className="sm:flex-auto">
                <h1 className="text-xl font-semibold text-gray-900">Gestion des Stocks</h1>
                <p className="mt-2 text-sm text-gray-700">
                  Vue d'ensemble des niveaux de stock actuels
                </p>
              </div>
              <div className="mt-4 sm:mt-0 sm:ml-16 sm:flex-none">
                <button
                  onClick={() => setShowMouvementModal(true)}
                  className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 transition-colors"
                >
                  + Nouveau Mouvement
                </button>
              </div>
            </div>

            <div className="bg-white shadow rounded-lg overflow-hidden">
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Produit</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Quantité Actuelle</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Quantité Min</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Quantité Max</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Statut</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Dernière MAJ</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {stocks.map((stock) => {
                      const isLowStock = stock.quantite_actuelle <= stock.quantite_min;
                      const produit = produits.find(p => p.id === stock.produit_id);
                      const unite = getDisplayUnit(produit?.unite);
                      
                      return (
                        <tr key={stock.id}>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div>
                              <div className="text-sm font-medium text-gray-900">
                                {stock.produit_nom || "Produit inconnu"}
                              </div>
                              {produit && (
                                <div className="text-xs text-gray-500">
                                  Catégorie: {produit.categorie || 'Non définie'}
                                </div>
                              )}
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="text-sm font-medium text-gray-900">
                              {formatQuantity(stock.quantite_actuelle, unite)}
                            </div>
                            <div className="text-xs text-gray-500">
                              Actuel
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="text-sm text-gray-500">
                              {formatQuantity(stock.quantite_min, unite)}
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="text-sm text-gray-500">
                              {stock.quantite_max ? 
                                formatQuantity(stock.quantite_max, unite) : 
                                'Non défini'}
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                              isLowStock ? 'bg-red-100 text-red-800' : 
                              stock.quantite_actuelle <= stock.quantite_min * 1.5 ? 'bg-yellow-100 text-yellow-800' :
                              'bg-green-100 text-green-800'
                            }`}>
                              {isLowStock ? "🔴 Stock faible" : 
                               stock.quantite_actuelle <= stock.quantite_min * 1.5 ? "⚠️ Attention" :
                               "✅ Normal"}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                            {new Date(stock.derniere_maj).toLocaleDateString('fr-FR', {
                              day: '2-digit',
                              month: '2-digit',
                              year: '2-digit',
                              hour: '2-digit',
                              minute: '2-digit'
                            })}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* Produits */}
        {activeTab === "produits" && (
          <div className="px-4 py-6 sm:px-0">
            <div className="sm:flex sm:items-center mb-6">
              <div className="sm:flex-auto">
                <h1 className="text-xl font-semibold text-gray-900">Gestion des Produits</h1>
                <p className="mt-2 text-sm text-gray-700">
                  Gérez votre catalogue de produits
                </p>
              </div>
              <div className="mt-4 sm:mt-0 sm:ml-16 sm:flex-none">
                <button
                  onClick={() => setShowProduitModal(true)}
                  className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 transition-colors"
                >
                  + Nouveau Produit
                </button>
              </div>
            </div>

            <div className="bg-white shadow rounded-lg overflow-hidden">
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Nom</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Catégorie</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Unité</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Prix Achat</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Fournisseur</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {produits.map((produit) => (
                      <tr key={produit.id}>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div>
                            <div className="text-sm font-medium text-gray-900">{produit.nom}</div>
                            <div className="text-sm text-gray-500">{produit.description}</div>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {produit.categorie || "-"}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {produit.unite}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {produit.prix_achat ? `${produit.prix_achat}€` : "-"}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {produit.fournisseur_nom || "-"}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                          <button 
                            onClick={() => handleEdit(produit, 'produit')}
                            className="text-blue-600 hover:text-blue-900 mr-3"
                          >
                            Modifier
                          </button>
                          <button 
                            onClick={() => handleDelete(produit.id, 'produit')}
                            className="text-red-600 hover:text-red-900"
                          >
                            Supprimer
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* Fournisseurs */}
        {activeTab === "fournisseurs" && (
          <div className="px-4 py-6 sm:px-0">
            <div className="sm:flex sm:items-center mb-6">
              <div className="sm:flex-auto">
                <h1 className="text-xl font-semibold text-gray-900">Gestion des Fournisseurs</h1>
                <p className="mt-2 text-sm text-gray-700">
                  Gérez vos contacts fournisseurs
                </p>
              </div>
              <div className="mt-4 sm:mt-0 sm:ml-16 sm:flex-none">
                <button
                  onClick={() => setShowFournisseurModal(true)}
                  className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 transition-colors"
                >
                  + Nouveau Fournisseur
                </button>
              </div>
            </div>

            <div className="bg-white shadow rounded-lg overflow-hidden">
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Nom</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Contact</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Email</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Téléphone</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {fournisseurs.map((fournisseur) => (
                      <tr key={fournisseur.id}>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm font-medium text-gray-900">{fournisseur.nom}</div>
                          <div className="text-sm text-gray-500">{fournisseur.adresse}</div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {fournisseur.contact || "-"}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {fournisseur.email || "-"}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {fournisseur.telephone || "-"}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                          <button 
                            onClick={() => handleEdit(fournisseur, 'fournisseur')}
                            className="text-blue-600 hover:text-blue-900 mr-3"
                          >
                            Modifier
                          </button>
                          <button 
                            onClick={() => handleDelete(fournisseur.id, 'fournisseur')}
                            className="text-red-600 hover:text-red-900"
                          >
                            Supprimer
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* Recettes */}
        {activeTab === "recettes" && (
          <div className="px-4 py-6 sm:px-0">
            <div className="sm:flex sm:items-center mb-6">
              <div className="sm:flex-auto">
                <h1 className="text-xl font-semibold text-gray-900">Gestion des Recettes</h1>
                <p className="mt-2 text-sm text-gray-700">
                  Gérez vos recettes et calculez la production possible
                </p>
              </div>
              <div className="mt-4 sm:mt-0 sm:ml-16 sm:flex-none space-x-2">
                <button
                  onClick={handleExportRecettes}
                  className="bg-green-600 text-white px-4 py-2 rounded-md hover:bg-green-700 transition-colors"
                >
                  📊 Export Excel
                </button>
                <label className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 transition-colors cursor-pointer">
                  📁 Import Excel
                  <input type="file" accept=".xlsx,.xls" onChange={handleImportRecettes} className="hidden" />
                </label>
                <button
                  onClick={() => setShowRecetteModal(true)}
                  className="bg-orange-600 text-white px-4 py-2 rounded-md hover:bg-orange-700 transition-colors"
                >
                  + Nouvelle Recette
                </button>
              </div>
            </div>

            <div className="bg-white shadow rounded-lg overflow-hidden">
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Nom</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Catégorie</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Portions</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Temps</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Prix Vente</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Production Max</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {recettes.map((recette) => (
                      <tr key={recette.id}>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div>
                            <div className="text-sm font-medium text-gray-900">{recette.nom}</div>
                            <div className="text-sm text-gray-500">{recette.description}</div>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                            recette.categorie === 'entrée' ? 'bg-blue-100 text-blue-800' :
                            recette.categorie === 'plat' ? 'bg-green-100 text-green-800' :
                            recette.categorie === 'dessert' ? 'bg-pink-100 text-pink-800' :
                            'bg-gray-100 text-gray-800'
                          }`}>
                            {recette.categorie || 'Non défini'}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {recette.portions}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {recette.temps_preparation ? `${recette.temps_preparation} min` : '-'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {recette.prix_vente ? `${recette.prix_vente}€` : '-'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm">
                          <button
                            onClick={() => calculateProductionCapacity(recette.id)}
                            className="bg-indigo-600 text-white px-3 py-1 rounded text-xs hover:bg-indigo-700"
                          >
                            Calculer
                          </button>
                          {selectedRecette === recette.id && productionCapacity && (
                            <div className="mt-1 text-xs text-indigo-600 font-medium">
                              {productionCapacity.portions_max} portions
                            </div>
                          )}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                          <button 
                            onClick={() => handleEdit(recette, 'recette')}
                            className="text-blue-600 hover:text-blue-900 mr-3"
                          >
                            Modifier
                          </button>
                          <button 
                            onClick={() => handleDelete(recette.id, 'recette')}
                            className="text-red-600 hover:text-red-900"
                          >
                            Supprimer
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Détails de production capacity */}
            {productionCapacity && (
              <div className="mt-6 bg-indigo-50 border border-indigo-200 rounded-lg p-6">
                <h3 className="text-lg font-medium text-indigo-900 mb-4">
                  Capacité de production: {productionCapacity.recette_nom}
                </h3>
                <div className="bg-white rounded-md p-4 mb-4">
                  <div className="text-2xl font-bold text-indigo-600 text-center">
                    Vous pouvez préparer <span className="text-3xl">{productionCapacity.portions_max}</span> portions
                  </div>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {productionCapacity.ingredients_status.map((ingredient, index) => (
                    <div key={index} className={`p-4 rounded-lg border ${
                      ingredient.portions_possibles === 0 ? 'bg-red-50 border-red-200' :
                      ingredient.portions_possibles < productionCapacity.portions_max + 1 ? 'bg-yellow-50 border-yellow-200' :
                      'bg-green-50 border-green-200'
                    }`}>
                      <h4 className="font-medium text-gray-900">{ingredient.produit_nom}</h4>
                      <div className="mt-2 text-sm text-gray-600">
                        <div>Disponible: {ingredient.quantite_disponible} {ingredient.unite}</div>
                        <div>Requis/portion: {ingredient.quantite_requise_par_portion} {ingredient.unite}</div>
                        <div className="font-medium">
                          Max portions: {ingredient.portions_possibles === Infinity ? '∞' : ingredient.portions_possibles}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* OCR Documents */}
        {activeTab === "ocr" && (
          <div className="px-4 py-6 sm:px-0">
            <div className="sm:flex sm:items-center mb-6">
              <div className="sm:flex-auto">
                <h1 className="text-xl font-semibold text-gray-900">Traitement OCR des Documents</h1>
                <p className="mt-2 text-sm text-gray-700">
                  Uploadez vos rapports Z et factures fournisseurs pour extraction automatique des données
                </p>
              </div>
              <div className="mt-4 sm:mt-0 sm:ml-16 sm:flex-none">
                <button
                  onClick={() => setShowOcrModal(true)}
                  className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 transition-colors"
                >
                  📷 Nouveau Document
                </button>
              </div>
            </div>

            {/* Liste des documents traités */}
            <div className="bg-white shadow rounded-lg overflow-hidden">
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Document</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Type</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Date Upload</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Statut</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Données Extraites</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {documentsOcr.map((doc) => (
                      <tr key={doc.id}>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm font-medium text-gray-900">{doc.nom_fichier}</div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                            doc.type_document === 'z_report' ? 'bg-purple-100 text-purple-800' : 'bg-orange-100 text-orange-800'
                          }`}>
                            {doc.type_document === 'z_report' ? 'Rapport Z' : 'Facture'}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {new Date(doc.date_upload).toLocaleDateString('fr-FR')}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                            doc.statut === 'traite' ? 'bg-green-100 text-green-800' :
                            doc.statut === 'stock_traite' ? 'bg-blue-100 text-blue-800' :
                            doc.statut === 'erreur' ? 'bg-red-100 text-red-800' :
                            'bg-yellow-100 text-yellow-800'
                          }`}>
                            {doc.statut === 'traite' ? 'OCR Traité' : 
                             doc.statut === 'stock_traite' ? 'Stock Traité' :
                             doc.statut === 'erreur' ? 'Erreur' : 'En Attente'}
                          </span>
                        </td>
                        <td className="px-6 py-4 text-sm text-gray-500">
                          {doc.type_document === 'z_report' && doc.donnees_parsees ? (
                            <div>
                              <div>{doc.donnees_parsees.plats_vendus?.length || 0} plats détectés</div>
                              {doc.donnees_parsees.total_ca && <div>CA: {doc.donnees_parsees.total_ca}€</div>}
                            </div>
                          ) : doc.type_document === 'facture_fournisseur' && doc.donnees_parsees ? (
                            <div>
                              <div>{doc.donnees_parsees.produits?.length || 0} produits</div>
                              {doc.donnees_parsees.fournisseur && <div>{doc.donnees_parsees.fournisseur}</div>}
                            </div>
                          ) : 'Aucune donnée'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                          {doc.type_document === 'z_report' && doc.statut === 'traite' && (
                            <button 
                              onClick={() => handleProcessZReport(doc.id)}
                              disabled={loading}
                              className="text-blue-600 hover:text-blue-900 mr-3 disabled:opacity-50"
                            >
                              🔄 Traiter Stock
                            </button>
                          )}
                          <button 
                            onClick={() => window.open(`data:application/json,${encodeURIComponent(JSON.stringify(doc.donnees_parsees, null, 2))}`, '_blank')}
                            className="text-green-600 hover:text-green-900 mr-3"
                          >
                            👁️ Voir
                          </button>
                        </td>
                      </tr>
                    ))}
                    {documentsOcr.length === 0 && (
                      <tr>
                        <td colSpan="6" className="px-6 py-4 text-center text-gray-500">
                          Aucun document traité. Uploadez votre premier document !
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* Mouvements */}
        {activeTab === "mouvements" && (
          <div className="px-4 py-6 sm:px-0">
            <div className="sm:flex sm:items-center mb-6">
              <div className="sm:flex-auto">
                <h1 className="text-xl font-semibold text-gray-900">Historique des Mouvements</h1>
                <p className="mt-2 text-sm text-gray-700">
                  Suivi complet des entrées et sorties de stock
                </p>
              </div>
            </div>

            <div className="bg-white shadow rounded-lg overflow-hidden">
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Date</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Produit</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Type</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Quantité</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Référence</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Commentaire</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {mouvements.map((mouvement) => (
                      <tr key={mouvement.id}>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {new Date(mouvement.date).toLocaleString('fr-FR')}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                          {mouvement.produit_nom || "Produit inconnu"}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                            mouvement.type === 'entree' ? 'bg-green-100 text-green-800' :
                            mouvement.type === 'sortie' ? 'bg-red-100 text-red-800' :
                            'bg-blue-100 text-blue-800'
                          }`}>
                            {mouvement.type}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {mouvement.quantite}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {mouvement.reference || "-"}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {mouvement.commentaire || "-"}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}
      </main>

      {/* Modal Produit */}
      {showProduitModal && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <h3 className="text-lg font-medium text-gray-900 mb-4">
                {editingItem ? "Modifier le produit" : "Nouveau produit"}
              </h3>
              <form onSubmit={handleProduitSubmit} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Nom *</label>
                  <input
                    type="text"
                    required
                    value={produitForm.nom}
                    onChange={(e) => setProduitForm({...produitForm, nom: e.target.value})}
                    className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Description</label>
                  <textarea
                    value={produitForm.description}
                    onChange={(e) => setProduitForm({...produitForm, description: e.target.value})}
                    className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Catégorie</label>
                  <input
                    type="text"
                    value={produitForm.categorie}
                    onChange={(e) => setProduitForm({...produitForm, categorie: e.target.value})}
                    className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Unité *</label>
                  <select
                    required
                    value={produitForm.unite}
                    onChange={(e) => setProduitForm({...produitForm, unite: e.target.value})}
                    className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="">Sélectionner</option>
                    <option value="kg">kg</option>
                    <option value="g">g</option>
                    <option value="L">L</option>
                    <option value="mL">mL</option>
                    <option value="pièce">pièce</option>
                    <option value="boîte">boîte</option>
                    <option value="paquet">paquet</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Prix d'achat (€)</label>
                  <input
                    type="number"
                    step="0.01"
                    value={produitForm.prix_achat}
                    onChange={(e) => setProduitForm({...produitForm, prix_achat: e.target.value})}
                    className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Fournisseur</label>
                  <select
                    value={produitForm.fournisseur_id}
                    onChange={(e) => setProduitForm({...produitForm, fournisseur_id: e.target.value})}
                    className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="">Aucun fournisseur</option>
                    {fournisseurs.map(f => (
                      <option key={f.id} value={f.id}>{f.nom}</option>
                    ))}
                  </select>
                </div>
                <div className="flex justify-end space-x-3 pt-4">
                  <button
                    type="button"
                    onClick={() => {
                      setShowProduitModal(false);
                      setEditingItem(null);
                      setProduitForm({ nom: "", description: "", categorie: "", unite: "", prix_achat: "", fournisseur_id: "" });
                    }}
                    className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50"
                  >
                    Annuler
                  </button>
                  <button
                    type="submit"
                    disabled={loading}
                    className="px-4 py-2 bg-blue-600 border border-transparent rounded-md text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
                  >
                    {loading ? "Sauvegarde..." : "Sauvegarder"}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}

      {/* Modal Fournisseur */}
      {showFournisseurModal && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <h3 className="text-lg font-medium text-gray-900 mb-4">
                {editingItem ? "Modifier le fournisseur" : "Nouveau fournisseur"}
              </h3>
              <form onSubmit={handleFournisseurSubmit} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Nom *</label>
                  <input
                    type="text"
                    required
                    value={fournisseurForm.nom}
                    onChange={(e) => setFournisseurForm({...fournisseurForm, nom: e.target.value})}
                    className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Contact</label>
                  <input
                    type="text"
                    value={fournisseurForm.contact}
                    onChange={(e) => setFournisseurForm({...fournisseurForm, contact: e.target.value})}
                    className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Email</label>
                  <input
                    type="email"
                    value={fournisseurForm.email}
                    onChange={(e) => setFournisseurForm({...fournisseurForm, email: e.target.value})}
                    className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Téléphone</label>
                  <input
                    type="tel"
                    value={fournisseurForm.telephone}
                    onChange={(e) => setFournisseurForm({...fournisseurForm, telephone: e.target.value})}
                    className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Adresse</label>
                  <textarea
                    value={fournisseurForm.adresse}
                    onChange={(e) => setFournisseurForm({...fournisseurForm, adresse: e.target.value})}
                    className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                <div className="flex justify-end space-x-3 pt-4">
                  <button
                    type="button"
                    onClick={() => {
                      setShowFournisseurModal(false);
                      setEditingItem(null);
                      setFournisseurForm({ nom: "", contact: "", email: "", telephone: "", adresse: "" });
                    }}
                    className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50"
                  >
                    Annuler
                  </button>
                  <button
                    type="submit"
                    disabled={loading}
                    className="px-4 py-2 bg-blue-600 border border-transparent rounded-md text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
                  >
                    {loading ? "Sauvegarde..." : "Sauvegarder"}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}

      {/* Modal Mouvement */}
      {showMouvementModal && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Nouveau mouvement de stock</h3>
              <form onSubmit={handleMouvementSubmit} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Produit *</label>
                  <select
                    required
                    value={mouvementForm.produit_id}
                    onChange={(e) => setMouvementForm({...mouvementForm, produit_id: e.target.value})}
                    className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="">Sélectionner un produit</option>
                    {produits.map(p => (
                      <option key={p.id} value={p.id}>{p.nom}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Type *</label>
                  <select
                    required
                    value={mouvementForm.type}
                    onChange={(e) => setMouvementForm({...mouvementForm, type: e.target.value})}
                    className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="entree">Entrée</option>
                    <option value="sortie">Sortie</option>
                    <option value="ajustement">Ajustement</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Quantité *</label>
                  <input
                    type="number"
                    step="0.01"
                    required
                    value={mouvementForm.quantite}
                    onChange={(e) => setMouvementForm({...mouvementForm, quantite: e.target.value})}
                    className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Référence</label>
                  <input
                    type="text"
                    value={mouvementForm.reference}
                    onChange={(e) => setMouvementForm({...mouvementForm, reference: e.target.value})}
                    className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Numéro de facture, bon de livraison..."
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Commentaire</label>
                  <textarea
                    value={mouvementForm.commentaire}
                    onChange={(e) => setMouvementForm({...mouvementForm, commentaire: e.target.value})}
                    className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Commentaire optionnel..."
                  />
                </div>
                <div className="flex justify-end space-x-3 pt-4">
                  <button
                    type="button"
                    onClick={() => {
                      setShowMouvementModal(false);
                      setMouvementForm({ produit_id: "", type: "entree", quantite: "", reference: "", commentaire: "" });
                    }}
                    className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50"
                  >
                    Annuler
                  </button>
                  <button
                    type="submit"
                    disabled={loading}
                    className="px-4 py-2 bg-blue-600 border border-transparent rounded-md text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
                  >
                    {loading ? "Sauvegarde..." : "Sauvegarder"}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}

      {/* Modal Recette */}
      {showRecetteModal && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-10 mx-auto p-5 border w-full max-w-4xl shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <h3 className="text-lg font-medium text-gray-900 mb-4">
                {editingItem ? "Modifier la recette" : "Nouvelle recette"}
              </h3>
              <form onSubmit={handleRecetteSubmit} className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Nom *</label>
                    <input
                      type="text"
                      required
                      value={recetteForm.nom}
                      onChange={(e) => setRecetteForm({...recetteForm, nom: e.target.value})}
                      className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-orange-500 focus:border-orange-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Catégorie</label>
                    <select
                      value={recetteForm.categorie}
                      onChange={(e) => setRecetteForm({...recetteForm, categorie: e.target.value})}
                      className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-orange-500 focus:border-orange-500"
                    >
                      <option value="">Sélectionner</option>
                      <option value="entrée">Entrée</option>
                      <option value="plat">Plat</option>
                      <option value="dessert">Dessert</option>
                      <option value="boisson">Boisson</option>
                    </select>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">Description</label>
                  <textarea
                    value={recetteForm.description}
                    onChange={(e) => setRecetteForm({...recetteForm, description: e.target.value})}
                    className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-orange-500 focus:border-orange-500"
                    rows="2"
                  />
                </div>

                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Portions *</label>
                    <input
                      type="number"
                      required
                      min="1"
                      value={recetteForm.portions}
                      onChange={(e) => setRecetteForm({...recetteForm, portions: e.target.value})}
                      className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-orange-500 focus:border-orange-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Temps (min)</label>
                    <input
                      type="number"
                      min="0"
                      value={recetteForm.temps_preparation}
                      onChange={(e) => setRecetteForm({...recetteForm, temps_preparation: e.target.value})}
                      className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-orange-500 focus:border-orange-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Prix vente (€)</label>
                    <input
                      type="number"
                      step="0.01"
                      min="0"
                      value={recetteForm.prix_vente}
                      onChange={(e) => setRecetteForm({...recetteForm, prix_vente: e.target.value})}
                      className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-orange-500 focus:border-orange-500"
                    />
                  </div>
                </div>

                {/* Section Ingrédients */}
                <div className="border-t pt-6">
                  <h4 className="text-md font-medium text-gray-900 mb-4">Ingrédients</h4>
                  
                  {/* Ajouter un ingrédient */}
                  <div className="grid grid-cols-4 gap-4 mb-4 p-4 bg-gray-50 rounded-md">
                    <div>
                      <label className="block text-sm font-medium text-gray-700">Produit</label>
                      <select
                        value={ingredientForm.produit_id}
                        onChange={(e) => setIngredientForm({...ingredientForm, produit_id: e.target.value})}
                        className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-orange-500 focus:border-orange-500 text-sm"
                      >
                        <option value="">Sélectionner</option>
                        {produits.map(p => (
                          <option key={p.id} value={p.id}>{p.nom}</option>
                        ))}
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700">Quantité</label>
                      <input
                        type="number"
                        step="0.01"
                        value={ingredientForm.quantite}
                        onChange={(e) => setIngredientForm({...ingredientForm, quantite: e.target.value})}
                        className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-orange-500 focus:border-orange-500 text-sm"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700">Unité</label>
                      <input
                        type="text"
                        value={ingredientForm.unite}
                        onChange={(e) => setIngredientForm({...ingredientForm, unite: e.target.value})}
                        className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-orange-500 focus:border-orange-500 text-sm"
                        placeholder="kg, g, L, mL..."
                      />
                    </div>
                    <div className="flex items-end">
                      <button
                        type="button"
                        onClick={addIngredient}
                        className="w-full bg-green-600 text-white px-3 py-2 rounded-md text-sm hover:bg-green-700"
                      >
                        Ajouter
                      </button>
                    </div>
                  </div>

                  {/* Liste des ingrédients */}
                  {recetteForm.ingredients.length > 0 && (
                    <div className="space-y-2">
                      {recetteForm.ingredients.map((ingredient, index) => (
                        <div key={index} className="flex items-center justify-between p-3 bg-white border rounded-md">
                          <div className="flex-1 grid grid-cols-3 gap-4">
                            <div className="font-medium">{ingredient.produit_nom}</div>
                            <div>{ingredient.quantite} {ingredient.unite}</div>
                            <div></div>
                          </div>
                          <button
                            type="button"
                            onClick={() => removeIngredient(index)}
                            className="text-red-600 hover:text-red-800 ml-4"
                          >
                            Supprimer
                          </button>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">Instructions</label>
                  <textarea
                    value={recetteForm.instructions}
                    onChange={(e) => setRecetteForm({...recetteForm, instructions: e.target.value})}
                    className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-orange-500 focus:border-orange-500"
                    rows="4"
                    placeholder="Étapes de préparation..."
                  />
                </div>

                <div className="flex justify-end space-x-3 pt-4 border-t">
                  <button
                    type="button"
                    onClick={() => {
                      setShowRecetteModal(false);
                      setEditingItem(null);
                      resetRecetteForm();
                    }}
                    className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50"
                  >
                    Annuler
                  </button>
                  <button
                    type="submit"
                    disabled={loading}
                    className="px-4 py-2 bg-orange-600 border border-transparent rounded-md text-sm font-medium text-white hover:bg-orange-700 disabled:opacity-50"
                  >
                    {loading ? "Sauvegarde..." : "Sauvegarder"}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}

      {/* Modal OCR */}
      {showOcrModal && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-10 mx-auto p-5 border w-full max-w-2xl shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <h3 className="text-lg font-medium text-gray-900 mb-4">
                Traitement OCR de Document
              </h3>
              
              {!ocrResult ? (
                <div className="space-y-6">
                  {/* Sélection du type de document */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Type de Document</label>
                    <div className="flex space-x-4">
                      <label className="flex items-center">
                        <input
                          type="radio"
                          value="z_report"
                          checked={ocrType === "z_report"}
                          onChange={(e) => setOcrType(e.target.value)}
                          className="mr-2"
                        />
                        <span className="text-sm">📊 Rapport Z (TPV)</span>
                      </label>
                      <label className="flex items-center">
                        <input
                          type="radio"
                          value="facture_fournisseur"
                          checked={ocrType === "facture_fournisseur"}
                          onChange={(e) => setOcrType(e.target.value)}
                          className="mr-2"
                        />
                        <span className="text-sm">🧾 Facture Fournisseur</span>
                      </label>
                    </div>
                  </div>

                  {/* Zone de drop et upload */}
                  <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
                    {ocrPreview ? (
                      <div className="space-y-4">
                        <img 
                          src={ocrPreview} 
                          alt="Aperçu" 
                          className="mx-auto max-h-64 rounded border"
                        />
                        <div>
                          <p className="text-sm text-gray-600 mb-2">Fichier sélectionné: {ocrFile?.name}</p>
                          <button
                            onClick={() => {
                              setOcrFile(null);
                              setOcrPreview(null);
                            }}
                            className="text-red-600 hover:text-red-800 text-sm"
                          >
                            Changer de fichier
                          </button>
                        </div>
                      </div>
                    ) : (
                      <div>
                        <div className="text-6xl text-gray-400 mb-4">📷</div>
                        <p className="text-lg font-medium text-gray-900 mb-2">
                          Sélectionnez une image à traiter
                        </p>
                        <p className="text-sm text-gray-500 mb-4">
                          Formats supportés: JPG, PNG, JPEG
                        </p>
                        <label className="cursor-pointer bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 inline-block">
                          📁 Choisir un fichier
                          <input 
                            type="file" 
                            accept="image/*" 
                            onChange={handleOcrFileSelect}
                            className="hidden"
                          />
                        </label>
                      </div>
                    )}
                  </div>

                  {/* Instructions */}
                  <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
                    <h4 className="text-sm font-medium text-blue-900 mb-2">💡 Conseils pour un meilleur OCR :</h4>
                    <ul className="text-sm text-blue-800 space-y-1">
                      <li>• Assurez-vous que le texte est lisible et bien éclairé</li>
                      <li>• Évitez les reflets et les ombres</li>
                      <li>• Tenez l'appareil photo bien droit</li>
                      <li>• Pour les rapports Z: capturez la section des ventes par plat</li>
                    </ul>
                  </div>
                </div>
              ) : (
                /* Résultats OCR */
                <div className="space-y-4">
                  <div className="bg-green-50 border border-green-200 rounded-md p-4">
                    <h4 className="text-sm font-medium text-green-900 mb-2">✅ Traitement réussi !</h4>
                    <p className="text-sm text-green-800">{ocrResult.message}</p>
                  </div>

                  <div>
                    <h4 className="text-sm font-medium text-gray-900 mb-2">Données extraites :</h4>
                    <div className="bg-gray-50 rounded-md p-4 max-h-64 overflow-y-auto">
                      <pre className="text-xs text-gray-700 whitespace-pre-wrap">
                        {JSON.stringify(ocrResult.donnees_parsees, null, 2)}
                      </pre>
                    </div>
                  </div>

                  {ocrType === 'z_report' && ocrResult.donnees_parsees.plats_vendus?.length > 0 && (
                    <div className="bg-yellow-50 border border-yellow-200 rounded-md p-4">
                      <p className="text-sm text-yellow-800">
                        💡 Vous pouvez maintenant fermer cette fenêtre et aller dans l'onglet "OCR Documents" pour traiter automatiquement les stocks.
                      </p>
                    </div>
                  )}
                </div>
              )}

              {/* Boutons */}
              <div className="flex justify-end space-x-3 pt-6 border-t mt-6">
                <button
                  type="button"
                  onClick={() => {
                    setShowOcrModal(false);
                    resetOcrModal();
                  }}
                  className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50"
                >
                  Fermer
                </button>
                {!ocrResult && ocrFile && (
                  <button
                    onClick={handleOcrUpload}
                    disabled={processingOcr}
                    className="px-4 py-2 bg-blue-600 border border-transparent rounded-md text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
                  >
                    {processingOcr ? "⏳ Traitement..." : "🔍 Analyser"}
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;