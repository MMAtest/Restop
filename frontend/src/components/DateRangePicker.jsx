import React, { useState, useEffect } from 'react';

const DateRangePicker = ({ onDateRangeChange, initialRange = null }) => {
  const [selectedRange, setSelectedRange] = useState('today');
  const [customStartDate, setCustomStartDate] = useState('');
  const [customEndDate, setCustomEndDate] = useState('');
  const [showCustomPicker, setShowCustomPicker] = useState(false);
  const [currentDateOffset, setCurrentDateOffset] = useState(0); // Nombre de jours depuis aujourd'hui

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
  const calculateDateRange = (range, offset = currentDateOffset) => {
    const now = new Date();
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    
    // Fonction helper pour formater les dates en français
    const formatDate = (date) => {
      const options = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
      return date.toLocaleDateString('fr-FR', options);
    };
    
    const formatDateShort = (date) => {
      return date.toLocaleDateString('fr-FR');
    };
    
    switch (range) {
      case 'today':
      case 'yesterday':
        // Pour aujourd'hui et hier, on applique l'offset
        const targetDate = new Date(today);
        targetDate.setDate(today.getDate() + offset);
        return { 
          startDate: targetDate, 
          endDate: targetDate,
          label: formatDate(targetDate)
        };
      
      case 'thisWeek':
        const startOfWeek = new Date(today);
        startOfWeek.setDate(today.getDate() - today.getDay() + 1); // Lundi
        return { 
          startDate: startOfWeek, 
          endDate: today,
          label: `Du ${formatDateShort(startOfWeek)} au ${formatDateShort(today)}`
        };
      
      case 'lastWeek':
        const lastWeekEnd = new Date(today);
        lastWeekEnd.setDate(today.getDate() - today.getDay());
        const lastWeekStart = new Date(lastWeekEnd);
        lastWeekStart.setDate(lastWeekEnd.getDate() - 6);
        return { 
          startDate: lastWeekStart, 
          endDate: lastWeekEnd,
          label: `Du ${formatDateShort(lastWeekStart)} au ${formatDateShort(lastWeekEnd)}`
        };
      
      case 'thisMonth':
        const startOfMonth = new Date(today.getFullYear(), today.getMonth(), 1);
        return { 
          startDate: startOfMonth, 
          endDate: today,
          label: `Du ${formatDateShort(startOfMonth)} au ${formatDateShort(today)}`
        };
      
      case 'lastMonth':
        const lastMonthStart = new Date(today.getFullYear(), today.getMonth() - 1, 1);
        const lastMonthEnd = new Date(today.getFullYear(), today.getMonth(), 0);
        return { 
          startDate: lastMonthStart, 
          endDate: lastMonthEnd,
          label: `Du ${formatDateShort(lastMonthStart)} au ${formatDateShort(lastMonthEnd)}`
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
        return { startDate: today, endDate: today, label: formatDate(today) };
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

  // Fonctions de navigation par flèches
  const handlePreviousDay = () => {
    if (selectedRange === 'today' || selectedRange === 'yesterday') {
      const newOffset = currentDateOffset - 1;
      setCurrentDateOffset(newOffset);
      const dateRange = calculateDateRange(selectedRange, newOffset);
      if (dateRange && onDateRangeChange) {
        onDateRangeChange(dateRange);
      }
    }
  };

  const handleNextDay = () => {
    if (selectedRange === 'today' || selectedRange === 'yesterday') {
      const newOffset = currentDateOffset + 1;
      setCurrentDateOffset(newOffset);
      const dateRange = calculateDateRange(selectedRange, newOffset);
      if (dateRange && onDateRangeChange) {
        onDateRangeChange(dateRange);
      }
    }
  };

  // Réinitialiser l'offset quand on change de type de période
  const handleRangeChangeWithReset = (rangeKey) => {
    setCurrentDateOffset(0);
    handleRangeChange(rangeKey);
  };

  return (
    <div className="date-range-picker">
      <div className="section-card" style={{ marginBottom: 'var(--spacing-md)' }}>
        {/* Titre avec boutons de navigation */}
        <div style={{ 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'space-between',
          marginBottom: 'var(--spacing-md)'
        }}>
          {/* Bouton précédent */}
          <button
            onClick={handlePreviousDay}
            disabled={selectedRange !== 'today' && selectedRange !== 'yesterday'}
            style={{
              background: 'var(--color-primary-green)',
              color: 'white',
              border: 'none',
              borderRadius: 'var(--border-radius-sm)',
              padding: '8px 12px',
              cursor: selectedRange === 'today' || selectedRange === 'yesterday' ? 'pointer' : 'not-allowed',
              opacity: selectedRange === 'today' || selectedRange === 'yesterday' ? 1 : 0.3,
              fontSize: '18px',
              fontWeight: 'bold',
              transition: 'all 0.2s ease'
            }}
            onMouseEnter={(e) => {
              if (selectedRange === 'today' || selectedRange === 'yesterday') {
                e.target.style.transform = 'scale(1.05)';
              }
            }}
            onMouseLeave={(e) => {
              e.target.style.transform = 'scale(1)';
            }}
          >
            ←
          </button>

          {/* Titre */}
          <div className="section-title" style={{ margin: 0, flex: 1, textAlign: 'center' }}>
            📅 Période d'analyse
          </div>

          {/* Bouton suivant */}
          <button
            onClick={handleNextDay}
            disabled={selectedRange !== 'today' && selectedRange !== 'yesterday'}
            style={{
              background: 'var(--color-primary-green)',
              color: 'white',
              border: 'none',
              borderRadius: 'var(--border-radius-sm)',
              padding: '8px 12px',
              cursor: selectedRange === 'today' || selectedRange === 'yesterday' ? 'pointer' : 'not-allowed',
              opacity: selectedRange === 'today' || selectedRange === 'yesterday' ? 1 : 0.3,
              fontSize: '18px',
              fontWeight: 'bold',
              transition: 'all 0.2s ease'
            }}
            onMouseEnter={(e) => {
              if (selectedRange === 'today' || selectedRange === 'yesterday') {
                e.target.style.transform = 'scale(1.05)';
              }
            }}
            onMouseLeave={(e) => {
              e.target.style.transform = 'scale(1)';
            }}
          >
            →
          </button>
        </div>
        
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
              onClick={() => handleRangeChangeWithReset(option.key)}
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

        {/* Affichage de la période sélectionnée avec navigation */}
        {selectedRange !== 'custom' && (
          <div style={{
            background: 'var(--color-success-green)',
            color: 'white',
            borderRadius: 'var(--border-radius-sm)',
            padding: 'var(--spacing-sm)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: 'var(--spacing-sm)'
          }}>
            {/* Flèche gauche */}
            <button
              onClick={handlePreviousDay}
              disabled={selectedRange !== 'today' && selectedRange !== 'yesterday'}
              style={{
                background: 'rgba(255, 255, 255, 0.2)',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                padding: '6px 10px',
                cursor: selectedRange === 'today' || selectedRange === 'yesterday' ? 'pointer' : 'not-allowed',
                opacity: selectedRange === 'today' || selectedRange === 'yesterday' ? 1 : 0.3,
                fontSize: '16px',
                fontWeight: 'bold',
                transition: 'all 0.2s ease',
                minWidth: '36px'
              }}
              onMouseEnter={(e) => {
                if (selectedRange === 'today' || selectedRange === 'yesterday') {
                  e.target.style.background = 'rgba(255, 255, 255, 0.3)';
                }
              }}
              onMouseLeave={(e) => {
                e.target.style.background = 'rgba(255, 255, 255, 0.2)';
              }}
            >
              ←
            </button>

            {/* Texte de la période avec date */}
            <div style={{
              flex: 1,
              textAlign: 'center',
              fontSize: '13px',
              fontWeight: '500'
            }}>
              ✓ {(() => {
                const dateRange = calculateDateRange(selectedRange, currentDateOffset);
                return dateRange?.label || rangeOptions.find(opt => opt.key === selectedRange)?.label;
              })()}
            </div>

            {/* Flèche droite */}
            <button
              onClick={handleNextDay}
              disabled={selectedRange !== 'today' && selectedRange !== 'yesterday'}
              style={{
                background: 'rgba(255, 255, 255, 0.2)',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                padding: '6px 10px',
                cursor: selectedRange === 'today' || selectedRange === 'yesterday' ? 'pointer' : 'not-allowed',
                opacity: selectedRange === 'today' || selectedRange === 'yesterday' ? 1 : 0.3,
                fontSize: '16px',
                fontWeight: 'bold',
                transition: 'all 0.2s ease',
                minWidth: '36px'
              }}
              onMouseEnter={(e) => {
                if (selectedRange === 'today' || selectedRange === 'yesterday') {
                  e.target.style.background = 'rgba(255, 255, 255, 0.3)';
                }
              }}
              onMouseLeave={(e) => {
                e.target.style.background = 'rgba(255, 255, 255, 0.2)';
              }}
            >
              →
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default DateRangePicker;