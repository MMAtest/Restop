# ✅ Checklist Pré-Déploiement

## Fichiers à Vérifier

### Backend
- [ ] `parsers_optimized.py` (nouveau)
- [ ] `google-vision-credentials.json`
- [ ] `requirements.txt` (emergentintegrations inclus)
- [ ] `.env` (avec EMERGENT_LLM_KEY)

### Frontend  
- [ ] `src/components/InvoiceValidationModal.jsx`
- [ ] `src/components/Pagination.jsx` (nouveau)
- [ ] `src/App.css` (classes pagination)
- [ ] `.env` (REACT_APP_BACKEND_URL correcte)

## Variables d'Environnement Production

```bash
# Backend
EMERGENT_LLM_KEY=sk-emergent-bCdC6A668C0A00cC12
GOOGLE_APPLICATION_CREDENTIALS=/app/backend/google-vision-credentials.json
MONGO_URL=[URL MongoDB production]
DB_NAME=[nom de la base production]

# Frontend
REACT_APP_BACKEND_URL=https://digigroupe.com
WDS_SOCKET_PORT=443
```

## Prêt pour Déploiement
Tous les problèmes SSR (window.innerWidth) corrigés ✅
