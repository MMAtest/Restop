import React, { useState, useEffect } from 'react';

const DateRangePicker = ({ onDateRangeChange, initialRange = null }) => {
  const [selectedRange, setSelectedRange] = useState('today');
  const [customStartDate, setCustomStartDate] = useState('');
  const [customEndDate, setCustomEndDate] = useState('');
  const [showCustomPicker, setShowCustomPicker] = useState(false);
  const [currentDateOffset, setCurrentDateOffset] = useState(0);

  const rangeOptions = [
    { key: 'today', label: "Aujourd'hui" },
    { key: 'yesterday', label: 'Hier' },
    { key: 'thisWeek', label: 'Semaine' },
    { key: 'lastWeek', label: 'Sem. dern.' },
    { key: 'thisMonth', label: 'Ce mois' },
    { key: 'lastMonth', label: 'Mois dern.' },
    { key: 'custom', label: 'Personnalis\u00e9' }
  ];

  const calculateDateRange = (range, offset = currentDateOffset) => {
    const now = new Date();
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    const formatDate = (date) => date.toLocaleDateString('fr-FR', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' });
    const formatDateShort = (date) => date.toLocaleDateString('fr-FR');

    switch (range) {
      case 'today': {
        const t = new Date(today); t.setDate(today.getDate() + offset);
        return { startDate: t, endDate: t, label: formatDate(t) };
      }
      case 'yesterday': {
        const y = new Date(today); y.setDate(today.getDate() - 1 + offset);
        return { startDate: y, endDate: y, label: formatDate(y) };
      }
      case 'thisWeek': {
        const s = new Date(today); s.setDate(today.getDate() - today.getDay() + 1);
        return { startDate: s, endDate: today, label: `Du ${formatDateShort(s)} au ${formatDateShort(today)}` };
      }
      case 'lastWeek': {
        const e = new Date(today); e.setDate(today.getDate() - today.getDay());
        const s = new Date(e); s.setDate(e.getDate() - 6);
        return { startDate: s, endDate: e, label: `Du ${formatDateShort(s)} au ${formatDateShort(e)}` };
      }
      case 'thisMonth': {
        const s = new Date(today.getFullYear(), today.getMonth(), 1);
        return { startDate: s, endDate: today, label: `Du ${formatDateShort(s)} au ${formatDateShort(today)}` };
      }
      case 'lastMonth': {
        const s = new Date(today.getFullYear(), today.getMonth() - 1, 1);
        const e = new Date(today.getFullYear(), today.getMonth(), 0);
        return { startDate: s, endDate: e, label: `Du ${formatDateShort(s)} au ${formatDateShort(e)}` };
      }
      case 'custom':
        if (customStartDate && customEndDate) {
          return { startDate: new Date(customStartDate), endDate: new Date(customEndDate), label: `Du ${new Date(customStartDate).toLocaleDateString('fr-FR')} au ${new Date(customEndDate).toLocaleDateString('fr-FR')}` };
        }
        return null;
      default:
        return { startDate: today, endDate: today, label: formatDate(today) };
    }
  };

  const handleRangeChange = (rangeKey) => {
    setSelectedRange(rangeKey);
    setShowCustomPicker(rangeKey === 'custom');
    if (rangeKey !== 'custom') {
      const dateRange = calculateDateRange(rangeKey, 0);
      if (dateRange && onDateRangeChange) onDateRangeChange(dateRange);
    }
  };

  const handleCustomDateChange = () => {
    if (customStartDate && customEndDate) {
      const dateRange = calculateDateRange('custom');
      if (dateRange && onDateRangeChange) onDateRangeChange(dateRange);
    }
  };

  useEffect(() => {
    if (!initialRange) {
      const todayRange = calculateDateRange('today');
      if (onDateRangeChange) onDateRangeChange(todayRange);
    }
  }, []);

  useEffect(() => {
    if (selectedRange === 'custom') handleCustomDateChange();
  }, [customStartDate, customEndDate]);

  const handlePreviousDay = () => {
    if (selectedRange === 'today' || selectedRange === 'yesterday') {
      const newOffset = currentDateOffset - 1;
      setCurrentDateOffset(newOffset);
      const dateRange = calculateDateRange(selectedRange, newOffset);
      if (dateRange && onDateRangeChange) onDateRangeChange(dateRange);
    }
  };

  const handleNextDay = () => {
    if (selectedRange === 'today' || selectedRange === 'yesterday') {
      const newOffset = currentDateOffset + 1;
      setCurrentDateOffset(newOffset);
      const dateRange = calculateDateRange(selectedRange, newOffset);
      if (dateRange && onDateRangeChange) onDateRangeChange(dateRange);
    }
  };

  const handleRangeChangeWithReset = (rangeKey) => {
    setCurrentDateOffset(0);
    handleRangeChange(rangeKey);
  };

  const canNavigate = selectedRange === 'today' || selectedRange === 'yesterday';

  return (
    <div data-testid="date-range-picker" style={{marginBottom: '16px'}}>
      {/* Pill selector - horizontal scroll */}
      <div style={{
        display: 'flex', gap: '6px', overflowX: 'auto', paddingBottom: '4px',
        scrollbarWidth: 'none', msOverflowStyle: 'none',
        WebkitOverflowScrolling: 'touch'
      }}>
        <style>{`.drp-scroll::-webkit-scrollbar{display:none}`}</style>
        {rangeOptions.map((option) => (
          <button
            key={option.key}
            data-testid={`period-${option.key}`}
            onClick={() => handleRangeChangeWithReset(option.key)}
            style={{
              padding: '8px 14px',
              borderRadius: '20px',
              fontFamily: 'Manrope, sans-serif',
              fontSize: '12px',
              fontWeight: selectedRange === option.key ? '700' : '600',
              whiteSpace: 'nowrap',
              border: 'none',
              cursor: 'pointer',
              transition: 'all 0.2s ease',
              background: selectedRange === option.key ? '#2C4A3B' : '#F5F5F0',
              color: selectedRange === option.key ? '#FFFFFF' : '#5C5C58',
              flexShrink: 0
            }}
          >
            {option.label}
          </button>
        ))}
      </div>

      {/* Custom date picker */}
      {showCustomPicker && (
        <div style={{
          background: '#FFFFFF', borderRadius: '12px', padding: '14px',
          border: '1px solid #E5E5E0', marginTop: '10px'
        }}>
          <div style={{
            display: 'grid', gridTemplateColumns: '1fr auto 1fr',
            gap: '8px', alignItems: 'center'
          }}>
            <div>
              <label style={{fontFamily: 'Manrope, sans-serif', fontSize: '10px', fontWeight: '700', color: '#8C8C88', textTransform: 'uppercase', letterSpacing: '0.5px', display: 'block', marginBottom: '4px'}}>
                Debut
              </label>
              <input type="date" className="form-input" value={customStartDate}
                onChange={(e) => setCustomStartDate(e.target.value)} style={{fontSize: '13px', padding: '8px 10px'}} />
            </div>
            <div style={{color: '#8C8C88', fontSize: '12px', textAlign: 'center', paddingTop: '16px'}}>au</div>
            <div>
              <label style={{fontFamily: 'Manrope, sans-serif', fontSize: '10px', fontWeight: '700', color: '#8C8C88', textTransform: 'uppercase', letterSpacing: '0.5px', display: 'block', marginBottom: '4px'}}>
                Fin
              </label>
              <input type="date" className="form-input" value={customEndDate}
                onChange={(e) => setCustomEndDate(e.target.value)} style={{fontSize: '13px', padding: '8px 10px'}} />
            </div>
          </div>
        </div>
      )}

      {/* Navigation bar - compact */}
      {selectedRange !== 'custom' && (
        <div data-testid="period-nav" style={{
          background: '#2C4A3B', borderRadius: '10px', marginTop: '10px',
          padding: '8px 10px', display: 'flex', alignItems: 'center',
          justifyContent: 'space-between', gap: '8px'
        }}>
          <button
            data-testid="period-prev"
            onClick={handlePreviousDay}
            disabled={!canNavigate}
            style={{
              background: 'rgba(255,255,255,0.15)', color: 'white', border: 'none',
              borderRadius: '8px', padding: '6px 10px', cursor: canNavigate ? 'pointer' : 'default',
              opacity: canNavigate ? 1 : 0.3, fontSize: '14px', fontWeight: '700',
              transition: 'all 0.2s ease', minWidth: '34px'
            }}
          >
            &#8592;
          </button>
          <div style={{
            flex: 1, textAlign: 'center', fontFamily: 'Work Sans, sans-serif',
            fontSize: '12px', fontWeight: '500', color: 'rgba(255,255,255,0.9)',
            overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap'
          }}>
            {(() => {
              const dateRange = calculateDateRange(selectedRange, currentDateOffset);
              return dateRange?.label || rangeOptions.find(opt => opt.key === selectedRange)?.label;
            })()}
          </div>
          <button
            data-testid="period-next"
            onClick={handleNextDay}
            disabled={!canNavigate}
            style={{
              background: 'rgba(255,255,255,0.15)', color: 'white', border: 'none',
              borderRadius: '8px', padding: '6px 10px', cursor: canNavigate ? 'pointer' : 'default',
              opacity: canNavigate ? 1 : 0.3, fontSize: '14px', fontWeight: '700',
              transition: 'all 0.2s ease', minWidth: '34px'
            }}
          >
            &#8594;
          </button>
        </div>
      )}
    </div>
  );
};

export default DateRangePicker;
