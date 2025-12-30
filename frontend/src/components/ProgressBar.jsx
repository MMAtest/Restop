import React, { useState, useEffect } from 'react';

const ProgressBar = ({ duration = 3000, message = "Traitement en cours..." }) => {
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    // Simulation de progression réaliste
    const intervals = [
      { time: 0, progress: 0 },
      { time: duration * 0.2, progress: 30 },
      { time: duration * 0.5, progress: 60 },
      { time: duration * 0.8, progress: 85 },
      { time: duration * 0.95, progress: 95 }
    ];

    let currentInterval = 0;
    const startTime = Date.now();

    const timer = setInterval(() => {
      const elapsed = Date.now() - startTime;
      
      // Trouver l'intervalle actuel
      while (currentInterval < intervals.length - 1 && 
             elapsed >= intervals[currentInterval + 1].time) {
        currentInterval++;
      }

      if (currentInterval < intervals.length - 1) {
        // Interpolation linéaire entre deux points
        const curr = intervals[currentInterval];
        const next = intervals[currentInterval + 1];
        const segmentProgress = (elapsed - curr.time) / (next.time - curr.time);
        const newProgress = curr.progress + (next.progress - curr.progress) * segmentProgress;
        setProgress(Math.min(95, Math.round(newProgress)));
      }

      if (elapsed >= duration) {
        clearInterval(timer);
      }
    }, 50);

    return () => clearInterval(timer);
  }, [duration]);

  return (
    <div style={{
      width: '100%',
      maxWidth: '400px',
      margin: '0 auto',
      textAlign: 'center'
    }}>
      <div style={{
        fontSize: '40px',
        marginBottom: '20px'
      }}>
        🤖
      </div>
      
      <h3 style={{marginBottom: '20px', fontSize: '18px'}}>
        {message}
      </h3>

      {/* Barre de progression */}
      <div style={{
        width: '100%',
        height: '32px',
        background: '#e0e0e0',
        borderRadius: '16px',
        overflow: 'hidden',
        position: 'relative',
        marginBottom: '12px',
        boxShadow: 'inset 0 2px 4px rgba(0,0,0,0.1)'
      }}>
        <div style={{
          width: `${progress}%`,
          height: '100%',
          background: 'linear-gradient(90deg, #10b981, #059669)',
          transition: 'width 0.3s ease',
          borderRadius: '16px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'flex-end',
          paddingRight: progress > 15 ? '12px' : '0'
        }}>
          {progress > 15 && (
            <span style={{
              color: 'white',
              fontWeight: 'bold',
              fontSize: '14px',
              textShadow: '0 1px 2px rgba(0,0,0,0.3)'
            }}>
              {progress}%
            </span>
          )}
        </div>
      </div>

      {/* Pourcentage en grand si barre trop petite */}
      {progress <= 15 && (
        <div style={{
          fontSize: '24px',
          fontWeight: 'bold',
          color: '#10b981',
          marginTop: '-8px',
          marginBottom: '8px'
        }}>
          {progress}%
        </div>
      )}

      <p style={{
        fontSize: '13px',
        color: '#666',
        marginTop: '8px'
      }}>
        {progress < 30 ? "Connexion à Gemini..." :
         progress < 60 ? "Analyse de l'image..." :
         progress < 85 ? "Extraction des données..." :
         "Finalisation..."}
      </p>
    </div>
  );
};

export default ProgressBar;
