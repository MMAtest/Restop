# ResTop - PRD (Product Requirements Document)

## Original Problem Statement
Application full-stack de gestion de restaurant (ResTop / La Table d'Augustine) :
- React + FastAPI + MongoDB
- OCR factures (Google Vision + Joker IA Gemini)
- Gestion produits, fournisseurs, recettes, préparations, stock
- Dashboard temps réel, alertes données manquantes
- PWA mobile/iPad
- **NEW** : Import des ventes journalières L'Addition avec décrément stock automatique

## User Personas
- **Super Admin** (skander_admin) : maintenance complète, migration BDD prod, import ventes
- **Patron** (patron_test) : pilotage, missions, validation
- **Chef de Cuisine / Sous-Chef / Caisse** : opérationnels

## Core Requirements (état au 29/04/2026)
- ✅ Picker d'ingrédients avec recherche + filtres
- ✅ UX/UI Premium (vert forêt/doré, responsive)
- ✅ Import Mercuriale + Menu via Excel
- ✅ Migration idempotente vers BDD production
- ✅ Alertes produits sans prix
- ✅ Service Worker v1.2.0 (no-cache pour API)
- ✅ Bouton Diagnostic BDD (Super Admin)
- ✅ **Import ventes L'Addition + décrément stock automatique**

## Implemented this session (29 Apr 2026)

### Bug Fixes critiques
- **FIX `/api/api/`** : 3 boutons super admin appelaient des URLs avec un double `/api/` → 404 silencieux. Corrigé.
- **FIX cache PWA** : Service Worker mettait les API en cache. Refait en v1.2.0 mode Network-Only pour APIs + auto-update du SW.

### Nouvelles features
- **Import boissons** (`backend/import_boissons.py`) : 178 produits, 17 sous-catégories miroir L'Addition.
- **43 recettes manquantes** (`backend/add_missing_recipes.py`) : poissons à la pesée, fromages, viandes, entrées, desserts.
- **Système d'import ventes journalières** (`backend/sales_import.py` + `frontend/src/components/SalesUploader.jsx`) :
  - 5 endpoints `/api/sales/*` (preview, apply, mappings CRUD, history)
  - Matching multi-niveaux : exact → pattern poisson au poids → pattern viande au poids → fuzzy keywords
  - **96-100% des items auto-mappés** (86/89 sur le fichier test)
  - 235 mappings pré-créés
  - Intégré dans la page Tickets Z existante
  - Mémoire des mappings : un mapping fait une fois = mémorisé pour toujours
- **Système Daily Specials** (`backend/daily_specials.py` + `frontend/src/components/DailySpecialMission.jsx`) :
  - Mission obligatoire chef : Plat du jour + Menu enfant à définir chaque jour
  - Bandeau de mission (orange si non défini, vert si complet) en haut du dashboard chef/patron
  - Modal : sélection recette existante OU création à la volée d'une nouvelle recette
  - Endpoints `/api/daily-specials/{today, mission-status, by-date}`
  - **Résolution dynamique dans sales_import** : "Plat du jour" et "Menu enfant" du fichier de ventes sont automatiquement liés à la recette définie ce jour-là, qui est ensuite utilisée pour le décrément stock
- **Mappings spéciaux** (`backend/setup_special_mappings.py`) :
  - "St george 1L" → produit "Eau St George 1L" (créé)
  - "Supp écrasé" → recette "Écrasé de pomme de terre"
  - "Caïpi Passion", "Moscow Mule", "Carafe eau" → ignore
  - "Plat du jour", "Menu enfant" → daily_special

### Endpoints critiques
- `POST /api/admin/migrate-data` : migration idempotente
- `GET /api/admin/db-status` : diagnostic BDD
- `POST /api/sales/preview` : prévisualisation upload ventes
- `POST /api/sales/apply` : application décrément stock
- `GET /api/sales/mappings` / `POST` / `DELETE` : gestion mappings
- `GET /api/sales/history` : historique imports
- `GET /api/daily-specials/today` : config plat du jour / menu enfant
- `POST /api/daily-specials/today` : définir / mettre à jour
- `GET /api/daily-specials/mission-status/today` : statut mission

### Nouvelles collections MongoDB
- `caisse_mappings` : `{caisse_nom, type (recette|produit_direct|ignore|daily_special), cible_id, cible_nom, daily_special_key?, ...}`
- `sales_imports_log` : journal d'audit complet de chaque import
- `daily_specials` : `{date, plat_du_jour, menu_enfant, set_by_user_id, set_by_user_nom, ...}`

## Backlog

### P0
- Tester le flow complet en utilisateur réel (upload sales-analysis du jour)
- Compléter les fiches techniques recettes (ingrédients × quantités) pour que le décrément stock soit effectif

### P1
- Connexion API L'Addition directe (en attente clé API + doc support)
- Optimisation des 7 parsers OCR restants
- Intelligence "Métier" : suggestion DLC + alertes inflation prix
- Compléter la BDD avec les ~45 recettes manquantes identifiées (poissons à la pesée, fromages, etc.)

### P2
- Bannière d'aide PWA pour iOS Safari
- Refactorisation `App.js` (>9000 lignes)

## Tech Stack
- Frontend : React, Tailwind, CSS variables (premium design)
- Backend : FastAPI, Motor (MongoDB async), Pydantic, openpyxl, pandas
- Intégrations : Google Vision API, Gemini 2.0 Flash (via Emergent LLM Key)

## Test Credentials
Voir `/app/memory/test_credentials.md`
