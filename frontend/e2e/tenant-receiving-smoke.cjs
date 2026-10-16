/** Run only against a compiled pilot build with REACT_APP_ENABLE_TENANT_V2=true.
 * Browser requests to /api are fully intercepted: no backend or customer writes.
 * NODE_PATH=/tmp/restop-receipt-browser/node_modules node frontend/e2e/tenant-receiving-smoke.cjs
 */
const {chromium}=require('playwright-core');
const url=(process.env.RESTOP_PREVIEW_URL||'http://127.0.0.1:4173').replace(/\/$/,'');
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:process.env.CHROME_EXECUTABLE||'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',args:['--no-sandbox']});
 for(const viewport of [{name:'desktop',width:1440,height:900},{name:'mobile',width:390,height:844}]){
  const page=await browser.newPage({viewport});let writes=0;const errors=[];
  page.on('pageerror',e=>errors.push(e.message));
  await page.addInitScript(()=>localStorage.setItem('user_session',JSON.stringify({session_id:'QA-fake-session',user:{id:'qa',role:'patron',full_name:'Camille',username:'qa'}})));
  const order={id:'order-demo-1234567',supplier_id:'supplier-demo-12345',status:'approved',estimated_total_cents:600,
    lines:[{product_id:'product-demo-001',quantity_milliunits:3000,unit_price_cents:200,unit:'kg'}]};
  const product={id:'product-demo-001',name:'Tomates de Provence',unit:'kg',purchase_price_cents:200};
  const doc={id:'document-demo-123',status:'needs_review',extension:'pdf',size_bytes:140,sha256:'a'.repeat(64),extraction_engine:'pdf_embedded_text'};
  let reviews=0,uploads=0;
  await page.route(/\/api\//,async route=>{
   const path=new URL(route.request().url()).pathname.replace(/^\/api\//,'');
   const method=route.request().method();
   let data=[];
   if(path==='auth/session')data={valid:true,user:{id:'qa',role:'patron',full_name:'Camille',username:'qa'}};
   else if(path==='tenant/purchase-orders')data=[order];
   else if(path==='tenant/products')data=[product];
   else if(path==='tenant/invoices/upload'){uploads++;data=doc;}
   else if(path==='tenant/invoices/document-demo-123')data={...doc,extracted_text:'FACTURE N FAC-ABC-001\nTomates de Provence',suggestions:{invoice_reference:'FAC-ABC-001',potential_product_matches:[{product_id:product.id,name:product.name}]}};
   else if(path==='tenant/invoices/document-demo-123/review'){reviews++;data={...doc,status:'reviewed'};}
   else if(path.endsWith('/receipts/preview'))data={issues:[],can_confirm:true,invoice_total_cents:600};
   else if(path.endsWith('/receipts/confirm')){writes++;const submitted=route.request().postDataJSON();if(submitted.invoice_document_id!==doc.id)throw Error('Document not linked to receipt');data={id:'receipt-demo-001',order_status_after:'received',replayed:false,invoice_document_id:doc.id}}
   else if(path==='dashboard/stats')data={};
   else if(path==='dashboard/missing-data-alerts')data={alerts:[]};
   else if(path==='analytics/alerts')data={expiring_products:[],low_stock_items:[],price_anomalies:[]};
   await route.fulfill({status:200,contentType:'application/json',body:JSON.stringify(data),headers:{'access-control-allow-origin':'*'}});
  });
  await page.goto(url+'/app');
  await page.getByText(/Bonjour Camille/).first().waitFor({timeout:15000});
  if(viewport.name==='mobile')await page.getByRole('button',{name:/Ouvrir le menu/i}).click();
  await page.getByRole('navigation',{name:'Navigation principale'}).getByRole('button',{name:'Stocks'}).click();
  await page.getByRole('group',{name:'Rubriques des stocks'}).getByRole('button',{name:/Réceptions.*pilote/}).click();
  await page.getByText('Réception fournisseur',{exact:true}).waitFor();
  await page.getByRole('button',{name:/Prête à recevoir/}).first().click();
  await page.getByText('Tomates de Provence').waitFor();
  const inputs=page.locator('.rt-receiving-fields input');
  await inputs.nth(0).fill('BL-ABC-001');
  await inputs.nth(1).fill('FAC-ABC-001');
  await page.getByLabel('Document de facture').setInputFiles({name:'fac-demo.pdf',mimeType:'application/pdf',buffer:Buffer.from('%PDF-1.4 DEMO ONLY')});
  await page.getByRole('button',{name:'Importer et analyser'}).click();
  await page.getByText('FACTURE N FAC-ABC-001').waitFor();
  await page.getByRole('button',{name:'Vérifier les écarts'}).click();
  await page.getByRole('alert').getByText(/Vérifiez les informations de la facture importée/).waitFor();
  const note=page.getByPlaceholder(/J’ai comparé le PDF/);
  await note.fill('Facture, quantités et prix vérifiés sur le document original.');
  await page.getByRole('button',{name:'Valider les données lues sur la facture'}).click();
  await page.getByText('Document vérifié.').waitFor();
  if(process.env.RESTOP_SCREENSHOT_DIR)await page.screenshot({path:`${process.env.RESTOP_SCREENSHOT_DIR}/invoice-review-${viewport.name}.png`,fullPage:false});
  await page.getByRole('button',{name:'Vérifier les écarts'}).click();
  await page.getByText('Montant facturé sur les lignes reçues').waitFor();
  if(writes!==0)throw Error('Confirm called before approval');
  await page.getByRole('button',{name:/Continuer vers validation/}).click();
  await page.getByText('Dernière vérification avant écriture en stock').waitFor();
  if(writes!==0)throw Error('Confirm called before last manual approval');
  await page.getByRole('button',{name:/Oui, confirmer la réception et le stock/}).click();
  await page.getByText('Réception enregistrée').waitFor();
  if(writes!==1||uploads!==1||reviews!==1)throw Error('Expected exactly one upload, review and confirm '+JSON.stringify({writes,uploads,reviews}));
  const dim=await page.evaluate(()=>({scroll:document.documentElement.scrollWidth,viewport:innerWidth}));
  if(dim.scroll>dim.viewport)throw Error('Horizontal overflow '+JSON.stringify(dim));
  if(errors.length)throw Error('Browser JS errors: '+errors.join('; '));
  if(process.env.RESTOP_SCREENSHOT_DIR)await page.screenshot({path:`${process.env.RESTOP_SCREENSHOT_DIR}/receiving-${viewport.name}.png`,fullPage:false});
  console.log(viewport.name,'PASS — selection, preview, explicit commit, no JS error, no page overflow',dim);
  await page.close();
 }
 await browser.close();
})().catch(e=>{console.error(e);process.exit(1)});
