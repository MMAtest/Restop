# Restop — formulaires, archivage et effacement sécurisé (15 octobre 2026, branche PR #1)

## Livré

- `FormModal` sert les écrans **Produit / Fournisseur / Mouvement de stock / Préparation / Recette**, sans remplacer la logique de soumission de chacun. Le wrapper gère la dénomination du dialogue, l'association des labels de base aux contrôles, le focus, la sortie clavier Escape, un fond assombri sobre et l'affichage mobile.
- **Garde contre les modifications abandonnées** : lorsqu'un utilisateur a saisi une valeur, Escape, fermer ou cliquer sur le fond affiche « Modifications non enregistrées », puis « Continuer la saisie » ou « Quitter sans enregistrer ».
- `ActionDialog` remplace les boîtes `window.prompt` d'archivage dans Production et Stocks, la restauration et suppression d'archives, et la double confirmation des suppressions irréversibles. Un **motif facultatif** est conservé pour archiver ; il faut saisir **SUPPRIMER** pour effacer définitivement ou **REMPLACER** avant auto-génération destructive des préparations.
- Notifications persistantes `ActionNotice` après les actions migrées ; aucune notification de réussite tant que la réponse serveur n'est pas reçue.
- L'action sur le serveur n'est jamais déclenchée depuis le montage d'un dialogue ou la saisie du mot de confirmation. Elle part seulement après un clic explicite de validation.

## Tests exécutés

- `CI=true yarn test --watchAll=false --runInBand` : **49/49 tests React**, y compris tests spécifiques des dialogues, de l'annulation, du motif, de la confirmation textuelle, des libellés et de la sortie d'un formulaire modifié.
- `CI=true yarn build` : build React réussi. Les avertissements CRA/Babel/Browserslist restent une dette technique.
- Backend Python ciblé `test_auth_guard`, `test_invoice_guard`, `test_invoice_reservation`, `test_invoice_transaction`, `test_ocr_route_security` : **18/18 tests** passés.
- Chrome headless réel 1440x900 et 390x844 sur une SPA locale et **API fictive interceptée** : formulaire Produit, abandon des modifications, archivage Tomates avec motif, effacement d'une préparation et confirmation renforcée, absence d'appel destructif avant validation, aucune erreur JS et pas de débordement horizontal. Le parcours `/demo` et le wizard OCR ont aussi passé leurs tests navigateur.
- Test reproductible : `frontend/e2e/dialogs-smoke.cjs`, après compilation et démarrage du serveur local ; ex. `RESTOP_PREVIEW_URL=http://127.0.0.1:4173 node frontend/e2e/dialogs-smoke.cjs`. Il nécessite `playwright-core` installé pour le test et un Chrome local. **Aucune requête vers un backend client n'est prévue dans le test.**

## Suite / points non validés

- L'ancien `App.js` conserve d'autres `window.confirm`, dont traitement Z, annulation de mercuriale, import catalogue et certains parcours OCR. Ils doivent être repris par catégorie après audit du comportement backend, pas remplacés aveuglément.
- Les modales de missions, OCR, DLC et mercuriales ne sont pas encore toutes harmonisées ; seules les cinq fenêtres de gestion listées plus haut utilisent `FormModal`.
- L'accessibilité lecteur d'écran n'a pas reçu d'audit WCAG complet, et Safari/iOS n'a pas été vérifié.
- La sécurité des routes serveur et l'isolation des données de plusieurs établissements ne sont **pas terminées** : maintenir la PR en brouillon et la production inchangée.
