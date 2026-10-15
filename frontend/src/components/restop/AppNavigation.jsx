import React, {useEffect, useRef, useState} from 'react';
import {House,Package,ShoppingCart,ChefHat,ChartBar,Users,Receipt,SignOut,ArrowClockwise,List,X,ArrowSquareOut,MagnifyingGlass,Command,ArrowRight} from '@phosphor-icons/react';
import Brand from './Brand';
import './navigation-premium.css';

const labels={patron:'Direction',super_admin:'Administrateur',gerant:'Gérant',chef_cuisine:'Cuisine',employe_cuisine:'Cuisine',caissier:'Caisse',barman:'Bar'};
const groupOf=id=>id==='overview'?'PILOTAGE':id==='dashboard'||id==='users'?'ANALYSE & ÉQUIPE':'OPÉRATIONS';

export default function AppNavigation({activeTab,onNavigate,user,onLogout,onRefresh,loading,canOrders,onSuppliers}) {
  const [open,setOpen]=useState(false);
  const [searchOpen,setSearchOpen]=useState(false);
  const [search,setSearch]=useState('');
  const searchRef=useRef(null);
  const manager=['patron','super_admin','gerant'].includes(user?.role);
  const items=[
    ['overview','Vue d’ensemble',House], ['stocks','Stocks',Package],
    ...(canOrders?[['orders','Achats',ShoppingCart]]:[]),
    ...(['patron','super_admin','gerant','chef_cuisine'].includes(user?.role)?[['production','Production',ChefHat]]:[]),
    ...(manager?[['dashboard','Ventes & analyses',ChartBar],...(user?.role!=='gerant'?[['users','Équipe',Users]]:[])]:[['dashboard','Mes missions',Users]])
  ];
  const pages=canOrders?[...items,['suppliers','Fournisseurs',Receipt]]:items;
  const filtered=pages.filter(item=>item[1].toLocaleLowerCase('fr').includes(search.trim().toLocaleLowerCase('fr')));
  const navigate=id=>{
    if(id==='suppliers'){onSuppliers();}else{onNavigate(id);}
    setOpen(false);setSearchOpen(false);setSearch('');window.scrollTo({top:0,behavior:'auto'});
  };
  const demo=user?.username==='commercial_demo'||/demo|démo/i.test(user?.full_name||'');
  useEffect(()=>{
    const keydown=event=>{
      if((event.metaKey||event.ctrlKey)&&event.key.toLowerCase()==='k'){
        event.preventDefault();setOpen(false);setSearchOpen(value=>!value);
      }else if(event.key==='Escape'){setOpen(false);setSearchOpen(false)}
    };
    window.addEventListener('keydown',keydown);
    return()=>window.removeEventListener('keydown',keydown);
  },[]);
  useEffect(()=>{if(searchOpen)searchRef.current?.focus()},[searchOpen]);
  useEffect(()=>{
    const old=document.body.style.overflow;
    if(open||searchOpen)document.body.style.overflow='hidden';
    return()=>{document.body.style.overflow=old};
  },[open,searchOpen]);
  return <>
    <button className="rt-mobile-menu" onClick={()=>setOpen(!open)} aria-expanded={open} aria-controls="rt-navigation" aria-label={open?'Fermer le menu':'Ouvrir le menu'}>{open?<X size={23}/>:<List size={23}/>}</button>
    {open&&<button className="rt-nav-backdrop" aria-label="Fermer le menu" onClick={()=>setOpen(false)}/>}
    <aside id="rt-navigation" className={`rt-sidebar rt-sidebar-v2 ${open?'is-open':''}`}>
      <a className="rt-sidebar-brand" href="/" aria-label="Restop — présentation"><Brand light/></a>
      <button className="rt-nav-search-trigger" onClick={()=>{setOpen(false);setSearchOpen(true)}}><MagnifyingGlass size={18}/><span>Rechercher une page</span><kbd>⌘ K</kbd></button>
      <nav aria-label="Navigation principale" className="rt-nav-groups">{['PILOTAGE','OPÉRATIONS','ANALYSE & ÉQUIPE'].map(group=>{
        const groupItems=items.filter(([id])=>groupOf(id)===group);
        return groupItems.length>0?<div className="rt-nav-group" key={group}>
          <p className="rt-nav-caption">{group}</p>
          {groupItems.map(([id,label,Icon])=><button key={id} aria-current={activeTab===id?'page':undefined} className={activeTab===id?'active':''} onClick={()=>navigate(id)}><Icon size={21} weight={activeTab===id?'regular':'light'}/><span>{label}</span>{activeTab===id&&<span aria-hidden="true" className="rt-nav-current-indicator"/>}</button>)}
        </div>:null;
      })}</nav>
      {canOrders&&<button className="rt-supplier-link" onClick={()=>navigate('suppliers')}><Receipt size={20} weight="light"/><span>Fournisseurs</span></button>}
      <div className="rt-sidebar-bottom"><a href="/">Présentation de Restop <ArrowSquareOut size={17}/></a><button onClick={onRefresh} disabled={loading}><ArrowClockwise size={18}/>{loading?'Actualisation…':'Actualiser les données'}</button><button onClick={onLogout}><SignOut size={18}/>Se déconnecter</button></div>
      <div className="rt-sidebar-user"><span className="rt-avatar">{(user?.full_name||user?.username||'R').slice(0,1).toUpperCase()}</span><span>{user?.full_name||user?.username}<small>{demo?'Espace de démonstration':(labels[user?.role]||'Équipe')}</small></span></div>
    </aside>
    <header className="rt-app-topbar rt-app-topbar-v2">
      <div className="rt-topbar-establishment"><span className="rt-topbar-pretitle">ESPACE RESTOP / {manager?'DIRECTION':'OPÉRATIONS'}</span><strong>{user?.restaurant_name||(demo?'La Table d’Augustine':'Mon établissement')}</strong><span>{demo?'Données de démonstration':'Votre espace de gestion'}</span></div>
      <div className="rt-topbar-actions"><button className="rt-topbar-search" onClick={()=>setSearchOpen(true)} aria-label="Rechercher une page (Ctrl+K)"><MagnifyingGlass size={17}/> <span>Rechercher</span><kbd>⌘ K</kbd></button><time dateTime={new Date().toISOString().slice(0,10)}>{new Date().toLocaleDateString('fr-FR',{day:'numeric',month:'long',year:'numeric'})}</time><span className="rt-avatar">{(user?.full_name||'R').slice(0,1)}</span></div>
    </header>
    <nav className="rt-mobile-bottom" aria-label="Accès rapides">{items.slice(0,4).map(([id,label,Icon])=><button key={id} className={activeTab===id?'active':''} aria-current={activeTab===id?'page':undefined} onClick={()=>navigate(id)}><Icon size={22}/>{id==='overview'?'Accueil':label}</button>)}</nav>
    {searchOpen&&<div className="rt-command-overlay" role="presentation" onMouseDown={event=>{if(event.target===event.currentTarget)setSearchOpen(false)}}>
      <div className="rt-command-dialog" role="dialog" aria-modal="true" aria-labelledby="rt-command-title" onKeyDown={event=>{
        if(event.key!=='Tab')return;
        const focusables=[...event.currentTarget.querySelectorAll('input:not(:disabled),button:not(:disabled)')];
        if(!focusables.length)return;
        const first=focusables[0],last=focusables[focusables.length-1];
        if(event.shiftKey&&document.activeElement===first){event.preventDefault();last.focus();}
        else if(!event.shiftKey&&document.activeElement===last){event.preventDefault();first.focus();}
      }}>
        <div className="rt-command-head"><MagnifyingGlass size={20}/><label id="rt-command-title" htmlFor="rt-page-search" className="rt-sr-only">Rechercher une page Restop</label><input ref={searchRef} id="rt-page-search" type="search" autoComplete="off" placeholder="Stocks, factures, ventes…" value={search} onChange={event=>setSearch(event.target.value)} onKeyDown={event=>{if(event.key==='Enter'&&filtered.length)navigate(filtered[0][0]);}}/><button type="button" onClick={()=>setSearchOpen(false)} aria-label="Fermer la recherche"><X size={19}/></button></div>
        <p className="rt-command-subtitle">NAVIGATION RAPIDE · {filtered.length} RÉSULTAT{filtered.length>1?'S':''}</p>
        <div className="rt-command-results">{filtered.length?filtered.map(([id,label,Icon])=><button key={id} onClick={()=>navigate(id)}><Icon size={21}/><span>{label}<small>{groupOf(id)==='PILOTAGE'?'Pilotage du restaurant':groupOf(id)==='OPÉRATIONS'?'Gestion quotidienne':'Suivi et administration'}</small></span><ArrowRight size={17}/></button>):<div className="rt-command-empty">Aucune rubrique trouvée. Essayez « stocks » ou « achats ».</div>}</div>
        <p className="rt-command-tip">Entrée pour ouvrir le premier résultat · Échap pour fermer</p>
      </div>
    </div>}
  </>;
}
