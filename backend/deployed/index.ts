
import { createClient } from "npm:@supabase/supabase-js@2.117.2";
import * as XLSX from "npm:xlsx@0.18.5";

const SUPABASE_URL = Deno.env.get("SUPABASE_URL")!;
const ANON_KEY = Deno.env.get("SUPABASE_ANON_KEY")!;
const SERVICE_KEY = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;

const anon = createClient(SUPABASE_URL, ANON_KEY, { auth: { persistSession: false, autoRefreshToken: false } });
const service = createClient(SUPABASE_URL, SERVICE_KEY, { auth: { persistSession: false, autoRefreshToken: false } });
const DEMO_TOKEN = "restop-demo-public-v1";
const DEMO_RID = "10000000-0000-4000-8000-000000000001";
const demoUser = {
  id: "demo-restop",
  username: "commercial_demo",
  email: "demo@digigroupe.com",
  role: "patron",
  full_name: "Démo Commerciale",
  is_active: true
};

const cors = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
  "Access-Control-Allow-Methods": "GET,POST,PUT,PATCH,DELETE,OPTIONS",
};

function json(data: unknown, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { ...cors, "Content-Type": "application/json" }
  });
}
function fail(detail: string, status = 400) {
  return json({ detail, message: detail }, status);
}
function batchStatus(expiryDate: string | null) {
  if(!expiryDate)return 'good';
  const expiry=String(expiryDate).slice(0,10),today=new Intl.DateTimeFormat('en-CA',{timeZone:'Europe/Paris',year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date());
  const week=new Date(new Date(today+'T12:00:00Z').getTime()+7*86400000).toISOString().slice(0,10);
  return expiry<today?'expired':expiry<=week?'critical':'good';
}
function cleanPath(req: Request) {
  let p = new URL(req.url).pathname;
  p = p.replace(/^\/functions\/v1\/restop-api/, "");
  p = p.replace(/^\/restop-api/, "");
  p = p.replace(/^\/api\/api\//, "/api/");
  return p || "/";
}
async function body(req: Request) {
  const ct = req.headers.get("content-type") || "";
  if (ct.includes("application/json")) return await req.json().catch(() => ({}));
  return {};
}
async function userFromToken(token: string) {
  const r = await anon.auth.getUser(token);
  return r.error ? null : r.data.user;
}
async function ctx(req: Request) {
  const h = req.headers.get("authorization") || "";
  if (!h.startsWith("Bearer ")) return null;
  const token = h.slice(7).trim();
  if (token === DEMO_TOKEN) {
    return {
      user: { id: null },
      profile: { ...demoUser, restaurant_id: DEMO_RID },
      restaurant_id: DEMO_RID,
      demo: true
    };
  }
  const user = await userFromToken(token);
  if (!user) return null;
  const q = await service.from("restop_profiles").select("*").eq("user_id", user.id).maybeSingle();
  if (!q.data || !q.data.is_active) return null;
  return { user, profile: q.data, restaurant_id: q.data.restaurant_id, demo: false };
}
function legacyUser(p: any) {
  return {
    id: p.user_id,
    username: p.username || p.email || "",
    email: p.email || "",
    role: p.role,
    full_name: p.full_name,
    is_active: p.is_active,
    created_at: p.created_at,
    last_login: p.last_login
  };
}
function legacySupplier(s: any) {
  return {
    id: s.id,
    nom: s.name,
    contact: s.contact,
    email: s.email,
    telephone: s.phone,
    adresse: s.address,
    couleur: s.color,
    logo: s.logo_url,
    categorie: s.categories && s.categories.length ? s.categories[0] : "frais",
    categories: s.categories || ["frais"],
    delivery_rules: {order_days:[],delivery_days:[],order_deadline_hour:11,delivery_delay_days:1,delivery_time:"12:00",special_rules:"",...(s.delivery_rules || {})},
    created_at: s.created_at
  };
}
function legacyProduct(p: any, supplierName: string | null = null) {
  return {
    id: p.id,
    nom: p.name,
    description: p.description,
    categorie: p.category,
    unite: p.unit,
    prix_achat: Number(p.unit_price || 0),
    reference_price: Number(p.reference_price ?? p.unit_price ?? 0),
    main_supplier_id: p.main_supplier_id || p.supplier_id,
    secondary_supplier_ids: p.secondary_supplier_ids || [],
    fournisseur_id: p.supplier_id || p.main_supplier_id,
    fournisseur_nom: supplierName,
    created_at: p.created_at
  };
}
async function supplierNames(rid: string) {
  const q = await service.from("restop_suppliers").select("id,name").eq("restaurant_id", rid);
  const map: Record<string,string> = {};
  for (const s of q.data || []) map[s.id] = s.name;
  return map;
}
async function listRecipes(rid: string) {
  const rq = await service.from("restop_recipes").select("*").eq("restaurant_id", rid).order("created_at");
  if (rq.error) throw rq.error;
  const ids = (rq.data || []).map((r: any) => r.id);
  let ing: any[] = [];
  if (ids.length) {
    const iq = await service.from("restop_recipe_ingredients").select("*").in("recipe_id", ids);
    if (iq.error) throw iq.error;
    ing = iq.data || [];
  }
  return (rq.data || []).map((r: any) => ({
    id: r.id,
    nom: r.name,
    description: r.description,
    categorie: r.category,
    portions: r.portions,
    temps_preparation: r.preparation_time,
    instructions: r.instructions,
    prix_vente: r.selling_price,
    coefficient_prevu: r.planned_coefficient,
    coefficient_reel: r.actual_coefficient,
    cout_matiere: r.material_cost,
    ingredients: ing.filter((i: any) => i.recipe_id === r.id).map((i: any) => ({
      ingredient_id: i.product_id,
      ingredient_type: "produit",
      ingredient_nom: i.product_name,
      produit_id: i.product_id,
      produit_nom: i.product_name,
      quantite: Number(i.quantity || 0),
      unite: i.unit || "unité"
    })),
    created_at: r.created_at
  }));
}


function restopDocumentShape(d:any, imageBase64:any=null){
  const name=String(d.file_name||"");
  const ext=name.toLowerCase().split(".").pop()||"";
  const fileType=ext==="pdf"?"pdf":(["png","jpg","jpeg","webp","gif"].includes(ext)?"image":ext||"file");
  return {
    id:d.id,
    type_document:d.document_type,
    nom_fichier:d.file_name,
    statut:d.status,
    donnees_parsees:d.ocr_data||{},
    donnees_extraites:d.ocr_data||{},
    date_upload:d.created_at,
    date_traitement:d.updated_at,
    file_type:fileType,
    image_base64:imageBase64,
    texte_extrait:d.ocr_data?.raw_text||"",
    supplier_id:d.supplier_id,
    document_date:d.document_date,
    total_amount:d.total_amount
  };
}
function normText(v:any){
  return String(v||"").normalize("NFD").replace(/[\u0300-\u036f]/g,"").toLowerCase().replace(/[^a-z0-9]+/g," ").trim();
}
function toIsoDate(v:any){
  if(!v)return new Date().toISOString().slice(0,10);
  const s=String(v);
  const m=s.match(/^(\d{2})\/(\d{2})\/(\d{4})$/);
  if(m)return m[3]+"-"+m[2]+"-"+m[1];
  return s.slice(0,10);
}
function demoOcrPayload(documentType:string){
  const today=new Date().toISOString().slice(0,10);
  if(documentType==="z_report"){
    return {
      report_date:today,service:"Soir",grand_total_sales:2876.30,total_ca:2876.30,nombre_couverts:74,
      items_by_category:{
        "Entrées":[{name:"Burrata & tomates de Provence",quantity_sold:14,unit_price:16}],
        "Plats":[{name:"Moules marinières",quantity_sold:19,unit_price:24},{name:"Entrecôte, frites maison",quantity_sold:17,unit_price:31},{name:"Linguine aux palourdes",quantity_sold:9,unit_price:26}],
        "Desserts":[{name:"Dessert du jour",quantity_sold:11,unit_price:11}],
        "Bar":[{name:"Eau pétillante",quantity_sold:22,unit_price:5.5}]
      },
      productions_detectees:[
        {nom:"Moules marinières",quantite:19,family:"Plats"},
        {nom:"Entrecôte, frites maison",quantite:17,family:"Plats"},
        {nom:"Burrata & tomates de Provence",quantite:14,family:"Entrées"}
      ],
      demo_simulation:true
    };
  }
  if(documentType==="mercuriale"){
    return {
      fournisseur:"Castelli Primeur",date:today,
      produits_detectes:[
        {nom:"Tomate cœur de bœuf",categorie:"Primeur",unite:"kg",prix_achat:4.20},
        {nom:"Persil plat",categorie:"Primeur",unite:"botte",prix_achat:1.20},
        {nom:"Pommes de terre Agria",categorie:"Primeur",unite:"kg",prix_achat:1.70},
        {nom:"Citron jaune",categorie:"Primeur",unite:"kg",prix_achat:2.90},
        {nom:"Roquette",categorie:"Primeur",unite:"kg",prix_achat:7.20}
      ],
      demo_simulation:true
    };
  }
  return {
    fournisseur:"RM Marée",date:today,numero_facture:"DEMO-RM-"+today.replaceAll("-",""),total_ht:375.09,total_ttc:412.60,
    produits:[
      {nom:"Moules de bouchot",quantite:30,unite:"kg",prix_unitaire:5.80,prix_total:174.00,dlc:new Date(Date.now()+3*86400000).toISOString().slice(0,10)},
      {nom:"Filet de loup",quantite:7,unite:"kg",prix_unitaire:22.00,prix_total:154.00,dlc:new Date(Date.now()+2*86400000).toISOString().slice(0,10)},
      {nom:"Palourdes",quantite:8.63,unite:"kg",prix_unitaire:9.80,prix_total:84.60,dlc:new Date(Date.now()+2*86400000).toISOString().slice(0,10)}
    ],
    demo_simulation:true
  };
}
async function invoiceAnalysis(rid:string,d:any,aiPowered=false){
  const data=d.ocr_data||{};
  const [sq,pq]=await Promise.all([
    service.from("restop_suppliers").select("id,name").eq("restaurant_id",rid),
    service.from("restop_products").select("id,name,unit").eq("restaurant_id",rid).eq("active",true)
  ]);
  const supplierRaw=String(data.fournisseur||"Fournisseur inconnu");
  const sn=normText(supplierRaw);
  const sm=(sq.data||[]).find((s:any)=>normText(s.name)===sn)||(sq.data||[]).find((s:any)=>normText(s.name).includes(sn)||sn.includes(normText(s.name)));
  const items=(Array.isArray(data.produits)?data.produits:[]).map((x:any)=>{
    const n=normText(x.nom);
    const pm=(pq.data||[]).find((p:any)=>normText(p.name)===n)||(pq.data||[]).find((p:any)=>normText(p.name).includes(n)||n.includes(normText(p.name)));
    const qty=Number(x.quantite||0), price=Number(x.prix_unitaire||0);
    return {
      ocr_name:x.nom||"",
      ocr_qty:qty,
      ocr_unit:x.unite||pm?.unit||"kg",
      ocr_price:price,
      ocr_total:Number(x.prix_total??qty*price),
      product_id:pm?.id||null,
      product_name:pm?.name||null,
      confidence:pm?0.98:0.35,
      status:pm?"matched":"new",
      selected_product_id:pm?.id||null,
      final_name:pm?.name||x.nom||"",
      final_qty:qty,
      final_unit:x.unite||pm?.unit||"kg",
      dlc:x.dlc||null,
      batch_number:x.batch_number||null
    };
  });
  return {
    document_id:d.id,
    supplier_id:sm?.id||null,
    supplier_name:sm?.name||supplierRaw,
    is_new_supplier:!sm,
    facture_date:toIsoDate(data.date||d.document_date),
    numero_facture:data.numero_facture||"N/A",
    items,
    ai_powered:aiPowered,
    confiance_globale:aiPowered?0.96:0.89,
    demo_simulation:!!data.demo_simulation
  };
}
async function blobToDataUri(blob:Blob,fileName:string){
  const bytes=new Uint8Array(await blob.arrayBuffer());
  let binary="";
  for(let i=0;i<bytes.length;i+=32768) binary+=String.fromCharCode(...bytes.subarray(i,Math.min(i+32768,bytes.length)));
  const lower=fileName.toLowerCase();
  const mime=lower.endsWith(".pdf")?"application/pdf":lower.endsWith(".png")?"image/png":lower.endsWith(".webp")?"image/webp":"image/jpeg";
  return "data:"+mime+";base64,"+btoa(binary);
}

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: cors });
  const path = cleanPath(req);

  try {
    if (path === "/" || path === "/health" || path === "/api/health") {
      return json({ status: "healthy", service: "restop-api", backend: "supabase" });
    }

    if (path === "/api/auth/demo" && (req.method === "GET" || req.method === "POST")) {
      return json({ success: true, session_id: DEMO_TOKEN, user: demoUser, demo: true });
    }

    if (path === "/api/auth/register" && req.method === "POST") {
      const b: any = await body(req);
      const username = String(b.username || "").trim();
      const email = String(b.email || "").trim().toLowerCase();
      const password = String(b.password || "");
      const fullName = String(b.full_name || username).trim();
      const restaurantName = String(b.restaurant_name || "Mon restaurant").trim();
      if (!username || !email || password.length < 8) return fail("Nom d'utilisateur, email et mot de passe de 8 caractères minimum requis", 422);

      const ex = await service.from("restop_profiles").select("user_id").ilike("username", username).maybeSingle();
      if (ex.data) return fail("Ce nom d'utilisateur existe déjà", 409);

      const cr = await service.auth.admin.createUser({
        email,
        password,
        email_confirm: true,
        user_metadata: { username, full_name: fullName, app: "restop" }
      });
      if (cr.error || !cr.data.user) return fail(cr.error?.message || "Création impossible", 400);
      const uid = cr.data.user.id;

      const rr = await service.from("restop_restaurants")
        .insert({ owner_user_id: uid, name: restaurantName })
        .select("*").single();
      if (rr.error) {
        await service.auth.admin.deleteUser(uid);
        return fail(rr.error.message, 400);
      }
      const pr = await service.from("restop_profiles").insert({
        user_id: uid,
        restaurant_id: rr.data.id,
        username,
        email,
        full_name: fullName,
        role: "patron",
        is_active: true
      }).select("*").single();
      if (pr.error) {await service.from("restop_restaurants").delete().eq("id",rr.data.id);await service.auth.admin.deleteUser(uid);return fail(pr.error.message,400);}

      const lg = await anon.auth.signInWithPassword({ email, password });
      if (lg.error || !lg.data.session) return fail("Compte créé mais connexion impossible", 400);
      return json({ success: true, session_id: lg.data.session.access_token, user: legacyUser(pr.data) });
    }

    if (path === "/api/auth/login" && req.method === "POST") {
      const b: any = await body(req);
      const identifier = String(b.username || b.email || "").trim();
      const password = String(b.password || "");
      if (!identifier || !password) return fail("Identifiants requis", 422);

      let q = service.from("restop_profiles").select("*");
      q = identifier.includes("@") ? q.ilike("email", identifier) : q.ilike("username", identifier);
      const pr = await q.maybeSingle();
      if (!pr.data || !pr.data.email || !pr.data.is_active) return fail("Identifiants incorrects", 401);

      const lg = await anon.auth.signInWithPassword({ email: pr.data.email, password });
      if (lg.error || !lg.data.session) return fail("Identifiants incorrects", 401);
      const now = new Date().toISOString();
      await service.from("restop_profiles").update({ last_login: now }).eq("user_id", pr.data.user_id);
      pr.data.last_login = now;
      return json({ success: true, session_id: lg.data.session.access_token, user: legacyUser(pr.data) });
    }

    if (path.startsWith("/api/auth/session/") && req.method === "GET") {
      const token = decodeURIComponent(path.substring("/api/auth/session/".length));
      if (token === DEMO_TOKEN) return json({ success: true, valid: true, user: demoUser, demo: true });
      const u = await userFromToken(token);
      if (!u) return fail("Session invalide", 401);
      const pr = await service.from("restop_profiles").select("*").eq("user_id", u.id).maybeSingle();
      if (!pr.data) return fail("Profil introuvable", 404);
      return json({ success: true, valid: true, user: legacyUser(pr.data) });
    }


    if (path === "/api/auth/session" && req.method === "GET") {
      const h = req.headers.get("authorization") || "";
      if (!h.startsWith("Bearer ")) return fail("Session invalide", 401);
      const sessionToken = h.slice(7).trim();
      if (sessionToken === DEMO_TOKEN) return json({ success: true, valid: true, user: demoUser, demo: true });
      const u = await userFromToken(sessionToken);
      if (!u) return fail("Session invalide", 401);
      const pr = await service.from("restop_profiles").select("*").eq("user_id", u.id).maybeSingle();
      if (!pr.data) return fail("Profil introuvable", 404);
      return json({ success: true, valid: true, user: legacyUser(pr.data) });
    }

    if (path === "/api/auth/logout" && req.method === "POST") return json({ success: true });

    const c = await ctx(req);
    if (!c) return fail("Authentification requise", 401);
    const rid = c.restaurant_id;
    const role = c.profile.role;
    if (path.startsWith('/api/admin/') && !['patron','super_admin'].includes(role)) return fail('Accès réservé à la direction',403);
    const managers=['patron','super_admin','gerant','chef_cuisine'];
    const stockAction=['/api/mouvements','/api/stock/advanced-adjustment'].includes(path) && req.method==='POST';
    const staffStock=['employe_cuisine','barman'].includes(role) && stockAction;
    const cashierAction=role==='caissier' && req.method==='POST' && (path==='/api/ocr/upload-document' || /^\/api\/ocr\/(process-z-report|analyze-ticket-z-ai)\//.test(path) || path==='/api/missions');
    const barOrder=role==='barman' && path==='/api/orders' && req.method==='POST';
    if (!['GET','OPTIONS'].includes(req.method) && !managers.includes(role) && !staffStock && !cashierAction && !barOrder && !path.startsWith('/api/missions/') && !path.startsWith('/api/notifications/')) return fail('Action non autorisée pour ce rôle',403);
    if(role==='barman' && stockAction) {
      const b:any=await body(req.clone()),id=b.produit_id || b.target_id;
      const product=await service.from('restop_products').select('category').eq('restaurant_id',rid).eq('id',id).maybeSingle();if(product.error)throw product.error;
      if(!product.data || !/bar|boisson|vin|alcool|soft/i.test(product.data.category || ''))return fail('Le barman peut ajuster uniquement les produits du bar',403);
    }

    if (path === '/api/unites' && req.method === 'GET') return json({unites:[
      {code:'kg',label:'Kilogramme',type:'poids'},{code:'g',label:'Gramme',type:'poids'},
      {code:'L',label:'Litre',type:'volume'},{code:'mL',label:'Millilitre',type:'volume'},
      {code:'cl',label:'Centilitre',type:'volume'},{code:'pièce',label:'Pièce',type:'unite'},
      {code:'portion',label:'Portion',type:'unite'},{code:'botte',label:'Botte',type:'unite'},{code:'colis',label:'Colis',type:'unite'}]});
    if (path === '/api/formes-decoupe' && req.method === 'GET') return json({predefined:['Entier','Émincé','Dés','Julienne','Brunoise','Tranches','Haché'],custom:[]});
    if (path === '/api/produits/by-categories' && req.method === 'GET') {
      const q=await service.from('restop_products').select('*').eq('restaurant_id',rid).eq('active',true);
      if(q.error)throw q.error;
      const names=await supplierNames(rid),categories:any={};
      for(const p of q.data || []){const key=p.category || 'Non classé';categories[key] ||= {products:[],count:0};categories[key].products.push(legacyProduct(p,names[p.supplier_id]));categories[key].count++;}
      return json({categories,total_categories:Object.keys(categories).length,total_products:(q.data || []).length});
    }
    if (path === '/api/dashboard/missing-data-alerts' && req.method === 'GET') {
      const pq=await service.from('restop_products').select('*').eq('restaurant_id',rid).eq('active',true);if(pq.error)throw pq.error;
      const alerts:any[]=[];
      for(const p of pq.data || []) if(!p.unit || !p.category || !p.supplier_id || Number(p.unit_price)<=0) alerts.push({id:p.id,type:'produit',nom:p.name,message:'Vérifier unité, catégorie, fournisseur et prix'});
      return json({alerts});
    }
    const batchMatch=path.match(/^\/api\/stock\/batch-info\/([0-9a-f-]+)$/i);
    if(batchMatch && req.method === 'GET') {
      const pq=await service.from('restop_products').select('*').eq('restaurant_id',rid).eq('id',batchMatch[1]).maybeSingle();if(pq.error)throw pq.error;if(!pq.data)return fail('Produit introuvable',404);
      const bq=await service.from('restop_product_batches').select('*').eq('restaurant_id',rid).eq('product_id',batchMatch[1]).eq('is_consumed',false);if(bq.error)throw bq.error;
      const now=Date.now(),batches=(bq.data || []).map((b:any)=>({...b,quantity:Number(b.quantity),status:batchStatus(b.expiry_date)}));
      return json({product_id:pq.data.id,product_name:pq.data.name,total_stock:Number(pq.data.current_stock),batches,expired_batches:batches.filter((b:any)=>b.status==='expired').length,critical_batches:batches.filter((b:any)=>b.status==='critical').length});
    }


    if (path === "/api/fournisseurs" && req.method === "GET") {
      const q = await service.from("restop_suppliers").select("*").eq("restaurant_id", rid).order("name");
      if (q.error) throw q.error;
      return json((q.data || []).map(legacySupplier));
    }
    if (path === "/api/fournisseurs" && req.method === "POST") {
      const b: any = await body(req);
      const q = await service.from("restop_suppliers").insert({
        restaurant_id: rid,
        name: b.nom,
        contact: b.contact || null,
        email: b.email || null,
        phone: b.telephone || null,
        address: b.adresse || null,
        color: b.couleur || "#3B82F6",
        logo_url: b.logo || null,
        categories: b.categories || [b.categorie || "frais"],
        delivery_rules: b.delivery_rules || {}
      }).select("*").single();
      if (q.error) return fail(q.error.message, 400);
      return json(legacySupplier(q.data));
    }

    let m = path.match(/^\/api\/fournisseurs\/([0-9a-f-]+)$/i);
    if (m && req.method === "PUT") {
      const b: any = await body(req);
      const patch: any = {};
      if (b.nom !== undefined) patch.name = b.nom;
      if (b.contact !== undefined) patch.contact = b.contact;
      if (b.email !== undefined) patch.email = b.email;
      if (b.telephone !== undefined) patch.phone = b.telephone;
      if (b.adresse !== undefined) patch.address = b.adresse;
      if (b.couleur !== undefined) patch.color = b.couleur;
      if (b.logo !== undefined) patch.logo_url = b.logo;
      if (b.categories !== undefined || b.categorie !== undefined) patch.categories = b.categories || [b.categorie];
      const q = await service.from("restop_suppliers").update(patch).eq("restaurant_id", rid).eq("id", m[1]).select("*").single();
      if (q.error) return fail(q.error.message, 400);
      return json(legacySupplier(q.data));
    }
    if (m && req.method === "DELETE") {
      const q = await service.from("restop_suppliers").delete().eq("restaurant_id", rid).eq("id", m[1]);
      if (q.error) return fail(q.error.message, 400);
      return json({ success: true });
    }

    if (path === "/api/produits" && req.method === "GET") {
      const q = await service.from("restop_products").select("*").eq("restaurant_id", rid).eq("active", true).order("name");
      if (q.error) throw q.error;
      const names = await supplierNames(rid);
      return json((q.data || []).map((p: any) => legacyProduct(p, names[p.supplier_id || p.main_supplier_id] || null)));
    }
    if (path === "/api/produits" && req.method === "POST") {
      const b: any = await body(req);
      const supplier = b.main_supplier_id || b.fournisseur_id || null;
      const price = Number(b.reference_price ?? b.prix_achat ?? 0);
      const q = await service.from("restop_products").insert({
        restaurant_id: rid,
        name: b.nom,
        description: b.description || null,
        category: b.categorie || null,
        unit: b.unite || "unité",
        unit_price: price,
        reference_price: price,
        supplier_id: supplier,
        main_supplier_id: supplier,
        secondary_supplier_ids: b.secondary_supplier_ids || [],
        current_stock: Number(b.quantite_actuelle || 0),
        min_stock: Number(b.quantite_min || 0),
        target_stock: b.quantite_max ?? null
      }).select("*").single();
      if (q.error) return fail(q.error.message, 400);
      const names = await supplierNames(rid);
      return json(legacyProduct(q.data, names[q.data.supplier_id || q.data.main_supplier_id] || null));
    }

    m = path.match(/^\/api\/produits\/([0-9a-f-]+)$/i);
    if (m && req.method === "GET") {
      const q = await service.from("restop_products").select("*").eq("restaurant_id", rid).eq("id", m[1]).maybeSingle();
      if (q.error) return fail(q.error.message,400);
      if (!q.data || !q.data.active) return fail("Produit introuvable",404);
      const names = await supplierNames(rid);
      return json(legacyProduct(q.data, names[q.data.supplier_id || q.data.main_supplier_id] || null));
    }
    if (m && req.method === "PUT") {
      const b: any = await body(req);
      const patch: any = {};
      if (b.nom !== undefined) patch.name = b.nom;
      if (b.description !== undefined) patch.description = b.description;
      if (b.categorie !== undefined) patch.category = b.categorie;
      if (b.unite !== undefined) patch.unit = b.unite;
      if (b.reference_price !== undefined || b.prix_achat !== undefined) {
        patch.reference_price = Number(b.reference_price ?? b.prix_achat);
        patch.unit_price = Number(b.reference_price ?? b.prix_achat);
      }
      if (b.main_supplier_id !== undefined || b.fournisseur_id !== undefined) {
        patch.main_supplier_id = b.main_supplier_id ?? b.fournisseur_id;
        patch.supplier_id = b.main_supplier_id ?? b.fournisseur_id;
      }
      if (b.secondary_supplier_ids !== undefined) patch.secondary_supplier_ids = b.secondary_supplier_ids;
      const q = await service.from("restop_products").update(patch).eq("restaurant_id", rid).eq("id", m[1]).select("*").single();
      if (q.error) return fail(q.error.message, 400);
      const names = await supplierNames(rid);
      return json(legacyProduct(q.data, names[q.data.supplier_id || q.data.main_supplier_id] || null));
    }
    if (m && req.method === "DELETE") {
      const q = await service.from("restop_products").update({ active: false }).eq("restaurant_id", rid).eq("id", m[1]);
      if (q.error) return fail(q.error.message, 400);
      return json({ success: true });
    }

    if (path === "/api/stocks" && req.method === "GET") {
      const q = await service.from("restop_products")
        .select("id,name,current_stock,min_stock,target_stock,updated_at")
        .eq("restaurant_id", rid).eq("active", true).order("name");
      if (q.error) throw q.error;
      return json((q.data || []).map((p: any) => ({
        id: p.id,
        produit_id: p.id,
        produit_nom: p.name,
        quantite_actuelle: Number(p.current_stock || 0),
        quantite_min: Number(p.min_stock || 0),
        quantite_max: p.target_stock,
        derniere_maj: p.updated_at
      })));
    }

    if (path === "/api/stocks/critiques/produits" && req.method === "GET") {
      const q = await service.from("restop_products").select("*").eq("restaurant_id", rid).eq("active", true);
      const rows = (q.data || []).filter((p: any) => Number(p.current_stock || 0) <= Number(p.min_stock || 0));
      return json(rows.map((p: any) => ({
        produit_id: p.id,
        produit_nom: p.name,
        quantite_actuelle: Number(p.current_stock || 0),
        quantite_min: Number(p.min_stock || 0)
      })));
    }

    if (path === "/api/mouvements" && req.method === "GET") {
      const q = await service.from("restop_stock_movements")
        .select("*,restop_products(name)")
        .eq("restaurant_id", rid).order("created_at", { ascending: false });
      if (q.error) throw q.error;
      return json((q.data || []).map((x: any) => ({
        id: x.id,
        produit_id: x.product_id,
        produit_nom: x.restop_products?.name || null,
        type: x.movement_type === "in" ? "entree" : x.movement_type === "out" ? "sortie" : "ajustement",
        quantite: Number(x.quantity || 0),
        date: x.created_at,
        commentaire: x.reason
      })));
    }

    if (path === "/api/mouvements" && req.method === "POST") {
      const b: any = await body(req);
      if(!['entree','sortie','ajustement'].includes(b.type) || !Number.isFinite(Number(b.quantite)) || Number(b.quantite)<0 || (b.type!=='ajustement' && Number(b.quantite)===0))return fail('Mouvement ou quantité invalide');
      const result=await service.rpc('restop_record_movement',{p_restaurant_id:rid,p_user_id:c.user.id,p_payload:b});
      if(result.error)return fail(result.error.message,400);
      return json(result.data);
    }

    if (path === "/api/recettes" && req.method === "GET") return json(await listRecipes(rid));

    const recipeEdit=path.match(/^\/api\/recettes\/([0-9a-f-]+)$/i);
    if ((path === '/api/recettes' && req.method === 'POST') || (recipeEdit && req.method === 'PUT')) {
      const b:any=await body(req);
      if(!String(b.nom || '').trim() || !Number.isInteger(Number(b.portions)) || Number(b.portions)<=0) return fail('Nom et nombre de portions positif requis');
      const ingredients=Array.isArray(b.ingredients)?b.ingredients:[];
      if(ingredients.some((i:any)=>i.ingredient_type === 'preparation')) return fail('Les ingrédients issus de préparations ne sont pas encore pris en charge. Sélectionnez un produit.',422);
      if(ingredients.some((i:any)=>!Number.isFinite(Number(i.quantite)) || Number(i.quantite)<=0 || !String(i.unite || '').trim()))return fail('Chaque ingrédient doit avoir une quantité positive et une unité');
      const result=await service.rpc('restop_save_recipe',{p_restaurant_id:rid,p_recipe_id:recipeEdit?.[1] || null,p_payload:b});
      if(result.error)return fail(result.error.message,400);
      const all=await listRecipes(rid);
      return json(all.find((x:any)=>x.id === result.data));
    }

    m = path.match(/^\/api\/recettes\/([0-9a-f-]+)$/i);
    if (m && req.method === "DELETE") {
      const q = await service.from("restop_recipes").delete().eq("restaurant_id", rid).eq("id", m[1]);
      if (q.error) return fail(q.error.message, 400);
      return json({ success: true });
    }


    const supplierCost=path.match(/^\/api\/supplier-cost-config\/([0-9a-f-]+)$/i);
    if ((supplierCost && ['GET','PUT'].includes(req.method)) || (path === '/api/supplier-cost-config' && req.method === 'POST')) {
      const b:any=req.method === 'GET'?{}:await body(req),supplierId=supplierCost?.[1] || b.supplier_id;
      const sq=await service.from('restop_suppliers').select('id').eq('restaurant_id',rid).eq('id',supplierId).maybeSingle();if(sq.error || !sq.data)return fail('Fournisseur introuvable',404);
      if(req.method === 'GET'){const q=await service.from('restop_supplier_cost_configs').select('*').eq('restaurant_id',rid).eq('supplier_id',supplierId).maybeSingle();if(q.error)throw q.error;return json(q.data || {supplier_id:supplierId,delivery_cost:0,extra_cost:0});}
      if([b.delivery_cost,b.extra_cost].some(x=>!Number.isFinite(Number(x)) || Number(x)<0))return fail('Coûts invalides');
      const q=await service.from('restop_supplier_cost_configs').upsert({restaurant_id:rid,supplier_id:supplierId,delivery_cost:Number(b.delivery_cost),extra_cost:Number(b.extra_cost),updated_at:new Date().toISOString()},{onConflict:'supplier_id'}).select('*').single();if(q.error)throw q.error;return json(q.data);
    }

    if(path === '/api/archives' && req.method === 'GET') {
      let q=service.from('restop_archives').select('*').eq('restaurant_id',rid).order('archived_at',{ascending:false});const type=new URL(req.url).searchParams.get('item_type');if(type)q=q.eq('item_type',type);const result=await q;if(result.error)throw result.error;return json(result.data || []);
    }
    if(path === '/api/archive' && req.method === 'POST') {
      const b:any=await body(req);const result=await service.rpc('restop_archive_item',{p_restaurant_id:rid,p_item_id:b.item_id,p_item_type:b.item_type,p_reason:b.reason || null});if(result.error)return fail(result.error.message,400);return json({success:true,id:result.data});
    }
    const restore=path.match(/^\/api\/restore\/([0-9a-f-]+)$/i);
    if(restore && req.method === 'POST'){const result=await service.rpc('restop_restore_item',{p_restaurant_id:rid,p_archive_id:restore[1]});if(result.error)return fail(result.error.message,400);return json({success:true,id:result.data});}
    const archiveDelete=path.match(/^\/api\/archives\/([0-9a-f-]+)$/i);
    if(archiveDelete && req.method === 'DELETE'){const result=await service.from('restop_archives').delete().eq('restaurant_id',rid).eq('id',archiveDelete[1]);if(result.error)throw result.error;return json({success:true});}

    // Preparations
    if (path === "/api/preparations" && req.method === "GET") {
      const q = await service.from("restop_preparations").select("*,restop_products(name)").eq("restaurant_id", rid).order("created_at");
      if (q.error) throw q.error;
      return json((q.data || []).map((p: any) => ({
        id: p.id, nom: p.name, produit_id: p.product_id, produit_nom: p.restop_products?.name || null,
        forme_decoupe: p.cut_form, forme_decoupe_custom: p.cut_form_custom,
        quantite_produit_brut: p.raw_quantity, unite_produit_brut: p.raw_unit,
        quantite_preparee: p.prepared_quantity, unite_preparee: p.prepared_unit,
        perte: p.loss_quantity, perte_pourcentage: p.loss_percent,
        nombre_portions: p.portion_count, taille_portion: p.portion_size, unite_portion: p.portion_unit,
        date_preparation: p.prepared_at, dlc: p.expiry_at, notes: p.notes,
        created_at: p.created_at, updated_at: p.updated_at
      })));
    }
    if (path === "/api/preparations" && req.method === "POST") {
      const b: any = await body(req);
      const q = await service.from("restop_preparations").insert({
        restaurant_id: rid, name: b.nom, product_id: b.produit_id || null,
        cut_form: b.forme_decoupe || null, cut_form_custom: b.forme_decoupe_custom || null,
        raw_quantity: b.quantite_produit_brut ?? null, raw_unit: b.unite_produit_brut || null,
        prepared_quantity: b.quantite_preparee ?? null, prepared_unit: b.unite_preparee || null,
        loss_quantity: b.perte ?? null, loss_percent: b.perte_pourcentage ?? null,
        portion_count: b.nombre_portions ?? null, portion_size: b.taille_portion ?? null,
        portion_unit: b.unite_portion || null, expiry_at: b.dlc || null, notes: b.notes || null
      }).select("*").single();
      if (q.error) return fail(q.error.message, 400);
      return json({ id: q.data.id, ...b, created_at: q.data.created_at, updated_at: q.data.updated_at });
    }
    let pm = path.match(/^\/api\/preparations\/([0-9a-f-]+)$/i);
    if (pm && req.method === "PUT") {
      const b: any = await body(req);
      const patch: any = {};
      const fields: Record<string,string> = {
        nom:"name", produit_id:"product_id", forme_decoupe:"cut_form", forme_decoupe_custom:"cut_form_custom",
        quantite_produit_brut:"raw_quantity", unite_produit_brut:"raw_unit", quantite_preparee:"prepared_quantity",
        unite_preparee:"prepared_unit", perte:"loss_quantity", perte_pourcentage:"loss_percent",
        nombre_portions:"portion_count", taille_portion:"portion_size", unite_portion:"portion_unit", dlc:"expiry_at", notes:"notes"
      };
      for (const [src,dst] of Object.entries(fields)) if (b[src] !== undefined) patch[dst] = b[src];
      const q = await service.from("restop_preparations").update(patch).eq("restaurant_id", rid).eq("id", pm[1]).select("*").single();
      if (q.error) return fail(q.error.message, 400);
      return json(q.data);
    }
    if (pm && req.method === "DELETE") {
      const q = await service.from("restop_preparations").delete().eq("restaurant_id", rid).eq("id", pm[1]);
      if (q.error) return fail(q.error.message, 400);
      return json({ success: true });
    }

    // Missions
    if ((path === "/api/missions" || path === "/api/missions/") && req.method === "GET") {
      const q = await service.from("restop_missions").select("*").eq("restaurant_id", rid).order("created_at", { ascending: false });
      if (q.error) throw q.error;
      return json(q.data || []);
    }
    if ((path === "/api/missions" || path === "/api/missions/") && req.method === "POST") {
      const b: any = await body(req);
      const q = await service.from("restop_missions").insert({
        restaurant_id: rid, title: b.title, description: b.description || "",
        mission_type: b.type || b.mission_type || null, category: b.category || null,
        assigned_to_user_id: b.assigned_to_user_id || null, assigned_by_user_id: c.user.id,
        status: b.status || "en_cours", priority: b.priority || "normale", due_date: b.due_date || null,
        related_product_id: b.related_product_id || null, related_preparation_id: b.related_preparation_id || null,
        related_supplier_id: b.related_supplier_id || null, target_quantity: b.target_quantity ?? null,
        target_unit: b.target_unit || null
      }).select("*").single();
      if (q.error) return fail(q.error.message, 400);
      return json(q.data);
    }
    let mm = path.match(/^\/api\/missions\/([0-9a-f-]+)$/i);
    if (mm && req.method === "PUT") {
      const b: any = await body(req);
      if (!['patron','super_admin','gerant','chef_cuisine'].includes(role)) {
        const existing=await service.from('restop_missions').select('assigned_to_user_id,status').eq('restaurant_id',rid).eq('id',mm[1]).maybeSingle();
        if(existing.error)throw existing.error;
        if(!existing.data || existing.data.assigned_to_user_id!==c.user.id)return fail('Mission non attribuée à cet utilisateur',403);
        if(b.status !== 'terminee_attente' || Object.keys(b).some(k=>!['status','employee_notes'].includes(k)))return fail('Seul un responsable peut valider ou modifier cette mission',403);
      }
      const patch: any = {};
      for (const k of ["status","employee_notes","validation_notes","priority","due_date"]) if (b[k] !== undefined) patch[k] = b[k];
      if (b.status === "terminee_attente") patch.completed_at = new Date().toISOString();
      if (b.status === "validee") patch.validated_at = new Date().toISOString();
      const q = await service.from("restop_missions").update(patch).eq("restaurant_id", rid).eq("id", mm[1]).select("*").single();
      if (q.error) return fail(q.error.message, 400);
      return json(q.data);
    }


    // RESTOP_FRONTEND_COMPAT_V2
    let mbu = path.match(/^\/api\/missions\/by-user\/([^/]+)$/i);
    if (mbu && req.method === "GET") {
      if(!c.demo && !["patron","super_admin","gerant","chef_cuisine"].includes(role) && mbu[1]!==c.user.id)return fail("Accès interdit",403);
      if (c.demo) {
        const q = await service.from("restop_missions").select("*").eq("restaurant_id", rid).order("created_at", {ascending:false});
        if (q.error) return fail(q.error.message,400);
        // Demo users intentionally share the realistic team mission pool.
        return json((q.data || []).slice(0,3));
      }
      const q = await service.from("restop_missions").select("*").eq("restaurant_id", rid).eq("assigned_to_user_id", mbu[1]).order("created_at",{ascending:false});
      if(q.error) return fail(q.error.message,400);
      return json(q.data || []);
    }

    let spi = path.match(/^\/api\/supplier-product-info\/([0-9a-f-]+)$/i);
    if (spi && req.method === "GET") {
      const q = await service.from("restop_products").select("*").eq("restaurant_id", rid)
        .or("supplier_id.eq."+spi[1]+",main_supplier_id.eq."+spi[1]).eq("active",true).order("name");
      if(q.error) return fail(q.error.message,400);
      return json((q.data||[]).map((p:any)=>({
        id:"rel-"+p.id,
        supplier_id:spi[1],
        product_id:p.id,
        price:Number(p.unit_price||p.reference_price||0),
        reference:p.reference||null,
        is_primary:p.main_supplier_id===spi[1],
        lead_time_days:1
      })));
    }

    let de = path.match(/^\/api\/suppliers\/([0-9a-f-]+)\/delivery-estimate$/i);
    if (de && req.method === "GET") {
      const sq=await service.from("restop_suppliers").select("*").eq("restaurant_id",rid).eq("id",de[1]).maybeSingle();
      if(sq.error || !sq.data) return fail("Fournisseur introuvable",404);
      const now=new Date();
      const estimated=new Date(now.getTime()+24*60*60*1000);
      estimated.setHours(8,30,0,0);
      const nextOrder=new Date(now.getTime()+24*60*60*1000);
      return json({
        supplier_id:de[1],
        supplier_name:sq.data.name,
        can_order_today:true,
        estimated_delivery_date:estimated.toISOString(),
        next_order_date:nextOrder.toISOString(),
        explanation:"Commande possible aujourd’hui — livraison estimée demain matin selon les règles fournisseur.",
        delivery_rules:sq.data.delivery_rules||{}
      });
    }

    let os = path.match(/^\/api\/orders\/([0-9a-f-]+)\/status$/i);
    if(os && req.method === "PUT"){
      const status=new URL(req.url).searchParams.get("status")||"pending";
      const patch:any={status};
      if(["delivered","received","livree","livré"].includes(status.toLowerCase())) patch.actual_delivery_date=new Date().toISOString();
      const q=await service.from("restop_orders").update(patch).eq("restaurant_id",rid).eq("id",os[1]).select("*").maybeSingle();
      if(q.error) return fail(q.error.message,400);
      if(!q.data) return fail("Commande introuvable",404);
      return json(q.data);
    }

    // Notifications
    if (path.startsWith("/api/notifications") && req.method === "GET") {
      let q = service.from("restop_notifications").select("*").eq("restaurant_id", rid);
      if (!c.demo && c.user?.id) q = q.or("user_id.is.null,user_id.eq." + c.user.id);
      const r = await q.order("created_at", { ascending: false });
      if (r.error) return fail(r.error.message,400);
      return json(r.data || []);
    }

    // Purchase orders
    if (path === "/api/orders" && req.method === "GET") {
      const q = await service.from("restop_orders").select("*,restop_order_items(*)")
        .eq("restaurant_id", rid).order("order_date", { ascending: false });
      if (q.error) throw q.error;
      return json((q.data || []).map((o: any) => ({
        id: o.id, order_number: o.order_number, supplier_id: o.supplier_id,
        items: (o.restop_order_items || []).map((i: any) => ({
          product_id: i.product_id, product_name: i.product_name, quantity: Number(i.quantity),
          unit: i.unit, unit_price: Number(i.unit_price), total_price: Number(i.total_price)
        })),
        total_amount: Number(o.total_amount), order_date: o.order_date,
        estimated_delivery_date: o.estimated_delivery_date, actual_delivery_date: o.actual_delivery_date,
        status: o.status, notes: o.notes, created_by: o.created_by,
        created_at: o.created_at, updated_at: o.updated_at
      })));
    }
    if (path === "/api/orders" && req.method === "POST") {
      const b: any = await body(req);
      const items = Array.isArray(b.items) ? b.items : [];
      if(!items.length || items.some((i:any)=>!Number.isFinite(Number(i.quantity)) || Number(i.quantity)<=0 || !Number.isFinite(Number(i.unit_price)) || Number(i.unit_price)<0))return fail('Une commande doit contenir des quantités positives et des prix valides');
      const sq=await service.from('restop_suppliers').select('id').eq('restaurant_id',rid).eq('id',b.supplier_id).maybeSingle();if(sq.error || !sq.data)return fail('Fournisseur introuvable');
      const productIds=items.map((i:any)=>i.product_id);
      const pq=await service.from('restop_products').select('id,category').eq('restaurant_id',rid).in('id',productIds);if(pq.error || items.some((i:any)=>!(pq.data || []).some((p:any)=>p.id===i.product_id)))return fail('Produit introuvable dans ce restaurant');
      if(role==='barman' && (pq.data || []).some((p:any)=>!/bar|boisson|vin|alcool|soft/i.test(p.category || '')))return fail('Le barman peut commander uniquement les produits du bar',403);
      const total = items.reduce((sum:number,i:any)=>sum+Number(i.quantity)*Number(i.unit_price),0);
      const orderNumber = "CMD-" + Date.now().toString().slice(-8);
      const oq = await service.from("restop_orders").insert({
        restaurant_id: rid, supplier_id: b.supplier_id || null, order_number: orderNumber,
        total_amount: total, notes: b.notes || null, created_by: c.user?.id || null,
        estimated_delivery_date: b.estimated_delivery_date || new Date(Date.now()+24*60*60*1000).toISOString()
      }).select("*").single();
      if (oq.error) return fail(oq.error.message, 400);
      if (items.length) {
        const iq = await service.from("restop_order_items").insert(items.map((i: any) => ({
          restaurant_id: rid, order_id: oq.data.id, product_id: i.product_id || null,
          product_name: i.product_name || "", quantity: Number(i.quantity || 0), unit: i.unit || null,
          unit_price: Number(i.unit_price || 0),
          total_price: Number(i.quantity)*Number(i.unit_price)
        })));
        if (iq.error) {await service.from("restop_orders").delete().eq("restaurant_id",rid).eq("id",oq.data.id);return fail(iq.error.message,400);}
      }
      return json({ ...oq.data, items });
    }
    let om = path.match(/^\/api\/orders\/([0-9a-f-]+)$/i);
    if (om && (req.method === "PUT" || req.method === "PATCH")) {
      const b: any = await body(req);
      const patch: any = {};
      for (const k of ["status","notes","estimated_delivery_date","actual_delivery_date"]) if (b[k] !== undefined) patch[k] = b[k];
      const q = await service.from("restop_orders").update(patch).eq("restaurant_id", rid).eq("id", om[1]).select("*").single();
      if (q.error) return fail(q.error.message, 400);
      return json(q.data);
    }

    if ((path === "/api/admin/users" || path === "/api/users") && req.method === "GET") {
      if (c.demo) {
        const q = await service.from("restop_demo_users").select("*").eq("restaurant_id", rid).order("created_at");
        if (q.error) throw q.error;
        return json(q.data || []);
      }
      const q = await service.from("restop_profiles").select("*").eq("restaurant_id", rid).order("created_at");
      if (q.error) throw q.error;
      return json((q.data || []).map(legacyUser));
    }

    if (path === '/api/admin/users' && req.method === 'POST' && !c.demo) {
      const b:any=await body(req),allowedRoles=role==='super_admin'?['patron','gerant','chef_cuisine','barman','caissier','employe_cuisine','super_admin']:['patron','gerant','chef_cuisine','barman','caissier','employe_cuisine'];
      if(!allowedRoles.includes(b.role) || !String(b.email || '').includes('@') || String(b.password || '').length<8 || !String(b.username || '').trim())return fail('Email, identifiant, mot de passe de huit caractères et rôle valides requis');
      const uq=await service.auth.admin.createUser({email:b.email,password:b.password,email_confirm:true});if(uq.error)return fail(uq.error.message,400);
      const pq=await service.from('restop_profiles').insert({user_id:uq.data.user.id,restaurant_id:rid,email:b.email,username:b.username,full_name:b.full_name || b.username,role:b.role,is_active:b.is_active!==false}).select('*').single();
      if(pq.error){await service.auth.admin.deleteUser(uq.data.user.id);return fail(pq.error.message,400);}return json(legacyUser(pq.data));
    }
    const realUserEdit=path.match(/^\/api\/admin\/users\/([0-9a-f-]+)$/i);
    if(realUserEdit && !c.demo && ['PUT','DELETE'].includes(req.method)) {
      const uq=await service.from('restop_profiles').select('*').eq('restaurant_id',rid).eq('user_id',realUserEdit[1]).maybeSingle();if(uq.error)throw uq.error;if(!uq.data)return fail('Utilisateur introuvable',404);
      if(uq.data.user_id===c.user.id)return fail('La modification de votre propre compte doit passer par la gestion du profil',403);
      if(uq.data.role==='super_admin' && role!=='super_admin')return fail('Accès réservé à un super administrateur',403);
      if(req.method === 'DELETE'){const result=await service.auth.admin.deleteUser(uq.data.user_id);if(result.error)return fail(result.error.message,400);await service.from('restop_profiles').delete().eq('restaurant_id',rid).eq('user_id',uq.data.user_id);return json({success:true});}
      const b:any=await body(req),allowedRoles=role==='super_admin'?['patron','gerant','chef_cuisine','barman','caissier','employe_cuisine','super_admin']:['patron','gerant','chef_cuisine','barman','caissier','employe_cuisine'];
      if(b.role!==undefined && !allowedRoles.includes(b.role))return fail('Rôle non autorisé',403);
      if(b.email && b.email!==uq.data.email)return fail('Le changement d’email doit passer par la vérification du compte',422);
      if(b.password && String(b.password).length<8)return fail('Mot de passe trop court');
      const patch:any={updated_at:new Date().toISOString()};for(const key of ['username','full_name','role','is_active'])if(b[key]!==undefined)patch[key]=b[key];
      if(b.password){const auth=await service.auth.admin.updateUserById(uq.data.user_id,{password:b.password});if(auth.error)return fail(auth.error.message,400);}
      const result=await service.from('restop_profiles').update(patch).eq('restaurant_id',rid).eq('user_id',uq.data.user_id).select('*').single();if(result.error)throw result.error;return json(legacyUser(result.data));
    }

    if (path === "/api/admin/users" && req.method === "POST" && c.demo) {
      const b: any = await body(req);
      if(!["patron","gerant","chef_cuisine","barman","caissier","employe_cuisine"].includes(b.role))return fail("Rôle non autorisé",403);
      const q = await service.from("restop_demo_users").insert({
        restaurant_id: rid,
        username: b.username,
        full_name: b.full_name || b.username,
        email: b.email || null,
        role: b.role || "employe_cuisine",
        is_active: true
      }).select("*").single();
      if (q.error) return fail(q.error.message, 400);
      return json(q.data);
    }

    const dum = path.match(/^\/api\/admin\/users\/([0-9a-f-]+)$/i);
    if (dum && c.demo && req.method === "PUT") {
      const b: any = await body(req);
      const patch: any = {};
      for (const k of ["username","full_name","email","role","is_active"]) if (b[k] !== undefined) patch[k] = b[k];
      const q = await service.from("restop_demo_users").update(patch).eq("restaurant_id", rid).eq("id", dum[1]).select("*").single();
      if (q.error) return fail(q.error.message, 400);
      return json(q.data);
    }
    if (dum && c.demo && req.method === "DELETE") {
      const q = await service.from("restop_demo_users").delete().eq("restaurant_id", rid).eq("id", dum[1]);
      if (q.error) return fail(q.error.message, 400);
      return json({ success: true });
    }

    if (path === "/api/rapports_z" && req.method === "GET") {
      const q = await service.from("restop_reports_z").select("*").eq("restaurant_id", rid).order("report_date", { ascending: false });
      if (q.error) throw q.error;
      return json((q.data || []).map((z: any) => ({
        id: z.id,
        date: z.report_date,
        ca_total: Number(z.ca_total || 0),
        produits: z.products || [],
        created_at: z.created_at
      })));
    }

    if (path === "/api/dashboard/stats" && req.method === "GET") {
      const pq = await service.from("restop_products").select("id,current_stock,min_stock").eq("restaurant_id", rid).eq("active", true);
      const sq = await service.from("restop_suppliers").select("id").eq("restaurant_id", rid);
      const mq = await service.from("restop_missions").select("id,status").eq("restaurant_id", rid);
      const zq = await service.from("restop_reports_z").select("ca_total").eq("restaurant_id", rid);
      const products = pq.data || [];
      return json({
        total_produits: products.length,
        total_fournisseurs: (sq.data || []).length,
        ruptures: products.filter((x: any) => Number(x.current_stock || 0) <= 0).length,
        stocks_critiques: products.filter((x: any) => Number(x.current_stock || 0) <= Number(x.min_stock || 0)).length,
        missions_en_cours: (mq.data || []).filter((x: any) => x.status !== "validee" && x.status !== "annulee").length,
        ca_total: (zq.data || []).reduce((s: number, x: any) => s + Number(x.ca_total || 0), 0)
      });
    }

    if (path === "/api/categories-production" && req.method === "GET") {
      return json(["Entrée", "Plat", "Dessert", "Bar", "Autres"]);
    }


    if(path === '/api/stock/batch-summary' && req.method === 'GET') {
      const q=await service.from('restop_product_batches').select('*,restop_products(name,current_stock)').eq('restaurant_id',rid).eq('is_consumed',false);if(q.error)throw q.error;
      const groups:any={},now=Date.now();for(const b of q.data || []) {const status=batchStatus(b.expiry_date);const row=groups[b.product_id] ||= {product_id:b.product_id,product_name:b.restop_products?.name || '',total_stock:Number(b.restop_products?.current_stock || 0),critical_batches:0,expired_batches:0,batches:[]};if(status==='expired')row.expired_batches++;if(status==='critical')row.critical_batches++;row.batches.push({...b,quantity:Number(b.quantity),status});}return json(Object.values(groups));
    }

    // DEMO_ANALYTICS_BLOCK
    if (c.demo && path === "/api/analytics/profitability" && req.method === "GET") {
      const q = await service.from("restop_recipes").select("*").eq("restaurant_id", rid).order("selling_price", { ascending: false });
      const sold: Record<string,number> = {
        "Moules marinières":178,
        "Entrecôte, frites maison":108,
        "Burrata & tomates de Provence":63,
        "Linguine aux palourdes":43,
        "Loup rôti, beurre citron":37
      };
      return json((q.data || []).map((r:any) => {
        const price=Number(r.selling_price||0), cost=Number(r.material_cost||0);
        const margin=price-cost, portions=sold[r.name]||20;
        return {
          recipe_id:r.id, recipe_name:r.name, selling_price:price, ingredient_cost:cost,
          profit_margin:margin, profit_percentage:price?margin/price*100:0,
          portions_sold:portions,total_revenue:portions*price,total_profit:portions*margin
        };
      }));
    }

    if (c.demo && path === "/api/analytics/sales-performance" && req.method === "GET") {
      const z = await service.from("restop_reports_z").select("*").eq("restaurant_id", rid).order("report_date");
      const total=(z.data||[]).reduce((s:number,x:any)=>s+Number(x.ca_total||0),0);
      return json({
        period:"weekly",
        total_sales:total,
        total_orders:5,
        average_order_value:total/5,
        top_recipes:[
          {name:"Moules marinières",quantity:178,revenue:4272},
          {name:"Entrecôte, frites maison",quantity:108,revenue:3348},
          {name:"Linguine aux palourdes",quantity:43,revenue:1118},
          {name:"Loup rôti, beurre citron",quantity:37,revenue:1073},
          {name:"Burrata & tomates",quantity:63,revenue:1008}
        ],
        sales_by_category:{Bar:2860,Entrées:2140,Plats:14290,Desserts:1548}
      });
    }

    if (c.demo && path === "/api/analytics/alerts" && req.method === "GET") {
      const p = await service.from("restop_products").select("*").eq("restaurant_id", rid).eq("active", true);
      const low=(p.data||[]).filter((x:any)=>Number(x.current_stock||0)<=Number(x.min_stock||0)).map((x:any)=>({
        product_name:x.name,current_quantity:Number(x.current_stock||0),minimum_quantity:Number(x.min_stock||0),
        shortage:Math.max(0,Number(x.min_stock||0)-Number(x.current_stock||0))
      }));
      const expiring=[
        {product_name:"Saumon frais",batch_id:"LOT-SAU-0610",quantity:2.5,expiry_date:new Date(Date.now()+2*86400000).toISOString(),days_to_expiry:2,urgency:"critical"},
        {product_name:"Burrata 125 g",batch_id:"LOT-BUR-0810",quantity:8,expiry_date:new Date(Date.now()+4*86400000).toISOString(),days_to_expiry:4,urgency:"warning"}
      ];
      const price=[
        {id:"price-demo-1",product_name:"Huile d'olive vierge",supplier_name:"Métro La Valentine",reference_price:7.30,actual_price:8.10,difference_percentage:10.96,alert_date:new Date(Date.now()-86400000).toISOString()}
      ];
      return json({expiring_products:expiring,price_anomalies:price,low_stock_items:low,unused_stock:[],total_alerts:expiring.length+price.length+low.length});
    }

    if (c.demo && path === "/api/analytics/cost-analysis" && req.method === "GET") {
      const p = await service.from("restop_products").select("*").eq("restaurant_id", rid).eq("active", true);
      const rows=p.data||[];
      const total=rows.reduce((s:number,x:any)=>s+Number(x.current_stock||0)*Number(x.reference_price??x.unit_price??0),0);
      const expensive=[...rows].sort((a:any,b:any)=>Number(b.reference_price||0)-Number(a.reference_price||0)).slice(0,8).map((x:any)=>({
        name:x.name,unit_price:Number(x.reference_price??x.unit_price??0),category:x.category||"Non classé"
      }));
      return json({
        total_inventory_value:total,
        avg_cost_per_recipe:7.78,
        most_expensive_ingredients:expensive,
        cost_trends:{monthly_change:2.5,quarterly_change:7.8,highest_cost_category:"Viandes et poissons",lowest_cost_category:"Épicerie sèche"},
        waste_analysis:{estimated_waste_percentage:6.4,estimated_waste_value:total*0.064,main_waste_sources:["Produits périssables","Surproduction","Découpe"]}
      });
    }

    if (c.demo && path === "/api/stock/adjustments-history" && req.method === "GET") {
      const q=await service.from("restop_stock_movements").select("*,restop_products(name)").eq("restaurant_id",rid).order("created_at",{ascending:false}).limit(25);
      return json((q.data||[]).map((x:any)=>({
        id:x.id,adjustment_type:"ingredient",target_id:x.product_id,target_name:x.restop_products?.name||"Produit",
        adjustment_reason:x.reason||"Ajustement de stock",quantity_adjusted:x.movement_type==="out"?-Number(x.quantity||0):Number(x.quantity||0),
        user_name:"Équipe démo",ingredient_deductions:[],created_at:x.created_at
      })));
    }

    if(path === '/api/stock/advanced-adjustment' && req.method === 'POST') {
      const b:any=await body(req),qty=Number(b.quantity_adjusted);
      if(b.adjustment_type!=='ingredient')return fail('Le stock de plats préparés n’est pas disponible sur cette version',422);
      if(!Number.isFinite(qty) || qty===0)return fail('Quantité d’ajustement invalide');
      const result=await service.rpc('restop_record_movement',{p_restaurant_id:rid,p_user_id:c.user.id,p_payload:{produit_id:b.target_id,type:qty>0?'entree':'sortie',quantite:Math.abs(qty),commentaire:b.adjustment_reason || 'Ajustement de stock'}});
      if(result.error)return fail(result.error.message,400);
      return json({id:result.data.id,adjustment_type:'ingredient',target_id:b.target_id,target_name:result.data.produit_nom,adjustment_reason:b.adjustment_reason,quantity_adjusted:qty,user_name:c.profile.full_name,ingredient_deductions:[],created_at:result.data.date});
    }

    if (c.demo && /^\/api\/price-anomalies\/.+\/resolve$/.test(path) && req.method === "POST") {
      return json({success:true,resolved:true});
    }

    if (c.demo && (path === "/api/demo/clean-duplicates" || path === "/api/demo/init-real-restaurant-data") && req.method === "POST") {
      return json({success:true,message:"Données de démonstration déjà initialisées"});
    }


    // RESTOP_OCR_V1
    if(path==="/api/ocr/documents"&&req.method==="GET"){
      let q=service.from("restop_documents").select("*").eq("restaurant_id",rid).order("created_at",{ascending:false});
      const dtype=new URL(req.url).searchParams.get("document_type");
      if(dtype)q=q.eq("document_type",dtype);
      const r=await q.limit(100);
      if(r.error)return fail(r.error.message,400);
      return json((r.data||[]).map((d:any)=>restopDocumentShape(d)));
    }

    if(path==="/api/ocr/upload-document"&&req.method==="POST"){
      const form=await req.formData();
      const file=form.get("file");
      const dtype=String(form.get("document_type")||"z_report");
      if(!(file instanceof File))return fail("Fichier requis",422);
      if(!["z_report","facture_fournisseur","mercuriale"].includes(dtype))return fail("Type de document invalide",400);
      if(file.size>15*1024*1024)return fail("Fichier trop volumineux (15 Mo maximum)",413);
      const safeName=(file.name||"document").replace(/[^a-zA-Z0-9À-ÿ._-]/g,"_");
      const storagePath=rid+"/"+crypto.randomUUID()+"-"+safeName;
      const bytes=new Uint8Array(await file.arrayBuffer());
      const up=await service.storage.from("restop-documents").upload(storagePath,bytes,{contentType:file.type||"application/octet-stream",upsert:false});
      if(up.error)return fail(up.error.message,400);

      const parsed=c.demo?demoOcrPayload(dtype):{};
      const status=c.demo?"traite":"uploaded";
      const amount=Number(parsed.total_ttc||parsed.grand_total_sales||0)||null;
      const iq=await service.from("restop_documents").insert({
        restaurant_id:rid,document_type:dtype,file_name:file.name||safeName,storage_path:storagePath,status,
        ocr_data:parsed,document_date:parsed.date||parsed.report_date||null,total_amount:amount,created_by:c.user?.id||null
      }).select("*").single();
      if(iq.error){
        await service.storage.from("restop-documents").remove([storagePath]);
        return fail(iq.error.message,400);
      }
      const shaped=restopDocumentShape(iq.data);
      return json({
        document_id:iq.data.id,type_document:dtype,texte_extrait:c.demo?"Données OCR simulées pour la démonstration.":"",
        donnees_parsees:parsed,message:c.demo?"Document analysé en mode démonstration":"Document chargé. Moteur OCR externe à configurer.",
        file_type:shaped.file_type,demo_simulation:c.demo,ocr_configured:c.demo
      });
    }

    let odm=path.match(/^\/api\/ocr\/document\/([0-9a-f-]+)$/i);
    if(odm&&req.method==="GET"){
      const q=await service.from("restop_documents").select("*").eq("restaurant_id",rid).eq("id",odm[1]).maybeSingle();
      if(q.error||!q.data)return fail("Document non trouvé",404);
      let dataUri:any=null;
      if(!String(q.data.storage_path||"").startsWith("demo://")){
        const dl=await service.storage.from("restop-documents").download(q.data.storage_path);
        if(!dl.error&&dl.data)dataUri=await blobToDataUri(dl.data,q.data.file_name);
      }
      return json(restopDocumentShape(q.data,dataUri));
    }
    // RESTOP_OCR_REMOVE_ALIAS
    let odrm=path.match(/^\/api\/ocr\/document\/([0-9a-f-]+)\/remove$/i);
    if(odrm&&req.method==="POST"){
      const q=await service.from("restop_documents").select("*").eq("restaurant_id",rid).eq("id",odrm[1]).maybeSingle();
      if(!q.data)return fail("Document non trouvé",404);
      if(c.demo&&String(q.data.id).startsWith("10000000-0000-4000-8000-000000014"))return json({message:"Document de démonstration conservé",demo:true});
      if(!String(q.data.storage_path||"").startsWith("demo://"))await service.storage.from("restop-documents").remove([q.data.storage_path]);
      const d=await service.from("restop_documents").delete().eq("id",q.data.id);
      if(d.error)return fail(d.error.message,400);
      return json({message:"Document supprimé"});
    }

    if(odm&&req.method==="DELETE"){
      const q=await service.from("restop_documents").select("*").eq("restaurant_id",rid).eq("id",odm[1]).maybeSingle();
      if(!q.data)return fail("Document non trouvé",404);
      if(c.demo&&String(q.data.id).startsWith("10000000-0000-4000-8000-000000014")){
        return json({message:"Document de démonstration conservé",demo:true});
      }
      if(!String(q.data.storage_path||"").startsWith("demo://"))await service.storage.from("restop-documents").remove([q.data.storage_path]);
      const d=await service.from("restop_documents").delete().eq("id",q.data.id);
      if(d.error)return fail(d.error.message,400);
      return json({message:"Document supprimé"});
    }

    if(path==="/api/ocr/documents/all"&&req.method==="DELETE"){
      if(c.demo)return json({message:"Historique démo réinitialisable conservé",deleted_count:0,demo:true});
      const q=await service.from("restop_documents").select("id,storage_path").eq("restaurant_id",rid);
      const paths=(q.data||[]).map((x:any)=>x.storage_path).filter((x:string)=>x&&!x.startsWith("demo://"));
      if(paths.length)await service.storage.from("restop-documents").remove(paths);
      const d=await service.from("restop_documents").delete().eq("restaurant_id",rid);
      if(d.error)return fail(d.error.message,400);
      return json({message:"Tous les documents OCR ont été supprimés",deleted_count:(q.data||[]).length});
    }

    let afm=path.match(/^\/api\/ocr\/analyze-facture(-ai)?\/([0-9a-f-]+)$/i);
    if(afm&&req.method==="POST"){
      const q=await service.from("restop_documents").select("*").eq("restaurant_id",rid).eq("id",afm[2]).maybeSingle();
      if(!q.data)return fail("Document OCR non trouvé",404);
      if(q.data.document_type!=="facture_fournisseur")return fail("Ce document n'est pas une facture fournisseur",400);
      if(!q.data.ocr_data||Object.keys(q.data.ocr_data).length===0){
        return fail("Le document est chargé mais le moteur OCR externe n'est pas encore configuré pour cette organisation.",503);
      }
      const analysis=await invoiceAnalysis(rid,q.data,!!afm[1]&&c.demo);
      if(afm[1]&&!c.demo)analysis.ai_powered=false;
      return json(analysis);
    }

    if(path==="/api/ocr/confirm-import"&&req.method==="POST"){
      const b:any=await body(req);
      const dq=await service.from("restop_documents").select("*").eq("restaurant_id",rid).eq("id",b.document_id).maybeSingle();
      if(!dq.data)return fail("Document OCR non trouvé",404);
      const items=Array.isArray(b.items)?b.items:[];
      if(c.demo){
        return json({
          success:true,demo:true,message:"Validation simulée : le jeu de données commercial reste réinitialisable.",
          stats:{products_created:items.filter((x:any)=>!x.selected_product_id).length,stock_entries:items.filter((x:any)=>Number(x.final_qty||x.ocr_qty||0)>0).length,batches_created:items.filter((x:any)=>Number(x.final_qty||x.ocr_qty||0)>0).length}
        });
      }

      if(!items.length || items.some((i:any)=>!Number.isFinite(Number(i.final_qty??i.ocr_qty)) || Number(i.final_qty??i.ocr_qty)<=0 || !Number.isFinite(Number(i.final_price??i.ocr_price??0)) || Number(i.final_price??i.ocr_price??0)<0))return fail('Chaque ligne doit avoir une quantité positive et un prix valide');
      const result=await service.rpc('restop_confirm_invoice',{p_restaurant_id:rid,p_payload:b});
      if(result.error)return fail(result.error.message,400);
      return json(result.data);
    }


    let pzm=path.match(/^\/api\/ocr\/process-z-report\/([0-9a-f-]+)$/i);
    if(pzm&&req.method==="POST"){
      const q=await service.from("restop_documents").select("*").eq("restaurant_id",rid).eq("id",pzm[1]).maybeSingle();
      if(!q.data)return fail("Document OCR non trouvé",404);
      if(q.data.document_type!=="z_report")return fail("Ce document n'est pas un ticket Z",400);
      const data=q.data.ocr_data||{};
      if(c.demo){
        return json({success:true,demo:true,message:"Ticket Z analysé : 74 couverts, CA 2 876,30 €. Déductions de stock simulées pour préserver la démo.",warnings:[]});
      }
      if(!Object.keys(data).length)return fail("OCR non disponible pour ce document",503);
      const products:any[]=[];
      for(const arr of Object.values(data.items_by_category||{}))for(const it of (arr as any[]))products.push({name:it.name,qty:Number(it.quantity_sold||0),price:Number(it.unit_price||0)});
      const rq=await service.from("restop_reports_z").insert({
        restaurant_id:rid,report_date:toIsoDate(data.report_date||q.data.document_date),ca_total:Number(data.grand_total_sales||data.total_ca||0),
        products:products.map((x:any)=>({name:x.name,qty:x.qty,ca:x.qty*x.price})),source_file_path:q.data.storage_path
      }).select("*").single();
      if(rq.error)return fail(rq.error.message,400);
      return json({success:true,message:"Ticket Z intégré.",warnings:[],rapport_z_id:rq.data.id});
    }


    // RESTOP_EXCEL_V1
    if(path==="/api/export/stocks"&&req.method==="GET"){
      const q=await service.from("restop_products").select("*").eq("restaurant_id",rid).eq("active",true).order("name");
      if(q.error)return fail(q.error.message,400);
      const rows=(q.data||[]).map((p:any)=>({
        "Produit ID":p.id,
        "Produit":p.name,
        "Catégorie":p.category||"",
        "Unité":p.unit||"",
        "Quantité Actuelle":Number(p.current_stock||0),
        "Quantité Min":Number(p.min_stock||0),
        "Quantité Max":Number(p.target_stock||0),
        "Prix Référence":Number(p.reference_price??p.unit_price??0)
      }));
      const ws=XLSX.utils.json_to_sheet(rows);
      const wb=XLSX.utils.book_new();
      XLSX.utils.book_append_sheet(wb,ws,"Stocks");
      const out=XLSX.write(wb,{type:"array",bookType:"xlsx"});
      return new Response(out,{status:200,headers:{...cors,"Content-Type":"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet","Content-Disposition":'attachment; filename="stocks_export.xlsx"'}});
    }

    if(path==="/api/export/recettes"&&req.method==="GET"){
      const recipes=await listRecipes(rid);
      const rows:any[]=[];
      for(const r of recipes){
        if(!r.ingredients.length)rows.push({
          "Nom Recette":r.nom,"Description":r.description||"","Catégorie":r.categorie||"","Portions":r.portions||1,
          "Temps Préparation":r.temps_preparation||"","Prix Vente":r.prix_vente||"","Produit ID":"","Quantité":"","Unité":""
        });
        for(const i of r.ingredients)rows.push({
          "Nom Recette":r.nom,"Description":r.description||"","Catégorie":r.categorie||"","Portions":r.portions||1,
          "Temps Préparation":r.temps_preparation||"","Prix Vente":r.prix_vente||"","Produit ID":i.produit_id||"",
          "Quantité":i.quantite||0,"Unité":i.unite||""
        });
      }
      const ws=XLSX.utils.json_to_sheet(rows);
      const wb=XLSX.utils.book_new();
      XLSX.utils.book_append_sheet(wb,ws,"Recettes");
      const out=XLSX.write(wb,{type:"array",bookType:"xlsx"});
      return new Response(out,{status:200,headers:{...cors,"Content-Type":"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet","Content-Disposition":'attachment; filename="recettes_export.xlsx"'}});
    }

    if((path==="/api/import/stocks"||path==="/api/import/recettes"||path==="/api/import/global-excel")&&req.method==="POST"){
      const form=await req.formData();
      const file=form.get("file");
      if(!(file instanceof File))return fail("Fichier Excel requis",422);
      const lower=(file.name||"").toLowerCase();
      if(!lower.endsWith(".xlsx")&&!lower.endsWith(".xls")&&!lower.endsWith(".csv"))return fail("Format non supporté. Utilisez .xlsx, .xls ou .csv",400);
      const buf=await file.arrayBuffer();
      let wb:any;
      try{ wb=XLSX.read(buf,{type:"array"}); }catch(e){ return fail("Fichier Excel illisible",400); }

      if(path==="/api/import/stocks"){
        const ws=wb.Sheets[wb.SheetNames[0]];
        const rows:any[]=XLSX.utils.sheet_to_json(ws,{defval:null});
        let imported=0; const errors:string[]=[];
        for(let i=0;i<rows.length;i++){
          const row=rows[i];
          const pid=String(row["Produit ID"]??row["produit_id"]??"").trim();
          if(!pid)continue;
          const pq=await service.from("restop_products").select("*").eq("restaurant_id",rid).eq("id",pid).maybeSingle();
          if(!pq.data){ errors.push("Ligne "+(i+2)+": produit "+pid+" introuvable"); continue; }
          if(c.demo){ imported++; continue; }
          const current=Number(row["Quantité Actuelle"]??row["quantite_actuelle"]??pq.data.current_stock??0);
          const min=Number(row["Quantité Min"]??row["quantite_min"]??pq.data.min_stock??0);
          const targetVal=row["Quantité Max"]??row["quantite_max"]??pq.data.target_stock;
          const target=targetVal===null||targetVal===undefined||targetVal===""?pq.data.target_stock:Number(targetVal);
          const uq=await service.from("restop_products").update({current_stock:current,min_stock:min,target_stock:target}).eq("id",pid);
          if(uq.error){ errors.push("Ligne "+(i+2)+": "+uq.error.message); continue; }
          imported++;
        }
        return json({message:imported+" lignes importées avec succès"+(c.demo?" (simulation démo)":""),errors,demo:c.demo});
      }

      if(path==="/api/import/recettes"){
        const ws=wb.Sheets[wb.SheetNames[0]];
        const rows:any[]=XLSX.utils.sheet_to_json(ws,{defval:null});
        const groups:Record<string,any>={}; const errors:string[]=[];
        for(let i=0;i<rows.length;i++){
          const row=rows[i];
          const name=String(row["Nom Recette"]??row["nom"]??"").trim();
          if(!name)continue;
          if(!groups[name])groups[name]={
            name,description:row["Description"]||null,category:row["Catégorie"]||row["Categorie"]||null,
            portions:Number(row["Portions"]||1),preparation_time:row["Temps Préparation"]?Number(row["Temps Préparation"]):null,
            selling_price:row["Prix Vente"]?Number(row["Prix Vente"]):null,ingredients:[]
          };
          const pid=String(row["Produit ID"]??"").trim();
          const qty=Number(row["Quantité"]??0);
          if(pid&&qty>0)groups[name].ingredients.push({product_id:pid,quantity:qty,unit:String(row["Unité"]||"")});
        }
        let imported=0;
        for(const g of Object.values(groups) as any[]){
          if(c.demo){ imported++; continue; }
          let rq=await service.from("restop_recipes").select("*").eq("restaurant_id",rid).eq("name",g.name).maybeSingle();
          let recipeId=rq.data?.id;
          if(recipeId){
            const up=await service.from("restop_recipes").update({
              description:g.description,category:g.category,portions:g.portions,preparation_time:g.preparation_time,selling_price:g.selling_price
            }).eq("id",recipeId);
            if(up.error){ errors.push(g.name+": "+up.error.message); continue; }
            await service.from("restop_recipe_ingredients").delete().eq("recipe_id",recipeId);
          }else{
            const ins=await service.from("restop_recipes").insert({
              restaurant_id:rid,name:g.name,description:g.description,category:g.category,portions:g.portions,
              preparation_time:g.preparation_time,selling_price:g.selling_price
            }).select("*").single();
            if(ins.error){ errors.push(g.name+": "+ins.error.message); continue; }
            recipeId=ins.data.id;
          }
          if(g.ingredients.length){
            const ids=g.ingredients.map((x:any)=>x.product_id);
            const pq=await service.from("restop_products").select("id,name").eq("restaurant_id",rid).in("id",ids);
            const names:Record<string,string>={}; for(const p of pq.data||[])names[p.id]=p.name;
            const valid=g.ingredients.filter((x:any)=>names[x.product_id]).map((x:any)=>({
              restaurant_id:rid,recipe_id:recipeId,product_id:x.product_id,product_name:names[x.product_id],quantity:x.quantity,unit:x.unit
            }));
            if(valid.length){
              const ii=await service.from("restop_recipe_ingredients").insert(valid);
              if(ii.error)errors.push(g.name+": "+ii.error.message);
            }
          }
          imported++;
        }
        return json({message:imported+" recettes importées avec succès"+(c.demo?" (simulation démo)":""),errors,demo:c.demo});
      }

      // Catalogue global multi-onglets.
      const result:any={total_processed:0,products_created:0,products_updated:0,errors:[],sheets_processed:[]};
      for(const sheetName of wb.SheetNames){
        if(/résumé|resume|sommaire/i.test(sheetName))continue;
        const rows:any[]=XLSX.utils.sheet_to_json(wb.Sheets[sheetName],{defval:null});
        let count=0;
        for(const row of rows){
          const entries=Object.entries(row);
          const find=(keys:string[])=>{
            const e=entries.find(([k])=>keys.some(x=>normText(k).includes(normText(x))));
            return e?e[1]:null;
          };
          const name=String(find(["nom","produit","désignation","designation","libellé","libelle","article"])||"").trim();
          if(!name)continue;
          const priceRaw=find(["prix","tarif","pu","montant"]);
          const price=Number(String(priceRaw??0).replace(",",".").replace("€","").trim())||0;
          const unit=String(find(["unité","unite","unit","cond","cdt"])||"pièce");
          const supplierName=String(find(["fournisseur","frs"])||"Fournisseur Inconnu").trim();
          result.total_processed++; count++;
          if(c.demo){ result.products_created++; continue; }
          let supplierId:any=null;
          if(supplierName&&supplierName!=="Fournisseur Inconnu"){
            const sq=await service.from("restop_suppliers").select("*").eq("restaurant_id",rid).ilike("name",supplierName).maybeSingle();
            if(sq.data)supplierId=sq.data.id;
            else{
              const si=await service.from("restop_suppliers").insert({restaurant_id:rid,name:supplierName,categories:["Divers"]}).select("*").single();
              if(!si.error)supplierId=si.data.id;
            }
          }
          const pq=await service.from("restop_products").select("*").eq("restaurant_id",rid).ilike("name",name).maybeSingle();
          if(pq.data){
            const up=await service.from("restop_products").update({unit_price:price||pq.data.unit_price,reference_price:price||pq.data.reference_price}).eq("id",pq.data.id);
            if(up.error)result.errors.push(name+": "+up.error.message); else result.products_updated++;
          }else{
            const ins=await service.from("restop_products").insert({
              restaurant_id:rid,name,category:sheetName,unit,unit_price:price,reference_price:price,
              supplier_id:supplierId,main_supplier_id:supplierId,current_stock:0,min_stock:0,target_stock:0,active:true
            });
            if(ins.error)result.errors.push(name+": "+ins.error.message); else result.products_created++;
          }
        }
        result.sheets_processed.push({name:sheetName,count});
      }
      result.demo=c.demo;
      return json(result);
    }

    if(path==="/api/recettes/calculer-couts"&&req.method==="GET"){
      const recipes=await listRecipes(rid);
      let totalCost=0,totalMargin=0,count=0;
      for(const recipe of recipes){
        let cost=0;
        for(const ing of recipe.ingredients||[]){
          const pq=await service.from("restop_products").select("unit_price,reference_price").eq("restaurant_id",rid).eq("id",ing.produit_id).maybeSingle();
          if(pq.data)cost+=Number(ing.quantite||0)*Number(pq.data.reference_price??pq.data.unit_price??0);
        }
        const price=Number(recipe.prix_vente||0);
        const coeff=cost>0?price/cost:null;
        const margin=price>0?(price-cost)/price*100:0;
        if(!c.demo)await service.from("restop_recipes").update({material_cost:cost,actual_coefficient:coeff}).eq("id",recipe.id);
        totalCost+=cost; totalMargin+=margin; count++;
      }
      return json({success:true,recettes_calculees:count,cout_moyen:count?Number((totalCost/count).toFixed(2)):0,marge_moyenne:count?Number((totalMargin/count).toFixed(1)):0,demo:c.demo});
    }

    if (req.method === "GET") return fail("Cette fonctionnalité n’est pas disponible sur cette version",404);
    return fail("Fonctionnalité avancée en cours de migration depuis Emergent", 501);
  } catch (e) {
    console.error(e);
    return fail(e instanceof Error ? e.message : "Erreur interne", 500);
  }
});

