# 🚀 Initialisation Base de Données Production

## Problème
Votre application déployée utilise une nouvelle base MongoDB Atlas vide. Vous devez y transférer les données essentielles (utilisateurs, produits, recettes).

## Solution : Appeler les Endpoints d'Initialisation

### 📝 Étape 1 : Initialiser les Utilisateurs

**Depuis votre navigateur ou Postman, appelez :**

```
POST https://VOTRE-APP.emergent.host/api/demo/init-missions-users
```

**Cela créera les comptes suivants :**

| Rôle | Email | Mot de passe | Nom |
|------|-------|--------------|-----|
| Super Admin | skander@table-augustine.fr | `password123` | Skander Ben Ali |
| Patron | patron@table-augustine.fr | `password123` | Antonin Portal |
| Chef Cuisine | chef@table-augustine.fr | `password123` | Marie Dubois |
| Sous-Chef | nabil@table-augustine.fr | `password123` | Nabil El Mansouri |
| Caissier | caisse@table-augustine.fr | `password123` | Jean Martin |
| Barman | barman@table-augustine.fr | `password123` | Sophie Leroy |
| Employé Cuisine | cuisine@table-augustine.fr | `password123` | Lucas Petit |

**Note** : Les mots de passe utilisent le hash `hashed_password123`. Vous devrez peut-être les réinitialiser après connexion.

---

### 📦 Étape 2 : Initialiser les Données Restaurant

**Depuis votre navigateur ou Postman, appelez :**

```
POST https://VOTRE-APP.emergent.host/api/demo/init-real-restaurant-data
```

**Cela créera :**
- ✅ 7 Fournisseurs (Pêcherie, Boucherie, Maraîcher, etc.)
- ✅ Tous les produits avec leurs relations fournisseurs
- ✅ Les préparations (bases de sauces, etc.)
- ✅ Les recettes complètes du restaurant

---

## 🔧 Méthode Alternative : Depuis le Menu Burger

Une fois connecté avec un compte admin (patron ou super_admin) :

1. **Cliquez sur le menu burger** (☰) en haut à droite
2. **Cliquez sur "🍽️ Données Restaurant"**
   - Cela appelle automatiquement l'endpoint `init-real-restaurant-data`
3. **Confirmez** l'importation

---

## 🌐 Exemple avec cURL

**Remplacez `VOTRE-APP.emergent.host` par l'URL de votre application déployée :**

```bash
# 1. Créer les utilisateurs
curl -X POST https://VOTRE-APP.emergent.host/api/demo/init-missions-users

# 2. Créer les données restaurant
curl -X POST https://VOTRE-APP.emergent.host/api/demo/init-real-restaurant-data
```

---

## ✅ Vérification

Après avoir exécuté ces commandes :
1. **Rafraîchissez votre application** (F5)
2. **Connectez-vous** avec `patron@table-augustine.fr` / `password123`
3. **Vérifiez** que les produits, recettes et fournisseurs sont visibles

---

## ⚠️ Important

Ces endpoints **suppriment les données existantes** avant de recréer les données de base. 
Utilisez-les uniquement lors de l'initialisation initiale ou si vous voulez réinitialiser complètement la base.
