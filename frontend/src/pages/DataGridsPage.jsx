import React, { useState, useEffect } from 'react';
import ProductsDataGrid from '../components/ProductsDataGrid';
import SuppliersDataGrid from '../components/SuppliersDataGrid';
import RecipesDataGrid from '../components/RecipesDataGrid';
import axios from 'axios';

const DataGridsPage = () => {
  const [activeGrid, setActiveGrid] = useState('products');
  const [selectedItem, setSelectedItem] = useState(null);
  
  // États pour les données réelles
  const [products, setProducts] = useState([]);
  const [suppliers, setSuppliers] = useState([]);
  const [recipes, setRecipes] = useState([]);
  const [loading, setLoading] = useState(false);

  const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
  const API = `${BACKEND_URL}/api`;

  // Charger les données au montage du composant
  useEffect(() => {
    fetchAllData();
  }, []);

  const fetchAllData = async () => {
    setLoading(true);
    try {
      await Promise.all([
        fetchProducts(),
        fetchSuppliers(), 
        fetchRecipes()
      ]);
    } catch (error) {
      console.error('Erreur lors du chargement des données:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchProducts = async () => {
    try {
      const response = await axios.get(`${API}/produits`);
      setProducts(response.data);
    } catch (error) {
      console.error('Erreur lors du chargement des produits:', error);
    }
  };

  const fetchSuppliers = async () => {
    try {
      const response = await axios.get(`${API}/fournisseurs`);
      setSuppliers(response.data);
    } catch (error) {
      console.error('Erreur lors du chargement des fournisseurs:', error);
    }
  };

  const fetchRecipes = async () => {
    try {
      const response = await axios.get(`${API}/recettes`);
      setRecipes(response.data);
    } catch (error) {
      console.error('Erreur lors du chargement des recettes:', error);
    }
  };

  const handleProductSelect = (product) => {
    setSelectedItem({ type: 'product', data: product });
  };

  const handleSupplierSelect = (supplier) => {
    setSelectedItem({ type: 'supplier', data: supplier });
  };

  const handleRecipeSelect = (recipe) => {
    setSelectedItem({ type: 'recipe', data: recipe });
  };

  const handleEdit = async (item) => {
    alert(`Édition de: ${item.nom}`);
    // Ici vous pouvez ouvrir un modal d'édition
    // Puis rafraîchir les données après modification
    await fetchAllData();
  };

  const handleDelete = async (item) => {
    if (window.confirm(`Confirmer la suppression de "${item.nom}" ?`)) {
      try {
        if (selectedItem?.type === 'product') {
          await axios.delete(`${API}/produits/${item.id}`);
        } else if (selectedItem?.type === 'supplier') {
          await axios.delete(`${API}/fournisseurs/${item.id}`);
        } else if (selectedItem?.type === 'recipe') {
          await axios.delete(`${API}/recettes/${item.id}`);
        }
        alert(`${item.nom} supprimé avec succès`);
        await fetchAllData(); // Rafraîchir les données
      } catch (error) {
        console.error('Erreur lors de la suppression:', error);
        alert('Erreur lors de la suppression');
      }
    }
  };

  const handleCalculateCosts = async (recipe) => {
    try {
      const response = await axios.get(`${API}/recettes/calculer-couts`);
      if (response.data.success) {
        alert(`Coûts calculés avec succès !\n\nRésumé:\n- ${response.data.recettes_calculees} recettes mises à jour\n- Coût moyen: ${response.data.cout_moyen}€\n- Marge moyenne: ${response.data.marge_moyenne}%`);
        await fetchRecipes(); // Rafraîchir les recettes
      }
    } catch (error) {
      console.error('Erreur lors du calcul des coûts:', error);
      alert('Erreur lors du calcul des coûts');
    }
  };

  return (
    <div className="p-6 bg-gradient-to-br from-gray-100 to-gray-200 min-h-screen">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-800 mb-2">
          Grilles de Données Professionnelles
        </h1>
        <p className="text-gray-600">
          Gestion avancée avec tri, filtrage, pagination et actions rapides
        </p>
      </div>

      {/* Tab Navigation */}
      <div className="mb-6">
        <div className="flex space-x-1 bg-white p-1 rounded-lg shadow-sm">
          <button
            onClick={() => setActiveGrid('products')}
            className={`flex items-center px-4 py-2 rounded-md text-sm font-medium transition-all ${
              activeGrid === 'products'
                ? 'bg-primary-500 text-white shadow-sm'
                : 'text-gray-500 hover:text-gray-700 hover:bg-gray-100'
            }`}
          >
            <span className="mr-2">🥕</span>
            Produits & Ingrédients
          </button>
          <button
            onClick={() => setActiveGrid('suppliers')}
            className={`flex items-center px-4 py-2 rounded-md text-sm font-medium transition-all ${
              activeGrid === 'suppliers'
                ? 'bg-primary-500 text-white shadow-sm'
                : 'text-gray-500 hover:text-gray-700 hover:bg-gray-100'
            }`}
          >
            <span className="mr-2">🏢</span>
            Fournisseurs
          </button>
          <button
            onClick={() => setActiveGrid('recipes')}
            className={`flex items-center px-4 py-2 rounded-md text-sm font-medium transition-all ${
              activeGrid === 'recipes'
                ? 'bg-primary-500 text-white shadow-sm'
                : 'text-gray-500 hover:text-gray-700 hover:bg-gray-100'
            }`}
          >
            <span className="mr-2">📋</span>
            Recettes & Plats
          </button>
        </div>
      </div>

      {/* Selection Info */}
      {selectedItem && (
        <div className="mb-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="font-semibold text-blue-900">
                {selectedItem.type === 'product' && 'Produit sélectionné'}
                {selectedItem.type === 'supplier' && 'Fournisseur sélectionné'}
                {selectedItem.type === 'recipe' && 'Recette sélectionnée'}
              </h3>
              <p className="text-blue-700">{selectedItem.data.nom}</p>
              {selectedItem.data.description && (
                <p className="text-blue-600 text-sm mt-1">{selectedItem.data.description}</p>
              )}
              {/* Informations supplémentaires */}
              {selectedItem.type === 'product' && selectedItem.data.prix_achat && (
                <p className="text-blue-600 text-sm">Prix d'achat: {selectedItem.data.prix_achat}€</p>
              )}
              {selectedItem.type === 'supplier' && selectedItem.data.email && (
                <p className="text-blue-600 text-sm">Email: {selectedItem.data.email}</p>
              )}
              {selectedItem.type === 'recipe' && selectedItem.data.prix_vente && (
                <p className="text-blue-600 text-sm">Prix de vente: {selectedItem.data.prix_vente}€</p>
              )}
            </div>
            <button
              onClick={() => setSelectedItem(null)}
              className="text-blue-600 hover:text-blue-800"
            >
              ✕
            </button>
          </div>
        </div>
      )}

      {/* Loading State */}
      {loading && (
        <div className="text-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500 mx-auto mb-2"></div>
          <p className="text-gray-600">Chargement des données...</p>
        </div>
      )}

      {/* Data Grids */}
      <div className="space-y-6">
        {activeGrid === 'products' && (
          <ProductsDataGrid
            products={products}
            onProductSelect={handleProductSelect}
            onProductEdit={handleEdit}
            onProductDelete={handleDelete}
            loading={loading}
          />
        )}

        {activeGrid === 'suppliers' && (
          <SuppliersDataGrid
            suppliers={suppliers}
            onSupplierSelect={handleSupplierSelect}
            onSupplierEdit={handleEdit}
            onSupplierDelete={handleDelete}
            loading={loading}
          />
        )}

        {activeGrid === 'recipes' && (
          <RecipesDataGrid
            recipes={recipes}
            onRecipeSelect={handleRecipeSelect}
            onRecipeEdit={handleEdit}
            onRecipeDelete={handleDelete}
            onCalculateCosts={handleCalculateCosts}
            loading={loading}
          />
        )}
      </div>

      {/* Features Info */}
      <div className="mt-8 bg-white rounded-lg shadow-sm p-6">
        <h3 className="text-lg font-semibold mb-4 flex items-center">
          <span className="mr-2">✨</span>
          Fonctionnalités Avancées
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <div className="flex items-start space-x-3">
            <span className="text-2xl">🔍</span>
            <div>
              <h4 className="font-medium">Filtrage Intelligent</h4>
              <p className="text-sm text-gray-600">
                Filtres par colonne avec recherche textuelle, numérique et par dates
              </p>
            </div>
          </div>
          <div className="flex items-start space-x-3">
            <span className="text-2xl">📊</span>
            <div>
              <h4 className="font-medium">Tri Multi-Colonnes</h4>
              <p className="text-sm text-gray-600">
                Tri ascendant/descendant sur toutes les colonnes avec indicateurs visuels
              </p>
            </div>
          </div>
          <div className="flex items-start space-x-3">
            <span className="text-2xl">📄</span>
            <div>
              <h4 className="font-medium">Pagination Avancée</h4>
              <p className="text-sm text-gray-600">
                Navigation par pages avec contrôle de la taille des pages
              </p>
            </div>
          </div>
          <div className="flex items-start space-x-3">
            <span className="text-2xl">📱</span>
            <div>
              <h4 className="font-medium">Responsive Design</h4>
              <p className="text-sm text-gray-600">
                Interface adaptative pour tous les écrans et appareils
              </p>
            </div>
          </div>
          <div className="flex items-start space-x-3">
            <span className="text-2xl">⚡</span>
            <div>
              <h4 className="font-medium">Actions Rapides</h4>
              <p className="text-sm text-gray-600">
                Boutons d'action intégrés pour édition, suppression, contact
              </p>
            </div>
          </div>
          <div className="flex items-start space-x-3">
            <span className="text-2xl">🎨</span>
            <div>
              <h4 className="font-medium">Rendu Personnalisé</h4>
              <p className="text-sm text-gray-600">
                Affichage enrichi avec icônes, couleurs et formatage intelligent
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DataGridsPage;