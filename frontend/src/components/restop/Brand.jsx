import React from 'react';
/** Scalable RESTOP logotype used by landing, preview and authenticated workspace. */
export default function Brand({ light = false }) {
  return <span className={`rt-brand${light ? ' rt-brand-light' : ''}`} aria-label="RESTOP"><img className="rt-brand-symbol" src="/restop-symbol.svg" width="48" height="48" alt="" aria-hidden="true" /><span className="rt-brand-word">RES<span>TOP</span></span></span>;
}
