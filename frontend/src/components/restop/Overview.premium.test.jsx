import React, {act} from 'react';
import {createRoot} from 'react-dom/client';
import Overview, {previewStocks} from './Overview';

let node,root;
const onStocks=jest.fn();
const onPurchases=jest.fn();
const onImport=jest.fn();

async function mount(props={}) {
  await act(async()=>root.render(<Overview stocks={previewStocks} user={{full_name:'Camille',role:'patron'}}
    onStocks={onStocks} onPurchases={onPurchases} onImport={onImport} {...props}/>));
}
const press=async pattern=>{
  const button=[...node.querySelectorAll('button')].find(el=>pattern.test(el.textContent));
  expect(button).toBeTruthy();
  await act(async()=>button.click());
};

beforeEach(()=>{
  global.IS_REACT_ACT_ENVIRONMENT=true;
  node=document.createElement('div');document.body.appendChild(node);
  root=createRoot(node);
});
afterEach(async()=>{await act(async()=>root.unmount());node.remove();jest.clearAllMocks()});

test('tableau lisible, vrais produits et niveaux de stock accessibles',async()=>{
  await mount();
  expect(node.textContent).toContain('État des stocks');
  expect(node.textContent).toContain('Mozzarella di bufala');
  expect(node.querySelectorAll('table tbody tr').length).toBe(3);
  expect(node.querySelectorAll('[role=meter]').length).toBe(6); // desktop table + mobile cards
  expect(node.textContent).toContain('Documents à vérifier');
  await press(/Voir l’inventaire/);
  expect(onStocks).toHaveBeenCalledTimes(1);
});

test('filtres interactifs : tous, rupture, puis retour à surveiller',async()=>{
  await mount({stocks:[...previewStocks,{produit_id:'healthy',produit_nom:'Eau minérale',quantite_actuelle:12,quantite_min:5,unite:'bouteille'},
    {produit_id:'empty',produit_nom:'Beurre',quantite_actuelle:0,quantite_min:8,unite:'kg'}]});
  expect(node.querySelectorAll('table tbody tr').length).toBe(4);
  await press(/Tous les produits/);
  expect(node.querySelectorAll('table tbody tr').length).toBe(5);
  expect(node.textContent).toContain('Eau minérale');
  await press(/Ruptures/);
  expect(node.querySelectorAll('table tbody tr').length).toBe(1);
  expect(node.textContent).toContain('Beurre');
  expect(node.querySelector('button[aria-pressed=true]')?.textContent).toContain('Ruptures');
  await press(/À surveiller/);
  expect(node.querySelectorAll('table tbody tr').length).toBe(4);
});

test('écran vide et erreur ont des actions claires',async()=>{
  await mount({stocks:[],error:''});
  expect(node.textContent).toContain('Votre suivi commence ici');
  expect(node.querySelector('table')).toBeNull();
  await mount({stocks:[],error:'Connexion indisponible',onRetry:onStocks});
  expect(node.querySelector('[role=alert]').textContent).toContain('Connexion indisponible');
  await press(/Réessayer/);
  expect(onStocks).toHaveBeenCalledTimes(1);
});
