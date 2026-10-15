# Restop — sortie sécurisée du backend historique

**Statut : plan de migration, non livré en production.** Branche `feat/restop-security-review-20261016`, PR #2 (brouillon), empilée sur PR #1.

## Résultat provisoire

- 95 routes historiques de gestion renforcées par dépendances FastAPI de session et de rôle.
- Revue automatique de **toutes les routes** : chaque endpoint doit maintenant déclarer une dépendance d'authentification via son décorateur ou sa signature. Seuls `POST /auth/login` et l'ancien `GET /auth/session/{session_id}` (qui renvoie toujours HTTP 410) sont volontairement sans contrôle.
- Les comptes comportant `restaurant_id` sont temporairement refusés (HTTP 503) sur les collections encore globales. **Ce blocage protège contre une confusion d'établissements, mais ne constitue pas une isolation multi-tenant.**
- Missions : identité de l'auteur validée côté serveur ; consultation et mise à jour par un employé limitées à ses propres missions ; validation par un responsable autorisé.
- Notifications : consultation et accusé de lecture limités à leur destinataire.
- Archive : préparation supportée à la création et la restauration.
- Rapport Z : création autorisée à la caisse et à la direction ; suppression réservée aux responsables.
- Les tests AST et de fonctions de garde ont été ajoutés à un job GitHub Actions Python 3.11, avec les anciennes régressions d'authentification et de factures.

## Migration nécessaire avant ouverture à plusieurs restaurants

### 1. Tenants et données historiques

Ajouter `restaurant_id` à l'ensemble des données métier : `produits`, `stocks`, `preparations`, `recettes`, `mouvements_stock`, `fournisseurs`, `orders`, `documents_ocr`, `product_batches`, `rapports_z`, `missions`, `notifications`, `archived_items`, prix fournisseurs, mercuriales et tables annexes.

Établir une table d'appartenance compte/restaurant avec statut et rôle explicite. Ne jamais inférer l'établissement d'un document à partir de son nom, de l'adresse IP, du nom fournisseur ou d'un identifiant utilisateur non validé. Les données ambiguës restent **en quarantaine** jusqu'à attribution manuelle.

### 2. Protection de tous les accès

Dans chaque endpoint : résoudre `restaurant_id` depuis la session serveur ; exiger ce champ dans chaque `find`, `find_one`, `update`, `delete`, `aggregate`, `count_documents`, stockage de fichier et calcul statistique.

Les recherches par `id` doivent être **composites** : `{"id": objet_id, "restaurant_id": restaurant_id}`. La même contrainte s'applique aux lots, mouvements, documents OCR, bons de commande, notifications, archives et rapprochements fournisseurs.

Créer les index composites nécessaires, dont les contraintes d'unicité adaptées à l'établissement (`restaurant_id + id`, `restaurant_id + numero_facture + fournisseur` après normalisation). Les agrégations doivent filtrer l'établissement avant les jointures `$lookup`.

### 3. Autorisations par rôle

| Parcours | Employé cuisine | Chef cuisine | Caissier | Gérant | Patron/Admin |
|---|---|---|---|---|---|
| Consulter stocks et recettes | Oui | Oui | Selon besoin | Oui | Oui |
| Ajuster / consommer les stocks | Sur mission autorisée, à définir | Oui | Non | Oui | Oui |
| Importer facture fournisseur | À définir | Oui | Non | Oui | Oui |
| Importer / enregistrer Z caisse | Non | Non | Oui | Oui | Oui |
| Gérer équipe et rôles | Non | Non | Non | À définir | Oui |
| Valider une mission | Non | Oui, selon équipe | Non | Oui | Oui |
| Effacement définitif | Non | Non | Non | Sous contrôle | Oui |

Ce tableau est **proposé pour validation produit**, et non une déclaration de permissions réellement finalisées sur tous les écrans.

### 4. Migration contrôlée

1. Sauvegarder MongoDB et vérifier la restauration sur une base isolée.
2. Générer un rapport pré-migration sans modification (documents sans restaurant, doublons, identifiants divergents et dépendances).
3. Attribuer les documents au bon établissement avec un fichier de correspondance validé.
4. Déployer la double lecture tenant-scopée sur préproduction, puis les écritures scellées par `restaurant_id`.
5. Vérifier l'idempotence et les transactions OCR, archivage/restauration, consommations de lots, rapprochement des factures, missions et clôtures Z.
6. Rejouer les scénarios de rejet croisé A/B en appelant directement l'API avec des sessions de deux établissements distincts.
7. Contrôler le rollback complet avant d'ouvrir le service. Lever les réponses HTTP 503 de protection provisoire **uniquement après ces tests**.

## Critères bloquants

- Échecs de tests d'autorisation 401/403/404 et de séparation tenant A/B.
- Lecture ou écriture transverse possible en utilisant l'identifiant d'un objet appartenant à un autre établissement.
- Opérations de stock sans transaction ni reprise après échec.
- Contrats frontend cassés par changement de rôle, de session ou de format d'erreur.
- Absence de sauvegarde testée, procédure de restauration, traçabilité des imports et confirmation des suppressions.
- Pas de validation des parcours réels (factures anonymisées, licences, utilisateurs tests, Chrome/Safari mobile).

**Ne pas fusionner PR #2 sur `main` ni rendre les anciennes routes disponibles aux comptes tenant-scopés avant cette migration.**
