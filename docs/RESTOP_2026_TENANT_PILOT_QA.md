# Restop — isolation réelle multi-restaurants : pilote en environnement séparé

Date : 16 octobre 2026. Branche d'intégration de préproduction **uniquement**.

## Architecture livrée

Un pilote d'API sous `/api/tenant/`, **désactivé par défaut**. Les routes ne sont créées que lorsque le serveur reçoit explicitement `RESTOP_ENABLE_TENANT_V2=1`, après audit de son environnement. L'interface web historique n'utilise pas encore ce module.

| Ressource | Collection indépendante | Protection |
| --- | --- | --- |
| Fournisseurs | `tenant_suppliers` | Session vérifiée, filtre `restaurant_id` du profil persistant |
| Produits | `tenant_products` | Même filtre ; référence fournisseur obligatoirement du même restaurant |
| Stocks | `tenant_stocks` | Identifiant déterministe haché par restaurant/produit ; filtre tenant + produit |
| Mouvements | `tenant_stock_movements` | Journal transactionnel, clé d'idempotence propre au restaurant |

Les collections anciennes (`produits`, `stocks`, `fournisseurs`, etc.) ne sont **jamais** utilisées par cette API. Les réponses n'exposent aucune donnée de l'autre établissement, y compris si un appelant dispose de son identifiant de produit. Des `404` identiques sont renvoyés pour une référence étrangère et une référence inexistante. Les champs de type `restaurant_id` injectés dans les requêtes sont refusés (422).

La saisie du stock utilise les **milliunités entières** : 1000 milliunités = 1 unité métier (kg, litre ou pièce déclarée). Les prix d'achat sont en centimes entiers. Cela évite les erreurs d'arrondi flottant ; une politique explicite sur les unités et conversions inter-fournisseurs reste à concevoir. Les ajustements requièrent un motif et une clé d'idempotence.

### Atomicité

Une entrée/sortie de stock passe par une transaction MongoDB englobant la modification de quantité et le mouvement d'audit. Un Mongo standalone refuse l'opération (503) : **aucune écriture non transactionnelle de secours**. Une quantité négative, une clé d'idempotence réutilisée avec un autre contenu ou une modification concurrente incompatible est refusée. Une reprise avec la même clé et le même contenu ne crée pas de second mouvement.

### Contrôles d'accès

- Authentification : fonction réelle `require_active_user` du backend, avec session en base et rôle courant ; pas de confiance dans `X-Role` ou le corps HTTP.
- Lecture : rôles opérationnels autorisés selon le contrat pilote.
- Création fournisseur/produit et ajustements de stocks : direction et chef cuisine seulement.
- Compte sans `restaurant_id` : refus 403. **Pas de fallback vers les anciennes tables partagées.**

## Tests reproductibles, sans données réelles

Sur une machine disposant de Docker :

```bash
bash scripts/test-restop-tenant-mongo.sh
```

Le script crée temporairement un conteneur `mongo:7` avec un replica set local, lance les tests HTTP FastAPI avec de faux comptes Alice/restaurant A et Bob/restaurant B dans un conteneur Python 3.11 éphémère, puis supprime les conteneurs de test même en cas d'échec. Il ne publie **aucun port** ni n'utilise les secrets, bases ou volumes de production. Chaque exécution crée puis supprime une base aléatoire `restop_tenant_qa_*`.

Les scénarios testent : absence de session (401), session expirée et compte désactivé (401), employés et caissiers sans droits d'édition (403), refus d'identifiants d'établissement forgés (422), lectures croisées A/B et écritures croisées (404), fournisseur d'un autre restaurant (404), rejets de stock négatif, idempotence, séparation des journaux et transactions. Une panne volontaire **après la mise à jour du stock et avant l'insertion du mouvement** confirme par inspection Mongo que les deux opérations ont été annulées.

Le job GitHub Actions `restop-tenant-mongo-qa.yml` exécute les mêmes tests sur la pull request avec Docker uniquement, sans donnée ni credential utilisateur.

## Ce qui n'est PAS terminé

Le pilote ne commercialise pas Restop en multi-tenant. Il n'expose que les collections fournisseurs, produits, stocks et mouvements propres au nouveau module ; ni les écrans existants, ni l'OCR, les commandes, les recettes, les missions, les tickets Z, les historiques et analytics n'ont été migrés vers les collections isolées. Les anciennes routes restent **bloquées pour les comptes ayant un `restaurant_id`**. L'activation du module et la migration de vraies données exigent une validation séparée.

Avant publication : isolation de tous les documents et sous-documents liés, plan de migration/rollback et sauvegarde restaurée, gestion de l'appartenance multi-restaurants par utilisateur, contraintes d'unicité métier, taux de TVA et unités des fournisseurs, tests sous charge, test de transaction sur infrastructure cible, audit d'autorisation endpoint par endpoint et QA sur véritables factures anonymisées.

**Ne pas activer `RESTOP_ENABLE_TENANT_V2` sur les environnements utilisés par les clients et ne pas fusionner cette branche dans `main` sans les validations précédentes.**
