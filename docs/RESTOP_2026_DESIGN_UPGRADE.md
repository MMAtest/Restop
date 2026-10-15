# Restop — refonte cockpit v2 (15 octobre 2026)

## Diagnostic de départ

- Tableau de stocks dense et peu lisible, sans jauges ni filtres opérationnels ; lignes trop serrées sur téléphone.
- Deux compteurs de même poids, aucune distinction entre suivi, urgence et documents.
- Brief opérationnel placé loin des données et présenté comme une succession de cartes sans hiérarchie.
- Effets de transition inexistants ; peu de retour visuel au changement de filtre.

## Direction livrée sur la branche

- **Précision calme** : fond ivoire clair, encre bordeaux, accents rouges réservés aux décisions et états à risque. Pas de graphiques fictifs ni d'estimations financières non étayées.
- **Typographie** : Inter pour le suivi dense, échelle 10–55px selon le rôle, chiffres à chasse tabulaire, titres resserrés ; convention colorimétrique conservée (bordeaux #681b32 et rouge #a82e4b).
- **Cockpit** : titre éditorial, CTA import clair, métriques réelles dont une dominante, inventaire filtrable (surveillance / tous / ruptures), jauges quantité/seuil et panneau radar adjacent sur grand écran.
- **Mobile** : métriques adaptées en 2 + 1, lignes de stocks transformées en fiches avec cibles tactiles, panneau radar après l'inventaire, aucun défilement horizontal global.
- **Motion raisonnable** : `motion/react` avec `AnimatedNumber` inspiré du composant MIT d'ibelick/motion-primitives, transitions de filtres avec `layoutId`, entrées de cartes/listes, `useReducedMotion` et repli CSS `prefers-reduced-motion`.
- **États** : chargement, erreur et inventaire vide ; actions pointant vers les écrans métier et non des liens fictifs.

## Références / droits

- Motion Primitives : https://github.com/ibelick/motion-primitives — MIT (adaptation de l'idée d'AnimatedNumber ; code réécrit en JS avec formatage FR et compatibilité React 19/CRA). Licence MIT : https://github.com/ibelick/motion-primitives/blob/main/LICENCE.md.
- Motion for React : https://motion.dev/docs/react — dépendance front `motion`.
- Skills installés **globalement sur le Mac pour Codex** via `npx skills add -g -a codex -y` : `design-taste-frontend` et `redesign-existing-projects` (Leonxlnx/taste-skill), `superdesign` (superdesigndev/superdesign-skill). Superdesign nécessitera son CLI/login pour l'atelier canvas ; aucune utilisation du service externe ou de crédits n'est revendiquée.

## Vérifications

- `CI=true yarn build` : compilation réussie.
- `CI=true yarn test --watchAll=false --runInBand` : 32/32 (incluant trois nouveaux tests dashboard).
- `python3 -m unittest test_auth_guard test_invoice_guard test_invoice_reservation test_invoice_transaction test_ocr_route_security` : 18/18.
- Script navigateur `frontend/e2e/demo-smoke.cjs` : démarrage de `/demo`, changement d'étapes du wizard, absence d'appels API et d'erreurs JS, viewport mobile 390px et desktop 1440px, sans débordement global.
- Captures Chrome revues localement : nouvelle grille de métriques, tableaux avec filtres, badges et jauges, version mobile en cartes.

## Limites / ne pas annoncer une commercialisation sûre

- La refonte porte prioritairement sur l'écran **Vue d'ensemble / Démo**, pas encore sur toutes les pages métier (achats, recettes, ventes, équipe).
- Le backend n'est pas totalement isolé par établissement ni audité pour tous les endpoints : maintenir la PR en brouillon et ne pas fusionner sur production.
- Les couleurs et certains parcours anciens restent à harmoniser hors cockpit ; CRA/CRACO est vieillissant.
- Des essais réels sur Safari/iOS, tablette et avec des stocks clients anonymisés restent nécessaires avant validation UI complète.
