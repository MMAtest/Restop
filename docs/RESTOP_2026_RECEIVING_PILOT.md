# Restop — réception fournisseur intelligente, pilote tenant-v2

**Statut : prototype de préproduction uniquement. `main` et la production sont inchangés.** Branche `feat/restop-tenant-receiving-20261016`, empilée sur les quatre précédentes PR de Restop.

## Parcours réel implémenté

1. Une commande d'achat **interne** est créée dans le pilote multi-restaurants (`/api/tenant/purchase-orders`). Son état initial est `draft`. Aucune commande externe n'est envoyée au fournisseur.
2. La direction approuve le brouillon par `POST /api/tenant/purchase-orders/{id}/approve`. Cela ne garantit pas une transmission au fournisseur : l'état devient `approved` interne uniquement.
3. À la livraison, le responsable saisit les références du **bon de livraison** et de la **facture contrôlée par un humain**, la quantité reçue, la quantité facturée et le prix unitaire facturé pour chaque produit.
4. `POST /api/tenant/purchase-orders/{id}/receipts/preview` calcule sans aucune écriture Mongo : quantités restantes par référence, différences quantité reçue/facturée, différence prix unitaire, lignes absentes, montants facturés. L'établissement de référence et la propriété des produits viennent exclusivement de la session serveur.
5. Une livraison partielle, une différence de prix ou de quantité, ou une ligne manquante exige **une case d'acceptation explicite et un motif de 8 caractères minimum**. Une surlivraison supérieure au reliquat n'est jamais autorisée dans ce pilote, même avec justification.
6. `POST /api/tenant/purchase-orders/{id}/receipts/confirm` recalcule les écarts **en transaction** avec la version la plus récente de la commande. Seule cette route effectue les écritures : chaque stock, chacun des mouvements d'audit, l'évolution du reliquat de commande (`receiving` / `received`) et le document de réception. Si une seule écriture échoue, MongoDB annule toute la transaction.
7. Chaque réception utilise une clé d'idempotence par restaurant, et une facture fournisseur ne peut être réceptionnée deux fois avec une autre clé. Une reprise après timeout peut consulter `GET /api/tenant/receipts/by-key/{key}` avant un nouvel envoi, pour éviter les doublons.

## API et collections

- `backend/tenant_receiving_api.py` : nouveau routeur sous `/api/tenant` ; **monté uniquement lorsque `RESTOP_ENABLE_TENANT_V2=1`**.
- Collections isolées existantes : `tenant_purchase_orders`, `tenant_products`, `tenant_stocks`, `tenant_stock_movements`.
- Nouvelle collection `tenant_receipts` avec contraintes composées `(restaurant_id, id)` et `(restaurant_id, supplier_id, invoice_reference)` ; identifiants internes de mouvements déterministes à partir de la réception et du produit.
- Montants en **centimes entiers**, quantités en **milliunités entières**. Aucun calcul monétaire flottant utilisé dans le rapprochement.
- API 401 sans session, 403 pour rôle non autorisé, 404 sur référence étrangère ou absente, 409 sur statut, reliquat ou double facture, 422 sur données invalides. Les champs clients de type `restaurant_id` ne sont jamais acceptés.

## Interface de pilotage

- `frontend/src/components/restop/TenantReceivingWizard.jsx` : sélection de brouillon/commande approuvée, approbation de direction, saisie contrôlée, détail des écarts, justification, dernière confirmation d'une écriture irréversible et récapitulatif de la réception.
- Accessible depuis `Stocks → Réceptions · pilote` **uniquement si `REACT_APP_ENABLE_TENANT_V2=true` est renseigné dans le build frontend**, à un rôle autorisé. L'API doit **également** être activée explicitement par `RESTOP_ENABLE_TENANT_V2=1`. Les deux flags sont absents par défaut.
- **Il n'existe pas encore de création de brouillon de commande pilotée depuis cette fenêtre** : les brouillons du pilote sont créés dans son API dédiée. Les anciennes commandes historiques ne sont pas accessibles à la réception multi-tenant.
- Le résultat du contrôle OCR est actuellement **saisi après vérification humaine** (`invoice_source: human_verified`) : cela n'implique **pas** que l'ancien OCR Restop est désormais isolé, ni que des images/PDF sont lus automatiquement par ce nouveau module. Un connecteur documentaire tenant-scopé, OCR et fichier de preuve devront être développés avant commercialisation.

## Tests et preuves

La commande suivante utilise Docker, un MongoDB 7 à replica set isolé et des bases aléatoires qui sont supprimées, sans port exposé ni connexion à un restaurant réel :

```bash
bash scripts/test-restop-tenant-mongo.sh
```

Les scénarios du pilote vérifient : un brouillon ne peut être réceptionné avant l'approbation de direction, pas de lecture/écriture entre restaurant A et B, contrôles de rôle, preview sans écriture, livraison partielle, écarts tarifaires ou quantités facturées, refus de confirmation sans justification, refus de surlivraison, idempotence, unicité facture par fournisseur/resto, stock incrémenté seulement après validation, commande soldée, panne volontaire après la première écriture de stock et confirmation concurrente sans doublons. Les tests existants Stocks/Recettes/Achats/Rapports Z restent actifs.

## QA réellement passée sur la branche de développement

- **12/12 tests FastAPI + MongoDB replica set** avec deux restaurants fictifs, dont quatre nouveaux scénarios de réception : rôles et approbation, écarts livrés/facturés, confirmation partielle et finale, replay sans double stock, refus facture doublonnée, panne injectée après écriture de stock (rollback), et confirmations concurrentes.
- **25/25 tests backend historiques ciblés** et **4/4 contrôles structurels supplémentaires** pour le module de réception.
- **51/51 tests React** (49 tests existants plus deux du wizard), compilation frontend avec `REACT_APP_ENABLE_TENANT_V2=true` réussie.
- Chrome réel **1440×900 et 390×844** avec API et session entièrement simulées (`frontend/e2e/tenant-receiving-smoke.cjs`) : sélection d'une commande, calcul de prévisualisation, étape de confirmation explicite, une seule écriture simulée, aucun débordement horizontal global ni erreur JS.
- Les conteneurs Docker et bases `restop_tenant_qa_*` sont supprimés automatiquement. Aucun accès client ou production n'est utilisé.
- Les avertissements techniques historiques CRA/Babel/Browserslist demeurent, sans empêcher la compilation.

## Restant indispensable avant production

- OCR réel tenant-scopé avec preuve documentaire PDF/image par établissement, extraction avec provenance ligne par ligne et correction humaine liée au document immuable.
- Rapprochement de plusieurs factures à une commande et plusieurs commandes à une facture ; TVA, avoirs, colisage, unités fournisseurs différentes des unités de stock, DLC/numéros de lot et livraisons multi-sites.
- Contrôles d'accès fins des chefs et réceptionnaires, circuit approbation/remboursement, preuve d'acceptation d'un écart sensible, gestion de prix fournisseur mis à jour, pièces comptables et exports.
- Résilience à forte concurrence et aux pannes réseau ambiguës, sauvegardes/restauration testées sur les données réelles, migration de l'ancienne base, sandbox multi-comptes, Safari/iOS et audit WCAG complet.

**Ne pas activer les flags tenant-v2 sur une instance client et ne pas fusionner vers `main` sans les gates précédentes.**
