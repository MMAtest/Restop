import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { ArrowRight, ArrowDown, House, Package, ShoppingCart, ChefHat, ChartBar, Users, CheckCircle, List, X, Receipt, Check } from '@phosphor-icons/react';
import Brand from '../components/restop/Brand';
import Overview, { previewStocks } from '../components/restop/Overview';

const features = [
  ['Stocks & inventaires', 'Sachez ce qu’il vous reste, et ce qu’il faut prévoir.', 'Quantités disponibles, seuils d’alerte, mouvements et suivi des lots : retrouvez les informations utiles avant de passer commande.', Package],
  ['Recettes & production', 'Gardez vos recettes au cœur de la gestion.', 'Centralisez vos ingrédients, vos préparations et vos fiches recettes. Consultez les coûts matière pour mieux suivre votre carte.', ChefHat],
  ['Ventes & pilotage', 'Prenez du recul après le service.', 'Retrouvez les rapports Z, consultez vos ventes et analysez les coûts sur la période de votre choix.', ChartBar],
];
const roles = [
  ['Gérant', 'Une vision d’ensemble, sans perdre le détail.', 'Retrouvez les stocks, les achats, les ventes et les accès de votre équipe dans un même espace.'],
  ['Cuisine', 'Les bonnes informations, au bon moment.', 'Consultez les produits disponibles, suivez les préparations et retrouvez les recettes utiles à la production.'],
  ['Bar & caisse', 'Chacun retrouve ses outils.', 'Des accès adaptés aux rôles pour suivre les opérations du bar, les clôtures et les missions confiées à l’équipe.'],
];

export default function LandingPage() {
  const [menu, setMenu] = useState(false);
  const [role, setRole] = useState(0);
  const [demoLoading, setDemoLoading] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();
  const demo = async () => {
    if (demoLoading) return;
    setDemoLoading(true); setError('');
    try {
      const { data } = await axios.post(`${process.env.REACT_APP_BACKEND_URL}/api/auth/demo`);
      if (!data.session_id || !data.user) throw new Error('Session indisponible');
      localStorage.setItem('user_session', JSON.stringify({ user: data.user, session_id: data.session_id, login_time: new Date().toISOString() }));
      axios.defaults.headers.common.Authorization = `Bearer ${data.session_id}`;
      navigate('/app');
    } catch (_) { setError('La démonstration est momentanément indisponible. Réessayez dans un instant ou accédez à la connexion.'); }
    finally { setDemoLoading(false); }
  };
  const DemoButton = ({ children = 'Découvrir la démo', secondary = false }) => <button className={`rt-button ${secondary ? 'rt-outline' : 'rt-peach'}`} onClick={demo} disabled={demoLoading}>{demoLoading ? 'Ouverture de la démo…' : children}<ArrowRight size={19} /></button>;
  return <div className="rt-landing">
    <a className="rt-skip" href="#contenu">Aller au contenu</a>
    <header className="rt-site-header"><Link to="/" aria-label="Restop, accueil"><Brand /></Link><button className="rt-site-menu-button" onClick={() => setMenu(!menu)} aria-expanded={menu} aria-controls="site-nav" aria-label={menu ? 'Fermer le menu' : 'Ouvrir le menu'}>{menu ? <X size={24} /> : <List size={24} />}</button><nav id="site-nav" className={menu ? 'is-open' : ''} aria-label="Navigation du site"><a href="#fonctionnalites" onClick={() => setMenu(false)}>Fonctionnalités</a><a href="#equipe" onClick={() => setMenu(false)}>Pour votre équipe</a><a href="#questions" onClick={() => setMenu(false)}>Questions fréquentes</a></nav><div className="rt-header-actions"><Link to="/connexion">Connexion</Link><DemoButton /></div></header>
    {error && <div className="rt-demo-error" role="alert">{error}<button aria-label="Fermer le message" onClick={() => setError('')}><X size={18} /></button></div>}
    <main id="contenu">
      <section className="rt-hero"><img className="rt-hero-photo" src="/images/restop-chef.webp" alt="Un chef dressant une assiette de légumes frais" fetchPriority="high" width="1400" height="1200" /><div className="rt-hero-copy"><p className="rt-eyebrow">Le quotidien du restaurant, simplement</p><h1>Moins de gestion.<br />Plus de cuisine.</h1><p className="rt-hero-intro">Stocks, achats, recettes et ventes :<br className="rt-desktop-br" /> votre restaurant, enfin au même endroit.</p><DemoButton /><span className="rt-hero-note">Explorez un restaurant de démonstration, sans inscription.</span></div></section>
      <section className="rt-preview-section" aria-label="Aperçu de l’application Restop"><div className="rt-product-preview"><aside className="rt-preview-sidebar"><Brand light /><div>{[[House,'Vue d’ensemble'],[Package,'Stocks'],[ShoppingCart,'Achats'],[ChefHat,'Production'],[ChartBar,'Ventes'],[Users,'Équipe']].map(([Icon,label],i) => <button key={label} className={i === 0 ? 'active' : ''} onClick={demo}><Icon size={23} weight="light" />{label}</button>)}</div><small>Votre quotidien,<br />un peu plus simple.</small></aside><div className="rt-preview-main"><div className="rt-preview-top"><div><strong>La Table d’Augustine</strong><span>Données de démonstration</span></div><span>Votre espace de gestion</span></div><Overview preview user={{full_name:'Démo'}} stocks={previewStocks} onStocks={demo} onImport={demo} onPurchases={demo} /></div></div><p className="rt-preview-caption">Un aperçu du produit. <button onClick={demo}>Explorez la démo interactive <ArrowRight size={16} /></button></p></section>
      <section id="fonctionnalites" className="rt-invoice-section rt-section"><div className="rt-invoice-copy"><p className="rt-eyebrow">Achats et stocks</p><h2>De la livraison au service,<br />tout se suit.</h2><p>Vos factures ne devraient pas vous prendre toute la soirée. Importez vos documents, vérifiez les informations extraites et validez vos réceptions.</p><p>Produits, fournisseurs et quantités restent au même endroit. Vous gardez la main à chaque étape.</p><DemoButton /></div><div className="rt-invoice-visual"><img src="/images/restop-invoice.webp" alt="Exemple de facture fournisseur, près d’ingrédients frais" width="1100" height="1000" loading="lazy" /><div className="rt-receipt-preview"><div><Receipt size={23} /><strong>Réception à vérifier</strong><span className="rt-example">Exemple</span></div><p><span>Tomates fraîches</span><span>10 kg</span><Check size={18} /></p><p><span>Mozzarella di bufala</span><span>2 kg</span><Check size={18} /></p><p><span>Basilic frais</span><span>100 g</span><Check size={18} /></p><button onClick={demo}>Voir le parcours dans la démo <ArrowRight size={17} /></button></div></div></section>
      <div className="rt-section-divider"><span>Une solution conçue pour votre quotidien</span></div>
      <section className="rt-features rt-section"><div className="rt-section-intro"><p className="rt-eyebrow">Chaque étape compte</p><h2>La cuisine avance.<br />La gestion suit.</h2><p>Du produit qui entre en réserve au bilan du service, retrouvez une continuité dans vos opérations.</p></div><div className="rt-feature-list">{features.map(([label,title,body,Icon]) => <article key={label}><Icon size={30} weight="light" /><div><p className="rt-eyebrow">{label}</p><h3>{title}</h3><p>{body}</p><button className="rt-text-link" onClick={demo}>Explorer dans Restop <ArrowRight size={17} /></button></div></article>)}</div></section>
      <section id="equipe" className="rt-team-section"><div className="rt-section"><p className="rt-eyebrow">Un outil partagé, des rôles clairs</p><h2>Une équipe.<br />Le même fil conducteur.</h2><div className="rt-team-layout"><div className="rt-role-tabs" role="tablist" aria-label="Votre rôle dans le restaurant">{roles.map(([label],i) => <button role="tab" key={label} id={`role-${i}`} aria-selected={role === i} aria-controls="role-panel" tabIndex={role === i ? 0 : -1} onKeyDown={e => { if (['ArrowRight','ArrowDown','ArrowLeft','ArrowUp'].includes(e.key)) { e.preventDefault(); const next=(role+(['ArrowRight','ArrowDown'].includes(e.key)?1:2))%3; setRole(next); document.getElementById(`role-${next}`)?.focus(); } }} onClick={() => setRole(i)}><span>{label}</span><ArrowRight size={23} /></button>)}</div><div id="role-panel" role="tabpanel" aria-labelledby={`role-${role}`} className="rt-role-panel"><Users size={34} weight="light" /><h3>{roles[role][1]}</h3><p>{roles[role][2]}</p><DemoButton /></div></div></div></section>
      <section id="questions" className="rt-faq rt-section"><div><p className="rt-eyebrow">Avant de commencer</p><h2>Les choses<br />à savoir.</h2></div><div>{[
        ['Puis-je essayer Restop sans créer de compte ?', 'Oui. La démonstration ouvre un espace avec des données d’exemple pour explorer les stocks, les achats, les recettes et les ventes. Il s’agit de données de démonstration, séparées de votre futur établissement.'],
        ['Puis-je l’utiliser sur téléphone ?', 'L’interface s’adapte au téléphone, à la tablette et à l’ordinateur. Vous pouvez consulter les stocks ou retrouver une information depuis un navigateur.'],
        ['Comment se passe l’import des factures ?', 'Vous importez votre document dans le module dédié. Vous vérifiez les informations proposées avant de valider leur utilisation dans la gestion de votre établissement.'],
        ['Toute mon équipe voit-elle les mêmes informations ?', 'Les fonctionnalités accessibles dépendent du rôle attribué : gérant, cuisine, bar ou caisse. Le gérant retrouve la gestion des utilisateurs dans son espace.'],
        ['Comment démarrer avec mon restaurant ?', 'Depuis Connexion, choisissez Créer un compte pour ouvrir l’espace de votre établissement. Vous pourrez ensuite renseigner vos fournisseurs, produits et recettes.'],
      ].map(([q,a]) => <details key={q}><summary>{q}<ArrowDown size={19} /></summary><p>{a}</p></details>)}</div></section>
      <section className="rt-final-cta"><p className="rt-eyebrow">Et si votre gestion devenait plus simple ?</p><h2>Votre prochain service<br />commence ici.</h2><DemoButton /><p><CheckCircle size={17} />Sans inscription · Avec des données d’exemple</p></section>
    </main>
    <footer className="rt-footer"><a href="/" aria-label="Restop, accueil"><Brand /></a><p>La gestion au service de la restauration.</p><nav aria-label="Navigation de pied de page"><a href="#fonctionnalites">Fonctionnalités</a><a href="#equipe">Équipe</a><Link to="/connexion">Connexion</Link></nav><small>© {new Date().getFullYear()} Restop · Un produit DIGIGROUPE</small></footer>
  </div>;
}
