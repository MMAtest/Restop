import React, { useState, useEffect } from "react";
import "./App.css";
import axios from "axios";
import HistoriqueZPage from "./pages/HistoriqueZPage";
import AnalyticsPage from "./pages/AnalyticsPage";
import AdvancedStockPage from "./pages/AdvancedStockPage";
import UserManagementPage from "./pages/UserManagementPage";
import DataGridsPage from "./pages/DataGridsPage";
import PurchaseOrderPage from "./pages/PurchaseOrderPage";
import DateRangePicker from "./components/DateRangePicker";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function App() {
  const [activeTab, setActiveTab] = useState("dashboard");
  const [activeProductionTab, setActiveProductionTab] = useState("produits");
  const [activeHistoriqueTab, setActiveHistoriqueTab] = useState("ventes");
  const [activeStockTab, setActiveStockTab] = useState("stocks");
  const [activeDashboardTab, setActiveDashboardTab] = useState("ventes"); // Nouveau state pour les onglets dashboard
  const [showBurgerMenu, setShowBurgerMenu] = useState(false);
  const [isDarkMode, setIsDarkMode] = useState(false); // State pour le thème (false = light par défaut)
  
  // États pour la sélection de dates et données filtrées
  const [selectedDateRange, setSelectedDateRange] = useState(null);
  const [filteredAnalytics, setFilteredAnalytics] = useState({
    caTotal: 27959.75,
    commandes: 21,
    panierMoyen: 1331.42,
    topRecettes: [
      { nom: "Rigatoni à la truffe", ventes: 2418, portions: 78 },
      { nom: "Fleurs de courgettes", ventes: 1911, portions: 91 },
      { nom: "Souris d'agneau", ventes: 1872, portions: 52 }
    ],
    ventesParCategorie: {
      plats: 6201,
      boissons: 4987,
      desserts: 2156
    }
  });
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
  const [showPreviewModal, setShowPreviewModal] = useState(false); // Nouvelle modal d'aperçu
  const [previewDocument, setPreviewDocument] = useState(null); // Document en cours d'aperçu
  const [editingItem, setEditingItem] = useState(null);
  const [selectedRecette, setSelectedRecette] = useState(null);
  const [productionCapacity, setProductionCapacity] = useState(null);

  // États OCR
  const [ocrFile, setOcrFile] = useState(null);
  const [ocrPreview, setOcrPreview] = useState(null);
  const [ocrType, setOcrType] = useState("z_report");
  const [ocrResult, setOcrResult] = useState(null);
  const [processingOcr, setProcessingOcr] = useState(false);
  const [selectedDocument, setSelectedDocument] = useState(null); // Nouveau: pour sélection document

  // Formulaires
  // Aperçu OCR - modal détaillée
  const [previewDocFull, setPreviewDocFull] = useState(null);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [previewTab, setPreviewTab] = useState('overview');

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

  // Fonction pour ajuster le stock d'un produit spécifique
  const handleAjusterStock = (stock) => {
    setMouvementForm({
      produit_id: stock.produit_id,
      type: "ajustement",
      quantite: "",
      reference: `ADJ-${Date.now()}`,
      commentaire: `Ajustement stock pour ${stock.produit_nom}`
    });
    setShowMouvementModal(true);
  };

  // Fonction pour basculer entre dark/light mode
  const toggleTheme = () => {
    const newTheme = !isDarkMode;
    setIsDarkMode(newTheme);
    if (newTheme) {
      document.documentElement.setAttribute('data-theme', 'dark');
      localStorage.setItem('theme', 'dark');
    } else {
      document.documentElement.removeAttribute('data-theme');
      localStorage.setItem('theme', 'light');
    }
  };

  // Fonction pour calculer les données selon la période sélectionnée
  const calculateAnalyticsForPeriod = (dateRange) => {
    if (!dateRange) return;

    console.log("Calcul pour période:", dateRange.label, "de", dateRange.startDate, "à", dateRange.endDate);

    // Données de base (pour aujourd'hui)
    const baseDayData = {
      caTotal: 27959.75,
      commandes: 21,
      panierMoyen: 1331.42,
      topRecettes: [
        { nom: "Rigatoni à la truffe", ventes: 2418, portions: 78 },
        { nom: "Fleurs de courgettes", ventes: 1911, portions: 91 },
        { nom: "Souris d'agneau", ventes: 1872, portions: 52 }
      ],
      ventesParCategorie: {
        plats: 6201,
        boissons: 4987,
        desserts: 2156
      }
    };

    // Calculer le multiplicateur selon la période avec des valeurs distinctes
    let periodMultiplier = 1;
    const daysDiff = Math.ceil((dateRange.endDate - dateRange.startDate) / (1000 * 60 * 60 * 24)) + 1;
    
    switch (true) {
      case dateRange.label.includes('Aujourd\'hui'):
        periodMultiplier = 1;
        break;
      case dateRange.label.includes('Hier'):
        periodMultiplier = 0.92; // Légèrement moins qu'aujourd'hui
        break;
      case dateRange.label.includes('Cette semaine'):
        periodMultiplier = daysDiff * 0.88; // Environ 5-6 jours de données
        break;
      case dateRange.label.includes('Semaine dernière'):
        periodMultiplier = 7 * 0.85; // 7 jours complets, légèrement moins
        break;
      case dateRange.label.includes('Ce mois'):
        periodMultiplier = daysDiff * 0.82; // Données du mois jusqu'à aujourd'hui
        break;
      case dateRange.label.includes('Mois dernier'):
        periodMultiplier = 30 * 0.80; // Mois complet, données historiques
        break;
      default:
        // Période personnalisée - utiliser le nombre de jours
        periodMultiplier = daysDiff * 0.87;
        break;
    }
    
    console.log("Période:", dateRange.label, "Multiplicateur:", periodMultiplier, "Jours:", daysDiff);
    
    const analytics = {
      caTotal: Math.round(baseDayData.caTotal * periodMultiplier * 100) / 100,
      commandes: Math.round(baseDayData.commandes * periodMultiplier),
      panierMoyen: Math.round((baseDayData.caTotal * periodMultiplier) / (baseDayData.commandes * periodMultiplier) * 100) / 100,
      topRecettes: baseDayData.topRecettes.map(recette => ({
        ...recette,
        ventes: Math.round(recette.ventes * periodMultiplier),
        portions: Math.round(recette.portions * periodMultiplier)
      })),
      ventesParCategorie: {
        plats: Math.round(baseDayData.ventesParCategorie.plats * periodMultiplier),
        boissons: Math.round(baseDayData.ventesParCategorie.boissons * periodMultiplier),
        desserts: Math.round(baseDayData.ventesParCategorie.desserts * periodMultiplier)
      }
    };

    console.log("Nouvelles données calculées:", analytics);
    setFilteredAnalytics(analytics);
  };

  // Gérer le changement de période
  const handleDateRangeChange = (dateRange) => {
    setSelectedDateRange(dateRange);
    calculateAnalyticsForPeriod(dateRange);
  };

  // Initialiser le thème au chargement
  useEffect(() => {
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme) {
      const isDark = savedTheme === 'dark';
      setIsDarkMode(isDark);
      if (isDark) {
        document.documentElement.setAttribute('data-theme', 'dark');
      } else {
        document.documentElement.removeAttribute('data-theme');
      }
    } else {
      // Par défaut : mode light
      document.documentElement.removeAttribute('data-theme');
      setIsDarkMode(false);
    }
  }, []);
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
      // Vérifier si c'est une image ou un PDF
      if (!file.type.startsWith('image/') && file.type !== 'application/pdf') {
        alert('Veuillez sélectionner un fichier image ou PDF');
        return;
      }
      
      setOcrFile(file);
      
      // Créer un aperçu selon le type de fichier
      if (file.type === 'application/pdf') {
        // Pour les PDF, afficher une icône et le nom du fichier
        setOcrPreview(`PDF: ${file.name}`);
      } else {
        // Pour les images, créer un aperçu visuel
        const reader = new FileReader();
        reader.onload = (e) => {
          setOcrPreview(e.target.result);
        };
        reader.readAsDataURL(file);
      }
    }
  };

  const handlePreviewDocument = async (document) => {
    try {
      setPreviewLoading(true);
      // fetch full document (with base64) from backend
      const { data } = await axios.get(`${API}/ocr/document/${document.id}`);
      setPreviewDocFull(data);
      setPreviewDocument(document);
      setPreviewTab('overview');
      setShowPreviewModal(true);
    } catch (e) {
      console.error('Erreur chargement du document OCR complet:', e);
      setPreviewDocument(document);
      setShowPreviewModal(true);
    } finally {
      setPreviewLoading(false);
    }
  };

  const closePreviewModal = () => {
    setShowPreviewModal(false);
    setPreviewDocument(null);
  };

  // Utilitaires d'affichage
  const formatEuro = (amount) => {
    if (amount === undefined || amount === null || isNaN(amount)) return '—';
    try {
      return new Intl.NumberFormat('fr-FR', { style: 'currency', currency: 'EUR' }).format(Number(amount));
    } catch {
      return `${amount}€`;
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
      
      // Fermer la pop-up d'aperçu si elle est ouverte
      if (showPreviewModal) {
        setTimeout(() => {
          closePreviewModal();
        }, 1000); // Délai de 1 seconde pour que l'utilisateur voie le succès
      }
      
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

  // Traitement Auto OCR
  const handleTraitementAuto = async () => {
    try {
      setLoading(true);
      // Cette fonctionnalité traiterait automatiquement tous les documents en attente
      const documentsEnAttente = documentsOcr.filter(doc => !doc.donnees_parsees || Object.keys(doc.donnees_parsees).length === 0);
      
      if (documentsEnAttente.length === 0) {
        alert("✅ Tous les documents ont déjà été traités !");
        return;
      }

      const confirmation = window.confirm(`🔄 TRAITEMENT AUTOMATIQUE:\n\nTraiter automatiquement ${documentsEnAttente.length} documents en attente ?\n\n(Cette opération peut prendre plusieurs minutes)`);
      
      if (confirmation) {
        alert(`🚀 Traitement automatique démarré pour ${documentsEnAttente.length} documents.\n\nLe traitement se fait en arrière-plan.\nVous recevrez une notification à la fin.`);
        
        // Ici on pourrait lancer un traitement batch en arrière-plan
        // Pour l'instant, on simule juste l'action
        
        setTimeout(() => {
          alert("✅ Traitement automatique terminé !\nConsultez l'historique pour voir les résultats.");
          fetchDocumentsOcr();
        }, 2000);
      }
    } catch (error) {
      console.error("Erreur traitement auto:", error);
      alert("Erreur lors du traitement automatique");
    } finally {
      setLoading(false);
    }
  };

  // Sélectionner document dans l'historique
  const handleSelectDocument = (doc) => {
    setSelectedDocument(doc);
    
    // Afficher les détails du document sélectionné
    const details = `📄 DOCUMENT SÉLECTIONNÉ:\n\n` +
      `📁 Fichier: ${doc.nom_fichier}\n` +
      `📅 Date: ${new Date(doc.date_upload).toLocaleDateString('fr-FR')}\n` +
      `📝 Type: ${doc.type_document === 'z_report' ? 'Rapport Z' : 'Facture Fournisseur'}\n\n`;

    if (doc.donnees_parsees && Object.keys(doc.donnees_parsees).length > 0) {
      const donnees = doc.donnees_parsees;
      let detailsDonnees = "📊 DONNÉES EXTRAITES:\n\n";
      
      if (doc.type_document === 'z_report') {
        detailsDonnees += `📅 Date rapport: ${donnees.date || 'Non trouvée'}\n`;
        detailsDonnees += `💰 CA Total: ${donnees.total_ca || 'Non trouvé'}€\n`;
        detailsDonnees += `🍽️ Plats vendus: ${donnees.plats_vendus?.length || 0}\n\n`;
        
        if (donnees.plats_vendus && donnees.plats_vendus.length > 0) {
          detailsDonnees += "🍽️ TOP 5 PLATS:\n";
          donnees.plats_vendus.slice(0, 5).forEach((plat, i) => {
            detailsDonnees += `${i + 1}. ${plat.quantite}x ${plat.nom}\n`;
          });
        }
      } else {
        detailsDonnees += `🏪 Fournisseur: ${donnees.fournisseur || 'Non trouvé'}\n`;
        detailsDonnees += `📅 Date: ${donnees.date || 'Non trouvée'}\n`;
    setPreviewDocFull(null);
    setPreviewLoading(false);
    setPreviewTab('overview');

        detailsDonnees += `🔢 N° facture: ${donnees.numero_facture || 'Non trouvé'}\n`;
        detailsDonnees += `💰 Total: ${donnees.total_ttc || donnees.total_ht || 'Non trouvé'}€\n`;
        detailsDonnees += `📦 Produits: ${donnees.produits?.length || 0}\n`;
      }
      
      alert(details + detailsDonnees);
    } else {
      alert(details + "❌ Aucune donnée extraite pour ce document.");
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
    <div className="App">
      {/* Header Mobile */}
      <div className="header">
        <h1>ResTop : La Table d'Augustine</h1>
        {/* Menu Burger */}
        <div className="burger-menu">
          <button onClick={() => setShowBurgerMenu(!showBurgerMenu)}>
            ☰
          </button>
          
          {/* Menu déroulant */}
          {showBurgerMenu && (
            <div className="burger-dropdown">
              <button 
                className="button" 
                onClick={() => {
                  setActiveTab("users");
                  setShowBurgerMenu(false);
                }}
                style={{width: '100%', marginBottom: '8px'}}
              >
                👑 Utilisateurs
              </button>
              
              <button 
                className="button secondary" 
                onClick={() => {
                  toggleTheme();
                  setShowBurgerMenu(false);
                }}
                style={{width: '100%', marginBottom: '8px'}}
              >
                {isDarkMode ? '☀️ Mode Clair' : '🌙 Mode Sombre'}
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Top Navigation Tabs (Analytics) */}
      {activeTab === "dashboard" && (
        <div className="top-nav-tabs">
          <button 
            className={`top-nav-tab ${activeDashboardTab === "ventes" ? "active" : ""}`}
            onClick={() => setActiveDashboardTab("ventes")}
          >
            VENTES
          </button>
          <button 
            className={`top-nav-tab ${activeDashboardTab === "alertes" ? "active" : ""}`}
            onClick={() => setActiveDashboardTab("alertes")}
          >
            ALERTES
          </button>
          <button 
            className={`top-nav-tab ${activeDashboardTab === "couts" ? "active" : ""}`}
            onClick={() => setActiveDashboardTab("couts")}
          >
            COÛTS
          </button>
          <button 
            className={`top-nav-tab ${activeDashboardTab === "rentabilite" ? "active" : ""}`}
            onClick={() => setActiveDashboardTab("rentabilite")}
          >
            RENTABILITÉ
          </button>
        </div>
      )}

      {/* Content Wrapper */}
      <div className="content-wrapper">
        <div id="dashboard" className={`wireframe-section ${activeTab === "dashboard" ? "active" : ""}`}>
          
          {/* Sélecteur de période - visible sur tous les onglets */}
          <DateRangePicker 
            onDateRangeChange={handleDateRangeChange}
          />

          {/* ONGLET VENTES */}
          {activeDashboardTab === "ventes" && (
            <div className="section-card">
              <div className="section-title">
                💰 Analyse des Ventes
                {selectedDateRange && (
                  <span style={{ 
                    fontSize: '12px', 
                    color: 'var(--color-text-muted)',
                    fontWeight: 'normal',
                    marginLeft: 'var(--spacing-sm)'
                  }}>
                    - {selectedDateRange.label}
                  </span>
                )}
              </div>
              
              {/* KPIs Ventes */}
              <div className="kpi-grid">
                <div className="kpi-card">
                  <div className="icon">💰</div>
                  <div className="title">CA Total</div>
                  <div className="value">{filteredAnalytics.caTotal.toLocaleString('fr-FR')} €</div>
                </div>
                
                <div className="kpi-card">
                  <div className="icon">🛒</div>
                  <div className="title">Commandes</div>
                  <div className="value">{filteredAnalytics.commandes}</div>
                </div>
                
                <div className="kpi-card">
                  <div className="icon">🧾</div>
                  <div className="title">Panier Moyen</div>
                  <div className="value">{filteredAnalytics.panierMoyen.toLocaleString('fr-FR')} €</div>
                </div>
              </div>

              {/* Top Recettes */}
              <div className="item-list">
                <div className="section-title">🍽️ Top Recettes</div>
                {filteredAnalytics.topRecettes.map((recette, index) => (
                  <div key={index} className="item-row">
                    <div className="item-info">
                      <div className="item-name">🍝 {recette.nom}</div>
                      <div className="item-details">{recette.portions} portions vendues</div>
                    </div>
                    <div className="item-value">{recette.ventes.toLocaleString('fr-FR')} €</div>
                  </div>
                ))}
              </div>

              {/* Ventes par catégorie */}
              <div className="kpi-grid">
                <div className="kpi-card">
                  <div className="icon">🍽️</div>
                  <div className="title">Plats</div>
                  <div className="value">{filteredAnalytics.ventesParCategorie.plats.toLocaleString('fr-FR')} €</div>
                </div>
                
                <div className="kpi-card">
                  <div className="icon">🍷</div>
                  <div className="title">Boissons</div>
                  <div className="value">{filteredAnalytics.ventesParCategorie.boissons.toLocaleString('fr-FR')} €</div>
                </div>
                
                <div className="kpi-card">
                  <div className="icon">🍰</div>
                  <div className="title">Desserts</div>
                  <div className="value">{filteredAnalytics.ventesParCategorie.desserts.toLocaleString('fr-FR')} €</div>
                </div>
              </div>
            </div>
          )}

          {/* ONGLET ALERTES */}
          {activeDashboardTab === "alertes" && (
            <div className="section-card">
              <div className="section-title">
                ⚠️ Alertes & Notifications
                {selectedDateRange && (
                  <span style={{ 
                    fontSize: '12px', 
                    color: 'var(--color-text-muted)',
                    fontWeight: 'normal',
                    marginLeft: 'var(--spacing-sm)'
                  }}>
                    - {selectedDateRange.label}
                  </span>
                )}
              </div>
              
              {/* Alertes de stock faible */}
              <div className="alert-section">
                <div className="alert-header">
                  <div className="alert-title">Stock Faible</div>
                  <div className="alert-count">3</div>
                </div>
                
                <div className="alert-card">
                  <div className="alert-item">
                    <div className="product-info">
                      <div className="product-name">🍅 Tomates cerises</div>
                      <div className="stock-info">
                        Stock: <span className="stock-current">1.2 kg</span> / Min: <span className="stock-min">5.0 kg</span>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="alert-card">
                  <div className="alert-item">
                    <div className="product-info">
                      <div className="product-name">🥬 Salade verte</div>
                      <div className="stock-info">
                        Stock: <span className="stock-current">5.3 kg</span> / Min: <span className="stock-min">10.0 kg</span>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="alert-card warning">
                  <div className="alert-item">
                    <div className="product-info">
                      <div className="product-name">🧀 Fromage de chèvre</div>
                      <div className="stock-info">
                        Stock: <span className="stock-current">3.3 kg</span> / Min: <span className="stock-min">8.0 kg</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Alertes basées sur la période */}
              <div className="alert-section">
                <div className="alert-header">
                  <div className="alert-title">Problèmes Période</div>
                  <div className="alert-count">{filteredAnalytics.commandes < 10 ? '1' : '0'}</div>
                </div>
                {filteredAnalytics.commandes < 10 ? (
                  <div className="alert-card">
                    <div className="alert-item">
                      <div className="product-info">
                        <div className="product-name">📉 Activité Faible</div>
                        <div className="stock-info">
                          Seulement {filteredAnalytics.commandes} commandes sur la période
                        </div>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="section-card">
                    <p style={{color: 'var(--color-success-green)', textAlign: 'center', padding: '20px'}}>
                      ✅ Activité normale pour la période
                    </p>
                  </div>
                )}
              </div>

              {/* Alertes d'expiration */}
              <div className="alert-section">
                <div className="alert-header">
                  <div className="alert-title">Produits Expirés</div>
                  <div className="alert-count">0</div>
                </div>
                <div className="section-card">
                  <p style={{color: 'var(--color-success-green)', textAlign: 'center', padding: '20px'}}>
                    ✅ Aucun produit expiré actuellement
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* ONGLET COÛTS */}
          {activeDashboardTab === "couts" && (
            <div className="section-card">
              <div className="section-title">
                💰 Analyse des Coûts
                {selectedDateRange && (
                  <span style={{ 
                    fontSize: '12px', 
                    color: 'var(--color-text-muted)',
                    fontWeight: 'normal',
                    marginLeft: 'var(--spacing-sm)'
                  }}>
                    - {selectedDateRange.label}
                  </span>
                )}
              </div>
              
              <div className="kpi-grid">
                <div className="kpi-card">
                  <div className="icon">💰</div>
                  <div className="title">Valeur Stock</div>
                  <div className="value">16 326,05 €</div>
                </div>
                
                <div className="kpi-card">
                  <div className="icon">📊</div>
                  <div className="title">Coût Moyen</div>
                  <div className="value">{(filteredAnalytics.caTotal / filteredAnalytics.commandes * 0.32).toFixed(2)} €</div>
                </div>
                
                <div className="kpi-card">
                  <div className="icon">📉</div>
                  <div className="title">Déchets</div>
                  <div className="value warning">{Math.round(filteredAnalytics.caTotal * 0.045)} €</div>
                </div>
              </div>

              <div className="item-list">
                <div className="section-title">Plus Coûteux</div>
                <div className="item-row">
                  <div className="item-info">
                    <div className="item-name">🥩 Côte de bœuf</div>
                    <div className="item-details">Viandes Premium</div>
                  </div>
                  <div className="item-value">847,20 €</div>
                </div>
                <div className="item-row">
                  <div className="item-info">
                    <div className="item-name">🍄 Truffe noire</div>
                    <div className="item-details">Épices & Aromates</div>
                  </div>
                  <div className="item-value">692,80 €</div>
                </div>
                <div className="item-row">
                  <div className="item-info">
                    <div className="item-name">🦞 Homard</div>
                    <div className="item-details">Fruits de mer</div>
                  </div>
                  <div className="item-value">543,15 €</div>
                </div>
              </div>

              {/* Analyse des coûts basée sur la période */}
              <div className="kpi-grid">
                <div className="kpi-card">
                  <div className="icon">💸</div>
                  <div className="title">Coûts Totaux</div>
                  <div className="value">{Math.round(filteredAnalytics.caTotal * 0.35).toLocaleString('fr-FR')} €</div>
                </div>
                
                <div className="kpi-card">
                  <div className="icon">📈</div>
                  <div className="title">Ratio Coûts/CA</div>
                  <div className="value">35%</div>
                </div>
                
                <div className="kpi-card">
                  <div className="icon">⚖️</div>
                  <div className="title">Économies</div>
                  <div className="value positive">{Math.round(filteredAnalytics.caTotal * 0.08).toLocaleString('fr-FR')} €</div>
                </div>
              </div>
            </div>
          )}

          {/* ONGLET RENTABILITÉ */}
          {activeDashboardTab === "rentabilite" && (
            <div className="section-card">
              <div className="section-title">
                📈 Analyse de Rentabilité
                {selectedDateRange && (
                  <span style={{ 
                    fontSize: '12px', 
                    color: 'var(--color-text-muted)',
                    fontWeight: 'normal',
                    marginLeft: 'var(--spacing-sm)'
                  }}>
                    - {selectedDateRange.label}
                  </span>
                )}
              </div>
              
              <div className="kpi-grid">
                <div className="kpi-card">
                  <div className="icon">💹</div>
                  <div className="title">Marge Globale</div>
                  <div className="value positive">68,5%</div>
                </div>
                
                <div className="kpi-card">
                  <div className="icon">🎯</div>
                  <div className="title">ROI Période</div>
                  <div className="value positive">+{((filteredAnalytics.caTotal / 100000) * 12.3).toFixed(1)}%</div>
                </div>
                
                <div className="kpi-card">
                  <div className="icon">📊</div>
                  <div className="title">Profit Net</div>
                  <div className="value positive">{Math.round(filteredAnalytics.caTotal * 0.685).toLocaleString('fr-FR')} €</div>
                </div>
              </div>

              <div className="item-list">
                <div className="section-title">Top Plats Rentables</div>
                {filteredAnalytics.topRecettes.map((recette, index) => (
                  <div key={index} className="item-row">
                    <div className="item-info">
                      <div className="item-name">🍝 {recette.nom}</div>
                      <div className="item-details">Marge: {76 + index * 2}% • {recette.portions} portions vendues</div>
                    </div>
                    <div className="item-value positive">{recette.ventes.toLocaleString('fr-FR')} €</div>
                  </div>
                ))}
              </div>

              {/* Analyse comparative selon la période */}
              <div className="kpi-grid">
                <div className="kpi-card">
                  <div className="icon">💰</div>
                  <div className="title">Revenus</div>
                  <div className="value">{filteredAnalytics.caTotal.toLocaleString('fr-FR')} €</div>
                </div>
                
                <div className="kpi-card">
                  <div className="icon">💸</div>
                  <div className="title">Charges</div>
                  <div className="value">{Math.round(filteredAnalytics.caTotal * 0.315).toLocaleString('fr-FR')} €</div>
                </div>
                
                <div className="kpi-card">
                  <div className="icon">💵</div>
                  <div className="title">Bénéfice</div>
                  <div className="value positive">{Math.round(filteredAnalytics.caTotal * 0.685).toLocaleString('fr-FR')} €</div>
                </div>
              </div>
            </div>
          )}

        </div>

        {/* GESTION DE STOCKS - avec OCR et Grilles de données */}
        <div id="stocks" className={`wireframe-section ${activeTab === "stocks" ? "active" : ""}`}>
          <div className="wireframe">
            <h2>📦 Gestion de Stocks Complète</h2>
            
            {/* Sous-navigation Stocks */}
            <div className="sub-nav-tabs">
              <button 
                className="button" 
                onClick={() => setActiveStockTab('stocks')}
                style={{
                  background: activeStockTab === 'stocks' ? 'var(--color-primary-blue)' : 'var(--color-background-card-light)',
                  color: activeStockTab === 'stocks' ? 'white' : 'var(--color-text-secondary)'
                }}
              >
                📦 Stocks
              </button>
              <button 
                className="button" 
                onClick={() => setActiveStockTab('ocr')}
                style={{
                  background: activeStockTab === 'ocr' ? 'var(--color-primary-blue)' : 'var(--color-background-card-light)',
                  color: activeStockTab === 'ocr' ? 'white' : 'var(--color-text-secondary)'
                }}
              >
                📱 OCR
              </button>
              <button 
                className="button" 
                onClick={() => setActiveStockTab('datagrids')}
                style={{
                  background: activeStockTab === 'datagrids' ? 'var(--color-primary-blue)' : 'var(--color-background-card-light)',
                  color: activeStockTab === 'datagrids' ? 'white' : 'var(--color-text-secondary)'
                }}
              >
                📋 Grilles Données
              </button>
            </div>

            {/* ONGLET STOCKS */}
            <div className={`production-tab ${activeStockTab === 'stocks' ? 'active' : ''}`}>
              <div className="section-card">
                <div className="section-title">📦 Gestion des Stocks</div>
                
                {/* Actions rapides */}
                <div style={{display: 'flex', gap: '10px', marginBottom: '20px', flexWrap: 'wrap'}}>
                  <button className="button" onClick={() => setShowProduitModal(true)}>➕ Nouveau Produit</button>
                  <button className="button" onClick={handleExport}>📊 Rapport Stock</button>
                  <button className="button warning" onClick={handleVoirAlertes}>⚠️ Alertes</button>
                  <button className="button" onClick={handlePageInventaire}>📱 Inventaire</button>
                </div>

                {/* KPIs Stocks */}
                <div className="kpi-grid">
                  <div className="kpi-card">
                    <div className="icon">📈</div>
                    <div className="title">Stock Total</div>
                    <div className="value">385 produits</div>
                  </div>
                  
                  <div className="kpi-card">
                    <div className="icon">⚠️</div>
                    <div className="title">Stocks Critiques</div>
                    <div className="value warning">42 alertes</div>
                  </div>
                  
                  <div className="kpi-card">
                    <div className="icon">💰</div>
                    <div className="title">Valeur Totale</div>
                    <div className="value">16 326,05 €</div>
                  </div>
                </div>

                {/* Liste des produits en stock */}
                <div className="item-list">
                  <div className="section-title">📋 Produits en Stock</div>
                  
                  {stocks.slice(0, 5).map((stock, index) => {
                    const isLowStock = stock.quantite_actuelle <= stock.quantite_min;
                    const produit = produits.find(p => p.id === stock.produit_id);
                    const unite = getDisplayUnit(produit?.unite);
                    
                    return (
                      <div key={index} className="item-row">
                        <div className="item-info">
                          <div className="item-name">
                            {produit?.categorie === 'légumes' ? '🍅' : 
                             produit?.categorie === 'épices' ? '🧄' : 
                             produit?.categorie === 'huiles' ? '🫒' : 
                             produit?.categorie === 'fromages' ? '🧀' : '📦'} {stock.produit_nom}
                          </div>
                          <div className="item-details">
                            Stock: {formatQuantity(stock.quantite_actuelle, unite)} / Min: {formatQuantity(stock.quantite_min, unite)}
                            {isLowStock && <span style={{color: 'var(--color-danger-red)', marginLeft: '8px'}}>⚠️ Critique</span>}
                          </div>
                        </div>
                        <div className="item-actions">
                          <button className="button small" onClick={() => handleEdit(produit, 'produit')}>✏️ Produit</button>
                          <button className="button small success" onClick={() => handleAjusterStock(stock)}>📊 Ajuster</button>
                          <button className="button small" onClick={() => setShowMouvementModal(true)}>🛒 Commander</button>
                        </div>
                      </div>
                    );
                  })}
                  
                  {stocks.length === 0 && (
                    <div style={{textAlign: 'center', padding: '40px', color: 'var(--color-text-muted)'}}>
                      <div style={{fontSize: '48px', marginBottom: '15px'}}>📦</div>
                      <p>Aucun stock disponible</p>
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* ONGLET OCR */}
            <div className={`production-tab ${activeStockTab === 'ocr' ? 'active' : ''}`}>
              <div className="section-card">
                <div className="section-title">📱 Module OCR</div>
                
                {/* Actions OCR */}
                <div style={{display: 'flex', gap: '10px', marginBottom: '20px', flexWrap: 'wrap'}}>
                  <button className="button" onClick={() => setShowOcrModal(true)}>📁 Importer Document</button>
                  <button className="button" onClick={handleTraitementAuto} disabled={loading}>🔄 Traitement Auto</button>
                </div>

                {/* Historique des documents */}
                <div className="item-list">
                  <div className="section-title">📄 Historique des Documents</div>
                  {documentsOcr.slice(0, 5).map((doc, index) => (
                    <div key={index} className="item-row">
                      <div className="item-info">
                        <div className="item-name">{doc.nom_fichier}</div>
                        <div className="item-details">
                          {doc.type_document === 'z_report' ? '📊 Rapport Z' : '🧾 Facture'} - 
                          {new Date(doc.date_upload).toLocaleDateString('fr-FR')}
                        </div>
                      </div>
                      <div className="item-actions">
                        <button 
                          className="button small"
                          onClick={() => handlePreviewDocument(doc)}
                        >
                          👁️ Aperçu
                        </button>
                        {doc.type_document === 'z_report' && (
                          <button 
                            className="button small"
                            onClick={() => handleProcessZReport(doc.id)}
                          >
                            ⚡ Traiter
                          </button>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* ONGLET GRILLES DE DONNÉES */}
            <div className={`production-tab ${activeStockTab === 'datagrids' ? 'active' : ''}`}>
              <DataGridsPage />
            </div>
          </div>
        </div>

        {/* PRODUCTION - avec Historique */}
        <div id="production" className={`wireframe-section ${activeTab === "production" ? "active" : ""}`}>
          <div className="section-card">
            <div className="section-title">🍳 Production & Historique</div>
            
            {/* Sous-navigation Production */}
            <div className="sub-nav-tabs">
              <button 
                className="button" 
                onClick={() => setActiveProductionTab('produits')}
                style={{
                  background: activeProductionTab === 'produits' ? 'var(--color-primary-blue)' : 'var(--color-background-card-light)',
                  color: activeProductionTab === 'produits' ? 'white' : 'var(--color-text-secondary)'
                }}
              >
                🥕 Ingrédients
              </button>
              <button 
                className="button" 
                onClick={() => setActiveProductionTab('fournisseurs')}
                style={{
                  background: activeProductionTab === 'fournisseurs' ? 'var(--color-primary-blue)' : 'var(--color-background-card-light)',
                  color: activeProductionTab === 'fournisseurs' ? 'white' : 'var(--color-text-secondary)'
                }}
              >
                🚚 Fournisseurs
              </button>
              <button 
                className="button" 
                onClick={() => setActiveProductionTab('recettes')}
                style={{
                  background: activeProductionTab === 'recettes' ? 'var(--color-primary-blue)' : 'var(--color-background-card-light)',
                  color: activeProductionTab === 'recettes' ? 'white' : 'var(--color-text-secondary)'
                }}
              >
                📝 Plats & Recettes
              </button>
              <button 
                className="button" 
                onClick={() => setActiveProductionTab('historique')}
                style={{
                  background: activeProductionTab === 'historique' ? 'var(--color-primary-blue)' : 'var(--color-background-card-light)',
                  color: activeProductionTab === 'historique' ? 'white' : 'var(--color-text-secondary)'
                }}
              >
                📊 Historique
              </button>
            </div>

            {/* ONGLET PRODUITS */}
            {activeProductionTab === 'produits' && (
              <div className="item-list">
                <div className="section-title">🥕 Gestion des Ingrédients</div>
                
                <div style={{display: 'flex', gap: '10px', marginBottom: '20px', flexWrap: 'wrap'}}>
                  <button className="button" onClick={() => setShowProduitModal(true)}>➕ Nouveau Produit</button>
                  <button className="button" onClick={handleAnalyseProduits}>📊 Analyse Produits</button>
                  <button className="button" onClick={handleGenererEtiquettes}>🏷️ Étiquettes</button>
                </div>

                {produits.slice(0, 6).map((produit, index) => (
                  <div key={index} className="item-row">
                    <div className="item-info">
                      <div className="item-name">
                        {produit.categorie === 'entrée' ? '🥗' : 
                         produit.categorie === 'plats' ? '🍽️' : 
                         produit.categorie === 'desserts' ? '🍰' : 
                         produit.categorie === 'boissons' ? '🍷' : '📦'} {produit.nom}
                      </div>
                      <div className="item-details">
                        {produit.description} • Prix: {produit.prix_achat}€
                      </div>
                    </div>
                    <div className="item-actions">
                      <button className="button small" onClick={() => handleEdit(produit, 'produit')}>✏️ Éditer</button>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* ONGLET FOURNISSEURS */}
            {activeProductionTab === 'fournisseurs' && (
              <div className="item-list">
                <div className="section-title">🚚 Gestion des Fournisseurs</div>
                
                <div style={{display: 'flex', gap: '10px', marginBottom: '20px', flexWrap: 'wrap'}}>
                  <button className="button" onClick={() => setShowFournisseurModal(true)}>➕ Nouveau Fournisseur</button>
                  <button className="button">📊 Évaluation</button>
                </div>

                {fournisseurs.slice(0, 4).map((fournisseur, index) => (
                  <div key={index} className="item-row">
                    <div className="item-info">
                      <div className="item-name">🏪 {fournisseur.nom}</div>
                      <div className="item-details">
                        {fournisseur.email} • Tel: {fournisseur.telephone}
                      </div>
                    </div>
                    <div className="item-actions">
                      <button className="button small" onClick={() => handleEdit(fournisseur, 'fournisseur')}>✏️ Éditer</button>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* ONGLET RECETTES */}
            {activeProductionTab === 'recettes' && (
              <div className="item-list">
                <div className="section-title">📝 Plats & Recettes</div>
                
                <div style={{display: 'flex', gap: '10px', marginBottom: '20px', flexWrap: 'wrap'}}>
                  <button className="button">➕ Nouvelle Recette</button>
                  <button className="button">💰 Calculer Coûts</button>
                </div>

                {recettes.slice(0, 5).map((recette, index) => (
                  <div key={index} className="item-row">
                    <div className="item-info">
                      <div className="item-name">
                        {recette.categorie === 'entrée' ? '🥗' : 
                         recette.categorie === 'plats' ? '🍽️' : 
                         recette.categorie === 'desserts' ? '🍰' : '📝'} {recette.nom}
                      </div>
                      <div className="item-details">
                        Prix: {recette.prix_vente}€ • Marge: {recette.marge_beneficiaire || 'N/A'}%
                      </div>
                    </div>
                    <div className="item-actions">
                      <button className="button small" onClick={() => handleEdit(recette, 'recette')}>✏️ Éditer</button>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* ONGLET HISTORIQUE */}
            {activeProductionTab === 'historique' && (
              <div>
                <div className="section-title">📊 Historique des Opérations</div>
                <div className="item-list">
                  <div className="item-row">
                    <div className="item-info">
                      <div className="item-name">📊 Rapport Z - Service Déjeuner</div>
                      <div className="item-details">Aujourd'hui 12:30 • CA: 2 418,00€ • 78 couverts</div>
                    </div>
                    <div className="item-value positive">✅ Traité</div>
                  </div>
                  <div className="item-row">
                    <div className="item-info">
                      <div className="item-name">🛒 Commande Rungis</div>
                      <div className="item-details">Hier 14:20 • 247,30€ • 15 produits</div>
                    </div>
                    <div className="item-value">🚚 En cours</div>
                  </div>
                  <div className="item-row">
                    <div className="item-info">
                      <div className="item-name">📝 Nouvelle recette</div>
                      <div className="item-details">2 jours • Risotto aux champignons</div>
                    </div>
                    <div className="item-value positive">✅ Validée</div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* COMMANDES */}
        <div id="orders" className={`wireframe-section ${activeTab === "orders" ? "active" : ""}`}>
          <div className="section-card">
            <div className="section-title">🛒 Gestion des Commandes</div>
            
            {/* Actions commandes */}
            <div style={{display: 'flex', gap: '10px', marginBottom: '20px', flexWrap: 'wrap'}}>
              <button className="button">➕ Nouvelle Commande</button>
              <button className="button">📊 Historique</button>
              <button className="button">🚚 Suivi Livraisons</button>
            </div>

            {/* KPIs Commandes */}
            <div className="kpi-grid">
              <div className="kpi-card">
                <div className="icon">📦</div>
                <div className="title">Commandes Actives</div>
                <div className="value">7</div>
              </div>
              
              <div className="kpi-card">
                <div className="icon">🚚</div>
                <div className="title">En Livraison</div>
                <div className="value">3</div>
              </div>
              
              <div className="kpi-card">
                <div className="icon">💰</div>
                <div className="title">Montant Total</div>
                <div className="value">2 847,30 €</div>
              </div>
            </div>

            {/* Liste des commandes */}
            <div className="item-list">
              <div className="section-title">📋 Commandes Récentes</div>
              
              {fournisseurs.slice(0, 4).map((fournisseur, index) => (
                <div key={index} className="item-row">
                  <div className="item-info">
                    <div className="item-name">
                      🏪 CMD-2025-{String(90 + index).padStart(3, '0')} - {fournisseur.nom}
                    </div>
                    <div className="item-details">
                      {new Date(Date.now() - index * 24 * 60 * 60 * 1000).toLocaleDateString('fr-FR')} • 
                      Montant: €{(Math.random() * 500 + 100).toFixed(2)}
                    </div>
                  </div>
                  <div className="item-value positive">✅ Livrée</div>
                  <div className="item-actions">
                    <button className="button small">👁️ Détails</button>
                  </div>
                </div>
              ))}
              
              {fournisseurs.length === 0 && (
                <div style={{textAlign: 'center', padding: '40px', color: 'var(--color-text-muted)'}}>
                  <div style={{fontSize: '48px', marginBottom: '15px'}}>🛒</div>
                  <p>Aucune commande enregistrée</p>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* USER MANAGEMENT */}
        <div id="users" className={`wireframe-section ${activeTab === "users" ? "active" : ""}`}>
          <UserManagementPage />
        </div>

      </div>

      {/* Bottom Navigation */}
      <div className="bottom-navigation">
        <button 
          className={`bottom-nav-item ${activeTab === "dashboard" ? "active" : ""}`}
          onClick={() => setActiveTab("dashboard")}
        >
          <div className="bottom-nav-icon">🏠</div>
          <div className="bottom-nav-label">Home</div>
        </button>
        
        <button 
          className={`bottom-nav-item ${activeTab === "stocks" ? "active" : ""}`}
          onClick={() => {
            console.log("Clic sur STOCK, activeTab actuel:", activeTab);
            setActiveTab("stocks");
            console.log("activeTab changé vers: stocks");
          }}
        >
          <div className="bottom-nav-icon">📦</div>
          <div className="bottom-nav-label">Stock</div>
        </button>
        
        <button 
          className={`bottom-nav-item ${activeTab === "production" ? "active" : ""}`}
          onClick={() => setActiveTab("production")}
        >
          <div className="bottom-nav-icon">🍳</div>
          <div className="bottom-nav-label">Production</div>
        </button>
        
        <button 
          className={`bottom-nav-item ${activeTab === "orders" ? "active" : ""}`}
          onClick={() => setActiveTab("orders")}
        >
          <div className="bottom-nav-icon">🛒</div>
          <div className="bottom-nav-label">Orders</div>
        </button>
      </div>
      <div id="users" className={`wireframe-section ${activeTab === "users" ? "active" : ""}`}>
        <UserManagementPage />
      </div>

      {/* PROFESSIONAL DATA GRIDS */}
      <div id="datagrids" className={`wireframe-section ${activeTab === "datagrids" ? "active" : ""}`}>
        <DataGridsPage />
      </div>

      {/* PURCHASE ORDERS */}
      <div id="orders" className={`wireframe-section ${activeTab === "orders" ? "active" : ""}`}>
        <PurchaseOrderPage />
      </div>

      {/* OCR */}
      <div id="ocr" className={`wireframe-section ${activeTab === "ocr" ? "active" : ""}`}>
        <div className="wireframe">
          <h2>📱 Module OCR - Numérisation Factures</h2>
          <div className="layout two-column">
            <div className="sidebar">
              <h3 style={{color: '#d4af37', marginBottom: '15px'}}>Actions</h3>
              <button className="button" onClick={() => setShowOcrModal(true)}>📁 Importer Document</button>
              <button className="button" onClick={handleTraitementAuto} disabled={loading}>🔄 Traitement Auto</button>
              <h4 style={{color: '#d4af37', margin: '20px 0 10px'}}>Historique (Cliquez pour détails)</h4>
              <div style={{fontSize: '0.9rem'}}>
                {documentsOcr.slice(0, 5).map((doc, index) => (
                  <div 
                    key={index} 
                    style={{
                      padding: '8px', 
                      margin: '5px 0', 
                      background: selectedDocument?.id === doc.id ? 'rgba(212, 175, 55, 0.3)' : 'rgba(255,255,255,0.2)', 
                      borderRadius: '5px',
                      cursor: 'pointer',
                      border: selectedDocument?.id === doc.id ? '2px solid #d4af37' : 'none'
                    }}
                    onClick={() => handleSelectDocument(doc)}
                  >
                    <div style={{fontWeight: 'bold'}}>{doc.nom_fichier}</div>
                    <div style={{fontSize: '0.8rem', opacity: 0.8}}>
                      {doc.type_document === 'z_report' ? '📊 Rapport Z' : '🧾 Facture'} - 
                      {new Date(doc.date_upload).toLocaleDateString('fr-FR')}
                    </div>
                  </div>
                ))}
                {documentsOcr.length === 0 && (
                  <div style={{padding: '8px', margin: '5px 0', background: 'rgba(255,255,255,0.2)', borderRadius: '5px'}}>
                    Aucun document traité
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
                <div className="table-header">Données Extraites - Document Sélectionné</div>
                {selectedDocument ? (
                  <div>
                    <div className="table-row">
                      <span><strong>📁 Fichier:</strong> {selectedDocument.nom_fichier}</span>
                    </div>
                    <div className="table-row">
                      <span><strong>📝 Type:</strong> {selectedDocument.type_document === 'z_report' ? 'Rapport Z' : 'Facture Fournisseur'}</span>
                    </div>
                    <div className="table-row">
                      <span><strong>📅 Date upload:</strong> {new Date(selectedDocument.date_upload).toLocaleDateString('fr-FR')}</span>
                    </div>
                    
                    {selectedDocument.donnees_parsees && Object.keys(selectedDocument.donnees_parsees).length > 0 ? (
                      <>
                        {selectedDocument.type_document === 'z_report' && (
                          <>
                            <div className="table-row">
                              <span><strong>💰 CA Total:</strong> {
                                (selectedDocument.donnees_parsees.grand_total_sales ?? selectedDocument.donnees_parsees.total_ca ?? 'Non calculé')
                              }{(selectedDocument.donnees_parsees.grand_total_sales ?? selectedDocument.donnees_parsees.total_ca) ? '€' : ''}</span>
                            </div>
                            <div className="table-row">
                              <span><strong>🍽️ Plats vendus:</strong> {
                                (selectedDocument.donnees_parsees.items_by_category ? Object.values(selectedDocument.donnees_parsees.items_by_category).reduce((acc, arr) => acc + arr.reduce((s, it) => s + (Number(it.quantity_sold) || 0), 0), 0) : (selectedDocument.donnees_parsees.plats_vendus?.reduce((s, it) => s + (Number(it.quantite) || 0), 0) || 0))
                              } plats</span>
                            </div>
                          </>
                        )}
                        
                        {selectedDocument.type_document === 'facture_fournisseur' && (
                          <>
                            <div className="table-row">
                              <span><strong>🏪 Fournisseur:</strong> {selectedDocument.donnees_parsees.fournisseur || 'Non identifié'}</span>
                            </div>
                            <div className="table-row">
                              <span><strong>💰 Total:</strong> {selectedDocument.donnees_parsees.total_ttc || selectedDocument.donnees_parsees.total_ht || 'Non calculé'}€</span>
                            </div>
                            <div className="table-row">
                              <span><strong>📦 Produits:</strong> {selectedDocument.donnees_parsees.produits?.length || 0} produits</span>
                            </div>
                          </>
                        )}
                      </>
                    ) : (
                      <div className="table-row">
                        <span style={{color: '#e53e3e'}}>❌ Aucune donnée extraite - Document nécessite un retraitement</span>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="table-row">
                    <span style={{fontStyle: 'italic', color: '#4a5568'}}>
                      👆 Sélectionnez un document dans l'historique pour voir les données extraites
                    </span>
                  </div>
                )}
              </div>
              
              <div style={{textAlign: 'center', marginTop: '20px'}}>
                <button className="button" onClick={() => setShowOcrModal(true)}>✅ Valider</button>
                <button className="button" onClick={async () => {
                  if (!selectedDocument) {
                    alert('Veuillez d\'abord sélectionner un document dans l\'historique.');
                    return;
                  }
                  // Ouvrir l'aperçu côté OCR pour corriger
                  await handlePreviewDocument(selectedDocument);
                  setPreviewTab('sidebyside');
                }}>✏️ Corriger</button>
                <button className="button">💾 Enregistrer</button>
              </div>
            </div>
          </div>
        </div>
      </div>


      {/* SECTION PRODUCTION DUPLIQUÉE SUPPRIMÉE - PLUS DE CONTENU ICI */}

      {/* PREVIEW MODAL OCR */}
      {showPreviewModal && (
        <div style={{position:'fixed', inset:0, background:'rgba(0,0,0,0.5)', display:'flex', alignItems:'center', justifyContent:'center', zIndex:1000}}>
          <div style={{width:'90%', maxWidth:'1200px', maxHeight:'85vh', background:'#fff', borderRadius:'12px', overflow:'hidden', boxShadow:'0 10px 30px rgba(0,0,0,0.3)'}}>
            {/* Header */}
            <div style={{display:'flex', alignItems:'center', justifyContent:'space-between', padding:'12px 16px', background:'linear-gradient(135deg, var(--color-primary-solid), var(--color-primary-dark))', color:'#fff'}}>
              <div style={{display:'flex', alignItems:'center', gap:'10px'}}>
                <span style={{fontSize:'20px'}}>👁️</span>
                <div>
                  <div style={{fontWeight:'700'}}>Aperçu du document</div>
                  <div style={{fontSize:'12px', opacity:0.9}}>{previewDocument?.nom_fichier}</div>
                </div>
              </div>
              <button className="button" onClick={closePreviewModal} style={{background:'#fff', color:'var(--color-primary-solid)'}}>✖️ Fermer</button>
            </div>

            {/* Tabs */}
            <div style={{display:'flex', gap:'8px', padding:'10px 12px', borderBottom:'1px solid #eee'}}>
              {[
                {id:'overview', label:'Résumé'},
                {id:'sidebyside', label:'Document + Données'},
                {id:'items', label:'Liste complète'},
                {id:'raw', label:'Texte brut'},
                {id:'analyse', label:'Analyse'},
              ].map(tab => (
                <button key={tab.id} onClick={() => setPreviewTab(tab.id)} className="button" style={{
                  background: previewTab===tab.id ? 'var(--color-primary-solid)' : 'var(--color-beige)',
                  color: previewTab===tab.id ? '#fff' : 'var(--color-primary-solid)'
                }}>
                  {tab.label}
                </button>
              ))}
            </div>

            {/* Body */}
            <div style={{padding:'12px', overflow:'auto', maxHeight:'65vh'}}>
              {previewLoading && (
                <div style={{textAlign:'center', padding:'30px'}}>Chargement...</div>
              )}

              {!previewLoading && (
                <>
                  {/* Overview */}
                  {previewTab==='overview' && (
                    <div className="layout two-column" style={{gap:'12px'}}>
                      <div className="card">
                        <div className="card-title">Informations</div>
                        <div className="card-content">
                          <div>Type: {previewDocFull?.type_document === 'z_report' ? 'Rapport Z' : 'Facture Fournisseur'}</div>
                          <div>Date upload: {previewDocFull?.date_upload ? new Date(previewDocFull.date_upload).toLocaleString('fr-FR') : '-'}</div>
                          <div>Service: {previewDocFull?.donnees_parsees?.service || '-'}</div>
                          <div>CA Total: {previewDocFull?.donnees_parsees?.grand_total_sales || previewDocFull?.donnees_parsees?.total_ttc || '-'}</div>
                        </div>
                      </div>
                      <div className="card">
                        <div className="card-title">Status</div>
                        <div className="card-content">
                          <div>Statut: {previewDocFull?.statut}</div>
                          <div>Traité le: {previewDocFull?.date_traitement ? new Date(previewDocFull.date_traitement).toLocaleString('fr-FR') : '-'}</div>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Side by side */}
                  {previewTab==='sidebyside' && (
                    <div className="layout two-column" style={{gap:'12px'}}>
                      <div className="card" style={{height:'60vh', overflow:'auto'}}>
                        <div className="card-title">Document</div>
                        <div className="card-content" style={{display:'flex', alignItems:'center', justifyContent:'center'}}>
                          {previewDocFull?.file_type==='pdf' ? (
                            <div style={{textAlign:'center'}}>
                              <div style={{fontSize:'48px'}}>📄</div>
                              <div>PDF chargé: {previewDocument?.nom_fichier}</div>
                              <div style={{fontSize:'12px', opacity:0.7}}>L'aperçu PDF intégré est simplifié ici</div>
                            </div>
                          ) : (
                            previewDocFull?.image_base64 ? (
                              <img src={previewDocFull.image_base64} alt="aperçu" style={{maxWidth:'100%', maxHeight:'50vh', borderRadius:'8px'}} />
                            ) : (
                              <div>Aucune image</div>
                            )
                          )}
                        </div>
                      </div>
                      <div className="card" style={{height:'60vh', overflow:'auto'}}>
                        <div className="card-title">Données extraites</div>
                        <div className="card-content">
                          {previewDocFull?.type_document==='z_report' ? (
                            <>
                              <div><strong>Date:</strong> {previewDocFull?.donnees_parsees?.report_date || '-'}</div>
                              <div><strong>Service:</strong> {previewDocFull?.donnees_parsees?.service || '-'}</div>
                              <div><strong>CA Total:</strong> {previewDocFull?.donnees_parsees?.grand_total_sales || '-'}</div>
                              <div style={{marginTop:'8px'}}><strong>Par catégorie</strong></div>
                              {['Bar','Entrées','Plats','Desserts'].map(cat => (
                                <div key={cat} style={{marginTop:'4px'}}>
                                  <div style={{fontWeight:'600'}}>{cat}</div>
                                  <ul style={{marginLeft:'16px'}}>
                                    {(previewDocFull?.donnees_parsees?.items_by_category?.[cat]||[]).map((it, i)=> (
                                      <li key={i}>{it.quantity_sold}x {it.name} {it.unit_price?`- €${it.unit_price}`:''}</li>
                                    ))}
                                  </ul>
                                </div>
                              ))}
                            </>
                          ) : (
                            <>
                              <div><strong>Fournisseur:</strong> {previewDocFull?.donnees_parsees?.fournisseur || '-'}</div>
                              <div><strong>Date facture:</strong> {previewDocFull?.donnees_parsees?.date || '-'}</div>
                              <div><strong>Total TTC:</strong> {previewDocFull?.donnees_parsees?.total_ttc || '-'}</div>
                            </>
                          )}
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Items list */}
                  {previewTab==='items' && (
                    <div className="card">
                      <div className="card-title">Liste complète des éléments détectés</div>
                      <div className="card-content">
                        {previewDocFull?.type_document==='z_report' ? (
                          <>
                            <ul>
                              {(previewDocFull?.donnees_parsees?.raw_items||[]).map((it, i)=> (
                                <li key={i}>• {it.quantity_sold}x {it.name} ({it.category}) {it.total_price?`= €${it.total_price}`:''}</li>
                              ))}
                            </ul>
                          </>
                        ) : (
                          <ul>
                            {(previewDocFull?.donnees_parsees?.produits||[]).map((p,i)=> (
                              <li key={i}>• {p.quantite} {p.unite || ''} {p.nom} à €{p.prix_unitaire || p.prix_total || ''}</li>
                            ))}
                          </ul>
                        )}
                      </div>
                    </div>
                  )}

                  {/* Analyse */}
                  {previewTab==='analyse' && (
                    <div className="card">
                      <div className="card-title">Analyse du rapport</div>
                      <div className="card-content">
                        {(() => {
                          const za = previewDocFull?.donnees_parsees?.z_analysis;
                          if (!za) return (<div>Aucune analyse disponible pour ce document.</div>);
                          const families = ['Bar','Entrées','Plats','Desserts','Autres'];
                          const totalCalc = za?.verification?.total_calculated;
                          const totalAff = za?.verification?.displayed_total;
                          const delta = za?.verification?.delta_eur;
                          const deltaPct = za?.verification?.delta_pct;
                          return (
                            <div>
                              <div style={{marginBottom:'10px'}}>
                                <div><strong>Date:</strong> {previewDocFull?.donnees_parsees?.report_date || '—'}</div>
                                <div><strong>Nombre de couverts:</strong> {za?.covers ?? '—'}</div>
                                <div><strong>CA Total affiché (TTC):</strong> {formatEuro(totalAff)}</div>
                              </div>
                              <div className="layout two-column" style={{gap:'12px'}}>
                                {families.map(f => (
                                  <div key={f} className="card">
                                    <div className="card-title">{f}</div>
                                    <div className="card-content">
                                      <div>Articles vendus: {za?.analysis?.[f]?.articles ?? 0}</div>
                                      <div>CA: {formatEuro(za?.analysis?.[f]?.ca)}</div>
                                      {za?.analysis?.[f]?.details?.length > 0 && (
                                        <details style={{marginTop:'6px'}}>
                                          <summary className="cursor-pointer text-sm">Détail sous-catégories</summary>
                                          <ul style={{marginLeft:'16px'}}>
                                            {za.analysis[f].details.map((d, i) => (
                                              <li key={i}>{d.name}: {d.quantity} articles – {formatEuro(d.amount)}</li>
                                            ))}
                                          </ul>
                                        </details>
                                      )}
                                    </div>
                                  </div>
                                ))}
                              </div>
                              <div className="card" style={{marginTop:'10px'}}>
                                <div className="card-title">Vérification</div>
                                <div className="card-content">
                                  <div>Total calculé: {formatEuro(totalCalc)}</div>
                                  <div>Total affiché: {formatEuro(totalAff)}</div>
                                  <div>Écart: {delta !== null && delta !== undefined ? `${formatEuro(delta)} (${deltaPct ?? '—'}%)` : '—'}</div>
                                  <div>Status: {(delta !== null && Math.abs(delta) < 0.01) ? '✅ Cohérent' : '⚠️ À vérifier'}</div>
                                </div>
                              </div>
                            </div>
                          );
                        })()}
                      </div>
                    </div>
                  )}

                  {/* Raw text */}
                  {previewTab==='raw' && (
                    <div className="card">
                      <div className="card-title">Texte brut OCR</div>
                      <pre style={{whiteSpace:'pre-wrap', padding:'12px'}}>{previewDocFull?.texte_extrait || '(vide)'}</pre>
                    </div>
                  )}
                </>
              )}
            </div>
          </div>
        </div>
      )}

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
            <h3 className="modal-header">
              {mouvementForm.type === 'ajustement' ? 'Ajuster le stock' : 'Nouveau mouvement de stock'}
            </h3>
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
                      {produit.nom} - {
                        (() => {
                          const stock = stocks.find(s => s.produit_id === produit.id);
                          const unite = getDisplayUnit(produit.unite);
                          return stock ? `Stock actuel: ${formatQuantity(stock.quantite_actuelle, unite)}` : 'Pas de stock';
                        })()
                      }
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
                  <option value="entree">➕ Entrée (Augmenter le stock)</option>
                  <option value="sortie">➖ Sortie (Diminuer le stock)</option>
                  <option value="ajustement">🔄 Ajustement (Corriger le stock)</option>
                </select>
              </div>
              <div className="form-group">
                <label className="form-label">
                  Quantité 
                  {mouvementForm.type === 'ajustement' && (
                    <span style={{fontSize: '0.8rem', color: '#666', marginLeft: '8px'}}>
                      (quantité à ajouter/retirer, ex: -5 pour retirer 5 unités)
                    </span>
                  )}
                </label>
                <input
                  type="number"
                  step="0.01"
                  className="form-input"
                  value={mouvementForm.quantite}
                  onChange={(e) => setMouvementForm({...mouvementForm, quantite: e.target.value})}
                  placeholder={mouvementForm.type === 'ajustement' ? 'Ex: -5 ou +10' : 'Quantité'}
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
              <label className="form-label">Fichier (Image ou PDF)</label>
              <input
                type="file"
                accept="image/*,.pdf"
                className="form-input"
                onChange={handleOcrFileSelect}
              />
              <p className="form-help">
                📷 Images: JPG, PNG, GIF, etc. • 📄 PDF: Factures et rapports Z
              </p>
            </div>

            {ocrPreview && (
              <div className="form-group">
                <label className="form-label">Aperçu</label>
                {ocrPreview.startsWith('PDF:') ? (
                  <div style={{
                    padding: '20px',
                    border: '2px dashed #ddd',
                    borderRadius: '5px',
                    textAlign: 'center',
                    backgroundColor: '#f9f9f9'
                  }}>
                    <div style={{fontSize: '48px', marginBottom: '10px'}}>📄</div>
                    <div style={{fontWeight: 'bold', color: '#666'}}>
                      {ocrPreview.replace('PDF: ', '')}
                    </div>
                    <div style={{fontSize: '12px', color: '#999', marginTop: '5px'}}>
                      Fichier PDF sélectionné
                    </div>
                  </div>
                ) : (
                  <img
                    src={ocrPreview}
                    alt="Aperçu du document"
                    style={{maxWidth: '100%', maxHeight: '200px', objectFit: 'contain', border: '1px solid #ddd', borderRadius: '5px'}}
                  />
                )}
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

      {/* Modal d'Aperçu des Documents OCR */}
      {showPreviewModal && previewDocument && (
        <div className="modal-overlay">
          <div className="modal-content" style={{ maxWidth: '90vw', maxHeight: '90vh' }}>
            <div className="modal-header">
              <h3>📄 Aperçu et Données Extraites</h3>
              <button 
                className="close-button"
                onClick={closePreviewModal}
              >
                ✕
              </button>
            </div>
            
            <div className="modal-body" style={{ padding: '20px', display: 'flex', gap: '20px', height: '70vh' }}>
              {/* Colonne Gauche - Aperçu du Document */}
              <div style={{ flex: '1', borderRight: '1px solid #ddd', paddingRight: '20px' }}>
                <h4 style={{ marginBottom: '15px', color: '#2D5016' }}>
                  📎 Document Source
                </h4>
                <div style={{ 
                  border: '2px solid #ddd', 
                  borderRadius: '8px', 
                  padding: '15px',
                  backgroundColor: '#f9f9f9',
                  height: '100%',
                  overflow: 'auto'
                }}>
                  {previewDocument.file_type === 'pdf' ? (
                    <div style={{ textAlign: 'center', padding: '40px' }}>
                      <div style={{ fontSize: '64px', marginBottom: '20px' }}>📄</div>
                      <h3 style={{ color: '#666', marginBottom: '10px' }}>
                        {previewDocument.nom_fichier}
                      </h3>
                      <p style={{ color: '#999', fontSize: '14px' }}>
                        Fichier PDF • Type: {previewDocument.type_document}
                      </p>
                      <p style={{ color: '#666', fontSize: '12px', marginTop: '20px' }}>
                        Traité le {new Date(previewDocument.date_traitement).toLocaleString('fr-FR')}
                      </p>
                      
                      {/* Texte extrait du PDF */}
                      <div style={{ 
                        marginTop: '20px', 
                        padding: '15px', 
                        backgroundColor: '#fff',
                        border: '1px solid #ddd',
                        borderRadius: '5px',
                        textAlign: 'left',
                        maxHeight: '300px',
                        overflow: 'auto',
                        fontSize: '12px',
                        fontFamily: 'monospace',
                        whiteSpace: 'pre-wrap'
                      }}>
                        <strong>Texte extrait du PDF :</strong><br />
                        {previewDocument.texte_extrait || 'Aucun texte extrait'}
                      </div>
                    </div>
                  ) : (
                    <img
                      src={previewDocument.image_base64}
                      alt="Aperçu du document"
                      style={{
                        maxWidth: '100%',
                        maxHeight: '100%',
                        objectFit: 'contain',
                        border: '1px solid #ccc',
                        borderRadius: '5px'
                      }}
                    />
                  )}
                </div>
              </div>

              {/* Colonne Droite - Données Extraites */}
              <div style={{ flex: '1', paddingLeft: '20px' }}>
                <h4 style={{ marginBottom: '15px', color: '#2D5016' }}>
                  🔍 Données Extraites et Organisées
                </h4>
                <div style={{ 
                  border: '2px solid #ddd', 
                  borderRadius: '8px', 
                  padding: '15px',
                  backgroundColor: '#f9f9f9',
                  height: '100%',
                  overflow: 'auto'
                }}>
                  {previewDocument.donnees_parsees ? (
                    <div>
                      {/* Informations générales */}
                      <div style={{ marginBottom: '20px', padding: '10px', backgroundColor: '#e8f5e8', borderRadius: '5px' }}>
                        <h5 style={{ margin: '0 0 10px 0', color: '#2D5016' }}>📊 Informations Générales</h5>
                        <div style={{ fontSize: '14px' }}>
                          {previewDocument.donnees_parsees.report_date && (
                            <p><strong>📅 Date :</strong> {previewDocument.donnees_parsees.report_date}</p>
                          )}
                          {previewDocument.donnees_parsees.service && (
                            <p><strong>🕐 Service :</strong> {previewDocument.donnees_parsees.service}</p>
                          )}
                          {previewDocument.donnees_parsees.grand_total_sales !== null && (
                            <p><strong>💰 CA Total :</strong> {previewDocument.donnees_parsees.grand_total_sales}€</p>
                          )}
                        </div>
                      </div>

                      {/* Articles par catégorie */}
                      {previewDocument.donnees_parsees.items_by_category && (
                        <div>
                          <h5 style={{ margin: '0 0 15px 0', color: '#2D5016' }}>🍽️ Articles par Catégorie</h5>
                          {Object.entries(previewDocument.donnees_parsees.items_by_category).map(([category, items]) => (
                            <div key={category} style={{ marginBottom: '15px' }}>
                              <div style={{ 
                                backgroundColor: '#f0f0f0', 
                                padding: '8px 12px', 
                                borderRadius: '5px',
                                fontWeight: 'bold',
                                marginBottom: '8px'
                              }}>
                                {category === 'Bar' && '🍷'} 
                                {category === 'Entrées' && '🥗'} 
                                {category === 'Plats' && '🍽️'} 
                                {category === 'Desserts' && '🍰'} 
                                {category} ({items.length} article{items.length > 1 ? 's' : ''})
                              </div>
                              {items.length > 0 ? (
                                <div style={{ paddingLeft: '10px' }}>
                                  {items.map((item, index) => (
                                    <div key={index} style={{ 
                                      display: 'flex', 
                                      justifyContent: 'space-between',
                                      padding: '5px 0',
                                      borderBottom: '1px solid #eee',
                                      fontSize: '13px'
                                    }}>
                                      <span>{item.name}</span>
                                      <div>
                                        <span style={{ fontWeight: 'bold' }}>×{item.quantity_sold}</span>
                                        {item.unit_price && (
                                          <span style={{ marginLeft: '10px', color: '#666' }}>
                                            {item.unit_price}€
                                          </span>
                                        )}
                                      </div>
                                    </div>
                                  ))}
                                </div>
                              ) : (
                                <div style={{ fontStyle: 'italic', color: '#999', paddingLeft: '10px' }}>
                                  Aucun article dans cette catégorie
                                </div>
                              )}
                            </div>
                          ))}
                        </div>
                      )}

                      {/* Articles bruts (fallback si pas de catégorisation) */}
                      {previewDocument.donnees_parsees.raw_items && previewDocument.donnees_parsees.raw_items.length > 0 && (
                        <div style={{ marginTop: '20px' }}>
                          <h5 style={{ margin: '0 0 10px 0', color: '#2D5016' }}>📋 Tous les Articles Détectés</h5>
                          <div style={{ fontSize: '12px' }}>
                            {previewDocument.donnees_parsees.raw_items.map((item, index) => (
                              <div key={index} style={{ 
                                padding: '5px 0',
                                borderBottom: '1px solid #eee'
                              }}>
                                <strong>{item.name}</strong> - Quantité: {item.quantity_sold}
                                {item.category && <span style={{ color: '#666' }}> (Catégorie: {item.category})</span>}
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Texte brut extrait */}
                      <div style={{ marginTop: '20px', padding: '10px', backgroundColor: '#f5f5f5', borderRadius: '5px' }}>
                        <h5 style={{ margin: '0 0 10px 0', color: '#2D5016' }}>📝 Texte Brut Extrait</h5>
                        <div style={{ 
                          fontSize: '11px', 
                          fontFamily: 'monospace',
                          maxHeight: '150px',
                          overflow: 'auto',
                          whiteSpace: 'pre-wrap',
                          color: '#555'
                        }}>
                          {previewDocument.texte_extrait || 'Aucun texte extrait'}
                        </div>
                      </div>
                    </div>
                  ) : (
                    <div style={{ textAlign: 'center', padding: '40px', color: '#999' }}>
                      <div style={{ fontSize: '48px', marginBottom: '15px' }}>⚠️</div>
                      <p>Aucune donnée parsée disponible</p>
                      <p style={{ fontSize: '12px' }}>
                        Le document n'a peut-être pas été traité correctement
                      </p>
                    </div>
                  )}
                </div>
              </div>
            </div>
            
            <div className="modal-footer">
              <button className="button secondary" onClick={closePreviewModal}>
                Fermer
              </button>
              {previewDocument.type_document === 'z_report' && (
                <button 
                  className="button primary"
                  onClick={() => {
                    handleProcessZReport(previewDocument.id);
                    closePreviewModal();
                  }}
                >
                  ⚡ Traiter ce Rapport Z
                </button>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;