import React, { useState } from 'react';
import ProductsDataGrid from '../components/ProductsDataGrid';
import SuppliersDataGrid from '../components/SuppliersDataGrid';
import RecipesDataGrid from '../components/RecipesDataGrid';

const DataGridsPage = () => {
  const [activeGrid, setActiveGrid] = useState('products');
  const [selectedItem, setSelectedItem] = useState(null);

  const handleProductSelect = (product) => {
    setSelectedItem({ type: 'product', data: product });
  };

  const handleSupplierSelect = (supplier) => {
    setSelectedItem({ type: 'supplier', data: supplier });
  };

  const handleRecipeSelect = (recipe) => {
    setSelectedItem({ type: 'recipe', data: recipe });
  };

  const handleEdit = (item) => {
    alert(`Édition de: ${item.nom}`);
    // Here you would open edit modal
  };

  const handleDelete = (item) => {
    if (window.confirm(`Confirmer la suppression de "${item.nom}" ?`)) {
      alert(`Suppression de: ${item.nom}`);
      // Here you would handle deletion
    }
  };

  const handleCalculateCosts = (recipe) => {
    alert(`Calcul des coûts pour: ${recipe === 'all' ? 'toutes les recettes' : recipe.nom}`);
    // Here you would handle cost calculations
  };

  return (
    <div className="p-6 bg-gradient-to-br from-white to-gray-50 min-h-screen">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-800 mb-2">
          📊 Grilles de Données Professionnelles
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
                {selectedItem.type === 'product' && '🥕 Produit sélectionné'}
                {selectedItem.type === 'supplier' && '🏢 Fournisseur sélectionné'}
                {selectedItem.type === 'recipe' && '📋 Recette sélectionnée'}
              </h3>
              <p className="text-blue-700">{selectedItem.data.nom}</p>
              {selectedItem.data.description && (
                <p className="text-blue-600 text-sm mt-1">{selectedItem.data.description}</p>
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

      {/* Data Grids */}
      <div className="space-y-6">
        {activeGrid === 'products' && (
          <ProductsDataGrid
            onProductSelect={handleProductSelect}
            onProductEdit={handleEdit}
            onProductDelete={handleDelete}
          />
        )}

        {activeGrid === 'suppliers' && (
          <SuppliersDataGrid
            onSupplierSelect={handleSupplierSelect}
            onSupplierEdit={handleEdit}
            onSupplierDelete={handleDelete}
          />
        )}

        {activeGrid === 'recipes' && (
          <RecipesDataGrid
            onRecipeSelect={handleRecipeSelect}
            onRecipeEdit={handleEdit}
            onRecipeDelete={handleDelete}
            onCalculateCosts={handleCalculateCosts}
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