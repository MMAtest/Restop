/** Chrome smoke test for mocked Restop /app actions.
 * Requires built frontend served with SPA fallback on RESTOP_PREVIEW_URL (default localhost:4173).
 * Uses fictitious authenticated session and intercepts /api/*; NO real API mutations.
 * Install playwright-core locally (npm install --no-save playwright-core), and set
 * CHROME_EXECUTABLE if Chrome does not live in /Applications/Google Chrome.app.
 */
const {chromium}=require('playwright-core');
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:process.env.CHROME_EXECUTABLE||'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',args:['--no-sandbox']});
 for(const config of [{name:'desktop',width:1440,height:900},{name:'mobile',width:390,height:844}]){
  const page=await browser.newPage({viewport:{width:config.width,height:config.height}});
  const product={id:'product-1',nom:'Tomates fraîches',prix_achat:3.4,unite:'kg',categorie:'Légumes'};
  const prep={id:'prep-1',nom:'Tomates découpées',produit_id:product.id,produit_nom:product.nom,quantite_preparee:3,unite_preparee:'kg',forme_decoupe:'julienne',perte:0,perte_pourcentage:0};
  const endpoints={produits:[product],preparations:[prep],stocks:[{produit_id:product.id,produit_nom:product.nom,quantite_actuelle:8,quantite_min:20,unite:'kg'}],fournisseurs:[],recettes:[],rapports_z:[],orders:[],mouvements:[], '/dashboard/stats':{},'/dashboard/missing-data-alerts':{alerts:[]},'/ocr/documents':[], '/analytics/alerts':{expiring_products:[],low_stock_items:[],price_anomalies:[]}};
  let errors=[], archiveCalls=0,deleteCalls=0;
  page.on('pageerror',e=>errors.push(e.message));
  await page.addInitScript(()=>localStorage.setItem('user_session',JSON.stringify({session_id:'fake-qa',user:{id:'qa-1',username:'qa',full_name:'Camille',role:'patron'}})));
  await page.route(/\/api\//, async route=>{
   const path=new URL(route.request().url()).pathname.replace(/^\/api\//,'');
   if(route.request().method()==='DELETE'){deleteCalls++;return route.fulfill({status:200,body:'{}',contentType:'application/json'});}
   if(route.request().method()==='POST'&&path==='archive'){archiveCalls++;return route.fulfill({status:200,body:'{}',contentType:'application/json'});}
   const data=path==='auth/session'?{valid:true,user:{id:'qa-1',username:'qa',full_name:'Camille',role:'patron'}}:(endpoints[path]??endpoints['/'+path]??[]);
   await route.fulfill({status:200,contentType:'application/json',body:JSON.stringify(data),headers:{'access-control-allow-origin':'*'}});
  });
  await page.goto((process.env.RESTOP_PREVIEW_URL||'http://127.0.0.1:4173').replace(/\/$/,'')+'/app');
  await page.getByText(/Bonjour Camille/).first().waitFor({timeout:16000});
  const nav=async name=>{
   if(config.name==='mobile')await page.getByRole('button',{name:'Ouvrir le menu'}).click();
   await page.getByRole('navigation',{name:'Navigation principale'}).getByRole('button',{name}).click();
  };
  await nav('Production');
  await page.getByRole('button',{name:'Nouveau Produit'}).first().click();
  const create=page.getByRole('dialog',{name:'Ajouter un produit'});
  await create.waitFor();
  if(await create.locator('input').first().getAttribute('id')===null)throw Error('Form label is not associated');
  if(process.env.RESTOP_SCREENSHOT_DIR)await page.screenshot({path:`${process.env.RESTOP_SCREENSHOT_DIR}/dialog-product-${config.name}.png`,fullPage:false});
  await create.locator('input').first().fill('Tomates cerises');
  await create.getByRole('button',{name:'Fermer le formulaire'}).click();
  await create.getByText(/Des modifications ne sont pas enregistrées/).waitFor();
  await create.getByRole('button',{name:'Continuer la saisie'}).click();
  await create.getByRole('button',{name:'Fermer le formulaire'}).click();
  await create.getByRole('button',{name:'Quitter sans enregistrer'}).click();
  if(await page.getByRole('dialog',{name:'Ajouter un produit'}).count())throw Error('Form not closed');
  // Deliberate archive decision, no requests until explicit submit.
  await page.getByRole('button',{name:'Archiver'}).first().click();
  const arch=page.getByRole('dialog',{name:/Archiver Tomates fraîches/});
  await arch.waitFor();
  if(archiveCalls)throw Error('Archive sent before consent');
  if(process.env.RESTOP_SCREENSHOT_DIR)await page.screenshot({path:`${process.env.RESTOP_SCREENSHOT_DIR}/dialog-archive-${config.name}.png`});
  await arch.getByRole('textbox',{name:/Motif/}).fill('Saison terminée');
  await arch.getByRole('button',{name:'Archiver',exact:true}).click();
  if(archiveCalls!==1)throw Error('Archive missing after consent '+archiveCalls);
  await page.getByRole('group',{name:'Rubriques de production'}).getByRole('button',{name:/Préparations/}).click();
  // Existing delete action on a preparation should require typed SUPPRIMER.
  const prepDel=page.getByRole('button',{name:/🗑️/}).first();
  await prepDel.click();
  const dialog=page.getByRole('dialog',{name:/Supprimer définitivement cet élément/});
  await dialog.waitFor();
  if(deleteCalls)throw Error('Delete called before consent');
  if(process.env.RESTOP_SCREENSHOT_DIR)await page.screenshot({path:`${process.env.RESTOP_SCREENSHOT_DIR}/dialog-delete-${config.name}.png`});
  const submit=dialog.getByRole('button',{name:'Supprimer définitivement'});
  if(!(await submit.isDisabled()))throw Error('Delete not gated');
  await dialog.getByRole('textbox',{name:/Saisir SUPPRIMER/}).fill('SUPPRIMER');
  await submit.click();
  if(deleteCalls!==1)throw Error('Delete action not sent exactly once '+deleteCalls);
  const dims=await page.evaluate(()=>({scroll:document.documentElement.scrollWidth,viewport:innerWidth}));
  if(dims.scroll>dims.viewport)throw Error('Horizontal overflow '+JSON.stringify(dims));
  if(errors.length)throw Error(errors.join(';'));
  console.log(config.name,'forms, unsaved guard, archiving, irreversible typed delete PASS',dims);
  await page.close();
 }
 await browser.close();
})().catch(e=>{console.error('CHROME QA ERROR',e);process.exit(1)})
