/** Optional live Chrome smoke test for the isolated /demo route.
 * Setup: npm install --no-save playwright-core (inside frontend)
 * Run: RESTOP_PREVIEW_URL=http://127.0.0.1:4173 node e2e/demo-smoke.cjs
 * Works on Mac with installed Google Chrome or CHROME_EXECUTABLE.
 * Requires built app served with SPA fallback. Never uses real restaurant data.
 */
const {chromium}=require('playwright-core');
const base=(process.env.RESTOP_PREVIEW_URL||'http://127.0.0.1:4173').replace(/\/$/,'');
const executablePath=process.env.CHROME_EXECUTABLE||'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath,args:['--no-sandbox']});
 const failures=[];
 for(const device of [{name:'desktop',width:1440,height:900},{name:'mobile',width:390,height:844}]){
  const page=await browser.newPage({viewport:{width:device.width,height:device.height}});
  const requests=[];const errors=[];
  page.on('request',r=>{if(r.url().includes('/api/'))requests.push(r.url())});
  page.on('pageerror',e=>errors.push(e.message));
  await page.goto(`${base}/`,{waitUntil:'networkidle'});
  await page.getByRole('button',{name:/Découvrir la démo/i}).first().click();
  await page.getByRole('heading',{name:/La gestion commence/i}).waitFor();
  await page.getByRole('button',{name:/Tester le wizard OCR/i}).click();
  const dialog=page.getByRole('dialog',{name:'Valider une facture fournisseur'});
  await dialog.waitFor();
  const box=await dialog.boundingBox();
  if(!box || box.y!==0 || box.height>device.height+1)failures.push(device.name+': overlay not in viewport');
  await page.getByRole('button',{name:/Continuer/i}).click();
  await page.getByText(/Étape 2\/3/).waitFor();
  await page.getByRole('button',{name:/Continuer/i}).click();
  await page.getByText(/Étape 3\/3/).waitFor();
  await page.getByRole('checkbox').check();
  await page.getByRole('button',{name:/Terminer la simulation/i}).click();
  await page.getByText(/Simulation terminée/i).waitFor();
  await page.getByRole('button',{name:/Fermer et voir les stocks/i}).click();
  const dimensions=await page.evaluate(()=>({w:document.documentElement.scrollWidth,v:innerWidth}));
  if(dimensions.w>dimensions.v)failures.push(device.name+': horizontal overflow');
  if(requests.length||errors.length)failures.push(`${device.name}: ${requests.length} API requests, ${errors.length} JS errors`);
  console.log(`${device.name}: wizard, navigation, security and viewport OK`);
  await page.close();
 }
 await browser.close();
 if(failures.length){console.error(failures.join('\n'));process.exit(1)}
})().catch(err=>{console.error(err);process.exit(1)});
