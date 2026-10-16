/** No backend writes: checks OCR and DLC UX with a mocked session / mocked API.
 * RESTOP_PREVIEW_URL=http://127.0.0.1:4173 NODE_PATH=/tmp/restop-visual/node_modules node frontend/e2e/ocr-dlc-smoke.cjs
 */
const {chromium}=require('playwright-core');
const base=(process.env.RESTOP_PREVIEW_URL||'http://127.0.0.1:4173').replace(/\/$/,'');
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:process.env.CHROME_EXECUTABLE||'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',args:['--no-sandbox']});
 const product={id:'p1',nom:'Tomates fraîches',categorie:'Légumes',prix_achat:4,unite:'kg'};
 for (const config of [{name:'desktop',width:1440,height:900},{name:'mobile',width:390,height:844}]) {
  const page=await browser.newPage({viewport:{width:config.width,height:config.height}});
  await page.addInitScript(()=>localStorage.setItem('user_session',JSON.stringify({session_id:'fake-qa',user:{id:'qa-1',role:'patron',full_name:'Camille',username:'qa'}})));
  let errors=[],uploads=0;
  page.on('pageerror',e=>errors.push(e.message));
  await page.route(/\/api\//,async route=>{
   const path=new URL(route.request().url()).pathname.replace(/^\/api\//,'');
   if(path.includes('/upload-document')||path.includes('/upload'))uploads++;
   const data=path==='auth/session'?{valid:true,user:{id:'qa-1',role:'patron',full_name:'Camille',username:'qa'}}:({
    produits:[product],preparations:[],stocks:[{produit_id:'p1',produit_nom:product.nom,quantite_actuelle:8,quantite_min:20,unite:'kg'}],fournisseurs:[],recettes:[],orders:[],rapports_z:[],mouvements:[],
    'stock/batch-summary':[{product_id:'p1',product_name:product.nom,total_stock:8,expired_batches:1,critical_batches:0,batches:[{batch_number:'L-01',quantity:8}]}],
    'stock/batch-info/p1':{product_id:'p1',product_name:product.nom,total_stock:8,expired_batches:1,near_expiry_batches:0,batches:[{batch_number:'L-01',quantity:8,received_date:'2026-10-01',expiry_date:'2026-10-14',is_consumed:false}]},
    'ocr/documents':[], 'analytics/alerts':{expiring_products:[],low_stock_items:[],price_anomalies:[],unused_stock:[]},'dashboard/stats':{},'dashboard/missing-data-alerts':{alerts:[]}
   })[path]??[];
   await route.fulfill({status:200,contentType:'application/json',body:JSON.stringify(data),headers:{'access-control-allow-origin':'*'}});
  });
  await page.goto(base+'/app');
  await page.getByText(/Bonjour Camille/).first().waitFor({timeout:12000});
  if(config.name==='mobile')await page.getByRole('button',{name:'Ouvrir le menu'}).click();
  await page.getByRole('navigation',{name:'Navigation principale'}).getByRole('button',{name:'Stocks'}).click();
  await page.getByRole('group',{name:'Rubriques des stocks'}).getByRole('button',{name:'OCR'}).click();
  await page.getByRole('button',{name:'Factures',exact:true}).first().click();
  await page.getByRole('button',{name:/Importer Facture/i}).first().click();
  const modal=page.getByRole('dialog',{name:'Importer une facture'});
  await modal.waitFor();
  await modal.getByText('01 · Import').waitFor();
  const file=modal.locator('input[type=file]').first();
  await file.setInputFiles({name:'trop-grand.pdf',mimeType:'application/pdf',buffer:Buffer.alloc(15*1024*1024+1)});
  await page.getByRole('alert').getByText(/dépasse 15 Mo/).waitFor({timeout:8000});
  if(uploads!==0)throw new Error('oversize document reached the server');
  await modal.getByRole('button',{name:'Fermer le formulaire'}).click();
  await modal.waitFor({state:'detached'});
  await page.getByRole('group',{name:'Rubriques des stocks'}).getByRole('button',{name:'Stocks & DLC'}).click();
  const details=page.getByRole('button',{name:'Voir lots',exact:true});
  if(await details.count()<1)throw Error('Bouton de lots absent du stock');
  await details.first().click();
  const batch=page.getByRole('dialog',{name:/Lots & DLC/});
  await batch.waitFor();
  if(await batch.getByRole('button',{name:'Consommer'}).count())throw Error('Inactive batch consumption button is still displayed');
  if(await batch.getByRole('button',{name:'Nouveau Lot'}).count())throw Error('Nonfunctional create-lot button is still displayed');
  await batch.getByRole('button',{name:'Fermer le formulaire'}).click();
  await batch.waitFor({state:'detached'});
  const width=await page.evaluate(()=>({scroll:document.documentElement.scrollWidth,viewport:innerWidth}));
  if(width.scroll>width.viewport)throw Error('horizontal overflow '+JSON.stringify(width));
  if(errors.length)throw Error('JS errors '+errors.join(';'));
  console.log(config.name,'OCR wizard + size guard + close PASS',width);
  await page.close();
 }
 await browser.close();
})().catch(err=>{console.error('E2E FAILED',err);process.exit(1)});
