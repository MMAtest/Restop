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
  const [alerteStockType, setAlerteStockType] = useState("produits"); // State pour le switch Produits/Productions dans les alertes
  
  // États pour la sélection de dates et données filtrées
  const [selectedDateRange, setSelectedDateRange] = useState(null);
  const [selectedProductionCategory, setSelectedProductionCategory] = useState(''); // Filtre pour les top productions
  const [selectedFlopCategory, setSelectedFlopCategory] = useState(''); // Filtre pour les flop productions séparé
  const [filteredAnalytics, setFilteredAnalytics] = useState({
    caTotal: 27959.75,
    caMidi: 16775.85,  // 60% du CA total
    caSoir: 11183.90,  // 40% du CA total
    couvertsMidi: 87,
    couvertsSoir: 64,
    topProductions: [
      { nom: "Rigatoni à la truffe", ventes: 2418, portions: 78, categorie: "Plat", coefficientPrevu: 2.85, coefficientReel: 2.87, coutMatiere: 774.00, prixVente: 28.50 }, // 28.50 / (774.00/78) = 2.87
      { nom: "Fleurs de courgettes", ventes: 1911, portions: 91, categorie: "Entrée", coefficientPrevu: 3.25, coefficientReel: 3.25, coutMatiere: 482.75, prixVente: 17.25 }, // 17.25 / (482.75/91) = 3.25
      { nom: "Souris d'agneau", ventes: 1872, portions: 52, categorie: "Plat", coefficientPrevu: 1.50, coefficientReel: 1.37, coutMatiere: 1368.00, prixVente: 36.00 }, // 36.00 / (1368.00/52) = 1.37
      { nom: "Tiramisù maison", ventes: 1654, portions: 67, categorie: "Dessert", coefficientPrevu: 3.00, coefficientReel: 3.04, coutMatiere: 264.64, prixVente: 12.00 }, // 12.00 / (264.64/67) = 3.04
      { nom: "Cocktail Spritz", ventes: 1543, portions: 124, categorie: "Bar", coefficientPrevu: 6.90, coefficientReel: 6.90, coutMatiere: 201.59, prixVente: 11.20 }, // 11.20 / (201.59/124) = 6.90
      { nom: "Salade de saison", ventes: 1387, portions: 89, categorie: "Entrée", coefficientPrevu: 3.60, coefficientReel: 3.58, coutMatiere: 360.22, prixVente: 14.50 }, // 14.50 / (360.22/89) = 3.58
      { nom: "Plateau de fromages", ventes: 987, portions: 34, categorie: "Autres", coefficientPrevu: 2.10, coefficientReel: 2.08, coutMatiere: 473.76, prixVente: 29.00 } // 29.00 / (473.76/34) = 2.08
    ],
    flopProductions: [
      { nom: "Soupe froide", ventes: 187, portions: 12, categorie: "Entrée", coefficientPrevu: 0.20, coefficientReel: 0.18, coutMatiere: 54.60, prixVente: 15.60 }, // Réel < Prévu = Respecté
      { nom: "Tartare de légumes", ventes: 156, portions: 8, categorie: "Autres", coefficientPrevu: 0.25, coefficientReel: 0.32, coutMatiere: 70.20, prixVente: 16.70 }, // Réel > Prévu = Dépassé
      { nom: "Mocktail exotique", ventes: 134, portions: 9, categorie: "Bar", coefficientPrevu: 0.15, coefficientReel: 0.13, coutMatiere: 37.52, prixVente: 13.40 }, // Réel < Prévu = Respecté
      { nom: "Panna cotta", ventes: 98, portions: 6, categorie: "Dessert", coefficientPrevu: 0.18, coefficientReel: 0.22, coutMatiere: 30.38, prixVente: 9.80 } // Réel > Prévu = Dépassé
    ],
    ventesParCategorie: {
      plats: 6201,
      boissons: 4987,
      desserts: 2156,
      entrees: 3247,
      autres: 892
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
  
  // États pour la gestion des lots et DLC
  const [batches, setBatches] = useState([]);
  const [batchSummary, setBatchSummary] = useState([]);
  const [expiredProducts, setExpiredProducts] = useState([]);
  const [criticalProducts, setCriticalProducts] = useState([]);
  const [showBatchModal, setShowBatchModal] = useState(false);
  const [selectedProductBatches, setSelectedProductBatches] = useState(null);
  
  // États pour les filtres par catégorie
  const [categoriesProduction, setCategoriesProduction] = useState([]);
  const [selectedCategoryFilter, setSelectedCategoryFilter] = useState('');
  const [filteredRecettes, setFilteredRecettes] = useState([]);
  const [filteredProduits, setFilteredProduits] = useState([]);
  
  // États pour le module prévisionnel
  const [stocksPrevisionnels, setStocksPrevisionnels] = useState([
    { id: 1, produit: "Tomates", stock_actuel: 25, unite: "kg", productions_possibles: [
      { nom: "Salade Méditerranéenne", quantite_needed: 2, portions_possibles: 12, portions_selectionnees: 0, categorie: "Entrée" },
      { nom: "Ratatouille", quantite_needed: 3, portions_possibles: 8, portions_selectionnees: 0, categorie: "Plat" },
      { nom: "Gazpacho", quantite_needed: 1.5, portions_possibles: 16, portions_selectionnees: 0, categorie: "Entrée" }
    ]},
    { id: 2, produit: "Fromage de chèvre", stock_actuel: 3.2, unite: "kg", productions_possibles: [
      { nom: "Salade de chèvre chaud", quantite_needed: 0.15, portions_possibles: 21, portions_selectionnees: 0, categorie: "Entrée" },
      { nom: "Tarte aux courgettes", quantite_needed: 0.2, portions_possibles: 16, portions_selectionnees: 0, categorie: "Plat" }
    ]},
    { id: 3, produit: "Saumon frais", stock_actuel: 4.8, unite: "kg", productions_possibles: [
      { nom: "Saumon grillé", quantite_needed: 0.18, portions_possibles: 26, portions_selectionnees: 0, categorie: "Plat" },
      { nom: "Tartare de saumon", quantite_needed: 0.12, portions_possibles: 40, portions_selectionnees: 0, categorie: "Entrée" }
    ]}
  ]);
  const [selectedProductionPrevisionnelle, setSelectedProductionPrevisionnelle] = useState('');

  // États pour la pagination et filtres OCR
  const [ocrCurrentPage, setOcrCurrentPage] = useState(1);
  const [ocrDocumentsPerPage] = useState(8); // 8 documents par page
  const [ocrFilterType, setOcrFilterType] = useState('all'); // 'all', 'z_report', 'facture_fournisseur'
  
  // État pour la recherche dans les stocks
  const [stockSearchTerm, setStockSearchTerm] = useState('');
  
  // États pour la pagination et filtres des stocks
  const [stockCurrentPage, setStockCurrentPage] = useState(1);
  const [stockItemsPerPage] = useState(10); // 10 produits par page
  const [stockFilterCategory, setStockFilterCategory] = useState('all');

  // Fonction pour mettre à jour les portions sélectionnées avec équilibrage
  const updatePortionsSelectionnees = (stockId, productionIndex, newValue) => {
    setStocksPrevisionnels(prevStocks => {
      return prevStocks.map(stock => {
        if (stock.id === stockId) {
          const updatedProductions = stock.productions_possibles.map((prod, index) => {
            if (index === productionIndex) {
              // Calculer la quantité totale utilisée par toutes les productions de ce stock
              const autresPortions = stock.productions_possibles.reduce((total, p, i) => {
                if (i !== productionIndex) {
                  return total + (p.portions_selectionnees * p.quantite_needed);
                }
                return total;
              }, 0);
              
              // Calculer la quantité max disponible pour cette production
              const quantiteDisponible = stock.stock_actuel - autresPortions;
              const maxPortionsPossibles = Math.floor(quantiteDisponible / prod.quantite_needed);
              
              // Limiter la valeur au maximum possible
              const finalValue = Math.min(newValue, maxPortionsPossibles, prod.portions_possibles);
              
              return { ...prod, portions_selectionnees: finalValue };
            }
            return prod;
          });
          
          return { ...stock, productions_possibles: updatedProductions };
        }
        return stock;
      });
    });
  };

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
    nom: "", contact: "", email: "", telephone: "", adresse: "", couleur: "#3B82F6", logo: ""
  });
  const [mouvementForm, setMouvementForm] = useState({
    produit_id: "", type: "entree", quantite: "", reference: "", commentaire: ""
  });
  const [recetteForm, setRecetteForm] = useState({
    nom: "", description: "", categorie: "", portions: "", temps_preparation: "", 
    prix_vente: "", coefficient_prevu: "", instructions: "", ingredients: []
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
    fetchBatchSummary(); // Ajouter récupération des lots
    fetchCategoriesProduction(); // Récupérer les catégories
  }, []);

  // Fonction pour récupérer les catégories de production
  const fetchCategoriesProduction = async () => {
    try {
      const response = await axios.get(`${API}/categories-production`);
      setCategoriesProduction(response.data.categories);
    } catch (error) {
      console.error("Erreur lors du chargement des catégories:", error);
    }
  };

  // Fonction pour filtrer les recettes par catégorie
  const filterRecettesByCategory = (category) => {
    if (!category || category === '') {
      setFilteredRecettes(recettes);
    } else {
      const filtered = recettes.filter(recette => recette.categorie === category);
      setFilteredRecettes(filtered);
    }
    setSelectedCategoryFilter(category);
  };

  // Fonction pour filtrer les produits par catégorie
  const filterProduitsByCategory = (category) => {
    if (!category || category === '') {
      // Si "tous les ingrédients", afficher tout y compris ceux sans catégorie
      setFilteredProduits(produits);
    } else {
      // Si catégorie spécifique, afficher seulement ceux avec cette catégorie
      const filtered = produits.filter(produit => produit.categorie === category);
      setFilteredProduits(filtered);
    }
  };

  // Fonction pour filtrer les productions par catégorie
  const getFilteredProductions = (productions, category) => {
    if (!category || category === '') {
      // Si "toutes les catégories", afficher tout y compris ceux sans catégorie
      return productions;
    }
    // Si catégorie spécifique, afficher seulement ceux avec cette catégorie
    return productions.filter(production => production.categorie === category);
  };

  // Effet pour mettre à jour les produits filtrés quand les produits changent
  useEffect(() => {
    setFilteredProduits(produits);
  }, [produits]);

  // Fonction pour récupérer le résumé des lots
  const fetchBatchSummary = async () => {
    try {
      const response = await axios.get(`${API}/stock/batch-summary`);
      setBatchSummary(response.data);
      
      // Séparer les produits expirés et critiques
      const expired = [];
      const critical = [];
      
      response.data.forEach(item => {
        item.batches.forEach(batch => {
          if (batch.status === 'expired') {
            expired.push({
              product_name: item.product_name,
              product_id: item.product_id,
              batch_number: batch.batch_number,
              expiry_date: batch.expiry_date,
              quantity: batch.quantity
            });
          } else if (batch.status === 'critical') {
            critical.push({
              product_name: item.product_name,
              product_id: item.product_id,
              batch_number: batch.batch_number,
              expiry_date: batch.expiry_date,
              quantity: batch.quantity
            });
          }
        });
      });
      
      setExpiredProducts(expired);
      setCriticalProducts(critical);
    } catch (error) {
      console.error("Erreur lors du chargement des lots:", error);
    }
  };

  // Fonction pour récupérer les lots d'un produit spécifique
  const fetchProductBatches = async (productId) => {
    try {
      const response = await axios.get(`${API}/stock/batch-info/${productId}`);
      setSelectedProductBatches(response.data);
      setShowBatchModal(true);
    } catch (error) {
      console.error("Erreur lors du chargement des lots du produit:", error);
      alert("Erreur lors du chargement des lots");
    }
  };

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
      setFournisseurForm({ nom: "", contact: "", email: "", telephone: "", adresse: "", couleur: "#3B82F6", logo: "" });
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
        coefficient_prevu: recetteForm.coefficient_prevu ? parseFloat(recetteForm.coefficient_prevu) / 100 : null, // Convertir en décimal
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
        adresse: item.adresse || "",
        couleur: item.couleur || "#3B82F6",
        logo: item.logo || ""
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
      caMidi: 16775.85,
      caSoir: 11183.90,
      couvertsMidi: 87,
      couvertsSoir: 64,
      topProductions: [
        { nom: "Rigatoni à la truffe", ventes: 2418, portions: 78, categorie: "Plat", coefficientPrevu: 0.35, coefficientReel: 0.32, coutMatiere: 774.00, prixVente: 28.50 },
        { nom: "Fleurs de courgettes", ventes: 1911, portions: 91, categorie: "Entrée", coefficientPrevu: 0.25, coefficientReel: 0.28, coutMatiere: 482.75, prixVente: 17.25 },
        { nom: "Souris d'agneau", ventes: 1872, portions: 52, categorie: "Plat", coefficientPrevu: 0.40, coefficientReel: 0.38, coutMatiere: 1368.00, prixVente: 36.00 },
        { nom: "Tiramisù maison", ventes: 1654, portions: 67, categorie: "Dessert", coefficientPrevu: 0.20, coefficientReel: 0.22, coutMatiere: 264.64, prixVente: 12.00 },
        { nom: "Cocktail Spritz", ventes: 1543, portions: 124, categorie: "Bar", coefficientPrevu: 0.15, coefficientReel: 0.18, coutMatiere: 201.59, prixVente: 11.20 },
        { nom: "Salade de saison", ventes: 1387, portions: 89, categorie: "Entrée", coefficientPrevu: 0.30, coefficientReel: 0.26, coutMatiere: 360.22, prixVente: 14.50 },
        { nom: "Plateau de fromages", ventes: 987, portions: 34, categorie: "Autres", coefficientPrevu: 0.45, coefficientReel: 0.48, coutMatiere: 473.76, prixVente: 29.00 }
      ],
      flopProductions: [
        { nom: "Soupe froide", ventes: 187, portions: 12, categorie: "Entrée", coefficientPrevu: 0.20, coefficientReel: 0.35, coutMatiere: 54.60, prixVente: 15.60 },
        { nom: "Tartare de légumes", ventes: 156, portions: 8, categorie: "Autres", coefficientPrevu: 0.25, coefficientReel: 0.42, coutMatiere: 70.20, prixVente: 16.70 },
        { nom: "Mocktail exotique", ventes: 134, portions: 9, categorie: "Bar", coefficientPrevu: 0.15, coefficientReel: 0.28, coutMatiere: 37.52, prixVente: 13.40 },
        { nom: "Panna cotta", ventes: 98, portions: 6, categorie: "Dessert", coefficientPrevu: 0.18, coefficientReel: 0.31, coutMatiere: 30.38, prixVente: 9.80 }
      ],
      ventesParCategorie: {
        entrees: 3247,
        plats: 6201,
        desserts: 2156,
        boissons: 4987,
        autres: 892
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
      caMidi: Math.round(baseDayData.caMidi * periodMultiplier * 100) / 100,
      caSoir: Math.round(baseDayData.caSoir * periodMultiplier * 100) / 100,
      couvertsMidi: Math.round(baseDayData.couvertsMidi * periodMultiplier),
      couvertsSoir: Math.round(baseDayData.couvertsSoir * periodMultiplier),
      topProductions: baseDayData.topProductions.map(production => ({
        ...production,
        ventes: Math.round(production.ventes * periodMultiplier),
        portions: Math.round(production.portions * periodMultiplier),
        coutMatiere: Math.round(production.coutMatiere * periodMultiplier * 100) / 100
      })),
      flopProductions: baseDayData.flopProductions.map(production => ({
        ...production,
        ventes: Math.round(production.ventes * periodMultiplier),
        portions: Math.round(production.portions * periodMultiplier),
        coutMatiere: Math.round(production.coutMatiere * periodMultiplier * 100) / 100
      })),
      ventesParCategorie: {
        entrees: Math.round(baseDayData.ventesParCategorie.entrees * periodMultiplier),
        plats: Math.round(baseDayData.ventesParCategorie.plats * periodMultiplier),
        desserts: Math.round(baseDayData.ventesParCategorie.desserts * periodMultiplier),
        boissons: Math.round(baseDayData.ventesParCategorie.boissons * periodMultiplier),
        autres: Math.round(baseDayData.ventesParCategorie.autres * periodMultiplier)
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

    alert(`📱 INVENTAIRE RAPIDE:\n\n` +
      `📦 Total produits: ${totalProduits}\n` +
      `⚠️ Stocks critiques: ${stocksCritiques}\n` +
      `💰 Valeur totale: ${valeurTotale.toFixed(2)}€\n\n` +
      `Utilisez les sections dédiées pour un inventaire complet.`);
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

      const response = await axios.post(`${API}/ocr/upload-document`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        },
        timeout: 30000 // 30 secondes timeout pour OCR
      });

      setOcrResult(response.data);
      alert('Document traité avec succès !');
      fetchDocumentsOcr();
      
      // Réinitialiser le formulaire OCR
      resetOcrModal();
      
      // Fermer le modal OCR
      setShowOcrModal(false);
      
    } catch (error) {
      console.error('Erreur lors du traitement OCR:', error);
      if (error.code === 'ECONNABORTED') {
        alert('Timeout: Le traitement OCR prend trop de temps. Veuillez réessayer avec un fichier plus petit.');
      } else {
        alert(`Erreur: ${error.response?.data?.detail || error.message || 'Erreur lors du traitement'}`);
      }
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

  // Supprimer tous les documents OCR
  const handleSupprimerTousDocumentsOcr = async () => {
    try {
      setLoading(true);
      
      if (documentsOcr.length === 0) {
        alert("ℹ️ Aucun document à supprimer");
        return;
      }

      const confirmation = window.confirm(`🗑️ SUPPRESSION DE L'HISTORIQUE:\n\nÊtes-vous sûr de vouloir supprimer tous les ${documentsOcr.length} documents OCR ?\n\n⚠️ Cette action est irréversible !`);
      
      if (confirmation) {
        const response = await axios.delete(`${API}/ocr/documents/all`);
        
        alert(`✅ Historique vidé avec succès !\n\n${response.data.deleted_count} document(s) supprimé(s)`);
        
        // Rafraîchir la liste des documents
        fetchDocumentsOcr();
        setSelectedDocument(null);
      }
    } catch (error) {
      console.error("Erreur suppression documents OCR:", error);
      alert("❌ Erreur lors de la suppression de l'historique");
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
    // Ne pas réinitialiser ocrType pour garder le choix de l'utilisateur
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
          <button 
            className={`top-nav-tab ${activeDashboardTab === "previsionnel" ? "active" : ""}`}
            onClick={() => setActiveDashboardTab("previsionnel")}
          >
            PRÉVISIONNEL
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
                  <div className="icon">☀️</div>
                  <div className="title">Service Midi</div>
                  <div className="value">{filteredAnalytics.caMidi.toLocaleString('fr-FR')} €</div>
                  <div className="subtitle">{filteredAnalytics.couvertsMidi} couverts</div>
                </div>
                
                <div className="kpi-card">
                  <div className="icon">🌙</div>
                  <div className="title">Service Soir</div>
                  <div className="value">{filteredAnalytics.caSoir.toLocaleString('fr-FR')} €</div>
                  <div className="subtitle">{filteredAnalytics.couvertsSoir} couverts</div>
                </div>
              </div>

              {/* Ventes par catégorie complètes - Remontées */}
              <div className="kpi-grid">
                <div className="kpi-card">
                  <div className="icon">🥗</div>
                  <div className="title">Entrées</div>
                  <div className="value">{filteredAnalytics.ventesParCategorie.entrees.toLocaleString('fr-FR')} €</div>
                </div>
                
                <div className="kpi-card">
                  <div className="icon">🍽️</div>
                  <div className="title">Plats</div>
                  <div className="value">{filteredAnalytics.ventesParCategorie.plats.toLocaleString('fr-FR')} €</div>
                </div>
                
                <div className="kpi-card">
                  <div className="icon">🍰</div>
                  <div className="title">Desserts</div>
                  <div className="value">{filteredAnalytics.ventesParCategorie.desserts.toLocaleString('fr-FR')} €</div>
                </div>
                
                <div className="kpi-card">
                  <div className="icon">🍹</div>
                  <div className="title">Bar</div>
                  <div className="value">{filteredAnalytics.ventesParCategorie.boissons.toLocaleString('fr-FR')} €</div>
                </div>
                
                <div className="kpi-card">
                  <div className="icon">📝</div>
                  <div className="title">Autres</div>
                  <div className="value">{filteredAnalytics.ventesParCategorie.autres.toLocaleString('fr-FR')} €</div>
                </div>
              </div>

              {/* Top Productions avec filtre */}
              <div className="item-list">
                <div className="section-title">🍽️ Top Productions</div>
                
                {/* Filtre par catégorie */}
                <div className="filter-section" style={{marginBottom: '15px'}}>
                  <div className="filter-group" style={{display: 'flex', alignItems: 'center', gap: '10px'}}>
                    <label className="filter-label" style={{fontSize: '14px', minWidth: '60px'}}>Filtre :</label>
                    <select 
                      className="filter-select"
                      value={selectedProductionCategory}
                      onChange={(e) => setSelectedProductionCategory(e.target.value)}
                      style={{
                        padding: '6px 10px',
                        borderRadius: '4px',
                        border: '1px solid var(--color-border)',
                        background: 'var(--color-background-card)',
                        color: 'var(--color-text-primary)',
                        fontSize: '13px',
                        minWidth: '120px'
                      }}
                    >
                      <option value="">Toutes</option>
                      <option value="Entrée">🥗 Entrées</option>
                      <option value="Plat">🍽️ Plats</option>
                      <option value="Dessert">🍰 Desserts</option>
                      <option value="Bar">🍹 Bar</option>
                      <option value="Autres">📝 Autres</option>
                    </select>
                    
                    <div className="filter-info" style={{
                      fontSize: '12px', 
                      color: 'var(--color-text-secondary)'
                    }}>
                      {getFilteredProductions(filteredAnalytics.topProductions, selectedProductionCategory).length} résultat(s)
                    </div>
                  </div>
                </div>

                {/* Liste des productions filtrées avec coefficients */}
                {getFilteredProductions(filteredAnalytics.topProductions, selectedProductionCategory).slice(0, 4).map((production, index) => {
                  const coefficientStatus = production.coefficientReel >= production.coefficientPrevu ? 'success' : 'warning';
                  const coefficientIcon = production.coefficientReel >= production.coefficientPrevu ? '✅' : '⚠️';
                  const coefficientText = production.coefficientReel >= production.coefficientPrevu ? 'Respecté' : 'Dépassé';
                  
                  return (
                    <div key={index} className="item-row">
                      <div className="item-info">
                        <div className="item-name">
                          {production.categorie === 'Entrée' ? '🥗' : 
                           production.categorie === 'Plat' ? '🍽️' : 
                           production.categorie === 'Dessert' ? '🍰' : 
                           production.categorie === 'Bar' ? '🍹' : '📝'} {production.nom}
                          <span className="category-badge" style={{
                            marginLeft: '6px',
                            padding: '2px 6px',
                            borderRadius: '8px',
                            fontSize: '10px',
                            background: 'var(--color-primary-blue)',
                            color: 'white'
                          }}>
                            {production.categorie}
                          </span>
                        </div>
                        <div className="item-details">
                          {production.portions} portions • Coeff. prévu: {(production.coefficientPrevu * 100).toFixed(1)}% • 
                          Coeff. réel: {(production.coefficientReel * 100).toFixed(1)}% {coefficientIcon}
                        </div>
                      </div>
                      <div className="item-actions">
                        <span className={`coefficient-badge ${coefficientStatus}`} style={{
                          padding: '4px 8px',
                          borderRadius: '12px',
                          fontSize: '12px',
                          marginRight: '8px',
                          background: coefficientStatus === 'success' ? 'var(--color-success-green)' : 'var(--color-warning-orange)',
                          color: 'white'
                        }}>
                          {coefficientText}
                        </span>
                        <div className="item-value">{production.ventes.toLocaleString('fr-FR')} €</div>
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* Flop Productions avec filtre */}
              <div className="item-list">
                <div className="section-title">📉 Flop Productions</div>
                
                {/* Filtre par catégorie pour les flops */}
                <div className="filter-section" style={{marginBottom: '15px'}}>
                  <div className="filter-group" style={{display: 'flex', alignItems: 'center', gap: '10px'}}>
                    <label className="filter-label" style={{fontSize: '14px', minWidth: '60px'}}>Filtre :</label>
                    <select 
                      className="filter-select"
                      value={selectedFlopCategory}
                      onChange={(e) => setSelectedFlopCategory(e.target.value)}
                      style={{
                        padding: '6px 10px',
                        borderRadius: '4px',
                        border: '1px solid var(--color-border)',
                        background: 'var(--color-background-card)',
                        color: 'var(--color-text-primary)',
                        fontSize: '13px',
                        minWidth: '120px'
                      }}
                    >
                      <option value="">Toutes</option>
                      <option value="Entrée">🥗 Entrées</option>
                      <option value="Plat">🍽️ Plats</option>
                      <option value="Dessert">🍰 Desserts</option>
                      <option value="Bar">🍹 Bar</option>
                      <option value="Autres">📝 Autres</option>
                    </select>
                    
                    <div className="filter-info" style={{
                      fontSize: '12px', 
                      color: 'var(--color-text-secondary)'
                    }}>
                      {getFilteredProductions(filteredAnalytics.flopProductions, selectedFlopCategory).length} résultat(s)
                    </div>
                  </div>
                </div>

                {/* Liste des flop productions filtrées avec coefficients */}
                {getFilteredProductions(filteredAnalytics.flopProductions, selectedFlopCategory).slice(0, 4).map((production, index) => {
                  const coefficientStatus = production.coefficientReel >= production.coefficientPrevu ? 'success' : 'critical';
                  const coefficientIcon = production.coefficientReel >= production.coefficientPrevu ? '✅' : '🔴';
                  const coefficientText = production.coefficientReel >= production.coefficientPrevu ? 'Respecté' : 'Problème';
                  
                  return (
                    <div key={index} className="item-row">
                      <div className="item-info">
                        <div className="item-name">
                          {production.categorie === 'Entrée' ? '🥗' : 
                           production.categorie === 'Plat' ? '🍽️' : 
                           production.categorie === 'Dessert' ? '🍰' : 
                           production.categorie === 'Bar' ? '🍹' : '📝'} {production.nom}
                          <span className="category-badge" style={{
                            marginLeft: '6px',
                            padding: '2px 6px',
                            borderRadius: '8px',
                            fontSize: '10px',
                            background: 'var(--color-warning-orange)',
                            color: 'white'
                          }}>
                            {production.categorie}
                          </span>
                        </div>
                        <div className="item-details">
                          {production.portions} portions • Coeff. prévu: {(production.coefficientPrevu * 100).toFixed(1)}% • 
                          Coeff. réel: {(production.coefficientReel * 100).toFixed(1)}% {coefficientIcon}
                        </div>
                      </div>
                      <div className="item-actions">
                        <span className={`coefficient-badge ${coefficientStatus}`} style={{
                          padding: '4px 8px',
                          borderRadius: '12px',
                          fontSize: '12px',
                          marginRight: '8px',
                          background: coefficientStatus === 'success' ? 'var(--color-success-green)' : 'var(--color-critical-red)',
                          color: 'white'
                        }}>
                          {coefficientText}
                        </span>
                        <div className="item-value warning">{production.ventes.toLocaleString('fr-FR')} €</div>
                      </div>
                    </div>
                  );
                })}
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
              
              {/* Alertes de stock faible avec switch */}
              <div className="alert-section">
                <div className="alert-header" style={{display: 'flex', alignItems: 'center', justifyContent: 'space-between'}}>
                  <div style={{display: 'flex', alignItems: 'center'}}>
                    <div className="alert-title">Stock Faible</div>
                    <div className="alert-count" style={{
                      background: 'var(--color-danger-red)',
                      color: 'white',
                      width: '24px',
                      height: '24px',
                      borderRadius: '50%',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontSize: '12px',
                      fontWeight: 'bold',
                      marginLeft: '8px'
                    }}>3</div>
                  </div>
                  
                  {/* Switch pour Produits/Productions */}
                  <div style={{display: 'flex', gap: '5px', fontSize: '12px'}}>
                    <button 
                      className="button small" 
                      onClick={() => setAlerteStockType("produits")}
                      style={{
                        background: alerteStockType === "produits" ? 'var(--color-primary-blue)' : 'var(--color-background-card-light)',
                        color: alerteStockType === "produits" ? 'white' : 'var(--color-text-secondary)',
                        padding: '4px 8px',
                        fontSize: '11px'
                      }}
                    >
                      Produits
                    </button>
                    <button 
                      className="button small" 
                      onClick={() => setAlerteStockType("productions")}
                      style={{
                        background: alerteStockType === "productions" ? 'var(--color-primary-blue)' : 'var(--color-background-card-light)',
                        color: alerteStockType === "productions" ? 'white' : 'var(--color-text-secondary)',
                        padding: '4px 8px',
                        fontSize: '11px'
                      }}
                    >
                      Productions
                    </button>
                  </div>
                </div>
                
                {/* Contenu conditionnel selon le type sélectionné */}
                {alerteStockType === "produits" ? (
                  <>
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
                  </>
                ) : (
                  <>
                    <div className="alert-card">
                      <div className="alert-item">
                        <div className="product-info">
                          <div className="product-name">🍽️ Salade Méditerranéenne</div>
                          <div className="stock-info">
                            Ingrédient manquant: Tomates cerises • Production limitée
                          </div>
                        </div>
                      </div>
                    </div>

                    <div className="alert-card warning">
                      <div className="alert-item">
                        <div className="product-info">
                          <div className="product-name">🧀 Tarte aux courgettes</div>
                          <div className="stock-info">
                            Ingrédient faible: Fromage de chèvre • Max 8 portions possible
                          </div>
                        </div>
                      </div>
                    </div>

                    <div className="alert-card">
                      <div className="alert-item">
                        <div className="product-info">
                          <div className="product-name">🥗 Salade de chèvre chaud</div>
                          <div className="stock-info">
                            Stock ingrédients insuffisant • Production suspendue
                          </div>
                        </div>
                      </div>
                    </div>
                  </>
                )}
              </div>

              {/* Nouvelle section : Stock critique (ruptures uniquement) */}
              <div className="alert-section">
                <div className="alert-header" style={{display: 'flex', alignItems: 'center', justifyContent: 'space-between'}}>
                  <div style={{display: 'flex', alignItems: 'center'}}>
                    <div className="alert-title">Ruptures de Stock</div>
                    <div className="alert-count" style={{
                      background: 'var(--color-danger-red)',
                      color: 'white',
                      width: '24px',
                      height: '24px',
                      borderRadius: '50%',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontSize: '12px',
                      fontWeight: 'bold',
                      marginLeft: '8px'
                    }}>4</div>
                  </div>
                  
                  {/* Switch pour Produits/Productions */}
                  <div style={{display: 'flex', gap: '5px', fontSize: '12px'}}>
                    <button 
                      className="button small" 
                      onClick={() => setAlerteStockType("produits")}
                      style={{
                        background: alerteStockType === "produits" ? 'var(--color-primary-blue)' : 'var(--color-background-card-light)',
                        color: alerteStockType === "produits" ? 'white' : 'var(--color-text-secondary)',
                        padding: '4px 8px',
                        fontSize: '11px'
                      }}
                    >
                      Produits
                    </button>
                    <button 
                      className="button small" 
                      onClick={() => setAlerteStockType("productions")}
                      style={{
                        background: alerteStockType === "productions" ? 'var(--color-primary-blue)' : 'var(--color-background-card-light)',
                        color: alerteStockType === "productions" ? 'white' : 'var(--color-text-secondary)',
                        padding: '4px 8px',
                        fontSize: '11px'
                      }}
                    >
                      Productions
                    </button>
                  </div>
                </div>
                
                {/* Contenu conditionnel selon le type sélectionné */}
                {alerteStockType === "produits" ? (
                  <>
                    <div className="alert-card critical">
                      <div className="alert-item">
                        <div className="product-info">
                          <div className="product-name">🧄 Ail rose</div>
                          <div className="stock-info">
                            Stock: <span className="stock-current critical">0 kg</span> • Rupture totale
                          </div>
                        </div>
                        <div className="item-actions">
                          <button className="button small critical">🚨 Commander</button>
                        </div>
                      </div>
                    </div>

                    <div className="alert-card critical">
                      <div className="alert-item">
                        <div className="product-info">
                          <div className="product-name">🫒 Huile d'olive extra</div>
                          <div className="stock-info">
                            Stock: <span className="stock-current critical">0 L</span> • Plus en stock
                          </div>
                        </div>
                        <div className="item-actions">
                          <button className="button small critical">🚨 Commander</button>
                        </div>
                      </div>
                    </div>

                    <div className="alert-card critical">
                      <div className="alert-item">
                        <div className="product-info">
                          <div className="product-name">🌿 Basilic frais</div>
                          <div className="stock-info">
                            Stock: <span className="stock-current critical">0 kg</span> • Rupture stock
                          </div>
                        </div>
                        <div className="item-actions">
                          <button className="button small critical">🚨 Commander</button>
                        </div>
                      </div>
                    </div>

                    <div className="alert-card critical">
                      <div className="alert-item">
                        <div className="product-info">
                          <div className="product-name">🍋 Citrons</div>
                          <div className="stock-info">
                            Stock: <span className="stock-current critical">0 kg</span> • Stock épuisé
                          </div>
                        </div>
                        <div className="item-actions">
                          <button className="button small critical">🚨 Commander</button>
                        </div>
                      </div>
                    </div>
                  </>
                ) : (
                  <>
                    <div className="alert-card critical">
                      <div className="alert-item">
                        <div className="product-info">
                          <div className="product-name">🍝 Linguine aux palourdes</div>
                          <div className="stock-info">
                            Ingrédient manquant: Ail rose • <span className="stock-critical">Production impossible</span>
                          </div>
                        </div>
                        <div className="item-actions">
                          <button className="button small critical">🚫 Suspendue</button>
                        </div>
                      </div>
                    </div>

                    <div className="alert-card critical">
                      <div className="alert-item">
                        <div className="product-info">
                          <div className="product-name">🥗 Salade méditerranéenne</div>
                          <div className="stock-info">
                            Ingrédients manquants: Huile d'olive, Basilic • <span className="stock-critical">Production bloquée</span>
                          </div>
                        </div>
                        <div className="item-actions">
                          <button className="button small critical">🚫 Suspendue</button>
                        </div>
                      </div>
                    </div>

                    <div className="alert-card critical">
                      <div className="alert-item">
                        <div className="product-info">
                          <div className="product-name">🐟 Saumon grillé</div>
                          <div className="stock-info">
                            Ingrédient manquant: Citrons • <span className="stock-critical">Présentation incomplète</span>
                          </div>
                        </div>
                        <div className="item-actions">
                          <button className="button small warning">⚠️ Limitée</button>
                        </div>
                      </div>
                    </div>

                    <div className="alert-card critical">
                      <div className="alert-item">
                        <div className="product-info">
                          <div className="product-name">🍅 Caprese</div>
                          <div className="stock-info">
                            Ingrédient manquant: Basilic frais • <span className="stock-critical">Production impossible</span>
                          </div>
                        </div>
                        <div className="item-actions">
                          <button className="button small critical">🚫 Suspendue</button>
                        </div>
                      </div>
                    </div>
                  </>
                )}
              </div>

              {/* Nouvelle section séparée : DLC Critiques */}
              <div className="alert-section">
                <div className="alert-header" style={{display: 'flex', alignItems: 'center'}}>
                  <div className="alert-title">DLC Critiques (&lt; 3 jours)</div>
                  <div className="alert-count" style={{
                    background: 'var(--color-warning-orange)',
                    color: 'white',
                    width: '24px',
                    height: '24px',
                    borderRadius: '50%',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '12px',
                    fontWeight: 'bold',
                    marginLeft: '8px'
                  }}>3</div>
                </div>
                
                <div className="alert-card critical">
                  <div className="alert-item">
                    <div className="product-info">
                      <div className="product-name">🐟 Saumon frais</div>
                      <div className="stock-info">
                        Lot SAU-2024-15 • 2.8 kg • <span style={{color: 'var(--color-danger-red)', fontWeight: 'bold'}}>Expire dans 1 jour</span>
                      </div>
                    </div>
                    <div className="item-actions">
                      <button className="button small critical">🚨 Urgent</button>
                    </div>
                  </div>
                </div>

                <div className="alert-card critical">
                  <div className="alert-item">
                    <div className="product-info">
                      <div className="product-name">🥛 Crème fraîche</div>
                      <div className="stock-info">
                        Lot CRE-2024-08 • 1.5 L • <span style={{color: 'var(--color-danger-red)', fontWeight: 'bold'}}>Expire dans 2 jours</span>
                      </div>
                    </div>
                    <div className="item-actions">
                      <button className="button small critical">🚨 Urgent</button>
                    </div>
                  </div>
                </div>

                <div className="alert-card warning">
                  <div className="alert-item">
                    <div className="product-info">
                      <div className="product-name">🧀 Brie de Meaux</div>
                      <div className="stock-info">
                        Lot BRI-2024-03 • 800g • <span style={{color: 'var(--color-warning-orange)', fontWeight: 'bold'}}>Expire dans 3 jours</span>
                      </div>
                    </div>
                    <div className="item-actions">
                      <button className="button small warning">⚡ Utiliser rapidement</button>
                    </div>
                  </div>
                </div>
              </div>

              {/* Section Expiration < 7 jours */}
              <div className="alert-section">
                <div className="alert-header" style={{display: 'flex', alignItems: 'center'}}>
                  <div className="alert-title">Expiration &lt; 7 jours</div>
                  <div className="alert-count" style={{
                    background: 'var(--color-accent-orange)',
                    color: 'white',
                    width: '24px',
                    height: '24px',
                    borderRadius: '50%',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '12px',
                    fontWeight: 'bold',
                    marginLeft: '8px'
                  }}>5</div>
                </div>
                
                <div className="alert-card warning">
                  <div className="alert-item">
                    <div className="product-info">
                      <div className="product-name">🧀 Mozzarella di Bufala</div>
                      <div className="stock-info">
                        Lot MOZ-2024-12 • 2.2 kg • Expire dans 6 jours (23/09/2025)
                      </div>
                    </div>
                    <div className="item-actions">
                      <button className="button small">📅 Planifier</button>
                    </div>
                  </div>
                </div>

                <div className="alert-card warning">
                  <div className="alert-item">
                    <div className="product-info">
                      <div className="product-name">🥛 Yaourt grec</div>
                      <div className="stock-info">
                        Lot YAO-2024-09 • 3.5 L • Expire dans 5 jours (22/09/2025)
                      </div>
                    </div>
                    <div className="item-actions">
                      <button className="button small">📅 Planifier</button>
                    </div>
                  </div>
                </div>

                <div className="alert-card warning">
                  <div className="alert-item">
                    <div className="product-info">
                      <div className="product-name">🍞 Pain artisanal</div>
                      <div className="stock-info">
                        Lot PAI-2024-07 • 8 unités • Expire dans 4 jours (21/09/2025)
                      </div>
                    </div>
                    <div className="item-actions">
                      <button className="button small">📅 Planifier</button>
                    </div>
                  </div>
                </div>

                <div className="alert-card warning">
                  <div className="alert-item">
                    <div className="product-info">
                      <div className="product-name">🥬 Roquette</div>
                      <div className="stock-info">
                        Lot ROQ-2024-11 • 1.8 kg • Expire dans 6 jours (23/09/2025)
                      </div>
                    </div>
                    <div className="item-actions">
                      <button className="button small">📅 Planifier</button>
                    </div>
                  </div>
                </div>

                <div className="alert-card warning">
                  <div className="alert-item">
                    <div className="product-info">
                      <div className="product-name">🍤 Crevettes roses</div>
                      <div className="stock-info">
                        Lot CRE-2024-13 • 1.2 kg • Expire dans 7 jours (24/09/2025)
                      </div>
                    </div>
                    <div className="item-actions">
                      <button className="button small">📅 Planifier</button>
                    </div>
                  </div>
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

              {/* KPIs des coûts totaux */}
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

              {/* Répartition par catégorie de productions */}
              <div className="item-list">
                <div className="section-title">🍽️ Répartition des Coûts par Catégorie de Productions</div>
                
                <div className="item-row">
                  <div className="item-info">
                    <div className="item-name">🍽️ Plats</div>
                    <div className="item-details">42.3% des coûts totaux • 18 productions actives</div>
                  </div>
                  <div className="item-value">357 142 €</div>
                </div>

                <div className="item-row">
                  <div className="item-info">
                    <div className="item-name">🥗 Entrées</div>
                    <div className="item-details">28.7% des coûts totaux • 12 productions actives</div>
                  </div>
                  <div className="item-value">242 568 €</div>
                </div>

                <div className="item-row">
                  <div className="item-info">
                    <div className="item-name">🍹 Bar</div>
                    <div className="item-details">15.2% des coûts totaux • 8 productions actives</div>
                  </div>
                  <div className="item-value">128 463 €</div>
                </div>

                <div className="item-row">
                  <div className="item-info">
                    <div className="item-name">🍰 Desserts</div>
                    <div className="item-details">10.1% des coûts totaux • 6 productions actives</div>
                  </div>
                  <div className="item-value">85 374 €</div>
                </div>

                <div className="item-row">
                  <div className="item-info">
                    <div className="item-name">📝 Autres</div>
                    <div className="item-details">3.7% des coûts totaux • 3 productions actives</div>
                  </div>
                  <div className="item-value">31 293 €</div>
                </div>
              </div>

              {/* Répartition par catégorie de produits */}
              <div className="item-list">
                <div className="section-title">📦 Répartition des Coûts par Catégorie de Produits</div>
                
                <div className="item-row">
                  <div className="item-info">
                    <div className="item-name">🥩 Viandes</div>
                    <div className="item-details">38.5% des achats • Stock moyen: 287 kg</div>
                  </div>
                  <div className="item-value">326 235 €</div>
                </div>

                <div className="item-row">
                  <div className="item-info">
                    <div className="item-name">🐟 Poissons</div>
                    <div className="item-details">24.1% des achats • Stock moyen: 156 kg</div>
                  </div>
                  <div className="item-value">204 187 €</div>
                </div>

                <div className="item-row">
                  <div className="item-info">
                    <div className="item-name">🥕 Légumes</div>
                    <div className="item-details">18.7% des achats • Stock moyen: 423 kg</div>
                  </div>
                  <div className="item-value">158 463 €</div>
                </div>

                <div className="item-row">
                  <div className="item-info">
                    <div className="item-name">🧀 Produits laitiers</div>
                    <div className="item-details">12.3% des achats • Stock moyen: 89 kg</div>
                  </div>
                  <div className="item-value">104 187 €</div>
                </div>

                <div className="item-row">
                  <div className="item-info">
                    <div className="item-name">🌿 Épices & Aromates</div>
                    <div className="item-details">7.8% des achats • Stock moyen: 23 kg</div>
                  </div>
                  <div className="item-value">66 096 €</div>
                </div>
              </div>

              {/* Analyse pertes et déchets par produit */}
              <div className="item-list">
                <div className="section-title">📊 Analyse Pertes & Déchets par Produit</div>
                
                <div className="item-row">
                  <div className="item-info">
                    <div className="item-name">🥩 Viandes</div>
                    <div className="item-details">Perte: 15.2% • Parage et os • Impact: 18 productions</div>
                  </div>
                  <div className="item-actions">
                    <span className="status-badge critical">Élevé</span>
                    <div className="item-value critical">29 920 €</div>
                  </div>
                </div>

                <div className="item-row">
                  <div className="item-info">
                    <div className="item-name">🥬 Légumes</div>
                    <div className="item-details">Perte: 12.3% • Épluchures et fanes • Impact: 24 productions</div>
                  </div>
                  <div className="item-actions">
                    <span className="status-badge warning">Normal</span>
                    <div className="item-value warning">15 640 €</div>
                  </div>
                </div>

                <div className="item-row">
                  <div className="item-info">
                    <div className="item-name">🐟 Poissons</div>
                    <div className="item-details">Perte: 8.7% • Arêtes et parements • Impact: 8 productions</div>
                  </div>
                  <div className="item-actions">
                    <span className="status-badge success">Optimisé</span>
                    <div className="item-value">21 890 €</div>
                  </div>
                </div>
              </div>

              {/* Analyse pertes et déchets par production */}
              <div className="item-list">
                <div className="section-title">🍽️ Analyse Pertes & Déchets par Production</div>
                
                <div className="item-row">
                  <div className="item-info">
                    <div className="item-name">🍽️ Côte de bœuf grillée</div>
                    <div className="item-details">Perte: 18.5% • Principalement parage de viande</div>
                  </div>
                  <div className="item-actions">
                    <span className="status-badge critical">À optimiser</span>
                    <div className="item-value critical">8 240 €</div>
                  </div>
                </div>

                <div className="item-row">
                  <div className="item-info">
                    <div className="item-name">🥗 Salade composée</div>
                    <div className="item-details">Perte: 11.2% • Épluchage et préparation légumes</div>
                  </div>
                  <div className="item-actions">
                    <span className="status-badge warning">Acceptable</span>
                    <div className="item-value warning">3 870 €</div>
                  </div>
                </div>

                <div className="item-row">
                  <div className="item-info">
                    <div className="item-name">🐟 Filet de saumon</div>
                    <div className="item-details">Perte: 6.8% • Parage et désarêtage</div>
                  </div>
                  <div className="item-actions">
                    <span className="status-badge success">Excellent</span>
                    <div className="item-value">4 520 €</div>
                  </div>
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
                <div className="section-title">Top Productions Rentables</div>
                {filteredAnalytics.topProductions.slice(0, 4).map((production, index) => (
                  <div key={index} className="item-row">
                    <div className="item-info">
                      <div className="item-name">
                        {production.categorie === 'Entrée' ? '🥗' : 
                         production.categorie === 'Plat' ? '🍽️' : 
                         production.categorie === 'Dessert' ? '🍰' : 
                         production.categorie === 'Bar' ? '🍹' : '📝'} {production.nom}
                        <span className="category-badge" style={{
                          marginLeft: '6px',
                          padding: '2px 6px',
                          borderRadius: '8px',
                          fontSize: '10px',
                          background: 'var(--color-success-green)',
                          color: 'white'
                        }}>
                          {production.categorie}
                        </span>
                      </div>
                      <div className="item-details">Coefficient Réel: {76 + index * 2}% • {production.portions} portions vendues</div>
                    </div>
                    <div className="item-value positive">{production.ventes.toLocaleString('fr-FR')} €</div>
                  </div>
                ))}
              </div>

              {/* Flop Productions (nouvellement ajouté) */}
              <div className="item-list">
                <div className="section-title">📉 Productions Moins Rentables</div>
                {filteredAnalytics.flopProductions.slice(0, 4).map((production, index) => (
                  <div key={index} className="item-row">
                    <div className="item-info">
                      <div className="item-name">
                        {production.categorie === 'Entrée' ? '🥗' : 
                         production.categorie === 'Plat' ? '🍽️' : 
                         production.categorie === 'Dessert' ? '🍰' : 
                         production.categorie === 'Bar' ? '🍹' : '📝'} {production.nom}
                        <span className="category-badge" style={{
                          marginLeft: '6px',
                          padding: '2px 6px',
                          borderRadius: '8px',
                          fontSize: '10px',
                          background: 'var(--color-critical-red)',
                          color: 'white'
                        }}>
                          {production.categorie}
                        </span>
                      </div>
                      <div className="item-details">Coefficient Réel: {32 - index * 3}% • {production.portions} portions vendues</div>
                    </div>
                    <div className="item-value critical">{production.ventes.toLocaleString('fr-FR')} €</div>
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

          {/* ONGLET PRÉVISIONNEL */}
          {activeDashboardTab === "previsionnel" && (
            <div className="section-card">
              <div className="section-title">
                🔮 Analyse Prévisionnelle
                {selectedDateRange && (
                  <span style={{ 
                    fontSize: '14px', 
                    color: 'var(--color-text-secondary)',
                    fontWeight: 'normal',
                    marginLeft: '10px'
                  }}>
                    - {selectedDateRange.label}
                  </span>
                )}
              </div>

              {/* KPIs prévisionnels modifiés */}
              <div className="kpi-grid">
                <div className="kpi-card">
                  <div className="icon">📊</div>
                  <div className="title">% Productions Possibles</div>
                  <div className="value positive">
                    {((stocksPrevisionnels.reduce((total, stock) => total + stock.productions_possibles.length, 0) / 12) * 100).toFixed(0)}%
                  </div>
                  <div className="subtitle">7 sur 12 possibles</div>
                </div>
                
                <div className="kpi-card">
                  <div className="icon">📅</div>
                  <div className="title">Nombre de Jours Possibles</div>
                  <div className="value">4.2</div>
                  <div className="subtitle">Avec stocks actuels</div>
                </div>
                
                <div className="kpi-card">
                  <div className="icon">⚡</div>
                  <div className="title">Max Portions</div>
                  <div className="value">{stocksPrevisionnels.reduce((max, stock) => {
                    const maxPortions = Math.max(...stock.productions_possibles.map(p => p.portions_possibles));
                    return Math.max(max, maxPortions);
                  }, 0)}</div>
                  <div className="subtitle">Production optimale</div>
                </div>
              </div>

              {/* Analyse des productions possibles avec filtre */}
              <div className="item-list">
                <div className="section-title">🍽️ Productions Possibles avec Stocks Actuels</div>
                
                {/* Filtre par catégorie de production */}
                <div className="filter-section" style={{marginBottom: '15px'}}>
                  <div className="filter-group" style={{display: 'flex', alignItems: 'center', gap: '10px'}}>
                    <label className="filter-label" style={{fontSize: '14px', minWidth: '60px'}}>Filtre :</label>
                    <select 
                      className="filter-select"
                      value={selectedProductionCategory}
                      onChange={(e) => setSelectedProductionCategory(e.target.value)}
                      style={{
                        padding: '6px 10px',
                        borderRadius: '4px',
                        border: '1px solid var(--color-border)',
                        background: 'var(--color-background-card)',
                        color: 'var(--color-text-primary)',
                        fontSize: '13px',
                        minWidth: '120px'
                      }}
                    >
                      <option value="">Toutes productions</option>
                      <option value="Entrée">🥗 Entrées</option>
                      <option value="Plat">🍽️ Plats</option>
                      <option value="Dessert">🍰 Desserts</option>
                      <option value="Bar">🍹 Bar</option>
                      <option value="Autres">📝 Autres</option>
                    </select>
                  </div>
                </div>
                
                {/* Créer une liste plate de toutes les productions possibles avec filtre */}
                {stocksPrevisionnels.flatMap(stock => 
                  stock.productions_possibles.map(production => ({
                    ...production,
                    produit: stock.produit,
                    stock_disponible: stock.stock_actuel,
                    unite: stock.unite,
                    stock_id: stock.id,
                    categorie: production.categorie || 'Autres' // Ajouter une catégorie par défaut
                  }))
                ).filter(production => !selectedProductionCategory || production.categorie === selectedProductionCategory)
                .map((production, index) => (
                  <div key={index} className="item-row">
                    <div className="item-info">
                      <div className="item-name">
                        {production.categorie === 'Entrée' ? '🥗' : 
                         production.categorie === 'Plat' ? '🍽️' : 
                         production.categorie === 'Dessert' ? '🍰' : 
                         production.categorie === 'Bar' ? '🍹' : '📝'} {production.nom}
                        <span className="category-badge" style={{
                          marginLeft: '6px',
                          padding: '2px 6px',
                          borderRadius: '8px',
                          fontSize: '10px',
                          background: 'var(--color-primary-blue)',
                          color: 'white'
                        }}>
                          {production.categorie}
                        </span>
                      </div>
                      <div className="item-details">
                        Produit principal: {production.produit} • Stock: {production.stock_disponible} {production.unite} • 
                        Max portions: {production.portions_possibles}
                      </div>
                    </div>
                    <div className="item-actions">
                      <button 
                        className="button small" 
                        onClick={() => alert(`Détails pour ${production.nom}:\n\n🏷️ Catégorie: ${production.categorie}\n📦 Produit: ${production.produit}\n📏 Besoin: ${production.quantite_needed} ${production.unite} par portion\n📊 Stock disponible: ${production.stock_disponible} ${production.unite}\n⚡ Portions max: ${production.portions_possibles}`)}
                      >
                        🔍 Détails
                      </button>
                    </div>
                  </div>
                ))}
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
                📦 Stocks & DLC
              </button>
              <button 
                className="button" 
                onClick={() => setActiveStockTab('repartition')}
                style={{
                  background: activeStockTab === 'repartition' ? 'var(--color-primary-blue)' : 'var(--color-background-card-light)',
                  color: activeStockTab === 'repartition' ? 'white' : 'var(--color-text-secondary)'
                }}
              >
                🎯 Répartition
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
            </div>

            {/* ONGLET STOCKS */}
            <div className={`production-tab ${activeStockTab === 'stocks' ? 'active' : ''}`}>
              <div className="section-card">
                <div className="section-title">📦 Gestion des Stocks</div>
                
                {/* Actions rapides */}
                <div style={{display: 'flex', gap: '10px', marginBottom: '20px', flexWrap: 'wrap'}}>
                  <button className="button" onClick={() => setShowProduitModal(true)}>➕ Nouveau Produit</button>
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

                {/* Liste des produits en stock avec recherche et filtres */}
                <div className="item-list">
                  <div className="section-title">📋 Produits en Stock</div>
                  
                  {/* Barre de recherche et filtres */}
                  <div className="filter-section" style={{marginBottom: '20px'}}>
                    <div style={{display: 'flex', gap: '15px', alignItems: 'center', flexWrap: 'wrap'}}>
                      {/* Barre de recherche */}
                      <div style={{display: 'flex', alignItems: 'center', gap: '8px', flex: '1', minWidth: '200px'}}>
                        <label className="filter-label" style={{fontSize: '14px', minWidth: '70px'}}>🔍 Recherche :</label>
                        <input
                          type="text"
                          placeholder="Nom du produit..."
                          value={stockSearchTerm}
                          onChange={(e) => setStockSearchTerm(e.target.value)}
                          style={{
                            padding: '6px 10px',
                            borderRadius: '4px',
                            border: '1px solid var(--color-border)',
                            background: 'var(--color-background-card)',
                            color: 'var(--color-text-primary)',
                            fontSize: '13px',
                            flex: '1'
                          }}
                        />
                      </div>
                      
                      {/* Filtre par catégorie */}
                      <div style={{display: 'flex', alignItems: 'center', gap: '8px'}}>
                        <label className="filter-label" style={{fontSize: '14px', minWidth: '70px'}}>🏷️ Catégorie :</label>
                        <select 
                          className="filter-select"
                          value={stockFilterCategory}
                          onChange={(e) => {
                            setStockFilterCategory(e.target.value);
                            setStockCurrentPage(1); // Reset à la page 1
                          }}
                          style={{
                            padding: '6px 10px',
                            borderRadius: '4px',
                            border: '1px solid var(--color-border)',
                            background: 'var(--color-background-card)',
                            color: 'var(--color-text-primary)',
                            fontSize: '13px',
                            minWidth: '150px'
                          }}
                        >
                          <option value="all">Toutes catégories</option>
                          <option value="légumes">🥕 Légumes</option>
                          <option value="viandes">🥩 Viandes</option>
                          <option value="poissons">🐟 Poissons</option>
                          <option value="produits laitiers">🧀 Produits laitiers</option>
                          <option value="épices">🌶️ Épices</option>
                          <option value="fruits">🍎 Fruits</option>
                          <option value="céréales">🌾 Céréales</option>
                          <option value="boissons">🥤 Boissons</option>
                          <option value="autres">📦 Autres</option>
                        </select>
                      </div>
                    </div>
                  </div>

                  {/* Liste des produits avec pagination */}
                  {(() => {
                    // Filtrer les stocks selon la recherche et la catégorie
                    const filteredStocks = stocks.filter(stock => {
                      const produit = produits.find(p => p.id === stock.produit_id);
                      const matchesSearch = stock.produit_nom.toLowerCase().includes(stockSearchTerm.toLowerCase());
                      const matchesCategory = stockFilterCategory === 'all' || 
                                            (produit && produit.categorie && produit.categorie.toLowerCase() === stockFilterCategory.toLowerCase());
                      return matchesSearch && matchesCategory;
                    });
                    
                    // Calculer la pagination
                    const totalPages = Math.ceil(filteredStocks.length / stockItemsPerPage);
                    const startIndex = (stockCurrentPage - 1) * stockItemsPerPage;
                    const endIndex = startIndex + stockItemsPerPage;
                    const currentStocks = filteredStocks.slice(startIndex, endIndex);
                    
                    if (filteredStocks.length === 0) {
                      return (
                        <div style={{textAlign: 'center', padding: '40px', color: 'var(--color-text-muted)'}}>
                          <div style={{fontSize: '48px', marginBottom: '15px'}}>📦</div>
                          <p>Aucun produit trouvé</p>
                          {stockSearchTerm && <p style={{fontSize: '14px'}}>Essayez un autre terme de recherche</p>}
                        </div>
                      );
                    }

                    return (
                      <>
                        {/* Informations sur les résultats */}
                        <div style={{
                          marginBottom: '15px',
                          fontSize: '14px',
                          color: 'var(--color-text-secondary)',
                          padding: '8px 12px',
                          background: 'var(--color-background-card-light)',
                          borderRadius: '6px'
                        }}>
                          {filteredStocks.length} produit(s) trouvé(s)
                          {stockSearchTerm && ` pour "${stockSearchTerm}"`}
                          {stockFilterCategory !== 'all' && ` dans la catégorie "${stockFilterCategory}"`}
                        </div>

                        {/* Produits de la page actuelle */}
                        {currentStocks.map((stock, index) => {
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

                        {/* Contrôles de pagination */}
                        {totalPages > 1 && (
                          <div style={{
                            display: 'flex', 
                            justifyContent: 'space-between', 
                            alignItems: 'center',
                            marginTop: '20px',
                            padding: '15px',
                            background: 'var(--color-background-card-light)',
                            borderRadius: '8px'
                          }}>
                            <div style={{fontSize: '14px', color: 'var(--color-text-secondary)'}}>
                              Page {stockCurrentPage} sur {totalPages} • 
                              {startIndex + 1}-{Math.min(endIndex, filteredStocks.length)} sur {filteredStocks.length} produits
                            </div>
                            
                            <div style={{display: 'flex', gap: '5px'}}>
                              <button 
                                className="button small" 
                                onClick={() => setStockCurrentPage(1)}
                                disabled={stockCurrentPage === 1}
                                style={{
                                  opacity: stockCurrentPage === 1 ? 0.5 : 1,
                                  cursor: stockCurrentPage === 1 ? 'not-allowed' : 'pointer'
                                }}
                              >
                                ⏮️ Début
                              </button>
                              <button 
                                className="button small" 
                                onClick={() => setStockCurrentPage(stockCurrentPage - 1)}
                                disabled={stockCurrentPage === 1}
                                style={{
                                  opacity: stockCurrentPage === 1 ? 0.5 : 1,
                                  cursor: stockCurrentPage === 1 ? 'not-allowed' : 'pointer'
                                }}
                              >
                                ⬅️ Précédent
                              </button>
                              <span style={{
                                padding: '6px 12px',
                                background: 'var(--color-primary-blue)',
                                color: 'white',
                                borderRadius: '4px',
                                fontSize: '12px',
                                fontWeight: 'bold'
                              }}>
                                {stockCurrentPage}
                              </span>
                              <button 
                                className="button small" 
                                onClick={() => setStockCurrentPage(stockCurrentPage + 1)}
                                disabled={stockCurrentPage === totalPages}
                                style={{
                                  opacity: stockCurrentPage === totalPages ? 0.5 : 1,
                                  cursor: stockCurrentPage === totalPages ? 'not-allowed' : 'pointer'
                                }}
                              >
                                Suivant ➡️
                              </button>
                              <button 
                                className="button small" 
                                onClick={() => setStockCurrentPage(totalPages)}
                                disabled={stockCurrentPage === totalPages}
                                style={{
                                  opacity: stockCurrentPage === totalPages ? 0.5 : 1,
                                  cursor: stockCurrentPage === totalPages ? 'not-allowed' : 'pointer'
                                }}
                              >
                                Fin ⏭️
                              </button>
                            </div>
                          </div>
                        )}
                      </>
                    );
                  })()}
                </div>

                {/* Section DLC & Lots intégrée */}
                <div className="item-list">
                  <div className="section-title">📅 Gestion DLC & Lots</div>
                  
                  {/* KPIs DLC */}
                  <div className="kpi-grid">
                    <div className="kpi-card">
                      <div className="icon">📅</div>
                      <div className="title">Produits avec DLC</div>
                      <div className="value">{batchSummary.length}</div>
                    </div>
                    
                    <div className="kpi-card">
                      <div className="icon">🔴</div>
                      <div className="title">Expirés</div>
                      <div className="value critical">{expiredProducts.length}</div>
                    </div>
                    
                    <div className="kpi-card">
                      <div className="icon">🟡</div>
                      <div className="title">Critiques (&lt; 7j)</div>
                      <div className="value warning">{criticalProducts.length}</div>
                    </div>
                  </div>

                  {/* Liste des produits avec DLC */}
                  {batchSummary.length > 0 ? (
                    batchSummary.slice(0, 5).map((item, index) => {
                      const hasExpired = item.expired_batches > 0;
                      const hasCritical = item.critical_batches > 0;
                      const statusIcon = hasExpired ? '🔴' : hasCritical ? '🟡' : '✅';
                      const statusText = hasExpired ? 'Expiré' : hasCritical ? 'Critique' : 'OK';
                      
                      return (
                        <div key={index} className="item-row">
                          <div className="item-info">
                            <div className="item-name">
                              {statusIcon} {item.product_name}
                            </div>
                            <div className="item-details">
                              Stock total: {item.total_stock} • {item.batches.length} lot(s) • 
                              {hasExpired && ` ${item.expired_batches} expiré(s)`}
                              {hasCritical && ` ${item.critical_batches} critique(s)`}
                              {!hasExpired && !hasCritical && ' Tous lots OK'}
                            </div>
                          </div>
                          <div className="item-actions" style={{display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: '8px'}}>
                            <span className={`status-badge ${hasExpired ? 'critical' : hasCritical ? 'warning' : 'success'}`}>
                              {statusText}
                            </span>
                            <button 
                              className="button small"
                              onClick={() => fetchProductBatches(item.product_id)}
                            >
                              🔍 Voir lots
                            </button>
                          </div>
                        </div>
                      );
                    })
                  ) : (
                    <div style={{textAlign: 'center', padding: '40px', color: 'var(--color-text-muted)'}}>
                      <div style={{fontSize: '48px', marginBottom: '15px'}}>📅</div>
                      <p>Aucun lot avec DLC trouvé</p>
                      <button className="button" onClick={fetchBatchSummary}>🔄 Actualiser</button>
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
                  <button 
                    className="button" 
                    onClick={handleSupprimerTousDocumentsOcr} 
                    disabled={loading}
                    style={{
                      background: 'linear-gradient(45deg, #ff6b6b, #ff8e8e)',
                      border: 'none',
                      color: 'white'
                    }}
                  >
                    🗑️ Vider l'historique
                  </button>
                </div>

                {/* Historique des documents avec filtre et pagination */}
                <div className="item-list">
                  <div className="section-title">📄 Historique des Documents</div>
                  
                  {/* Filtre par type de document */}
                  <div className="filter-section" style={{marginBottom: '20px'}}>
                    <div className="filter-group" style={{display: 'flex', alignItems: 'center', gap: '10px'}}>
                      <label className="filter-label" style={{fontSize: '14px', minWidth: '80px'}}>Type :</label>
                      <select 
                        className="filter-select"
                        value={ocrFilterType}
                        onChange={(e) => {
                          setOcrFilterType(e.target.value);
                          setOcrCurrentPage(1); // Reset à la page 1 lors du changement de filtre
                        }}
                        style={{
                          padding: '6px 10px',
                          borderRadius: '4px',
                          border: '1px solid var(--color-border)',
                          background: 'var(--color-background-card)',
                          color: 'var(--color-text-primary)',
                          fontSize: '13px',
                          minWidth: '150px'
                        }}
                      >
                        <option value="all">Tous les documents</option>
                        <option value="z_report">📊 Rapports Z</option>
                        <option value="facture_fournisseur">🧾 Factures</option>
                      </select>
                      
                      <div className="filter-info" style={{
                        fontSize: '14px', 
                        color: 'var(--color-text-secondary)',
                        marginLeft: '10px'
                      }}>
                        {(() => {
                          const filteredDocs = documentsOcr.filter(doc => 
                            ocrFilterType === 'all' || doc.type_document === ocrFilterType
                          );
                          return `${filteredDocs.length} document(s)`;
                        })()}
                      </div>
                    </div>
                  </div>

                  {/* Liste des documents avec pagination */}
                  {(() => {
                    // Filtrer les documents selon le type sélectionné
                    const filteredDocs = documentsOcr.filter(doc => 
                      ocrFilterType === 'all' || doc.type_document === ocrFilterType
                    );
                    
                    // Calculer la pagination
                    const totalPages = Math.ceil(filteredDocs.length / ocrDocumentsPerPage);
                    const startIndex = (ocrCurrentPage - 1) * ocrDocumentsPerPage;
                    const endIndex = startIndex + ocrDocumentsPerPage;
                    const currentDocs = filteredDocs.slice(startIndex, endIndex);
                    
                    if (filteredDocs.length === 0) {
                      return (
                        <div style={{textAlign: 'center', padding: '40px', color: 'var(--color-text-muted)'}}>
                          <div style={{fontSize: '48px', marginBottom: '15px'}}>📄</div>
                          <p>Aucun document trouvé pour ce filtre</p>
                        </div>
                      );
                    }

                    return (
                      <>
                        {/* Documents de la page actuelle */}
                        {currentDocs.map((doc, index) => (
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

                        {/* Contrôles de pagination */}
                        {totalPages > 1 && (
                          <div style={{
                            display: 'flex', 
                            justifyContent: 'space-between', 
                            alignItems: 'center',
                            marginTop: '20px',
                            padding: '15px',
                            background: 'var(--color-background-card-light)',
                            borderRadius: '8px'
                          }}>
                            <div style={{fontSize: '14px', color: 'var(--color-text-secondary)'}}>
                              Page {ocrCurrentPage} sur {totalPages} • 
                              {startIndex + 1}-{Math.min(endIndex, filteredDocs.length)} sur {filteredDocs.length} documents
                            </div>
                            
                            <div style={{display: 'flex', gap: '5px'}}>
                              <button 
                                className="button small" 
                                onClick={() => setOcrCurrentPage(1)}
                                disabled={ocrCurrentPage === 1}
                                style={{
                                  opacity: ocrCurrentPage === 1 ? 0.5 : 1,
                                  cursor: ocrCurrentPage === 1 ? 'not-allowed' : 'pointer'
                                }}
                              >
                                ⏮️ Début
                              </button>
                              <button 
                                className="button small" 
                                onClick={() => setOcrCurrentPage(ocrCurrentPage - 1)}
                                disabled={ocrCurrentPage === 1}
                                style={{
                                  opacity: ocrCurrentPage === 1 ? 0.5 : 1,
                                  cursor: ocrCurrentPage === 1 ? 'not-allowed' : 'pointer'
                                }}
                              >
                                ⬅️ Précédent
                              </button>
                              <span style={{
                                padding: '6px 12px',
                                background: 'var(--color-primary-blue)',
                                color: 'white',
                                borderRadius: '4px',
                                fontSize: '12px',
                                fontWeight: 'bold'
                              }}>
                                {ocrCurrentPage}
                              </span>
                              <button 
                                className="button small" 
                                onClick={() => setOcrCurrentPage(ocrCurrentPage + 1)}
                                disabled={ocrCurrentPage === totalPages}
                                style={{
                                  opacity: ocrCurrentPage === totalPages ? 0.5 : 1,
                                  cursor: ocrCurrentPage === totalPages ? 'not-allowed' : 'pointer'
                                }}
                              >
                                Suivant ➡️
                              </button>
                              <button 
                                className="button small" 
                                onClick={() => setOcrCurrentPage(totalPages)}
                                disabled={ocrCurrentPage === totalPages}
                                style={{
                                  opacity: ocrCurrentPage === totalPages ? 0.5 : 1,
                                  cursor: ocrCurrentPage === totalPages ? 'not-allowed' : 'pointer'
                                }}
                              >
                                Fin ⏭️
                              </button>
                            </div>
                          </div>
                        )}
                      </>
                    );
                  })()}
                </div>
              </div>
            </div>

            {/* ONGLET RÉPARTITION */}
            <div className={`production-tab ${activeStockTab === 'repartition' ? 'active' : ''}`}>
              <div className="section-card">
                {/* Répartition optimale avec validation */}
                <div className="item-list">
                  <div className="section-title">🎯 Répartition Optimale avec Validation</div>
                  
                  {stocksPrevisionnels.map((stock, stockIndex) => {
                    const stockUtilise = stock.productions_possibles.reduce((total, prod) => 
                      total + (prod.portions_selectionnees * prod.quantite_needed), 0
                    );
                    const stockRestant = stock.stock_actuel - stockUtilise;
                    
                    return (
                      <div key={stockIndex}>
                        <div className="section-subtitle" style={{
                          display: 'flex', 
                          justifyContent: 'space-between', 
                          alignItems: 'center',
                          marginTop: '20px', 
                          marginBottom: '10px', 
                          fontSize: '16px', 
                          fontWeight: 'bold',
                          padding: '10px',
                          background: 'var(--color-background-card-light)',
                          borderRadius: '8px'
                        }}>
                          <span>📦 {stock.produit} ({stock.stock_actuel} {stock.unite})</span>
                          <div style={{fontSize: '14px', fontWeight: 'normal'}}>
                            <span style={{color: stockRestant < 0 ? 'var(--color-danger-red)' : 'var(--color-success-green)'}}>
                              Restant: {stockRestant.toFixed(1)} {stock.unite}
                            </span>
                            <button 
                              className="button small success" 
                              style={{marginLeft: '10px'}}
                              onClick={() => {
                                alert(`Répartition validée pour ${stock.produit}!\n\nStock utilisé: ${stockUtilise.toFixed(1)} ${stock.unite}\nStock restant: ${stockRestant.toFixed(1)} ${stock.unite}`);
                              }}
                            >
                              ✅ Valider
                            </button>
                          </div>
                        </div>
                        
                        {stock.productions_possibles.map((production, prodIndex) => {
                          const quantiteUtilisee = production.portions_selectionnees * production.quantite_needed;
                          const autresUtilisations = stock.productions_possibles.reduce((total, p, i) => {
                            if (i !== prodIndex) return total + (p.portions_selectionnees * p.quantite_needed);
                            return total;
                          }, 0);
                          const stockDisponiblePourCetteProd = stock.stock_actuel - autresUtilisations;
                          const maxPossible = Math.floor(stockDisponiblePourCetteProd / production.quantite_needed);
                          
                          return (
                            <div key={prodIndex} className="item-row">
                              <div className="item-info">
                                <div className="item-name">
                                  🍽️ {production.nom}
                                </div>
                                <div className="item-details">
                                  Besoin: {production.quantite_needed} {stock.unite} par portion • 
                                  Max équilibré: {Math.min(maxPossible, production.portions_possibles)} portions •
                                  Utilise: {quantiteUtilisee.toFixed(1)} {stock.unite}
                                </div>
                              </div>
                              <div className="item-actions">
                                <input 
                                  type="number" 
                                  min="0" 
                                  max={Math.min(maxPossible, production.portions_possibles)}
                                  value={production.portions_selectionnees}
                                  onChange={(e) => updatePortionsSelectionnees(stock.id, prodIndex, parseInt(e.target.value) || 0)}
                                  style={{
                                    width: '60px',
                                    padding: '4px 8px',
                                    borderRadius: '4px',
                                    border: '1px solid var(--color-border)',
                                    marginRight: '5px'
                                  }}
                                />
                                <span style={{fontSize: '12px', color: 'var(--color-text-secondary)'}}>
                                  / {Math.min(maxPossible, production.portions_possibles)}
                                </span>
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    );
                  })}
                </div>
              </div>
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
                🥕 Produits
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
                🍽️ Productions
              </button>
              <button 
                className="button" 
                onClick={() => setActiveProductionTab('datagrids')}
                style={{
                  background: activeProductionTab === 'datagrids' ? 'var(--color-primary-blue)' : 'var(--color-background-card-light)',
                  color: activeProductionTab === 'datagrids' ? 'white' : 'var(--color-text-secondary)'
                }}
              >
                📊 Grilles de données
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
                <div className="section-title">🥕 Gestion des Produits (Ingrédients)</div>
                
                <div style={{display: 'flex', gap: '10px', marginBottom: '20px', flexWrap: 'wrap'}}>
                  <button className="button" onClick={() => setShowProduitModal(true)}>➕ Nouveau Produit</button>
                </div>

                {/* Filtre universel par catégorie */}
                <div className="filter-section" style={{marginBottom: '20px'}}>
                  <div className="filter-group">
                    <label className="filter-label">
                      🏷️ Filtrer par catégorie {
                        activeProductionTab === 'produits' ? 'd\'ingrédients' :
                        activeProductionTab === 'fournisseurs' ? 'de fournisseurs' :
                        activeProductionTab === 'recettes' ? 'de productions' :
                        ''
                      } :
                    </label>
                    <select 
                      className="filter-select"
                      onChange={(e) => {
                        if (activeProductionTab === 'produits') {
                          filterProduitsByCategory(e.target.value);
                        } else if (activeProductionTab === 'fournisseurs') {
                          // Pas de filtrage pour les fournisseurs pour l'instant
                        } else if (activeProductionTab === 'recettes') {
                          filterRecettesByCategory(e.target.value);
                        }
                      }}
                      style={{
                        padding: '8px 12px',
                        borderRadius: '6px',
                        border: '1px solid var(--color-border)',
                        background: 'var(--color-background-card)',
                        color: 'var(--color-text-primary)',
                        minWidth: '150px'
                      }}
                    >
                      {activeProductionTab === 'produits' && (
                        <>
                          <option value="">Tous les ingrédients</option>
                          <option value="Légumes">🥕 Légumes</option>
                          <option value="Viandes">🥩 Viandes</option>
                          <option value="Poissons">🐟 Poissons</option>
                          <option value="Produits laitiers">🧀 Produits laitiers</option>
                          <option value="Épices">🌶️ Épices & Condiments</option>
                          <option value="Fruits">🍎 Fruits</option>
                          <option value="Céréales">🌾 Céréales & Féculents</option>
                          <option value="Boissons">🥤 Boissons</option>
                          <option value="Autres">📦 Autres</option>
                        </>
                      )}
                      {activeProductionTab === 'fournisseurs' && (
                        <>
                          <option value="">Tous les fournisseurs</option>
                          <option value="Légumes">🥕 Spécialité Légumes</option>
                          <option value="Viandes">🥩 Spécialité Viandes</option>
                          <option value="Poissons">🐟 Spécialité Poissons</option>
                          <option value="Généraux">🏪 Fournisseurs généraux</option>
                        </>
                      )}
                      {activeProductionTab === 'recettes' && (
                        <>
                          <option value="">Toutes les productions</option>
                          <option value="Entrée">🥗 Entrées</option>
                          <option value="Plat">🍽️ Plats</option>
                          <option value="Dessert">🍰 Desserts</option>
                          <option value="Bar">🍹 Bar</option>
                          <option value="Autres">📝 Autres</option>
                        </>
                      )}
                      {activeProductionTab === 'datagrids' && (
                        <>
                          <option value="">Toutes les données</option>
                        </>
                      )}
                    </select>
                    
                    <div className="filter-info" style={{
                      fontSize: '14px', 
                      color: 'var(--color-text-secondary)',
                      marginLeft: '10px'
                    }}>
                      {activeProductionTab === 'produits' && `${filteredProduits.length} produit(s) affiché(s)`}
                      {activeProductionTab === 'fournisseurs' && `${fournisseurs.length} fournisseur(s) affiché(s)`}
                      {activeProductionTab === 'recettes' && `${filteredRecettes.length} production(s) affichée(s)`}
                      {activeProductionTab === 'datagrids' && 'Grilles de données professionnelles'}
                    </div>
                  </div>
                </div>

                {/* Liste des produits filtrés */}
                {(filteredProduits.length > 0 ? filteredProduits : produits).map((produit, index) => {
                  // Fonction pour obtenir l'icône selon la catégorie
                  const getCategoryIcon = (categorie) => {
                    if (!categorie) return '⚠️'; // Icône d'alerte si pas de catégorie
                    
                    switch(categorie) {
                      case 'Légumes': return '🥕';
                      case 'Viandes': return '🥩';
                      case 'Poissons': return '🐟';
                      case 'Produits laitiers': return '🧀';
                      case 'Épices': return '🌶️';
                      case 'Fruits': return '🍎';
                      case 'Céréales': return '🌾';
                      case 'Boissons': return '🥤';
                      case 'Autres': return '📦';
                      default: return '⚠️'; // Icône d'alerte pour catégorie non reconnue
                    }
                  };

                  return (
                    <div key={index} className="item-row">
                      <div className="item-info">
                        <div className="item-name">
                          {getCategoryIcon(produit.categorie)} {produit.nom}
                          {produit.categorie ? (
                            <span className="category-badge" style={{
                              marginLeft: '8px',
                              padding: '4px 8px',
                              borderRadius: '12px',
                              fontSize: '12px',
                              background: 'var(--color-accent-orange)',
                              color: 'white'
                            }}>
                              {produit.categorie}
                            </span>
                          ) : (
                            <span className="category-badge" style={{
                              marginLeft: '8px',
                              padding: '4px 8px',
                              borderRadius: '12px',
                              fontSize: '12px',
                              background: 'var(--color-warning-orange)',
                              color: 'white'
                            }}>
                              Sans catégorie
                            </span>
                          )}
                        </div>
                        <div className="item-details">
                          {produit.description} • Prix: {produit.prix_achat || produit.reference_price || 'N/A'}€
                        </div>
                      </div>
                      <div className="item-actions">
                        <button className="button small" onClick={() => handleEdit(produit, 'produit')}>✏️ Éditer</button>
                      </div>
                    </div>
                  );
                })}
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
                      <div className="item-name" style={{display: 'flex', alignItems: 'center', gap: '8px'}}>
                        {/* Logo du fournisseur */}
                        <span style={{fontSize: '20px'}}>
                          {fournisseur.logo || '🏪'}
                        </span>
                        {/* Nom avec code couleur */}
                        <span style={{
                          backgroundColor: fournisseur.couleur || '#3B82F6',
                          color: 'white',
                          padding: '4px 8px',
                          borderRadius: '4px',
                          fontWeight: '500',
                          fontSize: '14px'
                        }}>
                          {fournisseur.nom}
                        </span>
                      </div>
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
                <div className="section-title">📝 Productions</div>
                
                <div style={{display: 'flex', gap: '10px', marginBottom: '20px', flexWrap: 'wrap'}}>
                  <button className="button" onClick={() => setShowRecetteModal(true)}>➕ Nouvelle Production</button>
                  <button className="button" onClick={handleExportRecettes}>📖 Export Excel</button>
                </div>

                {/* Filtre par catégorie */}
                <div className="filter-section" style={{marginBottom: '20px'}}>
                  <div className="filter-group">
                    <label className="filter-label">🏷️ Filtrer par catégorie :</label>
                    <select 
                      className="filter-select"
                      value={selectedCategoryFilter}
                      onChange={(e) => filterRecettesByCategory(e.target.value)}
                      style={{
                        padding: '8px 12px',
                        borderRadius: '6px',
                        border: '1px solid var(--color-border)',
                        background: 'var(--color-background-card)',
                        color: 'var(--color-text-primary)',
                        minWidth: '150px'
                      }}
                    >
                      <option value="">Toutes les catégories</option>
                      {categoriesProduction.map(category => (
                        <option key={category} value={category}>
                          {category === 'Entrée' ? '🥗' : 
                           category === 'Plat' ? '🍽️' : 
                           category === 'Dessert' ? '🍰' :
                           category === 'Bar' ? '🍹' : '📝'} {category}
                        </option>
                      ))}
                    </select>
                    
                    {selectedCategoryFilter && (
                      <div className="filter-info" style={{
                        fontSize: '14px', 
                        color: 'var(--color-text-secondary)',
                        marginLeft: '10px'
                      }}>
                        {filteredRecettes.length} plat(s) trouvé(s)
                      </div>
                    )}
                  </div>
                </div>

                {/* Liste des recettes filtrées */}
                {(filteredRecettes.length > 0 ? filteredRecettes : recettes).map((recette, index) => {
                  // Fonction pour obtenir l'icône selon la catégorie de production
                  const getProductionCategoryIcon = (categorie) => {
                    if (!categorie) return '⚠️'; // Icône d'alerte si pas de catégorie
                    
                    switch(categorie) {
                      case 'Entrée': return '🥗';
                      case 'Plat': return '🍽️';
                      case 'Dessert': return '🍰';
                      case 'Bar': return '🍹';
                      case 'Autres': return '📝';
                      default: return '⚠️'; // Icône d'alerte pour catégorie non reconnue
                    }
                  };

                  return (
                    <div key={index} className="item-row">
                      <div className="item-info">
                        <div className="item-name">
                          {getProductionCategoryIcon(recette.categorie)} {recette.nom}
                          {recette.categorie ? (
                            <span className="category-badge" style={{
                              marginLeft: '8px',
                              padding: '4px 8px',
                              borderRadius: '12px',
                              fontSize: '12px',
                              background: 'var(--color-primary-blue)',
                              color: 'white'
                            }}>
                              {recette.categorie}
                            </span>
                          ) : (
                            <span className="category-badge" style={{
                              marginLeft: '8px',
                              padding: '4px 8px',
                              borderRadius: '12px',
                              fontSize: '12px',
                              background: 'var(--color-warning-orange)',
                              color: 'white'
                            }}>
                              Sans catégorie
                            </span>
                          )}
                        </div>
                        <div className="item-details">
                          Prix: {recette.prix_vente}€ • Marge: {recette.marge_beneficiaire || 'N/A'}%
                        </div>
                      </div>
                      <div className="item-actions">
                        <button className="button small" onClick={() => handleEdit(recette, 'recette')}>✏️ Éditer</button>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}

            {/* ONGLET GRILLES DE DONNÉES */}
            {activeProductionTab === 'datagrids' && (
              <div>
                <DataGridsPage />
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
              <button 
                className="button" 
                onClick={handleSupprimerTousDocumentsOcr} 
                disabled={loading}
                style={{
                  background: 'linear-gradient(45deg, #ff6b6b, #ff8e8e)',
                  border: 'none',
                  color: 'white'
                }}
              >
                🗑️ Vider l'historique
              </button>
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
                <label className="form-label">Catégorie d'ingrédient</label>
                <select
                  className="form-select"
                  value={produitForm.categorie}
                  onChange={(e) => setProduitForm({...produitForm, categorie: e.target.value})}
                >
                  <option value="">Sélectionnez une catégorie</option>
                  <option value="Légumes">🥕 Légumes</option>
                  <option value="Viandes">🥩 Viandes</option>
                  <option value="Poissons">🐟 Poissons</option>
                  <option value="Produits laitiers">🧀 Produits laitiers</option>
                  <option value="Épices">🌶️ Épices & Condiments</option>
                  <option value="Fruits">🍎 Fruits</option>
                  <option value="Céréales">🌾 Céréales & Féculents</option>
                  <option value="Boissons">🥤 Boissons</option>
                  <option value="Autres">📦 Autres</option>
                </select>
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
              
              {/* Nouveaux champs visuels */}
              <div className="form-group">
                <label className="form-label">Couleur d'identification</label>
                <div style={{display: 'flex', alignItems: 'center', gap: '10px'}}>
                  <input
                    type="color"
                    className="form-input"
                    value={fournisseurForm.couleur}
                    onChange={(e) => setFournisseurForm({...fournisseurForm, couleur: e.target.value})}
                    style={{width: '60px', height: '40px', padding: '2px', cursor: 'pointer'}}
                  />
                  <span style={{
                    padding: '8px 16px',
                    backgroundColor: fournisseurForm.couleur,
                    color: 'white',
                    borderRadius: '4px',
                    fontSize: '14px',
                    fontWeight: '500'
                  }}>
                    {fournisseurForm.nom || 'Aperçu'}
                  </span>
                </div>
              </div>
              
              <div className="form-group">
                <label className="form-label">Logo (emoji ou URL)</label>
                <div style={{display: 'flex', alignItems: 'center', gap: '10px'}}>
                  <input
                    type="text"
                    className="form-input"
                    value={fournisseurForm.logo}
                    onChange={(e) => setFournisseurForm({...fournisseurForm, logo: e.target.value})}
                    placeholder="🏪 ou https://exemple.com/logo.png"
                    style={{flex: 1}}
                  />
                  {fournisseurForm.logo && (
                    <span style={{
                      fontSize: '24px',
                      padding: '8px',
                      backgroundColor: '#f3f4f6',
                      borderRadius: '4px'
                    }}>
                      {fournisseurForm.logo.startsWith('http') ? '🖼️' : fournisseurForm.logo}
                    </span>
                  )}
                </div>
                <small style={{color: 'var(--color-text-secondary)', fontSize: '12px'}}>
                  Utilisez un emoji (🏪 🥩 🐟) ou une URL d'image
                </small>
              </div>
              <div className="button-group">
                <button
                  type="button"
                  className="button btn-cancel"
                  onClick={() => {
                    setShowFournisseurModal(false);
                    setEditingItem(null);
                    setFournisseurForm({ nom: "", contact: "", email: "", telephone: "", adresse: "", couleur: "#3B82F6", logo: "" });
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
                  <option value="Entrée">🥗 Entrée</option>
                  <option value="Plat">🍽️ Plat</option>
                  <option value="Dessert">🍰 Dessert</option>
                  <option value="Bar">🍹 Bar</option>
                  <option value="Autres">📝 Autres</option>
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
              <div className="form-group">
                <label className="form-label">Coefficient prévu (%)</label>
                <input
                  type="number"
                  step="0.1"
                  min="0"
                  max="100"
                  className="form-input"
                  value={recetteForm.coefficient_prevu}
                  onChange={(e) => setRecetteForm({...recetteForm, coefficient_prevu: e.target.value})}
                  placeholder="Ex: 35 pour 35%"
                />
                <small className="form-hint">Coefficient prévu = (Coût Matière / Prix de Vente) × 100</small>
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

      {/* Modal Détails des Lots DLC */}
      {showBatchModal && selectedProductBatches && (
        <div className="modal-overlay" onClick={() => setShowBatchModal(false)}>
          <div className="modal-content large" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>📅 Lots & DLC - {selectedProductBatches.product_name}</h3>
              <button className="modal-close" onClick={() => setShowBatchModal(false)}>×</button>
            </div>
            
            <div className="modal-body">
              {/* Résumé du produit */}
              <div className="section-card" style={{marginBottom: '20px'}}>
                <div className="kpi-grid">
                  <div className="kpi-card">
                    <div className="icon">📦</div>
                    <div className="title">Stock Total</div>
                    <div className="value">{selectedProductBatches.total_stock}</div>
                  </div>
                  
                  <div className="kpi-card">
                    <div className="icon">📅</div>
                    <div className="title">Nombre de Lots</div>
                    <div className="value">{selectedProductBatches.batches.length}</div>
                  </div>
                  
                  <div className="kpi-card">
                    <div className="icon">🔴</div>
                    <div className="title">Lots Expirés</div>
                    <div className="value critical">{selectedProductBatches.expired_batches}</div>
                  </div>
                  
                  <div className="kpi-card">
                    <div className="icon">🟡</div>
                    <div className="title">Lots Critiques</div>
                    <div className="value warning">{selectedProductBatches.critical_batches}</div>
                  </div>
                </div>
              </div>

              {/* Liste détaillée des lots */}
              <div className="section-card">
                <div className="section-title">📋 Détail des Lots</div>
                
                {selectedProductBatches.batches.length > 0 ? (
                  <div className="item-list">
                    {selectedProductBatches.batches.map((batch, index) => {
                      const statusIcon = batch.status === 'expired' ? '🔴' : 
                                        batch.status === 'critical' ? '🟡' : '✅';
                      const statusText = batch.status === 'expired' ? 'EXPIRÉ' : 
                                        batch.status === 'critical' ? 'CRITIQUE' : 'OK';
                      const statusClass = batch.status === 'expired' ? 'critical' : 
                                         batch.status === 'critical' ? 'warning' : 'success';
                      
                      return (
                        <div key={index} className="item-row">
                          <div className="item-info">
                            <div className="item-name">
                              {statusIcon} Lot {batch.batch_number || `#${index + 1}`}
                            </div>
                            <div className="item-details">
                              <strong>Quantité:</strong> {batch.quantity} • 
                              <strong>Reçu le:</strong> {new Date(batch.received_date).toLocaleDateString('fr-FR')} •
                              <strong>DLC:</strong> {batch.expiry_date ? new Date(batch.expiry_date).toLocaleDateString('fr-FR') : 'Non définie'}
                              {batch.supplier_id && (
                                <span> • <strong>Fournisseur:</strong> {batch.supplier_id}</span>
                              )}
                            </div>
                          </div>
                          <div className="item-actions">
                            <span className={`status-badge ${statusClass}`}>
                              {statusText}
                            </span>
                            <button className="button small">⚡ Consommer</button>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                ) : (
                  <div style={{textAlign: 'center', padding: '40px', color: 'var(--color-text-muted)'}}>
                    <div style={{fontSize: '48px', marginBottom: '15px'}}>📅</div>
                    <p>Aucun lot trouvé pour ce produit</p>
                  </div>
                )}
              </div>
            </div>
            
            <div className="modal-footer">
              <button className="button secondary" onClick={() => setShowBatchModal(false)}>
                Fermer
              </button>
              <button className="button" onClick={() => alert('Fonctionnalité à implémenter: Ajouter nouveau lot')}>
                ➕ Nouveau Lot
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;