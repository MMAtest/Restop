import React, { useMemo } from 'react';
import DataGrid from './DataGrid';

const RecipesDataGrid = ({ recipes = [], loading, onRecipeSelect, onRecipeEdit, onRecipeDelete, onCalculateCosts }) => {

  // Actions renderer
  const ActionsRenderer = ({ data }) => (
    <div className="flex space-x-1">
      <button
        onClick={() => onRecipeEdit && onRecipeEdit(data)}
        className="text-blue-600 hover:text-blue-800 font-medium text-sm"
        title="Modifier"
      >
        ✏️
      </button>
      <button
        onClick={() => onCalculateCosts && onCalculateCosts(data)}
        className="text-green-600 hover:text-green-800 font-medium text-sm"
        title="Calculer Coûts"
      >
        💰
      </button>
      <button
        onClick={() => onRecipeDelete && onRecipeDelete(data)}
        className="text-red-600 hover:text-red-800 font-medium text-sm"
        title="Supprimer"
      >
        🗑️
      </button>
    </div>
  );

  // Ingredients renderer
  const IngredientsRenderer = ({ data }) => {
    const ingredients = data.ingredients || [];
    const maxShow = 3;
    const shown = ingredients.slice(0, maxShow);
    const remaining = ingredients.length - maxShow;

    return (
      <div className="text-sm">
        {shown.map((ingredient, index) => (
          <div key={index} className="text-gray-600">
            • {ingredient.produit_nom || 'Ingrédient'} ({ingredient.quantite} {ingredient.unite})
          </div>
        ))}
        {remaining > 0 && (
          <div className="text-gray-400 text-xs">
            ... et {remaining} autre{remaining > 1 ? 's' : ''}
          </div>
        )}
        {ingredients.length === 0 && (
          <span className="text-gray-400">Aucun ingrédient</span>
        )}
      </div>
    );
  };

  // Price renderer
  const PriceRenderer = ({ value }) => {
    if (!value) return '-';
    return new Intl.NumberFormat('fr-FR', {
      style: 'currency',
      currency: 'EUR'
    }).format(value);
  };

  // Category renderer with icon
  const CategoryRenderer = ({ value }) => {
    const categoryIcons = {
      'Entrées': '🥗',
      'Plats': '🍽️',
      'Desserts': '🍰',
      'Boissons': '🍷',
      'Bar': '🍸',
      'Autres': '🍴'
    };
    
    const icon = categoryIcons[value] || '🍴';
    return (
      <span className="flex items-center">
        <span className="mr-2">{icon}</span>
        {value || 'Non classé'}
      </span>
    );
  };

  // Time renderer
  const TimeRenderer = ({ value }) => {
    if (!value) return '-';
    return `${value} min`;
  };

  // Portions renderer
  const PortionsRenderer = ({ value }) => {
    if (!value) return '-';
    return (
      <span className="flex items-center">
        <span className="mr-1">👥</span>
        {value} portion{value > 1 ? 's' : ''}
      </span>
    );
  };

  // Profitability renderer (calculated)
  const ProfitabilityRenderer = ({ data }) => {
    const sellingPrice = data.prix_vente || 0;
    const ingredients = data.ingredients || [];
    
    // Simple cost calculation (would be better to get from analytics API)
    let estimatedCost = 0;
    ingredients.forEach(ingredient => {
      // Rough estimation - in real scenario, get actual prices
      const avgPrice = 5; // €5 per unit as rough estimate
      estimatedCost += (ingredient.quantite || 0) * avgPrice / (data.portions || 1);
    });

    const margin = sellingPrice - estimatedCost;
    const marginPercent = sellingPrice > 0 ? (margin / sellingPrice) * 100 : 0;

    if (sellingPrice === 0) {
      return <span className="text-gray-400">Prix non défini</span>;
    }

    const isGoodMargin = marginPercent >= 60;
    const isFairMargin = marginPercent >= 30;

    return (
      <div className="text-sm">
        <div className={`font-medium ${
          isGoodMargin ? 'text-green-600' : 
          isFairMargin ? 'text-yellow-600' : 'text-red-600'
        }`}>
          {marginPercent.toFixed(1)}%
        </div>
        <div className="text-xs text-gray-500">
          Marge: {margin.toFixed(2)}€
        </div>
      </div>
    );
  };

  // Date renderer
  const DateRenderer = ({ value }) => {
    if (!value) return '-';
    return new Date(value).toLocaleDateString('fr-FR');
  };

  // Column definitions
  const columnDefs = useMemo(() => [
    {
      headerName: 'Recette',
      field: 'nom',
      pinned: 'left',
      width: 200,
      cellStyle: { fontWeight: 'bold' }
    },
    {
      headerName: 'Catégorie',
      field: 'categorie',
      width: 130,
      cellRenderer: CategoryRenderer,
      filter: 'agSetColumnFilter'
    },
    {
      headerName: 'Portions',
      field: 'portions',
      width: 100,
      cellRenderer: PortionsRenderer,
      type: 'numericColumn',
      filter: 'agNumberColumnFilter'
    },
    {
      headerName: 'Prix Vente',
      field: 'prix_vente',
      width: 110,
      cellRenderer: PriceRenderer,
      type: 'numericColumn',
      filter: 'agNumberColumnFilter'
    },
    {
      headerName: 'Rentabilité',
      field: 'profitability',
      width: 120,
      cellRenderer: ProfitabilityRenderer,
      sortable: false,
      filter: false
    },
    {
      headerName: 'Temps Prep.',
      field: 'temps_preparation',
      width: 120,
      cellRenderer: TimeRenderer,
      type: 'numericColumn',
      filter: 'agNumberColumnFilter'
    },
    {
      headerName: 'Ingrédients',
      field: 'ingredients_summary',
      width: 250,
      cellRenderer: IngredientsRenderer,
      sortable: false,
      filter: false
    },
    {
      headerName: 'Description',
      field: 'description',
      width: 200,
      filter: 'agTextColumnFilter',
      cellRenderer: ({ value }) => (
        <div className="text-sm text-gray-600 truncate" title={value}>
          {value || 'Pas de description'}
        </div>
      )
    },
    {
      headerName: 'Créé le',
      field: 'created_at',
      width: 120,
      cellRenderer: DateRenderer,
      filter: 'agDateColumnFilter'
    },
    {
      headerName: 'Actions',
      field: 'actions',
      width: 120,
      cellRenderer: ActionsRenderer,
      sortable: false,
      filter: false,
      pinned: 'right'
    }
  ], []);

  const handleRowClicked = (event) => {
    if (onRecipeSelect) {
      onRecipeSelect(event.data);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500 mx-auto"></div>
          <p className="mt-2 text-gray-600">Chargement des recettes...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-sm">
      <div className="p-4 border-b border-gray-200">
        <div className="flex justify-between items-center">
          <div>
            <h3 className="text-lg font-semibold flex items-center">
              <span className="mr-2">📋</span>
              Gestion des Recettes & Plats
            </h3>
            <p className="text-sm text-gray-600 mt-1">
              {recipes.length} recettes • Analyse de rentabilité intégrée • Gestion des ingrédients
            </p>
          </div>
          <div className="flex space-x-2">
            <button
              onClick={() => onCalculateCosts && onCalculateCosts('all')}
              className="text-green-600 hover:text-green-700 font-medium flex items-center text-sm"
            >
              <span className="mr-1">💰</span>
              Calculer Tous les Coûts
            </button>
            <button
              onClick={() => window.location.reload()}
              className="text-primary-500 hover:text-primary-600 font-medium flex items-center"
            >
              <span className="mr-1">🔄</span>
              Actualiser
            </button>
          </div>
        </div>
      </div>
      
      <div className="p-4">
        <DataGrid
          data={recipes}
          columns={columnDefs}
          height="600px"
          onRowClicked={handleRowClicked}
          paginationPageSize={15}
          className="rounded-lg overflow-hidden border border-gray-200"
        />
      </div>
    </div>
  );
};

export default RecipesDataGrid;