import React, { useState, useEffect } from 'react';

const ProgressBar = ({ duration = 3000, message = "Traitement en cours..." }) => {
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    // Simulation de progression réaliste et équilibrée
    const intervals = [
      { time: 0, progress: 0 },
      { time: duration * 0.15, progress: 20 },      // 15% du temps → 20%
      { time: duration * 0.35, progress: 40 },      // 35% du temps → 40%
      { time: duration * 0.55, progress: 60 },      // 55% du temps → 60%
      { time: duration * 0.75, progress: 75 },      // 75% du temps → 75%
      { time: duration * 0.90, progress: 85 },      // 90% du temps → 85%
      { time: duration * 0.98, progress: 92 }       // 98% du temps → 92%
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
        setProgress(Math.min(92, Math.round(newProgress)));
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
        {progress < 20 ? "Initialisation..." :
         progress < 40 ? "Connexion à Gemini..." :
         progress < 60 ? "Analyse de l'image..." :
         progress < 75 ? "Extraction des produits..." :
         progress < 85 ? "Détection des quantités et prix..." :
         "Finalisation..."}
      </p>
    </div>
  );
};

export default ProgressBar;
