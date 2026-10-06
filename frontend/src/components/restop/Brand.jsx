import React from 'react';

export default function Brand({ light = false }) {
  return <span className={`rt-brand${light ? ' rt-brand-light' : ''}`} aria-label="Restop">rest<span>op</span></span>;
}
