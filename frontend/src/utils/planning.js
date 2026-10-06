import { asList, number } from './contracts';
const key = value => String(value || '').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase().trim();
const measures = {kg:['mass',1],g:['mass',.001],l:['volume',1],ml:['volume',.001],cl:['volume',.01],piece:['count',1],pieces:['count',1],pcs:['count',1]};
export function convertQuantity(quantity, from, to) {
 const a=key(from),b=key(to);if(!a || !b) return null;
 if(a===b) return number(quantity);
 const source=measures[a],target=measures[b];
 return source && target && source[0]===target[0] ? number(quantity)*source[1]/target[1] : null;
}
export function recipeCapacity(recipe,products=[],stocks=[]) {
 const errors=[],ingredients=[],batchSize=number(recipe.portions);
 let maximum=Infinity,cost=0;
 if(batchSize<=0) errors.push('Nombre de portions manquant');
 if(!asList(recipe.ingredients).length) errors.push('Ingrédients manquants');
 for(const ing of asList(recipe.ingredients)) {
  const product=products.find(p=>p.id===(ing.produit_id || ing.ingredient_id));
  if(!product || ing.ingredient_type==='preparation') {errors.push(`Ingrédient non disponible : ${ing.produit_nom || ing.ingredient_nom || 'sans correspondance'}`);continue;}
  const quantity=convertQuantity(ing.quantite,ing.unite,product.unite);
  if(quantity===null || quantity<=0 || batchSize<=0) {errors.push(`Quantité ou unité incompatible : ${product.nom}`);continue;}
  const perPortion=quantity/batchSize,stock=number(stocks.find(s=>s.produit_id===product.id)?.quantite_actuelle);
  maximum=Math.min(maximum,Math.floor(Math.max(0,stock)/perPortion+1e-9));
  cost+=quantity*number(product.prix_achat ?? product.reference_price);
  ingredients.push({product,perPortion,stock,quantity});
 }
 return {recipe,ingredients,errors,portions:errors.length || !Number.isFinite(maximum) ? null : maximum,costPerPortion:errors.length ? null : cost/batchSize};
}
export function buildPurchaseDrafts(recipes,products,stocks,suppliers) {
 const errors=[],required=new Map(),orders=new Map();
 for(const r of asList(recipes)) {
  const qty=number(r.selectedQuantity);if(qty<=0){errors.push(`${r.nom} : nombre de portions invalide`);continue;}
  const capacity=recipeCapacity(r,products,stocks);errors.push(...capacity.errors.map(e=>`${r.nom} : ${e}`));
  for(const ingredient of capacity.ingredients) {
   const id=ingredient.product.id,prior=required.get(id);
   required.set(id,{...ingredient,needed:(prior?.needed || 0)+ingredient.perPortion*qty});
  }
 }
 if(errors.length) return {orders:[],errors};
 for(const row of required.values()) {
  const quantity=Math.max(0,Math.round((row.needed-row.stock)*1000000)/1000000);if(!quantity)continue;
  const product=row.product,supplierId=product.main_supplier_id || product.fournisseur_id;
  const supplier=suppliers.find(s=>s.id===supplierId);
  if(!supplier){errors.push(`${product.nom} : fournisseur non renseigné`);continue;}
  const order=orders.get(supplierId) || {supplierId,supplierName:supplier.nom,products:[],total:0};
  const price=number(product.prix_achat ?? product.reference_price);
  order.products.push({productId:product.id,productName:product.nom,quantity,unit:product.unite,pricePerUnit:price,totalPrice:quantity*price});
  order.total+=quantity*price;orders.set(supplierId,order);
 }
 return {orders:errors.length ? [] : [...orders.values()],errors};
}
