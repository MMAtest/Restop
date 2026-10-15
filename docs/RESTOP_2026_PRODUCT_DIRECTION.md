# Restop 2026 — Décisions produit et feuille de route

Date : 15 octobre 2026. Statut : orientation produit, **pas une liste de fonctionnalités livrées**.

## Positionnement

**Restop — l'assistant de rentabilité pour restaurants indépendants.**

Promesse à éprouver en pilote : transformer une facture fournisseur, un inventaire ou un rapport de caisse Z en **actions quotidiennes vérifiables**, sans obligation d'une API caisse payante. Le bénéfice n'est pas « encore un dashboard », mais « savoir quoi faire avant le service ».

Client prioritaire : restaurant indépendant de 1 à 3 établissements, gérant sans analyste, chef de cuisine et équipe qui saisit les réceptions. Ne pas concurrencer frontalement les ERP multi-sites par un catalogue de fonctions.

## Ce que font déjà les concurrents (sites éditeurs consultés le 15/10/2026)

| Éditeur | Fonctions annoncées | Conséquence Restop |
| --- | --- | --- |
| Komia | Stocks, inventaires, fournisseurs, marges, HACCP, connexion caisse | Ne pas vendre « stocks + commandes » comme innovation. |
| Inpulse | Prévisions / commandes IA, stocks, pilotage des marges multi-sites | Éviter d'imiter la complexité de déploiement des réseaux. |
| MarginEdge | Factures automatisées, coût matière, recettes, rapports, assistant IA | L'OCR seul ne différencie plus ; relier extraction aux décisions. |
| Apicbase | Recettes, inventaires multi-sites, comptage vocal, prévisions, MCP | Miser d'abord sur 1-3 restaurants avant le multi-site avancé. |

Sources : https://www.komia.io/gestion-des-stocks ; https://www.inpulse.ai/ ; https://www.marginedge.com/ ; https://get.apicbase.com/ . Comparaisons des pages publiques, pas tests complets ni audit tarifaire.

## Parcours cible

1. **Capture** — photo, PDF, Factur-X ou facture structurée. Analyse locale prioritaire sur PDF numérique, OCR cloud uniquement quand nécessaire ; retours de confiance par champ et document source conservé.
2. **Contrôle** — fournisseur, TVA/HT/TTC, lignes, conditionnement (colis -> kg), corrections mémorisées et doublons. Les inconnues et erreurs bloquent l'import ; l'humain valide.
3. **Action** — lots/DLC, seuil de réassort, écarts de prix fournisseurs, produits dormants. Chaque carte cite la donnée source et ouvre le bon écran métier.
4. **Boucle hebdomadaire** — rapport Z + achats + stocks comptés -> écarts théorique/réel, marges par recette, pistes de négociation, niveau de confiance.

## P0 — fiabilité et activation, avant vente

- [x] Nouvelle palette bordeaux / rouge / blanc, première passe.
- [x] Protections de base OCR et vérification humaine avant import, sur branche dédiée.
- [x] Brief opérationnel en accueil (DLC, rupture, hausse de prix, factures, stock sans mouvement), sans coût IA additionnel.
- [ ] Imports robustement idempotents, y compris deux imports simultanés ; opérations transactionnelles / reprise sur erreur.
- [ ] Détection inter-document robuste des doublons (normalisation fournisseur / numéro, hash, tolérance OCR), sans faux positifs silencieux.
- [ ] Contrôles fiables HT/TVA/TTC, remises, prix/kg vs prix/colis, unités, poids variable et exceptions fournisseur.
- [ ] Tests d'un jeu de factures réelles anonymisées couvrant 6–7 fournisseurs, y compris multi-pages / mauvaises photos.
- [ ] Politique d'accès et isolation des données par restaurant démontrée par tests ; supprimer les identifiants et données fictives du parcours réel.
- [ ] Tests de compilation, accessibilité mobile et non-régression des rôles avant mise en ligne.

## P1 — avantages commerciaux à faible coût

- **Réception express** : comparer commande, bon livraison, facture, quantité livrée et écarts ; proposer un litige fournisseur documenté, jamais l'envoyer sans accord.
- **Score de fiabilité produit** : correspondances connues ou incertaines, correction réutilisable par fournisseur, journal d'audit.
- **Mon argent à risque** : euros *potentiellement* exposés par variations de prix, pertes ou DLC à partir de quantité et prix disponibles, avec hypothèses explicites (pas d'économie promise).
- **Brief du matin sur téléphone** : les 3 actions les plus urgentes, temps estimé de résolution fondé sur tests utilisateur, statut « vu / traité » journalisé.
- **Inventaire assisté** : smartphone, scan code-barres GS1 lorsque disponible, recherche tolérante, saisie vocale avec confirmation, offline-PWA + synchronisation sécurisée.
- **Tarification adaptée** : zéro intégration obligatoire, coût OCR plafonné et visible ; 1 établissement d'abord, upsell par site.

## P2 — différenciation vérifiable

- **Copilote « Pourquoi ma marge baisse ? »** : requêtes contrôlées sur les données du restaurant avec affichage des sources, calculs explicables et autorisations ; aucun mouvement de stock automatique.
- **Assistant menus** : coût matière réel, rentabilité recette, alternatives fournisseurs disponibles, allergènes et saisonnalité, suggestions validées par chef.
- **Prévision de commande** : commande suggérée selon ventes Z historiques + couvert prévisionnel + stocks réels + DLC, avec niveau de confiance et possibilité de refuser.
- **Réception de facture électronique** : import Factur-X / UBL / CII ou connecteur de plateforme agréée, sans se présenter comme plateforme agréée.
- **Multi-restaurants / reporting** uniquement après test d'isolation des données et de permissions.

## Contexte réglementaire en France

Depuis le 01/09/2026, toutes les entreprises assujetties établies en France doivent pouvoir recevoir les factures électroniques entrant dans le champ de la réforme ; émission obligatoire depuis le 01/09/2026 pour GE/ETI et à partir du 01/09/2027 pour PME/microentreprises. La conformité de Restop **n'est pas établie** : intégration à une plateforme agréée à cadrer et à faire valider. Source officielle : https://entreprendre.service-public.gouv.fr/vosdroits/F23208 .

## Architecture (non décidée / pas migrée)

- Court terme : conserver React + FastAPI + base actuelle pour livrer des parcours testables ; pas de migration massive sans bénéfice utilisateur quantifié.
- Revoir progressivement CRA/CRACO, dépendances et versions prises en charge ; envisager Vite ou Next.js **après** audit des usages SPA, auth et déploiement.
- OCR hybride : PDF texte local, Vision si image ou scan, cache/empreinte des analyses, file de tâches avec délais et reprises, coût/taux d'erreur observables. Vérification par champ.
- Données : journal d'événements (documents, approbations, prix, lots, réceptions), audit, sauvegardes, séparation stricte par établissement, consentement et suppression RGPD.
- IA : explicabilité et sources ; estimation de coût par appel ; appels cloud optionnels, pas de dépendance forcée au LLM.

## Critères de validation pilotes (hypothèses à mesurer)

- 3 à 5 restaurants pilotes, au moins 100 factures anonymisées variées.
- Mesurer correction ligne à ligne, taux de doublons détectés, montant d'écarts valides, temps de traitement d'une facture, faux positifs, adoption hebdomadaire des actions.
- Objectif de conception (non mesuré) : une facture simple validée en moins de 2 minutes après extraction et une décision utile identifiée en moins de 30 secondes à l'ouverture.
- Aucun chiffre d'économie ou de conformité annoncé avant audit.

## Actions interdites sans validation explicite

Import automatique en stock, envoi de commande ou litige, modification de fiche allergène, déclassement d'un produit, facture transmise comptablement, calcul de « gains réalisés » sans preuve.
