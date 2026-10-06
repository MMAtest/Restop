export const asList = (value, key) => (Array.isArray(value) ? value : Array.isArray(value?.[key]) ? value[key] : []).filter(v => v != null);
export const number = (value, fallback = 0) => value !== null && value !== '' && Number.isFinite(Number(value)) ? Number(value) : fallback;
export const CATEGORIES = ['Entrée', 'Plat', 'Dessert', 'Bar', 'Autres'];
export const UNITS = [
  {code:'kg',label:'Kilogramme (kg)',type:'poids'}, {code:'g',label:'Gramme (g)',type:'poids'},
  {code:'L',label:'Litre (L)',type:'volume'}, {code:'mL',label:'Millilitre (mL)',type:'volume'},
  {code:'cl',label:'Centilitre (cl)',type:'volume'}, {code:'pièce',label:'Pièce',type:'unite'},
  {code:'portion',label:'Portion',type:'unite'}, {code:'botte',label:'Botte',type:'unite'}, {code:'colis',label:'Colis',type:'unite'}
];
export function categories(value) { const rows=asList(value,'categories').filter(v=>typeof v==='string'); return rows.length ? rows : CATEGORIES; }
export function units(value) { const rows=asList(value,'unites').filter(v=>v && typeof v.code==='string'); return rows.length ? rows : UNITS; }
export function recipe(row) {
 return {...row,nom:String(row.nom || row.name || ''),portions:number(row.portions,1),prix_vente:number(row.prix_vente),coefficient_prevu:number(row.coefficient_prevu),coefficient_reel:number(row.coefficient_reel),cout_matiere:number(row.cout_matiere),ingredients:asList(row.ingredients).map(i=>({...i,quantite:number(i.quantite),cout_unitaire:number(i.cout_unitaire),cout_total:number(i.cout_total)}))};
}
export function missionGroups(value,userId) {
 if (!Array.isArray(value)) return {assigned_to_me:asList(value,'assigned_to_me'),created_by_me:asList(value,'created_by_me')};
 return {assigned_to_me:value.filter(m=>m && (m.assigned_to_user_id===userId || userId==='demo-restop')),created_by_me:value.filter(m=>m && (m.assigned_by_user_id===userId || userId==='demo-restop'))};
}
export function groupedProducts(value,products=[]) {
 if (value && !Array.isArray(value) && value.categories && typeof value.categories==='object') return {...value,categories:Object.fromEntries(Object.entries(value.categories).map(([key,v])=>[key,{...v,products:asList(v,'products')}]))};
 const groups={};for(const p of asList(products)){const key=p.categorie || 'Non classé';if(!groups[key])groups[key]={products:[],count:0};groups[key].products.push(p);groups[key].count++;}
 return {categories:groups,total_categories:Object.keys(groups).length,total_products:products.length};
}

export const cutFormCode = value => String(value || '').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase().trim();
export function cutForms(value) {
 const normalize = rows => rows.map(row => typeof row === 'string' ? {id:cutFormCode(row),nom:row,description:''} : row).filter(row=>row && row.id && row.nom);
 const predefined = normalize(asList(value,'predefined'));
 for(const row of [{id:'sauce',nom:'Sauce',description:'Transformé en sauce'},{id:'frites',nom:'Frites',description:'Taillé en bâtonnets'}]) if(!predefined.some(f=>f.id===row.id))predefined.push(row);
 return {predefined,custom:normalize(asList(value,'custom'))};
}

export function restaurantDate(value) {
 if (!value) return '';
 if (/^\d{4}-\d{2}-\d{2}$/.test(value)) return value;
 const date=new Date(value); if (!Number.isFinite(date.getTime())) return '';
 const parts=new Intl.DateTimeFormat('en-CA',{timeZone:'Europe/Paris',year:'numeric',month:'2-digit',day:'2-digit'}).formatToParts(date);
 const get=type=>parts.find(p=>p.type===type).value;
 return `${get('year')}-${get('month')}-${get('day')}`;
}
