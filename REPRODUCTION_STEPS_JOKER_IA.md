# 🔍 Steps to Reproduce - Joker IA Gemini Issue

## Environment Information

**Preview URL** (Works): `https://receipt-scanner-64.preview.emergentagent.com`
**Production URL** (Error): `https://digigroupe.com`

**API Key Used**: `sk-emergent-fA3AdBcC44aFb58664`
**Model**: Gemini 2.5 Flash
**Feature**: AI-powered invoice analysis

---

## Reproduction Steps

### 1. Access the Application

**Preview Environment**:
```
URL: https://receipt-scanner-64.preview.emergentagent.com
Login: patron_test
Password: password123
```

**Production Environment**:
```
URL: https://digigroupe.com
Login: patron_test  
Password: password123
```

### 2. Navigate to Invoice Section

1. Click on bottom navigation: **PRODUCTION**
2. Click on tab: **🧾 Factures**
3. You should see the invoices list

### 3. Upload a Test Invoice

**Option A - Use Existing**:
- Look for invoice "IMG-20251222-WA0001.jpg" (SAS THE PRIMEUR)
- Or any other invoice in the list

**Option B - Upload New**:
- Click "📁 Importer une Facture"
- Select the test invoice file
- Wait for upload to complete

### 4. Open Validation Modal

1. Find the invoice in the list under "⏳ Factures À Valider" section
2. Click the green **"✅ Valider"** button
3. A full-screen modal should open with:
   - Header: "📝 Validation Facture"
   - Supplier dropdown
   - Date and invoice number fields
   - List of detected products

### 5. Trigger Gemini AI Analysis

**Look for the AI button**:
- Either: Yellow banner at top (if <80% products matched)
  ```
  🤖 Amélioration IA disponible
  [🚀 Améliorer avec IA (~0.003€)]
  ```
- Or: Green button at bottom
  ```
  [🤖 Améliorer avec Gemini IA]
  ```

**Click the button**

### 6. Observe the Result

**Expected in Preview** ✅:
```
Loading modal appears with progress bar
→ "Analyse intelligente des produits..."
→ 2-3 seconds
→ Success alert:
   "🤖 Analyse IA terminée !
    ✅ 8/8 produits automatiquement reconnus
    💰 Coût estimé : ~0.003€"
→ Modal updates with Gemini results
→ Badge appears: "✨ Analysé avec Gemini 2.0 Flash"
```

**Error in Production** ❌:
```
Loading modal appears
→ Error alert:
   "Erreur lors de l'analyse IA : 
    Erreur analyse IA : 500: 
    Erreur analyse Gemini : 
    Failed to generate chat completion: 
    litellm.AuthenticationError: 
    GeminiException - {
      "error": {
        "code": 400,
        "message": "API key not valid",
        "status": "INVALID_ARGUMENT"
      }
    }"
```

---

## Debug Information to Collect

### 1. Browser Console Logs

**How to access**:
- Press F12 (or Cmd+Option+I on Mac)
- Go to "Console" tab
- Look for errors (red text)

**What to look for**:
```
📊 Factures validées (statut=integre): X
🚀 Envoi à Gemini...
❌ Error: [error message]
```

### 2. Network Tab

**How to access**:
- F12 → Network tab
- Filter: XHR or Fetch
- Click "🤖 Améliorer avec Gemini"
- Look for request to `/ocr/analyze-facture-ai/`

**Check**:
- Request URL
- Status code (200, 400, 500)
- Response body (error message)
- Request payload (document_id)

### 3. Backend Logs (Preview Only)

**If testing in preview**, check backend logs:
```bash
tail -50 /var/log/supervisor/backend.err.log
tail -50 /var/log/supervisor/backend.out.log | grep -A5 "Gemini"
```

**Look for**:
```
🤖 Activation Joker IA (Gemini 2.0 Flash) pour document [id]
🔑 EMERGENT_LLM_KEY : ✅ Chargée (sk-emergent-fA3...)
✅ Gemini OCR : 8 produits détectés
OR
❌ Erreur Gemini OCR : [error]
```

---

## Expected vs. Actual Behavior

### Expected (Preview)

**API Call**:
```
POST /api/ocr/analyze-facture-ai/b9d00507-0ccb-44fc-b7b8-5e12c61fa549
Response: 200 OK
{
  "document_id": "...",
  "supplier_name": "SAS THE PRIMEUR",
  "items": [...8 products...],
  "ai_powered": true,
  "confiance_globale": 0.95
}
```

**Frontend**:
- Modal updates with 8 products
- Badge "✨ Analysé avec Gemini" appears
- Alert shows success message

### Actual (Production)

**API Call**:
```
POST /api/ocr/analyze-facture-ai/[document_id]
Response: 500 Internal Server Error
{
  "detail": "Erreur analyse Gemini : ...API key not valid..."
}
```

**Frontend**:
- Error alert appears
- Modal doesn't update
- No Gemini results

---

## Root Cause (Already Identified)

**Issue**: `EMERGENT_LLM_KEY` environment variable not accessible in production

**Why it works in preview**:
- Preview auto-injects environment variables
- Code can access `os.environ.get('EMERGENT_LLM_KEY')`

**Why it fails in production**:
- Kubernetes doesn't inject the variable to supervisor process
- Code reads from `config_keys.py` as fallback
- **BUT** if `config_keys.py` is not deployed → key is None → error

---

## Verification Checklist

### In Preview (Should Work ✅)

- [ ] Login successful
- [ ] Can navigate to Factures
- [ ] Can open validation modal
- [ ] Gemini button visible
- [ ] Clicking Gemini button shows progress bar
- [ ] Analysis completes successfully
- [ ] 8 products detected
- [ ] Badge "Analysé avec Gemini" appears

### In Production (Currently Fails ❌)

- [ ] Login successful
- [ ] Can navigate to Factures
- [ ] Can open validation modal
- [ ] Gemini button visible
- [ ] Clicking Gemini button shows error
- [ ] Error message: "API key not valid"

---

## Files to Verify in Deployment

### Must be deployed:
- ✅ `backend/config_keys.py` (contains the key)
- ✅ `backend/.env` (backup key)
- ✅ `backend/server.py` (triple fallback loading)
- ✅ `backend/parsers_optimized.py` (category detection)
- ✅ `backend/requirements.txt` (emergentintegrations)

### Check in GitHub:
```bash
git status
# Should show all files committed

git log --oneline -5
# Should show recent commits with these files
```

---

## Quick Test Script

**To test the endpoint directly**:

```bash
# Get a document ID
curl -s https://receipt-scanner-64.preview.emergentagent.com/api/ocr/documents | jq '.[] | select(.type_document=="facture_fournisseur") | .id' | head -1

# Test the Gemini endpoint (replace DOCUMENT_ID)
curl -X POST "https://receipt-scanner-64.preview.emergentagent.com/api/ocr/analyze-facture-ai/DOCUMENT_ID"
```

---

## Next Steps

1. **Test in preview first** - Confirm it works
2. **Deploy to production** - Save to GitHub + Deploy
3. **Wait 10-15 minutes** - Full deployment
4. **Clear browser cache** - Hard refresh (Ctrl+Shift+R)
5. **Test in production** - Should work now

If still failing, collect:
- Browser console logs
- Network tab (request/response for the failing API call)
- Production backend logs (if accessible)
