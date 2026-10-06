# API de production Restop

`index.ts` est la source de la fonction Supabase `restop-api`, récupérée depuis la version 12 puis corrigée et déployée en version 13.

L’authentification est implémentée dans la fonction. La configuration existante `verify_jwt=false` est conservée, car elle utilise aussi le jeton public de démonstration et les routes de connexion. Cela ne dispense pas les routes métier de leurs contrôles de session, de rôle et de restaurant.

Les fonctions transactionnelles se trouvent dans `../../supabase/migrations`. Elles sont exécutables uniquement par `service_role` et appelées après validation côté Edge API.

Contrôle des routes : `node backend/deployed/tests/routes.cjs` depuis la racine du dépôt. Le test simule le client Supabase ; il ne modifie pas la production.
