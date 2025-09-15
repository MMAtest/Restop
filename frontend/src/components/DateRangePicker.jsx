import React, { useState, useEffect } from 'react';

const DateRangePicker = ({ onDateRangeChange, initialRange = null }) => {
  const [selectedRange, setSelectedRange] = useState('today');
  const [customStartDate, setCustomStartDate] = useState('');
  const [customEndDate, setCustomEndDate] = useState('');
  const [showCustomPicker, setShowCustomPicker] = useState(false);

  // Options prédéfinies
  const rangeOptions = [
    { key: 'today', label: "Aujourd'hui", icon: '📅' },
    { key: 'yesterday', label: 'Hier', icon: '📄' },
    { key: 'thisWeek', label: 'Cette semaine', icon: '📊' },
    { key: 'lastWeek', label: 'Semaine dernière', icon: '📋' },
    { key: 'thisMonth', label: 'Ce mois', icon: '📆' },
    { key: 'lastMonth', label: 'Mois dernier', icon: '🗓️' },
    { key: 'custom', label: 'Période personnalisée', icon: '🎯' }
  ];

  // Calculer les dates selon l'option sélectionnée
  const calculateDateRange = (range) => {
    const now = new Date();
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    
    switch (range) {
      case 'today':
        return { 
          startDate: today, 
          endDate: today,
          label: 'Aujourd\'hui'
        };
      
      case 'yesterday':
        const yesterday = new Date(today);
        yesterday.setDate(yesterday.getDate() - 1);
        return { 
          startDate: yesterday, 
          endDate: yesterday,
          label: 'Hier'
        };
      
      case 'thisWeek':
        const startOfWeek = new Date(today);
        startOfWeek.setDate(today.getDate() - today.getDay() + 1); // Lundi
        return { 
          startDate: startOfWeek, 
          endDate: today,
          label: 'Cette semaine'
        };
      
      case 'lastWeek':
        const lastWeekEnd = new Date(today);
        lastWeekEnd.setDate(today.getDate() - today.getDay());
        const lastWeekStart = new Date(lastWeekEnd);
        lastWeekStart.setDate(lastWeekEnd.getDate() - 6);
        return { 
          startDate: lastWeekStart, 
          endDate: lastWeekEnd,
          label: 'Semaine dernière'
        };
      
      case 'thisMonth':
        const startOfMonth = new Date(today.getFullYear(), today.getMonth(), 1);
        return { 
          startDate: startOfMonth, 
          endDate: today,
          label: 'Ce mois'
        };
      
      case 'lastMonth':
        const lastMonthStart = new Date(today.getFullYear(), today.getMonth() - 1, 1);
        const lastMonthEnd = new Date(today.getFullYear(), today.getMonth(), 0);
        return { 
          startDate: lastMonthStart, 
          endDate: lastMonthEnd,
          label: 'Mois dernier'
        };
      
      case 'custom':
        if (customStartDate && customEndDate) {
          return {
            startDate: new Date(customStartDate),
            endDate: new Date(customEndDate),
            label: `Du ${new Date(customStartDate).toLocaleDateString('fr-FR')} au ${new Date(customEndDate).toLocaleDateString('fr-FR')}`
          };
        }
        return null;
      
      default:
        return { startDate: today, endDate: today, label: 'Aujourd\'hui' };
    }
  };

  // Gérer le changement de période
  const handleRangeChange = (rangeKey) => {
    setSelectedRange(rangeKey);
    setShowCustomPicker(rangeKey === 'custom');
    
    if (rangeKey !== 'custom') {
      const dateRange = calculateDateRange(rangeKey);
      if (dateRange && onDateRangeChange) {
        onDateRangeChange(dateRange);
      }
    }
  };

  // Gérer les dates personnalisées
  const handleCustomDateChange = () => {
    if (customStartDate && customEndDate) {
      const dateRange = calculateDateRange('custom');
      if (dateRange && onDateRangeChange) {
        onDateRangeChange(dateRange);
      }
    }
  };

  // Initialiser avec la date du jour
  useEffect(() => {
    if (!initialRange) {
      const todayRange = calculateDateRange('today');
      if (onDateRangeChange) {
        onDateRangeChange(todayRange);
      }
    }
  }, []);

  // Mettre à jour quand les dates personnalisées changent
  useEffect(() => {
    if (selectedRange === 'custom') {
      handleCustomDateChange();
    }
  }, [customStartDate, customEndDate]);

  return (
    <div className="date-range-picker">
      <div className="section-card" style={{ marginBottom: 'var(--spacing-md)' }}>
        <div className="section-title">📅 Période d'analyse</div>
        
        {/* Options rapides */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))',
          gap: 'var(--spacing-sm)',
          marginBottom: 'var(--spacing-md)'
        }}>
          {rangeOptions.map((option) => (
            <button
              key={option.key}
              className={`button small ${selectedRange === option.key ? '' : 'secondary'}`}
              onClick={() => handleRangeChange(option.key)}
              style={{
                background: selectedRange === option.key 
                  ? 'var(--color-primary-blue)' 
                  : 'var(--color-background-card-light)',
                color: selectedRange === option.key 
                  ? 'white' 
                  : 'var(--color-text-secondary)',
                fontSize: '12px',
                padding: 'var(--spacing-sm)',
                textAlign: 'center'
              }}
            >
              <div>{option.icon}</div>
              <div>{option.label}</div>
            </button>
          ))}
        </div>

        {/* Sélection personnalisée */}
        {showCustomPicker && (
          <div style={{
            background: 'var(--color-background-card-light)',
            borderRadius: 'var(--border-radius-md)',
            padding: 'var(--spacing-md)',
            border: '1px solid var(--color-border)'
          }}>
            <div className="section-title" style={{ fontSize: '14px', marginBottom: 'var(--spacing-sm)' }}>
              📆 Sélection personnalisée
            </div>
            
            <div style={{
              display: 'grid',
              gridTemplateColumns: '1fr auto 1fr',
              gap: 'var(--spacing-sm)',
              alignItems: 'center'
            }}>
              <div>
                <label className="form-label" style={{ fontSize: '12px' }}>Date de début</label>
                <input
                  type="date"
                  className="form-input"
                  value={customStartDate}
                  onChange={(e) => setCustomStartDate(e.target.value)}
                  style={{ fontSize: '12px' }}
                />
              </div>
              
              <div style={{ 
                color: 'var(--color-text-muted)', 
                fontSize: '12px',
                textAlign: 'center',
                padding: 'var(--spacing-sm) 0'
              }}>
                au
              </div>
              
              <div>
                <label className="form-label" style={{ fontSize: '12px' }}>Date de fin</label>
                <input
                  type="date"
                  className="form-input"
                  value={customEndDate}
                  onChange={(e) => setCustomEndDate(e.target.value)}
                  style={{ fontSize: '12px' }}
                />
              </div>
            </div>
          </div>
        )}

        {/* Affichage de la période sélectionnée */}
        {selectedRange !== 'custom' && (
          <div style={{
            background: 'var(--color-success-green)',
            color: 'white',
            borderRadius: 'var(--border-radius-sm)',
            padding: 'var(--spacing-sm)',
            textAlign: 'center',
            fontSize: '12px',
            fontWeight: '500'
          }}>
            ✓ {rangeOptions.find(opt => opt.key === selectedRange)?.label}
          </div>
        )}
      </div>
    </div>
  );
};

export default DateRangePicker;