# Restop — nouveaux workflows isolés par restaurant (pilote, 16 octobre 2026)

**Branche de revue :** `feat/restop-tenant-workflows-20261016`, issue de `feat/restop-ui-security-integration-20261016`. **Ne pas activer en production.**

## Fonctionnalités codées

Un second module d'API FastAPI, `backend/tenant_workflows_api.py`, prolonge le pilote `/api/tenant/` déjà existant. Le montage des routes et les index MongoDB sont intégrés derrière **`RESTOP_ENABLE_TENANT_V2=1`**, donc **désactivés par défaut**. L'interface historique et les anciennes collections restent inchangées.

| Parcours | Routes expérimentales | Collection isolée | Contraintes |
| --- | --- | --- | --- |
| Recettes | `GET /recipes`, `GET /recipes/{id}`, `POST /recipes` | `tenant_recipes` | Produit de même restaurant, quantités strictes, pas d'ingrédient dupliqué, coût matière instantané en centimes, portions déclarées |
| Achats | `GET /purchase-orders`, `GET /purchase-orders/{id}`, `POST /purchase-orders` | `tenant_purchase_orders` | Fournisseur et produits du même restaurant, produits liés au fournisseur, coûts d'achat exprimés en centimes et quantités milliunités |
| Rapports Z | `GET /z-reports`, `GET /z-reports/{id}`, `POST /z-reports` | `tenant_z_reports` | Accès caisse et direction, équilibre espèces + CB + autres = total, référence unique par établissement, rejets 409 si doublon modifié |

**Point essentiel : les commandes sont des brouillons internes (`status: draft`).** La création ne transmet aucune commande à un fournisseur et ne modifie pas automatiquement les stocks. Les rapports Z ne déclenchent aucune déduction de stock automatique.

### Calculs et sécurité

La précision monétaire s'appuie exclusivement sur des **centimes entiers**, des quantités en **milliunités entières**, et le module Python `Decimal` pour les conversions, avec arrondi commercial `ROUND_HALF_UP`. Le coût matière de la recette correspond à un **instantané des tarifs produits au moment de sa création**, et non à un coût automatiquement actualisé ni à une marge nette incluant les charges.

Toutes les créations rejettent les champs supplémentaires, notamment `restaurant_id`, `created_by`, ou un statut de commande imposé par le navigateur. L'authentification et les rôles proviennent de la session persistée côté serveur. L'établissement du client n'est jamais repris depuis l'URL ou le corps HTTP ; toutes les recherches d'objets, relations fournisseur/produit, listes et insertions sont contrôlées par l'identifiant de restaurant de la session. Les identifiants d'objets d'un autre établissement renvoient **404**.

Les chefs, gérants, patrons et administrateurs peuvent gérer recettes et brouillons ; les rapports Z ne sont accessibles qu'aux caissiers, gérants, patrons et administrateurs, selon les rôles actuels du pilote. Aucun endpoint de suppression n'est ouvert dans ce module.

### QA / régression

`backend/test_tenant_workflows_mongo_integration.py` vérifie en HTTP FastAPI sur une vraie base MongoDB 7 temporaire : rôles, sessions, lecture croisée A/B, références externes interdîtes, recette à prix calculé, fournisseur d'une autre entreprise, brouillon interne, incohérence de paiement du Z, idempotence du Z, et plusieurs établissements utilisant la même référence Z sans collision.

La même commande autonome, **sans secret ni volume partagé avec les restaurants**, exécute désormais les tests Stocks + Workflows :

```bash
bash scripts/test-restop-tenant-mongo.sh
```

Le workflow `.github/workflows/restop-tenant-mongo-qa.yml` déclenche cette commande sur les branches/PR de développement concernés. **Vérifier que GitHub Actions marque le job en succès avant de considérer les nouveaux parcours comme validés.**

## Ce qui reste interdit / non terminé

- Pas d'interface commerciale ou de wizard branché à ces routes nouvelles.
- Aucun remplacement de la base historique, aucune migration automatique de documents ni de stock.
- Aucune facture OCR, ligne de réception, rapprochement commande-facture, ticket réel de caisse, ou vente détaillée multi-tenants.
- Aucune autorisation d'émettre une commande externe ni de modifier la comptabilité.
- Pas de politique complète de TVA, d'unités convertibles, de correction/annulation Z, de gestion multi-établissements pour un seul utilisateur, ni de permissions d'équipe fine.
- La suite d'intégration ne simule pas une charge concurrente élevée et n'est pas un audit de sécurité tiers.

**La production, la branche `main` et les données utilisateurs restent inchangées.** La PR est destinée uniquement à la revue de code et aux essais sur MongoDB jetable avant de poursuivre la migration du SaaS.
