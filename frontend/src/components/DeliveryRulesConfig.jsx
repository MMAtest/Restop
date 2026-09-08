import React, { useState } from 'react';

const DeliveryRulesConfig = ({ supplier, onSave, onCancel }) => {
  const [rules, setRules] = useState(supplier.delivery_rules || {
    order_days: [],
    order_deadline_hour: 11,
    delivery_days: [],
    delivery_delay_days: 1,
    delivery_time: "12:00",
    special_rules: ""
  });

  const daysOfWeek = [
    { value: 'lundi', label: 'Lundi' },
    { value: 'mardi', label: 'Mardi' },
    { value: 'mercredi', label: 'Mercredi' },
    { value: 'jeudi', label: 'Jeudi' },
    { value: 'vendredi', label: 'Vendredi' },
    { value: 'samedi', label: 'Samedi' },
    { value: 'dimanche', label: 'Dimanche' }
  ];

  const toggleDay = (dayValue, field) => {
    const currentDays = rules[field] || [];
    const newDays = currentDays.includes(dayValue)
      ? currentDays.filter(d => d !== dayValue)
      : [...currentDays, dayValue];
    setRules({ ...rules, [field]: newDays });
  };

  const handleSave = () => {
    onSave({
      ...supplier,
      delivery_rules: rules
    });
  };

  // Exemples prédéfinis
  const applyPreset = (preset) => {
    const presets = {
      metro: {
        order_days: ['lundi', 'mardi', 'mercredi', 'jeudi', 'vendredi', 'samedi'],
        order_deadline_hour: 11,
        delivery_days: [],
        delivery_delay_days: 1,
        delivery_time: "12:00",
        special_rules: "Livraison le lendemain midi. Commande samedi → livraison lundi"
      },
      montaner: {
        order_days: ['mardi', 'vendredi'],
        order_deadline_hour: 11,
        delivery_days: [],
        delivery_delay_days: 1,
        delivery_time: "11:00",
        special_rules: "Livraison le lendemain avant 11h"
      },
      royaumeMers: {
        order_days: [],
        order_deadline_hour: 12,
        delivery_days: ['mardi', 'samedi'],
        delivery_delay_days: 0,
        delivery_time: "11:00",
        special_rules: "Commande tous les jours avant midi, livraison uniquement mardi et samedi"
      }
    };
    setRules(presets[preset]);
  };

  return (
    <div className="bg-white rounded-lg border border-gray-300 p-6">
      <h3 className="text-lg font-bold mb-4">
        Règles de livraison - {supplier.nom}
      </h3>

      {/* Exemples prédéfinis */}
      <div className="mb-6 p-4 bg-blue-50 rounded-lg">
        <p className="text-sm font-medium text-blue-800 mb-2">📋 Modèles prédéfinis</p>
        <div className="flex gap-2 flex-wrap">
          <button
            onClick={() => applyPreset('metro')}
            className="px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700"
          >
            METRO
          </button>
          <button
            onClick={() => applyPreset('montaner')}
            className="px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700"
          >
            Montaner
          </button>
          <button
            onClick={() => applyPreset('royaumeMers')}
            className="px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700"
          >
            Royaume des Mers
          </button>
        </div>
      </div>

      {/* Jours de prise de commande */}
      <div className="mb-6">
        <label className="block font-medium mb-2">
          📅 Jours de prise de commande
          <span className="text-sm text-gray-500 ml-2">(laisser vide = tous les jours)</span>
        </label>
        <div className="flex gap-2 flex-wrap">
          {daysOfWeek.map(day => (
            <button
              key={day.value}
              onClick={() => toggleDay(day.value, 'order_days')}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                (rules.order_days || []).includes(day.value)
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              }`}
            >
              {day.label}
            </button>
          ))}
        </div>
      </div>

      {/* Heure limite */}
      <div className="mb-6">
        <label className="block font-medium mb-2">
          ⏰ Heure limite de commande
        </label>
        <input
          type="number"
          min="0"
          max="23"
          value={rules.order_deadline_hour || 11}
          onChange={(e) => setRules({ ...rules, order_deadline_hour: parseInt(e.target.value) })}
          className="w-32 px-4 py-2 border border-gray-300 rounded-lg"
        />
        <span className="ml-2 text-gray-600">heures</span>
      </div>

      {/* Jours de livraison */}
      <div className="mb-6">
        <label className="block font-medium mb-2">
          🚚 Jours de livraison spécifiques
          <span className="text-sm text-gray-500 ml-2">(laisser vide pour utiliser le délai)</span>
        </label>
        <div className="flex gap-2 flex-wrap">
          {daysOfWeek.map(day => (
            <button
              key={day.value}
              onClick={() => toggleDay(day.value, 'delivery_days')}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                (rules.delivery_days || []).includes(day.value)
                  ? 'bg-green-600 text-white'
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              }`}
            >
              {day.label}
            </button>
          ))}
        </div>
      </div>

      {/* Délai de livraison */}
      <div className="mb-6">
        <label className="block font-medium mb-2">
          📦 Délai de livraison (jours)
        </label>
        <input
          type="number"
          min="0"
          max="14"
          value={rules.delivery_delay_days || 1}
          onChange={(e) => setRules({ ...rules, delivery_delay_days: parseInt(e.target.value) })}
          className="w-32 px-4 py-2 border border-gray-300 rounded-lg"
        />
        <span className="ml-2 text-gray-600">jour(s)</span>
      </div>

      {/* Heure de livraison */}
      <div className="mb-6">
        <label className="block font-medium mb-2">
          🕐 Heure de livraison
        </label>
        <input
          type="time"
          value={rules.delivery_time || "12:00"}
          onChange={(e) => setRules({ ...rules, delivery_time: e.target.value })}
          className="w-40 px-4 py-2 border border-gray-300 rounded-lg"
        />
      </div>

      {/* Règles spéciales */}
      <div className="mb-6">
        <label className="block font-medium mb-2">
          📝 Règles spéciales (optionnel)
        </label>
        <textarea
          value={rules.special_rules || ''}
          onChange={(e) => setRules({ ...rules, special_rules: e.target.value })}
          placeholder="Ex: Commande samedi → livraison lundi"
          className="w-full px-4 py-2 border border-gray-300 rounded-lg"
          rows="3"
        />
      </div>

      {/* Boutons d'action */}
      <div className="flex gap-3">
        <button
          onClick={handleSave}
          className="flex-1 bg-blue-600 text-white py-2 px-4 rounded-lg font-medium hover:bg-blue-700"
        >
          Sauvegarder les règles
        </button>
        <button
          onClick={onCancel}
          className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
        >
          Annuler
        </button>
      </div>
    </div>
  );
};

export default DeliveryRulesConfig;