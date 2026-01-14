# 🧪 Guide de Test - Joker IA Gemini 2.0 Flash

## Objectif
Tester le nouveau système "Joker IA" avec la facture **SAS THE PRIMEUR**

---

## 📋 Étapes de Test

### 1. Connexion à l'Application
- URL : `https://ocr-manager.preview.emergentagent.com`
- Identifiants : `patron_test` / `password123`

### 2. Navigation vers OCR
- Cliquer sur l'onglet **PRODUCTION** (bottom nav)
- Sélectionner l'onglet **📱 Factures**

### 3. Upload de la Facture
- Cliquer sur **"📁 Importer une Facture"**
- Sélectionner la photo : `IMG-20251222-WA0001.jpg` (SAS THE PRIMEUR)
- Observer :
  - ✅ Compression automatique (console log)
  - ✅ Upload en cours
  - ✅ Barre de progression immédiate

### 4. Vérifier l'Analyse Initiale
- La facture apparaît dans l'historique
- Cliquer sur **"✅ Valider"**
- Observer :
  - Fournisseur détecté : "SAS THE PRIMEUR"
  - Produits listés (peut-être 4-6 sur 8)
  - **Taux de matching probablement faible (30-50%)**

### 5. Activation du Joker IA 🎯

**Scénario A : Suggestion Automatique**
Si moins de 70% des produits sont matchés, vous devriez voir :
```
┌────────────────────────────────────────────────────┐
│ 🤖 Amélioration IA disponible                      │
│ Beaucoup de produits non reconnus. L'analyse IA    │
│ peut améliorer la précision jusqu'à 90%.           │
│                                                     │
│ [🚀 Améliorer avec IA (~0.003€)]  [✕]             │
└────────────────────────────────────────────────────┘
```

**Cliquer sur "🚀 Améliorer avec IA"**

**Scénario B : Pas de suggestion automatique**
Si le taux est >70%, pas de suggestion. Mais vous pouvez quand même tester en :
- Fermant la modal
- Modifiant le code pour forcer l'affichage
- Ou en testant directement l'endpoint backend (voir section "Test Backend Direct" ci-dessous)

### 6. Observer le Résultat Gemini

**Pendant le traitement (2-3s)** :
- Barre de progression animée visible
- Message : "Analyse intelligente des produits..."

**Après le traitement** :
```
✨ Analysé avec Gemini 2.0 Flash • Précision améliorée
```

**Alert box** :
```
🤖 Analyse IA terminée !

✅ 7/8 produits automatiquement reconnus
💰 Coût estimé : ~0.003€
```

**Vérifier dans l'interface** :
- ✅ 8 produits listés (AIL PELE, CIBOULETTE, FRAMBOISE, etc.)
- ✅ Quantités correctes (10.0, 6.0, etc.)
- ✅ Unités correctes (KG, PIECE, BUNCH)
- ✅ Prix unitaires exacts (5.50€, 0.80€, 2.99€, etc.)
- ✅ Lots auto-générés si DLC présentes

### 7. Validation et Import
- Vérifier/ajuster les données
- Cliquer **"✅ Valider et Intégrer au Stock"**
- Vérifier que le stock est mis à jour

---

## 🔬 Test Backend Direct (Alternative)

Si vous voulez tester l'endpoint Gemini directement sans passer par l'interface :

```bash
# 1. Uploader la facture
curl -X POST "https://ocr-manager.preview.emergentagent.com/api/ocr/upload-document" \
  -F "file=@IMG-20251222-WA0001.jpg" \
  -F "document_type=facture_fournisseur"

# Récupérer le document_id de la réponse

# 2. Analyser avec Gemini (remplacer DOCUMENT_ID)
curl -X POST "https://ocr-manager.preview.emergentagent.com/api/ocr/analyze-facture-ai/DOCUMENT_ID"

# 3. Observer le résultat JSON
```

---

## ✅ Résultats Attendus

### Avec Parser GENERIC (Sans Gemini)
- Fournisseur : "SAS THE PRIMEUR" ✅
- Produits détectés : ~4-5 sur 8 (50-60%)
- Problèmes attendus :
  - Lignes administratives non filtrées
  - Quantités parfois mal interprétées
  - Unités "BUNCH" peut-être non reconnues
  - Prix unitaires vs. totaux confondus

### Avec Joker IA Gemini
- Fournisseur : "SAS THE PRIMEUR" ✅
- Produits détectés : 7-8 sur 8 (90-100%) ⭐
- Avantages :
  - ✅ Toutes les lignes de bruit filtrées
  - ✅ Quantités exactes (10.0, 6.0, 1.0, etc.)
  - ✅ Unités variées reconnues (KG, PIECE, BUNCH)
  - ✅ Prix unitaires correctement extraits
  - ✅ Structure de tableau comprise

---

## 📊 Comparaison Visuelle

**AVANT (Parser GENERIC)** :
```
🏢 SAS THE PRIMEUR
📅 22/12/2025 • BL-1049

Produits détectés : 4/8 (50%)
❌ AIL PELE - Quantité : ??? - Prix : ???
❌ Lignes de bruit incluses (adresse, capital social)
⚠️ BUNCH non reconnu comme unité
```

**APRÈS (Gemini)** :
```
🏢 SAS THE PRIMEUR
📅 2025-12-22 • BL-1049
✨ Analysé avec Gemini 2.0 Flash

Produits détectés : 8/8 (100%)
✅ AIL PELE - 10.0 KG - 5.50€
✅ CIBOULETTE - 10.0 PIECE - 0.80€
✅ FRAMBOISE - 6.0 PIECE - 2.99€
✅ POUSSE ÉPINARD - 1.0 KG - 7.50€
✅ CITRON VERT - 5.0 KG - 2.99€
✅ BASILIC POT - 2.0 PIECE - 2.40€
✅ THYM - 2.0 BUNCH - 0.80€
✅ MENTHE - 1.0 BUNCH - 0.60€
```

---

## 🎯 Points de Validation

**Checklist** :
- [ ] Barre de chargement visible au premier plan (z-index 9999)
- [ ] Compression d'image effectuée (console log)
- [ ] Suggestion Joker IA affichée (banner jaune)
- [ ] Bouton "Améliorer avec IA" fonctionnel
- [ ] Traitement Gemini en 2-3s
- [ ] Badge "✨ Analysé avec Gemini" affiché
- [ ] 8 produits détectés correctement
- [ ] Quantités et unités exactes
- [ ] Pagination mobile sans débordement
- [ ] Boutons Aperçu/Valider bien positionnés

---

## 💡 Recommandations Post-Test

**Si le test est concluant** :
1. Activer automatiquement pour tous les nouveaux fournisseurs
2. Ajouter un toggle dans les paramètres : "Toujours utiliser IA avancée"
3. Dashboard analytics : économies de temps mesurées

**Si des ajustements sont nécessaires** :
- Modifier le seuil de suggestion (70% → 60% ou 80%)
- Ajuster le prompt Gemini pour mieux coller à vos factures
- Ajouter des règles spécifiques (ex: toujours détecter DLC)

---

**Testez maintenant et partagez-moi vos observations !** 🚀
