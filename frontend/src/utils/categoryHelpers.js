// Couleurs par catégorie de production
export const getCategoryColor = (category) => {
  const colors = {
    'Entrée': '#10B981', // Vert
    'Plat': '#F59E0B',   // Orange/Jaune
    'Dessert': '#EC4899', // Rose
    'Bar': '#8B5CF6',     // Violet
    'Autres': '#6B7280'   // Gris
  };
  return colors[category] || colors['Autres'];
};

export const getCategoryIcon = (category) => {
  const icons = {
    'Entrée': '🥗',
    'Plat': '🍽️',
    'Dessert': '🍰',
    'Bar': '🍹',
    'Autres': '📝'
  };
  return icons[category] || icons['Autres'];
};
