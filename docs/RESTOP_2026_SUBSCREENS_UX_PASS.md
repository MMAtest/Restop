# Restop — sous-parcours Stocks / Production / Analyses (15 octobre 2026)

Branche : `feat/ocr-bordeaux-20261015` ; ne pas fusionner automatiquement dans `main`.

## Livraison

**Stocks**
- KPI devenus des contrôles accessibles clavier (sauf la valorisation non interactive), filtrage des seuils et DLC, indication de sélection et désactivation des filtres incohérents avec le mode affiché.
- Les fiches critiquées et DLC restent fondées sur les données renvoyées par l'application. La valorisation est **indicative**, issue des quantités et prix renseignés ; aucun chiffre fictif ajouté.
- Navigation principale Stocks & DLC / Répartition / OCR et modes Par produit / Par préparation / Par production alignés sur un composant commun. Recherche et catégorie nommées pour lecteur d'écran, page de résultat réinitialisée à chaque changement de filtre.
- Ancienne couleur verte du bouton Ajuster harmonisée en bordeaux.

**Production**
- Rubriques Produits / Fournisseurs / Préparations / Productions / Archives, avec Grilles et Historique uniquement pour super_admin : onglets accessibles, sans animation latérale envahissante ; responsive horizontal sur smartphone.
- Présentation des listes, titres, champs de recherche, badges et états vides harmonisée avec la charte bordeaux/ivoire, sans changer les opérations de création/édition/archivage.
- Avertissement toujours visible pour la génération automatique de préparations : l'opération **peut remplacer et supprimer les préparations existantes**. La confirmation backend/frontend préexistante reste obligatoire. Ne pas déclencher sur de vraies données sans sauvegarde.

**Ventes & analyses**
- Sous-navigation normalisée Ventes / Alertes / Coûts / Rentabilité / Prévisionnel.
- Sous-écrans de coûts, rentabilité et capacité plus lisibles : recherche de production, rappel de provenance du calcul, signalement des fiches incomplètes, absence de marge inventée si la recette n'est pas associée à la vente.
- Les estimations ne comprennent pas les charges fixes, et les capacités des recettes partageant les stocks ne sont pas cumulables.

## Vérifications

- `CI=true yarn test --watchAll=false --runInBand` : **44/44 tests React** ; ajout de `ModuleTabs`, `StockKpiBar`, `OperationalAnalytics`.
- `CI=true yarn build` : **compilation réussie après les derniers correctifs**. Les avertissements de maintenance CRA/CRACO subsistent.
- Chrome réel avec API et session **fictives**, desktop 1440x900 et mobile 390x844 : navigation Stocks, seuils, remise à zéro, modes de stocks, Production Préparations/Productions, analyses Coûts, recherche et aucun débordement horizontal global ni erreur JS (**rejoués après le dernier build** ; pas de connexion à un backend client).

## Hors périmètre actuel / contraintes de mise en production

- L'application comporte encore un `App.js` historique très volumineux ; ses modales de Production/Stocks, certains vieux tableaux et boutons emoji restent à reprendre. La refonte de ce tour ne constitue **pas** une migration de stack ni un audit complet d'accessibilité WCAG.
- L'auto-génération des préparations est une opération destructive ; son endpoint nécessite une politique de sauvegarde et de restauration documentée avant usage client.
- Autorisations de toutes les API, isolation multi-restaurants, migrations comptes et tests réels de l'OCR sur factures anonymisées restent obligatoires avant fusion en production.
- Conserver la production inchangée, prévisualiser dans la branche Vercel protégée.

- Test supplémentaire `/demo` avec Chrome desktop et mobile : wizard trois étapes, action de fin, pas d’appel API ni erreurs JS.
