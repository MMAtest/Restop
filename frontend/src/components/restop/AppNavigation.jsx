import React, { useState } from 'react';
import { House, Package, ShoppingCart, ChefHat, ChartBar, Users, Receipt, SignOut, ArrowClockwise, List, X, ArrowSquareOut } from '@phosphor-icons/react';
import Brand from './Brand';

export default function AppNavigation({ activeTab, onNavigate, user, onLogout, onRefresh, loading, canOrders, onSuppliers }) {
  const [open, setOpen] = useState(false);
  const manager = ['patron', 'super_admin','gerant'].includes(user?.role);
  const items = [
    ['overview', 'Vue d’ensemble', House], ['stocks', 'Stocks', Package],
    ...(canOrders ? [['orders', 'Achats', ShoppingCart]] : []),
    ...(['patron','super_admin','gerant','chef_cuisine'].includes(user?.role) ? [['production', 'Production', ChefHat]] : []),
    ...(manager ? [['dashboard', 'Ventes & analyses', ChartBar], ...(user?.role !== 'gerant' ? [['users','Équipe',Users]] : [])] : [['dashboard', 'Mes missions', Users]]),
  ];
  const navigate = (id) => { onNavigate(id); setOpen(false); window.scrollTo({ top: 0 }); };
  const demo = user?.username === 'commercial_demo' || /demo|démo/i.test(user?.full_name || '');
  return <>
    <button className="rt-mobile-menu" onClick={() => setOpen(!open)} aria-expanded={open} aria-controls="rt-navigation" aria-label={open ? 'Fermer le menu' : 'Ouvrir le menu'}>{open ? <X size={23} /> : <List size={23} />}</button>
    {open && <button className="rt-nav-backdrop" aria-label="Fermer le menu" onClick={() => setOpen(false)} />}
    <aside id="rt-navigation" className={`rt-sidebar ${open ? 'is-open' : ''}`}>
      <a className="rt-sidebar-brand" href="/" aria-label="Restop — accueil"><Brand light /></a>
      <p className="rt-nav-caption">VOTRE ÉTABLISSEMENT</p>
      <nav aria-label="Navigation principale">{items.map(([id, label, Icon]) => <button key={id} aria-current={activeTab === id ? 'page' : undefined} className={activeTab === id ? 'active' : ''} onClick={() => navigate(id)}><Icon size={22} weight="light" />{label}</button>)}</nav>
      {canOrders && <button className="rt-supplier-link" onClick={() => { onSuppliers(); setOpen(false); }}><Receipt size={21} weight="light" />Fournisseurs</button>}
      <div className="rt-sidebar-bottom"><a href="/">Présentation de Restop <ArrowSquareOut size={17} /></a><button onClick={onRefresh} disabled={loading}><ArrowClockwise size={19} />{loading ? 'Actualisation…' : 'Actualiser les données'}</button><button onClick={onLogout}><SignOut size={19} />Se déconnecter</button></div>
      <div className="rt-sidebar-user"><span className="rt-avatar">{(user?.full_name || user?.username || 'R').slice(0, 1).toUpperCase()}</span><span>{user?.full_name || user?.username}<small>{demo ? 'Espace de démonstration' : ({patron:'Gérant',super_admin:'Administrateur',chef:'Chef de cuisine',employe_cuisine:'Cuisine',caissier:'Caisse',barman:'Bar'}[user?.role] || 'Équipe')}</small></span></div>
    </aside>
    <header className="rt-app-topbar"><div><strong>{user?.restaurant_name || (demo ? 'La Table d’Augustine' : 'Mon établissement')}</strong><span>{demo ? 'Données de démonstration' : 'Votre espace de gestion'}</span></div><time>{new Date().toLocaleDateString('fr-FR', {day:'numeric',month:'long',year:'numeric'})}</time><span className="rt-avatar">{(user?.full_name || 'R').slice(0, 1)}</span></header>
    <nav className="rt-mobile-bottom" aria-label="Accès rapides">{items.slice(0, 4).map(([id, label, Icon]) => <button key={id} className={activeTab === id ? 'active' : ''} aria-current={activeTab === id ? 'page' : undefined} onClick={() => navigate(id)}><Icon size={22} />{id === 'overview' ? 'Accueil' : label}</button>)}</nav>
  </>;
}
