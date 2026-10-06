import React from 'react';
export default class ErrorBoundary extends React.Component {
 state = {error:false};
 static getDerivedStateFromError() { return {error:true}; }
 componentDidCatch(error) { console.error('Restop: erreur d’affichage',error); }
 render() {
  if (!this.state.error) return this.props.children;
  return <main className="rt-loading" role="alert"><h1>Cet écran n’a pas pu s’afficher.</h1><p>Vos données enregistrées sont conservées. Rechargez l’application pour revenir à votre espace.</p><button className="rt-button rt-peach" onClick={()=>window.location.reload()}>Recharger l’application</button><a href="/">Retour à l’accueil</a></main>;
 }
}
