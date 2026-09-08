# 📔 Carnet de Passation — ResTop / La Table d'Augustine

**Dernière mise à jour** : 5 mai 2026
**Client** : Skander Boughanmi (Digigroupe / La Table d'Augustine, Marseille)
**Domaine production** : https://digigroupe.com
**Plateforme d'hébergement** : Emergent (préview + production)
**Langue de travail** : Français

---

## 1. 🎯 Vision produit

### Contexte
**ResTop** est une application SaaS de gestion complète pour restaurant, développée pour le restaurant "La Table d'Augustine" à Marseille. L'objectif est de digitaliser toute la chaîne de valeur :
- Gestion des stocks matières premières
- Fiches techniques recettes
- Rentabilité en temps réel (food cost)
- OCR des factures fournisseurs
- **Décrément stock automatique** basé sur les ventes de caisse (L'Addition)
- Missions journalières (Plat du jour, Menu enfant)
- Multi-rôles (Super Admin, Patron, Chef, Sous-Chef, Employé, Caisse)

### Ambition long terme
- Multi-établissements (le nom "Digigroupe" laisse penser à une déclinaison SaaS multi-restos)
- Connexion API L'Addition (caisse) pour temps réel
- Connexion API fournisseurs (commandes automatiques)
- Intelligence métier (alertes DLC, inflation prix, prévisionnel)

---

## 2. 🏗️ Architecture technique

### Stack

| Couche | Technologie | Notes |
|---|---|---|
| Frontend | React 18 + Tailwind + CSS variables premium | Fichier monolithique `App.js` (>9500 lignes) |
| Backend | FastAPI + Motor (MongoDB async) + Pydantic | Fichier monolithique `server.py` (>10000 lignes) |
| BDD | MongoDB (via Emergent-managed instance) | Preview et Prod = **BDD séparées** ⚠️ |
| PWA | Service Worker v1.2.0 | No-cache API + auto-update SW |
| IA | Gemini 2.5 Flash via emergentintegrations | Emergent LLM Key (Universal Key) |
| OCR | Google Vision API (base) + Gemini (Joker IA avancé) | Google Vision = clé utilisateur, Gemini = Universal |

### Structure des dossiers
```
/app/
├── backend/
│   ├── server.py                        # Monolithe principal (10000+ lignes)
│   ├── sales_import.py                  # Import ventes L'Addition + décrément stock
│   ├── daily_specials.py                # Mission Plat du jour / Menu enfant
│   ├── config_keys.py                   # EMERGENT_LLM_KEY loader
│   ├── parsers_optimized.py             # Parsers OCR par fournisseur
│   ├── import_boissons.py               # Script import 178 boissons carte L'Addition
│   ├── import_data.py                   # Script import mercuriale + menu original
│   ├── import_recettes_mappings.py      # Pré-mappings caisse -> recettes (fuzzy)
│   ├── add_missing_recipes.py           # 43 recettes ajoutées post-import
│   ├── create_missing_raw_materials.py  # 48 MP pour fiches techniques IA
│   ├── generate_recipe_ingredients.py   # Génération IA fiches techniques (Gemini)
│   ├── audit_recipe_costs.py            # Détection coûts aberrants
│   ├── export_ai_recipes.py             # Export JSON fiches IA pour migration prod
│   ├── setup_special_mappings.py        # Mappings spéciaux (St George, Plat du jour...)
│   ├── fix_import.py                    # Cleanup doublons
│   ├── requirements.txt
│   ├── .env                             # MONGO_URL, DB_NAME, EMERGENT_LLM_KEY
│   └── data/
│       ├── mercuriale.xlsx              # Import initial fournisseurs + produits
│       ├── menu.xlsx                    # 33 recettes du menu original
│       ├── carte_caisse.xlsx            # Carte L'Addition (produits + boissons + plats)
│       └── ai_recipe_ingredients.json   # 43 fiches techniques IA (portable prod)
└── frontend/
    ├── src/
    │   ├── App.js                       # UI + logique monolithique
    │   ├── App.css & index.css          # Design premium (vert forêt/doré)
    │   └── components/
    │       ├── RoleBasedDashboard.jsx   # Dashboard multi-rôles
    │       ├── DateRangePicker.jsx
    │       ├── SalesUploader.jsx        # Upload ventes L'Addition
    │       └── DailySpecialMission.jsx  # Mission chef Plat du jour
    ├── public/
    │   ├── sw.js                        # Service Worker v1.2.0
    │   └── manifest.json                # PWA
    └── .env                             # REACT_APP_BACKEND_URL
```

### Environnements

| | Preview (dev) | Production (live) |
|---|---|---|
| URL | https://ocr-joker-1.preview.emergentagent.com | https://digigroupe.com |
| BDD MongoDB | Instance preview isolée | Instance prod isolée |
| Déploiement | Auto sur commit | Manuel : "Save to Github" + "Deploy" |
| Utilisation | Tests, dev, démos | Utilisée par le client + ses équipes |

⚠️ **RÈGLE CRITIQUE** : preview et prod ont **2 bases MongoDB séparées**. Les changements de données faits en preview ne sont **PAS** automatiquement propagés en prod. C'est la raison d'être du bouton "📦 Migrer Données".

---

## 3. 🔑 Endpoints API critiques

### Administration (Super Admin uniquement)
- `POST /api/admin/migrate-data` — Migration base (mercuriale + menu) idempotente
- `POST /api/admin/migrate-extras` — Migration nouveautés (boissons + 43 recettes + mappings + fiches techniques IA)
- `GET  /api/admin/db-status` — Diagnostic complet BDD (compteurs + samples + fichiers Excel)

### Import ventes L'Addition
- `POST /api/sales/preview` — Parse fichier Excel + preview mapping
- `POST /api/sales/apply` — Applique décrément stock + crée Rapport Z
- `GET  /api/sales/mappings` — Liste des 242 mappings caisse
- `POST /api/sales/mappings` — Sauvegarde d'un mapping manuel
- `DELETE /api/sales/mappings/{caisse_nom}` — Suppression
- `GET  /api/sales/history` — Historique des imports
- `GET  /api/sales/history/{rapport_z_id}` — Détail d'un import

### Mission Plat du jour / Menu enfant
- `GET  /api/daily-specials/today` — Config du jour
- `POST /api/daily-specials/today` — Définir/modifier
- `GET  /api/daily-specials/mission-status/today` — Statut mission (complète ou non)
- `GET  /api/daily-specials/{date}` — Config d'une date passée

### OCR
- `POST /api/ocr/analyze-ticket-z-ai/{id}` — Joker IA Gemini (avancé)
- `POST /api/ocr/analyze-facture` — OCR facture fournisseur
- Autres endpoints classiques Google Vision

### Dashboard
- `GET /api/dashboard/missing-data-alerts` — Produits sans prix, etc.

### CRUD standard
- `/api/produits`, `/api/recettes`, `/api/preparations`, `/api/fournisseurs`, `/api/users`, etc.

---

## 4. 📊 État de la base de données (Preview - 5 mai 2026)

| Collection | Nombre | Note |
|---|---|---|
| `produits` | **493** | dont 182 boissons (bar) + 48 MP pour fiches techniques |
| `recettes` | **76** | 100% avec fiche technique complète |
| `preparations` | 12 | Base propre après cleanup 337 auto-générées |
| `fournisseurs` | 25 | Mercuriale + fournisseurs boissons |
| `caisse_mappings` | **242** | 55 recettes + 182 produits directs + 3 ignore + 2 daily_special |
| `daily_specials` | 0 | Aucune mission complétée en preview |
| `sales_imports_log` | 0 | Aucun import réel testé (juste des simulations) |
| `rapports_z` | 0 | idem |
| `users` | 7 | Super Admin + Patron + Chef + Sous-Chef + Employé + Caisse + démo |

**Food cost moyen** : 25.6% (excellent — cible resto = 25-35%)

---

## 5. ✅ Ce qui a été fait (chronologie)

### Session Février 2026 (agent précédent)
- MVP initial : gestion produits/recettes/stocks
- OCR factures avec Google Vision + Joker IA Gemini
- Multi-rôles + permissions
- Import mercuriale (160 produits) + menu.xlsx (33 recettes)
- Cleanup 337 préparations auto-générées absurdes
- Design UX/UI Premium (vert forêt/doré)
- Endpoint `/api/admin/migrate-data` + bouton Super Admin

### Session Avril 2026 (current)

#### Fix critiques
- **Bug URL `/api/api/`** : 3 boutons Super Admin appelaient un endpoint inexistant → 404 silencieux. Corrigé.
- **Bug cache PWA** : Service Worker mettait les API en cache sans expiration → vieilles données affichées. Refait en v1.2.0 mode Network-Only pour APIs + auto-update SW.
- **Endpoint diagnostic** : Nouveau `/api/admin/db-status` + bouton UI "🩺 Diagnostic Base".

#### Import données L'Addition
- **178 boissons** importées (`import_boissons.py`) avec 17 sous-catégories miroir (Vin verre R/B/R, Bouteille, Bière pression 25/50cl, Cocktails, Spiritueux, Sodas, Cafés, Jus PAGO)
- **43 nouvelles recettes** (`add_missing_recipes.py`) : poissons à la pesée, fromages, viandes, entrées, desserts
- **48 matières premières** (`create_missing_raw_materials.py`) pour supporter les fiches techniques
- **235 mappings caisse → BDD** pré-créés (fuzzy + pattern poisson au poids)
- **8 mappings spéciaux** : St George → produit, Supp écrasé → recette, Caïpi/Moscow/Carafe eau → ignore, Plat du jour + Menu enfant → daily_special
- **43 fiches techniques IA** générées via Gemini 2.5 Flash (coût ~1€ Universal Key)
- **3 coûts aberrants corrigés** : Risotto St-Jacques 7133€→9.75€, Magret 1339€→4.33€, Escargots 82€→2.21€ (unités kg/g mal interprétées par IA)

#### Système Import Ventes
- Module `sales_import.py` : 6 endpoints + moteur décrément stock
- Composant `SalesUploader.jsx` intégré dans la page **Tickets Z existante** (pas de nouvelle page)
- **Support de 2 formats L'Addition** :
  - "sales-analysis" (1 sheet)
  - "Products" (multi-sheets, plus riche : catégorie, ID, TAG, etc.)
- Détection automatique du format
- **Conversion auto poids → services** : "Loup entier 2400g" → 2 services, "St Pierre 2900g" → 3 services
- Matching multi-niveaux : exact → pattern poisson → pattern viande au poids → fuzzy keywords
- **94-96% de match automatique** sur les fichiers testés
- Mémoire des mappings : un mapping fait 1 fois = mémorisé pour toujours

#### Mission Plat du jour / Menu enfant
- Module `daily_specials.py` : collection + endpoints
- Composant `DailySpecialMission.jsx` : bandeau orange sur dashboard chef/patron/super_admin
- Modal : sélection recette existante OU création à la volée
- **Résolution dynamique dans sales_import** : "Plat du jour" et "Menu enfant" du fichier de ventes sont automatiquement liés à la recette du chef

#### Migration Prod enrichie
- `POST /api/admin/migrate-extras` créé + intégré au bouton "📦 Migrer Données"
- **Migre en 1 clic** : 178 boissons + 43 recettes + 48 MP + 235 mappings + 43 fiches techniques IA
- **Fichier JSON portable** : `ai_recipe_ingredients.json` embarqué avec le code = pas besoin de re-payer l'IA en prod
- Idempotent : peut être relancé sans risque de doublons

---

## 6. 🚧 Ce qui reste à faire

### 🔴 P0 (bloquant / urgent)

| Task | Détails |
|---|---|
| **Déployer + Migrer en prod** | Le client doit cliquer "📦 Migrer Données" en prod pour recevoir toutes les nouveautés (boissons, 43 recettes, mappings, fiches IA) |
| **Tester upload sales-analysis en prod** | Valider que le décrément stock fonctionne en conditions réelles avec un vrai fichier client |
| **Recette borderline à corriger** | "Homard bleu (entrée)" : food cost 137% (32€/24€) — l'IA a mis trop de homard, à ajuster manuellement |

### 🟠 P1 (important)

| Task | Effort | Notes |
|---|---|---|
| **Connexion API L'Addition** | 3-5 jours | En attente clé API + doc (client a fait la demande support). Passer de l'upload manuel à la sync auto toutes les 15 min |
| **Optimisation 7 parsers OCR restants** | 2-3 jours | METRO, Mammafiore, etc. dans `parsers_optimized.py`. Réduit le recours au Joker IA payant |
| **Intelligence Métier** | 5 jours | Suggestion DLC auto par produit + alertes inflation prix + prévisionnel |
| **Commandes fournisseurs par email PDF** | 3-4 jours | Génération PDF + envoi email auto (Resend). Marche avec 100% des fournisseurs sans intégration IT |
| **Compléter mercuriales manquantes** | Client | Frais, surgelés, primeur (51 produits sans prix restent) |
| **Notification push mission chef** | 30 min | Rappel automatique 9h du matin si mission Plat du jour non complétée |

### 🟡 P2 (backlog moyen terme)

| Task | Effort | Notes |
|---|---|---|
| **Dashboard Analyse Marge** | 4-6h | Food cost par recette/catégorie, top/flop rentabilité, alertes >35% |
| **Bannière aide PWA iOS Safari** | 2h | Guide "Ajouter à l'écran d'accueil" |
| **Refactorisation `App.js`** | 3-5 jours | Fichier de >9500 lignes = risque futur. Split en pages/composants |
| **Refactorisation `server.py`** | 2-3 jours | Idem, split en modules routes/models/services |
| **Backup MongoDB automatique** | 4h | Cron + S3 (Emergent ou externe) |

### 🟢 P3 (long terme / vision)

- Multi-établissements (SaaS pour groupe Digigroupe)
- API commandes fournisseurs (Metro, Pomona, Transgourmet via EDI)
- Intégration plateforme d'agrégation (Choco, Innovorder, Foodmeup)
- App mobile native (React Native ?) au lieu de PWA
- Prévisionnel IA (prédiction ventes selon historique + météo)
- Comparateur prix multi-fournisseurs
- Module RH (planning, pointage)
- Migration OVH (VPS Essential 10€/mois) si le client veut sortir d'Emergent

---

## 7. ⚠️ Points de tension / risques identifiés

### 🔥 Techniques

**1. `App.js` de 9500+ lignes**
- **Risque** : bugs d'affichage difficiles à débugger, temps de chargement, refactor dangereux
- **Historique** : déjà causé 2 régressions de listes vides au démarrage
- **Mitigation** : refactor progressif en P2

**2. `server.py` de 10000+ lignes**
- **Risque** : dette technique, 111 warnings de lint (E701, E722, F841)
- **Mitigation** : nouveaux modules séparés (sales_import, daily_specials) — continuer cette approche

**3. Base MongoDB séparées preview/prod**
- **Risque** : le client oublie de cliquer "Migrer Données" et croit qu'il y a un bug
- **Mitigation** : bouton "🩺 Diagnostic Base" en 1 clic + message explicite dans la doc utilisateur

**4. Fiches techniques IA à unités incohérentes**
- **Risque** : Gemini peut proposer 200g de truffe à 950€/kg = 190€. Auto-audit détecte mais ne corrige pas toujours.
- **Mitigation** : script `audit_recipe_costs.py` + revue humaine des recettes >1.5× prix vente

**5. Emergent LLM Key budget**
- **Risque** : si trop d'utilisation IA (OCR Joker + génération fiches), budget dépassé
- **Mitigation actuelle** : limite quotidienne (`api_usage` collection) + fiches IA générées **une fois** puis exportées en JSON portable
- **Suivre** : profil → Manage plan → Universal Key balance

### 💰 Business / opérationnel

**6. Dépendance à Emergent (plateforme)**
- **Risque** : lock-in, coût mensuel, downtime éventuel, changement de politique
- **Alternative envisagée** : migration OVH VPS (~10€/mois) — kit de déploiement à préparer si décision de migration
- **Actions** : documenter le stack pour rendre portable (Docker Compose)

**7. Google Vision API (clé utilisateur)**
- **Risque** : facturation directe Google, quotas, coupure si limite dépassée
- **Mitigation** : Joker IA Gemini en fallback (via Universal Key)

**8. L'Addition API en attente**
- **Risque** : le support L'Addition met du temps à répondre (fait courant chez les éditeurs POS)
- **Mitigation** : le système d'upload manuel Excel est prêt à basculer en API dès réception (code réutilisable à ~90%)

**9. Fournisseurs sans API**
- **Risque** : la moitié des fournisseurs sont artisanaux (Boucherie Coquières, RM Mar, Mamma Fiore) → jamais d'intégration technique
- **Mitigation** : email PDF auto (P1) — 100% des fournisseurs supportent l'email

**10. Multi-établissements = refonte structurelle**
- **Risque** : passer d'1 restaurant à N restaurants demandera un `restaurant_id` sur toutes les collections + isolation des données + permissions par établissement
- **Décision à prendre** : quand le client veut lancer un 2e resto, prévoir 2-3 semaines de refactor

### 🧑‍🍳 Adoption utilisateur

**11. Formation équipe**
- **Risque** : le chef et les serveurs doivent comprendre le flow "Plat du jour → upload sales-analysis → décrément"
- **Mitigation** : bandeau orange visuel + notifications futures + doc utilisateur

**12. Qualité des données saisies**
- **Risque** : si les fiches techniques IA ne sont pas revues par le chef, les coûts matières et food cost seront faux
- **Mitigation** : dashboard analyse marge (P2) qui met en évidence les recettes suspectes

**13. Recettes sans ingrédients = décrément silencieux**
- **Actuel** : 76/76 recettes ont une fiche technique ✅
- **Futur** : les nouvelles recettes créées à la volée (ex: "Plat du jour") sont vides → le décrément ne fera rien, warning mais pas visible

---

## 8. 🔐 Credentials & accès

### Test / Dev
Voir `/app/memory/test_credentials.md`
- Super Admin : `skander_admin` / `password`
- Patron : `patron_test` / `password`

### Production
- URL : https://digigroupe.com
- Comptes créés par le client lui-même (Super Admin puis les autres)

### Clés externes
- **Google Vision API** : clé fournie par le client (dans `.env` prod uniquement)
- **Emergent LLM Key** : géré automatiquement par la plateforme (`EMERGENT_LLM_KEY`)
- **MongoDB** : `MONGO_URL` + `DB_NAME` gérés par Emergent

---

## 9. 📚 Documentation utilisateur clé

### Comment redéployer les changements en prod
1. Preview → tester
2. Chat Emergent → "Save to Github"
3. Chat Emergent → "Deploy"
4. Attendre 2-5 min
5. Aller sur https://digigroupe.com → menu burger ☰ → **📦 Migrer Données (Complète)** (pour appliquer les nouveautés de données)
6. Cliquer **🩺 Diagnostic Base** pour vérifier les compteurs

### Comment uploader les ventes du jour
1. Se connecter en Super Admin (ou rôle avec accès)
2. Bottom nav → **STOCK**
3. Sous-onglet **📱 OCR**
4. Sous-sous-onglet **📊 Tickets Z**
5. Section "Import des ventes journalières"
6. Upload le fichier Excel L'Addition (sales-analysis OU Products)
7. Preview → onglet **✅ Auto-mappés** (rien à faire)
8. Onglet **🟡 À mapper** : dropdown pour chaque nouveau nom (mémorisé pour le futur)
9. Bouton **✅ Appliquer le décrément stock**
10. Alert récap → Rapport Z créé + stocks à jour

### Comment définir le Plat du jour
1. Se connecter en Chef ou Patron
2. Dashboard : bandeau orange en haut
3. Clic sur **⚡ Définir maintenant**
4. Modal → 2 sections (Plat du jour + Menu enfant)
5. Choisir recette existante dans le dropdown OU cliquer "➕ créer une nouvelle recette"
6. Validation → le bandeau passe au vert

---

## 10. 📞 Contact & continuité

**Client principal** : Skander Boughanmi
**Établissement** : La Table d'Augustine, Marseille
**Groupe** : Digigroupe (potentiel multi-établissements à l'avenir)

**Historique jobs Emergent** :
- Job initial : MVP (agent précédent, février 2026)
- Job en cours : Import L'Addition + décrément stock + missions chef (avril-mai 2026)

**Documents attachés** :
- `/app/memory/PRD.md` : Product Requirements complètes
- `/app/memory/test_credentials.md` : Credentials test
- `/app/design_guidelines.md` : Design system Premium (vert forêt/doré)
- `/app/backend/data/*.xlsx` : Fichiers Excel embarqués pour migration
- `/app/backend/data/ai_recipe_ingredients.json` : Fiches techniques IA portables

---

## 11. 🎓 Sagesse accumulée (pour agent suivant)

### À FAIRE
- ✅ Toujours utiliser les scripts Python côté `backend/` pour manipuler la BDD (pas de modifs manuelles dans MongoDB Compass)
- ✅ Rendre chaque migration **idempotente** (upsert, `if not exists`, etc.)
- ✅ Embarquer les fichiers de données dans `/app/backend/data/` (Excel + JSON) — ils sont trackés Git donc partent en prod
- ✅ Fuzzy match pour les noms produits (accents, casse, "œ" vs "oe", "à" vs "a")
- ✅ Documenter dans PRD.md à chaque finish
- ✅ Répondre en français au client

### À NE PAS FAIRE
- ❌ **Ne JAMAIS ré-implémenter l'auto-génération des préparations** (337 entrées absurdes créées, cleanup douloureux)
- ❌ **Ne pas croire aux quantités IA sans vérification** (Gemini confond kg/g souvent)
- ❌ Ne pas ajouter de nouveaux boutons Super Admin sans data-testid + confirmation modale
- ❌ Ne pas modifier `.env` directement (variables protégées)
- ❌ Ne pas oublier que preview ≠ prod pour la BDD MongoDB

### Bugs récurrents à surveiller
1. **Listes vides au démarrage** (bug historique) : quand on fetch les données, penser à initialiser `filteredRecettes`, `filteredProduits`, etc. dans les useEffect
2. **Double `/api/api/`** : `${API}/api/...` alors que `API = ${BACKEND_URL}/api` → toujours écrire `${API}/route` (pas `${API}/api/route`)
3. **Cache PWA** : après update majeure, faire `Ctrl+Shift+R` en dev ou désinstaller/réinstaller la PWA

---

*Fin du carnet de passation — v1.0 - 5 mai 2026*
