# 🚀 Guide de Déploiement - Production

## ⚠️ Problème Actuel
L'application fonctionne en développement/preview mais a des erreurs réseau en production.

## 🔍 Causes Probables

### 1. Variables d'Environnement Manquantes

**Fichiers à vérifier en production** :
- `/app/backend/.env`

**Variables critiques** :
```bash
MONGO_URL="mongodb://localhost:27017"
GOOGLE_APPLICATION_CREDENTIALS=/app/backend/google-vision-credentials.json
EMERGENT_LLM_KEY=sk-emergent-bCdC6A668C0A00cC12
```

**⚠️ IMPORTANT** : Ces variables doivent être configurées dans les **variables d'environnement de production** Kubernetes/Emergent, pas seulement dans le fichier `.env` local.

---

### 2. Fichiers Manquants en Production

**Fichiers critiques** :
- ✅ `/app/backend/google-vision-credentials.json` (credentials Google Vision)
- ✅ `/app/backend/parsers_optimized.py` (nouveau fichier créé aujourd'hui)
- ✅ `/app/backend/requirements.txt` (doit inclure emergentintegrations)

**Vérifiez** que ces fichiers sont bien **committés dans Git** et déployés.

---

### 3. Dependencies Python Non Installées

**Package critique** :
```bash
emergentintegrations --extra-index-url https://d33sy5i8bnduwe.cloudfront.net/simple/
```

**Vérification** :
- Le fichier `requirements.txt` doit inclure toutes les dépendances
- L'index `https://d33sy5i8bnduwe.cloudfront.net/simple/` doit être accessible en production

---

### 4. URLs et Configuration Réseau

**Variables frontend** :
- `REACT_APP_BACKEND_URL` doit pointer vers l'URL de production correcte

**Actuellement configuré** :
```
REACT_APP_BACKEND_URL=https://ocr-joker-1.preview.emergentagent.com
```

**Pour production** :
```
REACT_APP_BACKEND_URL=https://digigroupe.com
```

---

## ✅ Checklist de Déploiement

### Étape 1 : Vérifier les Fichiers Git

```bash
# Vérifier que tous les nouveaux fichiers sont committés
git status

# Fichiers qui DOIVENT être committés :
# - backend/parsers_optimized.py
# - backend/requirements.txt (mis à jour)
# - backend/google-vision-credentials.json
# - frontend/src/components/InvoiceValidationModal.jsx
# - frontend/src/components/Pagination.jsx
```

### Étape 2 : Variables d'Environnement Production

**Sur la plateforme Emergent** :
1. Aller dans Settings → Environment Variables
2. Ajouter/Vérifier :
   ```
   EMERGENT_LLM_KEY=sk-emergent-bCdC6A668C0A00cC12
   GOOGLE_APPLICATION_CREDENTIALS=/app/backend/google-vision-credentials.json
   MONGO_URL=[URL MongoDB production]
   ```

### Étape 3 : Vérifier requirements.txt

**Doit contenir** :
```
emergentintegrations
google-cloud-vision
google-generativeai
pillow
pandas
rapidfuzz
... (autres dépendances)
```

### Étape 4 : Index PyPI Custom

**Vérifier que l'index est accessible** :
```bash
pip install emergentintegrations --extra-index-url https://d33sy5i8bnduwe.cloudfront.net/simple/
```

**Configuration pip** (si nécessaire) :
Créer `/app/backend/pip.conf` :
```ini
[global]
extra-index-url = https://d33sy5i8bnduwe.cloudfront.net/simple/
```

---

## 🎯 Différence Preview vs. Production

**Preview (Cet environnement agent)** :
- URL : `https://ocr-joker-1.preview.emergentagent.com`
- Base de données : MongoDB local (ephemeral)
- Variables .env : Fichier local
- ✅ **Tout fonctionne**

**Production (Déployée)** :
- URL : `https://digigroupe.com` (ou autre)
- Base de données : MongoDB production (persistant)
- Variables .env : Kubernetes ConfigMap/Secrets
- ❌ **Erreurs réseau**

---

## 🔧 Actions Immédiates

**1. Sur Emergent Platform** :
- Vérifiez que `EMERGENT_LLM_KEY` est dans les variables d'environnement
- Vérifiez que le fichier `google-vision-credentials.json` est déployé

**2. Vérifiez les Logs de Production** :
- Regardez les logs backend de production
- Cherchez les erreurs d'import ou de module manquant

**3. Testez les Endpoints** :
```bash
# Tester depuis production
curl -X POST https://digigroupe.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"patron_test","password":"password123"}'
```

---

## 📋 Résumé

**Votre environnement de développement (preview) est INDÉPENDANT de la production.**

Quand vous "déployez", vous devez :
1. ✅ Committer tous les fichiers dans Git
2. ✅ Configurer les variables d'environnement en production
3. ✅ Vérifier que les dependencies sont installées
4. ✅ S'assurer que les fichiers credentials sont présents

**L'environnement agent (preview) n'affecte PAS la production.**

---

## 💡 Recommandation

Utilisez la fonctionnalité **"Deploy"** ou **"Push to GitHub"** d'Emergent pour déployer vos changements, puis configurez les variables d'environnement dans l'interface de la plateforme.

Besoin d'aide pour configurer le déploiement ? Demandez-moi des instructions spécifiques.
