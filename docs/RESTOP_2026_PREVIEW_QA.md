# Restop 2026 — préproduction et recette visuelle

15 octobre 2026. Cette note concerne la branche `feat/ocr-bordeaux-20261015` et **ne valide pas la fusion sur `main`**.

## Constat et correctifs

- Le bouton public « Découvrir la démo » appelait `/api/auth/demo`, route absente du backend examiné. Il navigue désormais vers `/demo`, **une expérience entièrement statique et fictive**, sans compte utilisateur, requête API ou écriture en base.
- `/demo` affiche un accueil de restaurant, des alertes d'exemple, les stocks fictifs et un bouton **Tester le wizard OCR**. Le wizard réutilise le composant de production avec `previewData` : toute confirmation se termine en simulation locale (pas de fichier téléchargé, pas de service OCR/IA, pas de requête réseau).
- La vue de test ouvre le wizard dans une superposition en pleine fenêtre ; ce CSS manquait au premier essai Chrome et a été corrigé avant validation. Contrôles desktop 1440×900 et mobile 390×844 : étape 1/2/3, confirmation, message de réussite, pas de débordement horizontal ni d'erreurs JavaScript.
- Le frontend interroge `/api/auth/session`, alors que le backend ne proposait que `/auth/session/{session_id}`. Une route backend sécurisée compatible avec `Authorization: Bearer` a été ajoutée. L'ancienne route contenant le jeton dans l'URL répond désormais 410 ; la déconnexion passe le jeton dans l'en-tête, pas l'URL. Durée absolue des sessions : 12 heures.
- Les boutons de stock dans la démo renvoient aux stocks fictifs et non au wizard ; les boutons facture ouvrent le wizard.

## Tests et reproductibilité

- `cd frontend && CI=true yarn build && CI=true yarn test --watchAll=false --runInBand` : tests d'interface incluant un test de simulation sans API.
- `cd backend && python3 -m unittest test_auth_guard test_invoice_guard test_invoice_reservation test_invoice_transaction test_ocr_route_security -v` : tests ciblés backend (mock / structures). Voir l'autre document QA pour le test Docker sur MongoDB réel.
- Test de navigateur optionnel `frontend/e2e/demo-smoke.cjs` : installer localement `playwright-core` comme dépendance de test, compiler et servir l'app avec fallback SPA, lancer `RESTOP_PREVIEW_URL=http://127.0.0.1:4173 node e2e/demo-smoke.cjs`. Nécessite un binaire Chrome local ou `CHROME_EXECUTABLE`.

## Risques non résolus

- L'application authentifiée n'est **pas** sécurisée intégralement. Ne pas ouvrir de vraies données client en preview, ne pas fusionner avant audit de l'ensemble des routes / autorisations / isolation multi-tenant.
- L'expérience `/demo` est une simulation explicite : elle ne garantit pas que le backend OCR et toutes les chaînes de stock fonctionnent sur production.
- La production et la branche principale restent intactes. Prévisualiser seulement les URLs Vercel de la branche, éventuellement protégées par connexion Vercel.
- CRA/CRACO affiche encore des avertissements de maintenance ; migration à prioriser après stabilisation du backend.
