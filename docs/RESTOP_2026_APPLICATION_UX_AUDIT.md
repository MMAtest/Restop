# Restop 2026 — revue UI/UX transversale

Date : 15 octobre 2026 · branche `feat/ocr-bordeaux-20261015` · statut : préproduction, non fusionnée.

## Périmètre parcouru

- **Navigation et structure** : accueil, Stocks, Achats, Production, Ventes/analyses, Équipe, Fournisseurs, sous-onglets OCR, mobile et rôles.
- **Pages métier** : PurchaseOrderPage, AdvancedStockPage, AnalyticsPage, UserManagementPage, DataGridsPage, HistoriqueZPage, grilles AG Grid et composants de navigation.
- **Parcours critique** : import OCR, validation guidée, messages d'erreur, contrôle de la session, circulation entre modules.
- **Précédemment traité** : dashboard/Overview, priorités opérationnelles, page de démo isolée, wizard facture OCR.

## Défauts identifiés et traitements réalisés

| Défaut identifié | Intervention | Test |
|---|---|---|
| Style hétérogène entre cockpit et pages internes | Fichier `application-system.css` avec design system commun, surfaces, titres, formulaires, alertes, tables, responsive, states et hiérarchie | Build React et tests de régression |
| Barre latérale non structurée et page difficile à trouver | Groupement Pilotage / Opérations / Analyse & équipe, recherche accessible Ctrl/Cmd K, sous-rubriques et droits selon rôle, navigation mobile | Tests dédiés + Chrome simulé desktop/mobile |
| Résultat d'une action affiché dans un `alert()` navigateur | Composant `ActionNotice` et messages persistants pour Achats, Grilles, Équipe et Stocks avancés | Tests de régression existants |
| Rapports Z en pseudo-table et détails en popup | Vue liste accessible, véritables métriques, détail en panneau latéral, états chargement/vide/erreur et export conservé | Nouveaux tests `HistoriqueZPage.test.jsx` |
| Boutons « Traitement Auto » simulant une tâche et « Vider l'historique » contraire aux règles du backend | Actions retirées des deux anciens espaces OCR ; texte explicite indiquant la validation humaine | Tests d'App |
| Reprise de session authentifiée `axios` incohérente | Rétablissement de l'en-tête bearer lors de reprise de session et base d'API commune sans `/undefined/api`; `apiFetch` ne transmet pas le bearer à un tiers | Tests `api.session.test.js`, mock Chrome |
| Tableau utilisateur avec colonne Mot de passe inutile | Colonne supprimée, sans exposer les secrets | Tests de gestion des utilisateurs |
| Grilles AG Grid peu adaptées à la charte, focus clavier supprimé | Thème bordeaux/ivoire et focus des cellules rétabli | Build + tests |
| Commande fournisseur : onglets au texte noir sur rouge, fournisseur sélectionné seulement à la souris | Onglets avec états sélectionnés, pictos cohérents, fournisseur accessible par bouton, navigation sans recharge vers les fournisseurs | Tests Achats ; recette visuelle à finaliser |

## Tests réalisés

- `CI=true yarn test --watchAll=false --runInBand` : **39/39 tests React** après harmonisation et API.
- `CI=true yarn build` : **compilation réussie après le dernier lot Achats** (CRA/CRACO affiche toujours les avertissements de maintenance).
- Chrome headless **réel**, uniquement avec utilisateurs et API simulés en navigateur ; desktop 1440×900 et mobile 390×844 : accueil, Achats, Équipe, recherche rapide, absence d'erreurs JS et de débordement global. Ces données ne proviennent pas d'une base restaurant.
- Les tests de facturation sous Docker (MongoDB replica set isolé) ont été validés lors de la phase précédente ; pas rejoués sur chaque changement purement UX.

## Toujours à faire : approfondissement écran par écran

Le travail de cette PR harmonise les écrans réellement existants, mais le vieux code métier garde des composants très longs, des emojis, styles inline et quelques popups dans App.js et dans les sous-parcours de Production/Ventes. Cela mérite une passe de refactorisation par modules avec captures sur un vrai compte de préproduction. En particulier :

1. Inventaire, mouvements, lots, DLC : clarifier les tableaux des sous-onglets, hiérarchie des actions et zones tactiles.
2. Production (recettes et préparations) : extraire les formulaires de `App.js`, restructurer leurs validations et confirmations.
3. Ventes/analyses : réorganiser les KPI très nombreux, filtrage temporel et provenance des chiffres.
4. Achat : confirmation de commande et traitements fournisseurs sur une base de test ; remplacer les dernières alertes de `App.js` après audit fonctionnel.
5. Équipe : rendre les rôles et la réinitialisation des comptes plus pédagogiques ; migration/auth encore incomplète.
6. Test de lecteur d'écran, Safari iOS, tablettes, clavier uniquement, contraste WCAG et longs libellés/données réalistes.

**Ne pas fusionner en production** : contrôle d'accès backend global, isolation multi-restaurants et migration des comptes sont encore des prérequis indépendants du design.

## Skills

Skills installés précédemment sur le Mac dans `~/.agents/skills` pour Codex : `superdesign`, `design-taste-frontend`, `redesign-existing-projects`. Aucun skill supplémentaire nécessaire pour cette passe ; outils en place = React, Phosphor Icons, Motion et AG Grid.
