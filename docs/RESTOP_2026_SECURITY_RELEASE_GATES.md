# Restop — portes de validation avant toute fusion et mise en production

Date : 15 octobre 2026. Cette branche est un chantier **non déployé**. Ne pas utiliser les résultats de tests unitaires comme preuve d'intégration MongoDB ou de conformité.

## Livré sur la branche

- Vérification bcrypt au login (plus de mot de passe universel).
- Mise à jour et création des mots de passe avec bcrypt, minimum 12 caractères.
- Contrôles session côté serveur pour les quatre endpoints d'administration utilisateurs et la confirmation d'import OCR ; rôles interrogés dans la base, pas dans la requête.
- Le semis de démonstration à la création d'une base vide devient opt-in et limité aux bases dont le nom contient `demo`.
- L'ancienne création d'un administrateur avec mot de passe public et connu est remplacée par les variables `RESTOP_BOOTSTRAP_ADMIN_EMAIL` et `RESTOP_BOOTSTRAP_ADMIN_PASSWORD` (minimum 12 caractères) dans le parcours de migration. **Ne pas déposer ces valeurs dans un dépôt.**
- Analyse advisory des totaux HT/TTC et des lignes ; les alertes exigent confirmation humaine avant intégration.
- Réservation MongoDB conditionnelle du document : une seule requête peut déclencher l'import d'un document.
- Empreinte fournisseur + numéro de facture réservée avec clé `_id` unique pour les doublons entre documents ; normalisation des accents et séparateurs.
- Incrément atomique `$inc` des stocks existants ; vérifications avant import des références fournisseur/produit.
- En cas d'échec possiblement partiel, statut `import_incomplet` et **interdiction de réimporter automatiquement**.

## Limites bloquantes

1. **Authentification / autorisation insuffisantes globalement.** Seules quelques routes critiques sont protégées sur cette branche. Faire un inventaire et sécuriser **tous** les endpoints de lecture/écriture, JWT/session expiration, droits métier, limites de débit, CORS, cookies et audit. Aucune revendication « sécurisé » en production avant audit.
2. **Base multi-établissements non isolée.** Inspecter chaque requête métier pour le filtrage par établissement et vérifier les séparations en base par tests négatifs. Les empreintes globales peuvent heurter des fournisseurs d'établissements différents quand le document ne dispose pas de `restaurant_id`.
3. **Imports Mongo multi-collections pas transactionnels.** La réservation évite les doubles imports concurrents d'un même document ; en cas de panne réseau ou insertion partielle, des stocks/produits/lots peuvent être écrits avant échec. Migrer vers une transaction MongoDB sur replica set, avec index uniques, ou workflow robuste d'événements compensables avant activation réelle.
4. **Comptes hérités de démo invalides.** Le login bcrypt refuse les champs `password_hash` tels que `hashed_password123`. Faire une migration de mots de passe sécurisée (réinitialisation individuelle ou via l'admin **déjà authentifié**), tester chaque rôle et révoquer les anciennes sessions. Ne jamais préserver le mot de passe partagé.
5. **Démonstration publique.** La landing appelle `/api/auth/demo`, mais aucun endpoint de démo isolée n'a été identifié dans cette version. Isoler une base de démonstration avec quotas et réinitialisation, ou corriger la promesse avant publication.
6. **Vérification exhaustive OCR/TVA à faire.** Tester tarifs HT/TTC, remises, consignes, acomptes, retours, plusieurs taux de TVA, prix au kilo/conditionnement, factures multiples et photos dégradées. Les audits actuels sont des avertissements, pas un moteur comptable.
7. **Sécurité des fichiers.** Vérifier scan anti-malware, redaction et accès aux originaux, stockage chiffré, règles de durée de conservation, export/suppression RGPD, limites pages/images.
8. **Pile technique obsolescente.** CRA/CRACO affiche des avertissements de maintenance. Planifier migration évaluée vers Vite avec mesure de bundle et tests avant remplacement.

## Tests exigés avant fusion

- `cd backend && python3 -m unittest test_invoice_guard test_invoice_reservation test_auth_guard -v`
- `cd frontend && CI=true yarn build && CI=true yarn test --watchAll=false --runInBand`
- Intégration Mongo sur copie de données anonymisées : 2 requêtes identiques concurrentes, 2 documents pour le même numéro, panne après chaque étape d'écriture, écriture d'une quantité simultanée sur produit existant et restauration contrôlée.
- QA responsive clavier, mobile, profil patron, gérant, chef, caissier et employé ; aucune modification sans rôle.
- Vérification fonctionnelle de la démonstration et des parcours OCR réels.
- Procédure de migration comptes et sauvegarde préalable, plan de rollback vérifié.

## Priorité

Bloquer la fusion jusqu'à résolution des points 1–4 au minimum. Les changements de login rendent les anciens comptes fictifs intentionnellement inutilisables ; un jeu de tests locaux ne vaut pas validation de l'authentification sur la base déployée.
