import React, { Suspense, lazy } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import LandingPage from './pages/LandingPage';
import ErrorBoundary from './components/restop/ErrorBoundary';
import '@fontsource/inter/400.css';
import '@fontsource/inter/500.css';
import '@fontsource/inter/600.css';
import '@fontsource/dm-serif-display/400.css';
import './styles/restop.css';

const App = lazy(() => import('./App'));
export default function Root() {
  return <ErrorBoundary><BrowserRouter><Suspense fallback={<div className="rt-loading" role="status">Ouverture de votre espace…</div>}><Routes><Route path="/" element={<LandingPage />} /><Route path="/connexion" element={<App />} /><Route path="/app/*" element={<App />} /><Route path="*" element={<div className="rt-loading"><h1>Cette page n’existe pas.</h1><a href="/">Revenir à l’accueil</a></div>} /></Routes></Suspense></BrowserRouter></ErrorBoundary>;
}
