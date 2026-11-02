# E-Facture DIGIGROUPE — prévalidation hors ligne (19 octobre 2026)

## Statut
Prototype backend **sur branche de travail**, pas un produit de facturation légalement connecté.
Zéro appel externe, zéro fournisseur facturant à l'usage, zéro émission et zéro e-reporting.
Tiime reste le prestataire préféré pour DIGIGROUPE, mais **aucun accès partenaire ni API de production n'a été configuré**.

## Contrat commun
Les deux dépôts possèdent une **copie à l'identique** de `einvoice-contract.mjs`.
Version `digigroupe.einvoice.draft.v1` (remplacer les copies par un paquet versionné commun avant la généralisation).

Payload JSON :
```json
{
  "documentType": "invoice",
  "number": "F-2026-001",
  "issueDate": "2026-10-19",
  "currency": "EUR",
  "seller": {"name": "Prestataire", "siret": "12345678901234"},
  "buyer": {"name": "Client", "siret": "98765432109876"},
  "lines": [{"description": "Service", "quantity": 1, "unitPriceExclTax": "100.00", "vatRate": 20}]
}
```
Les numéros SIRET de l'exemple sont fictifs. Ce contrôle de présence/format n'est pas une validation de l'existence légale ou de la TVA.

## Business OS — CRM Cloudflare
- `GET /e-invoice/capabilities`
- `POST /e-invoice/preview`
- Bearer `CRM_API_SECRET` **et** session individuelle `X-Business-Session` obligatoires.
- Compte `admin` exclusivement ; comptes commerciaux interdits.
- Aucun enregistrement D1/R2 : calcul uniquement, retourne HTTP 422 en cas d'anomalie.

## RESTOP — Supabase Edge
- `GET /api/e-invoice/capabilities`
- `POST /api/e-invoice/preview`
- `POST /api/e-invoice/preview-supplier` avec `{"documentId":"uuid","buyer":{"name":"...","siret":"..."}}`
- Session RESTOP nécessaire et rôle `patron`, `super_admin` ou `gerant`.
- Un OCR fournisseur est lu dans `restop_documents` avec filtre obligatoire `restaurant_id`. Aucune pièce jointe n'est transmise et aucune facture n'est créée.
- Les factures OCR peuvent ne contenir ni SIRET ni TVA par ligne. Dans ce cas la réponse **422** pointe les lacunes : ne jamais compléter avec des valeurs inventées.

## Ce que le module ne fait PAS
- Ni génération Factur-X, ni UBL/CII, ni dépôt auprès d'une plateforme agréée.
- Ni réception depuis Tiime, ni émission de facture, ni automatisation en production.
- Pas de contrôle complet fiscal/réglementaire : acomptes, autoliquidation, exonérations, arrondis multi-taux, conditions de paiement, annuaire, e-reporting, vérification de SIRET réel et statut de conformité.
- Aucune donnée réelle ne doit être considérée conforme à partir de cette prévalidation seule.

## Activation future de l'automatisation
1. Recevoir les spécifications officielles et autorisations Tiime pour un intégrateur (OAuth multi-entreprises, lecture/écriture, webhooks, coûts, limites).
2. Ajouter secrets par tenant côté serveur, chiffrement, RLS/permissions, idempotence, file d'attente, gestion des doublons et audit immuable.
3. Générer et valider réglementairement les documents avec une bibliothèque certifiée/testée ; couvrir le e-reporting Restop.
4. Tester en sandbox uniquement après confirmation d'absence de frais à l'usage.
5. Obtenir validation explicite avant **toute** émission réelle ou activation d'API payantes.

## Tests
- `node --test cloudflare/crm-worker/tests/einvoice.integration.test.mjs` dans Business.
- `node --test backend/deployed/tests/einvoice.contract.test.mjs` et `node backend/deployed/tests/routes.cjs` dans Restop.
- Après consolidation de la branche et avant toute mise en production, lancer la suite globale et les tests UI/rôles définis par AGENTS.md.
