# Restop — intégration UI et sécurité (16 octobre 2026)

**Branche de préproduction :** `feat/restop-ui-security-integration-20261016`. Dérivée de `feat/restop-security-review-20261016`, pas de `main`. **Ne pas fusionner directement en production.**

## Travail repris après une interruption du Mac

Les modifications locales et non publiées ont été copiées dans `/tmp/restop-20261016-recovery/` puis conservées dans un `git stash` sur le Mac. Le backend provisoire local n'a pas été superposé à la version relue et testée sur GitHub : la base est la branche de sécurité de la PR #2.

## Interfaces harmonisées

- `FormModal` utilisé pour **Mouvement de préparation**, **Création de mission**, **Validation d'une mercuriale**, **Import OCR**, **Aperçu de document** et **Lots/DLC**, en plus des cinq formulaires de produits, recettes et fournisseurs déjà migrés.
- Titres de dialogue accessibles, focus clavier, sortie Escape, présentation responsive et avertissement des saisies non enregistrées (sauf fenêtre OCR lorsqu'une pièce refusée ne constitue aucune saisie à sauvegarder).
- Mercuriale : avertissement explicite sur la création de produits et obligation de sélectionner un fournisseur et au moins un produit avant validation côté interface.
- OCR : parcours en 3 étapes, contrôle client de la limite de 15 Mio alignée sur l'API, blocage du fichier vide, formats PDF/JPG/PNG/WebP affichés, indication qu'aucune entrée de stock ne se fait sans vérification.
- Lots/DLC : suppression des boutons inertes « Consommer » et « Nouveau lot » ; indications vers les mouvements et réceptions de stock. L'aperçu des documents OCR dispose d'une vraie fenêtre accessible.

## Sécurité de la branche de base

- Dépendances FastAPI de session et de rôle sur **95 routes métier** auparavant accessibles plus largement.
- Contrôles sur les missions et notifications personnelles, rôles de caisse/direction et archivage/restauration des préparations.
- Compte `restaurant_id` bloqué sur les anciennes collections globales jusqu'à l'isolation réelle par établissement. Ce blocage n'est **pas** une authentique partition de données multi-tenant.
- Plan de migration : `docs/RESTOP_2026_TENANT_MIGRATION_PLAN.md`.

## Vérifications réalisées

- **49/49 tests React** (`CI=true yarn test --watchAll=false --runInBand`) ; **25/25 tests backend ciblés** (`python3 -m unittest test_legacy_security test_auth_guard test_invoice_guard test_invoice_reservation test_invoice_transaction test_ocr_route_security -q`).
- **Build CRA/CRACO réussi**, mais les avertissements de maintenance de CRA, Babel et Browserslist persistent.
- **Chrome réel desktop 1440×900 et mobile 390×844, tous scénarios réussis**, avec API totalement fictive : `frontend/e2e/dialogs-smoke.cjs`, `frontend/e2e/ocr-dlc-smoke.cjs`, `frontend/e2e/demo-smoke.cjs`. Tests de refus d’un PDF de plus de 15 Mio, fermeture OCR, ouverture Lots/DLC sans actions factices, création de produit, abandon des saisies, archivage et suppression à confirmation renforcée, navigation du wizard en 3 étapes. Aucun débordement horizontal global ni erreur JS détecté sur ces scénarios.

## Bloquants avant déploiement réel

1. Test des vrais rôles sur une base MongoDB isolée avec deux établissements et un vrai utilisateur de caisse/cuisine. La revue des routes par AST n'est pas suffisante.
2. Isolation de toutes les collections et agrégations par `restaurant_id`, tests de non-divulgation inter-établissements et migration sans perte des données.
3. Test du processus OCR et de la facture fournisseur sur de vrais documents anonymisés (types, TVA, unités, doublons, écritures transactionnelles).
4. Gestion des sauvegardes/rollback et autorisations de suppression/génération automatique, cohérentes avec les privilèges backend.
5. Safari/iOS, lecteurs d'écran, tests WCAG et données très nombreuses dans les tableaux et modales.

**Production inchangée.**
