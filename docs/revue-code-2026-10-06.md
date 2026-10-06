# Restop — revue et correctifs du 6 octobre 2026

La revue porte sur le frontend effectivement compilé et l’API Deno Supabase effectivement déployée. Le serveur Python historique ne sert pas l’application en production. Les fichiers `.bak`, `.broken` et `temp_content.jsx` non importés ne font pas partie du bundle actif.

## Défauts corrigés

- Page blanche sur **Productions** : les catégories renvoyées en tableau étaient traitées comme un objet. Normalisation des deux contrats.
- Page blanche sur **Nouveau produit** : unités absentes ou contrat incorrect. Liste standard disponible côté serveur et valeur de secours côté client.
- Champs nullables de préparations et décimaux renvoyés en chaînes : édition et formatage sécurisés.
- Session locale JSON corrompue : démarrage protégé et nettoyage de la session invalide.
- Suppression du remplacement global de `window.fetch`. Les pages passent par un client explicite avec authentification et délai maximal.
- Barrière React contre les erreurs de rendu inattendues, avec possibilité de recharger l’espace.
- Recettes chargées mais absentes de la liste filtrée : synchronisation des filtres et des données.
- Création après édition : réinitialisation de l’identité et du formulaire pour éviter une mise à jour involontaire.
- Missions masquées par une différence de contrat tableau/objet : normalisation des missions attribuées et créées.
- Alertes de stocks critiques masquées : prise en charge du tableau retourné par l’API.
- Détails des lots, produits regroupés, unités et découpes : routes et contrats ajoutés.
- Calculs de coûts, marges et prévisionnel fondés sur des valeurs fixes : remplacement par les stocks, recettes et ventes disponibles. Les données insuffisantes sont indiquées. La marge matière n’est pas présentée comme un bénéfice net ou un ROI.
- Commandes automatiques utilisant des fournisseurs et produits fictifs : calcul réel, conversion des unités compatibles, agrégation des ingrédients partagés avant déduction du stock, regroupement par fournisseur réel.
- Changement de fournisseur : panier vidé et réponses tardives ignorées. Modification du choix des recettes : suggestions invalidées.
- Quantités invalides de commandes refusées. Totaux calculés par le serveur et produits/fournisseurs vérifiés dans le restaurant courant.
- Montant et statut des commandes : utilisation de `total_amount`, `status` et `order_date`.
- Faux succès PDF/email/validation : exports CSV utilisables et enregistrement réel des suggestions. Aucun email annoncé envoyé sans service d’envoi.
- Export des rapports Z et libellés/quantités : actions branchées et champs compatibles.
- Suppression dans les grilles : type de ressource issu de la ligne concernée, indépendant de la dernière sélection.
- Conflit de thèmes AG Grid : thème legacy explicite.
- Faux mot de passe partagé affiché pour chaque collaborateur : supprimé. Les mots de passe existants ne sont jamais récupérés.
- Droits d’administration et mutations contrôlés côté serveur ; validation de mission par un responsable, employés limités à leurs missions attribuées.
- Création/édition des collaborateurs réels implémentées côté serveur, avec contrôle des rôles et du restaurant. Aucun compte réel créé ou supprimé pendant la vérification.
- Coûts fournisseurs : lecture et sauvegarde, y compris la remise à zéro ; erreurs de sauvegarde non dissimulées.
- Recettes : POST et PUT transactionnels. Un ingrédient refusé annule la sauvegarde complète.
- Stock : mouvement et quantité du produit modifiés dans une seule transaction avec verrouillage de ligne ; stock insuffisant refusé.
- Import facture : transaction complète et verrouillage du document. Une facture déjà intégrée n’ajoute pas à nouveau le stock. Le prix corrigé dans la validation est utilisé.
- Archives/restauration : transaction, conservation des ingrédients de recette et contrôle du restaurant.
- Routes GET inconnues : erreur explicite au lieu d’un tableau vide donnant une impression de succès.

## Vérification

- `cd frontend && npm test -- --watchAll=false --runInBand` : **15 tests réussis**.
- `cd frontend && npm run lint` : aucune erreur sur le code actif pour les identifiants inconnus, clés dupliquées et chaînes optionnelles dangereuses.
- `cd frontend && npm run build` : compilation de production réussie.
- `node backend/deployed/tests/routes.cjs` : **10 contrôles de routes et de droits réussis** sur le vrai fichier serveur avec client de base simulé.
- Tests SQL exécutés dans des transactions annulées : création de recette, refus d’ingrédient étranger sans modification, refus de stock insuffisant sans mouvement, facture importée deux fois sans doublon, archivage/restauration des produits et des recettes sans perte d’ingrédients.
- Contrôles HTTP de l’API déployée : unités, formes de découpe, catégories, regroupement des produits, archives et détail des lots.

Les tests SQL ne laissent pas de commandes, de comptes ou de modifications de stock de test en production. Le parcours interactif est vérifié dans l’espace de démonstration sans valider de commandes réelles.

## Limites fonctionnelles explicites

Le moteur OCR externe et l’envoi d’emails fournisseurs nécessitent encore une configuration de service. Les écrans avancés hérités qui ne disposent pas d’une route serveur ne doivent pas annoncer un succès : l’API renvoie une indisponibilité explicite. Les ingrédients de recette issus de préparations sont refusés tant que leur persistance n’est pas prise en charge par le schéma actuel. La capacité de chaque recette est calculée séparément ; le calcul de commande, lui, additionne les ingrédients communs.

Ces vérifications établissent les correctifs ci-dessus. Elles ne constituent pas une garantie d’absence absolue de bugs sur toutes les données et intégrations possibles. L’ancienne chaîne Create React App reste un chantier de maintenance distinct.
