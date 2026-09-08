#!/usr/bin/env python3
"""
Test d'analyse détaillée de la fonction OCR optimisée
Analyse des résultats actuels et identification des problèmes
"""

import requests
import json
from datetime import datetime
import sys

# Configuration
BASE_URL = "https://ocr-joker-1.preview.emergentagent.com/api"
HEADERS = {"Content-Type": "application/json"}

class OCRAnalysisTest:
    def __init__(self):
        self.test_results = []
        
    def log_result(self, test_name, success, message="", details=None):
        """Enregistre le résultat d'un test"""
        result = {
            "test": test_name,
            "success": success,
            "message": message,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {test_name}: {message}")
        if details and not success:
            print(f"   Détails: {details}")

    def analyze_current_ocr_behavior(self):
        """Analyse le comportement actuel de l'OCR avec le document existant"""
        print("\n🔍 ANALYSE DÉTAILLÉE DU COMPORTEMENT OCR ACTUEL")
        print("=" * 80)
        
        # Utiliser le document créé précédemment
        document_id = "42cd9f45-a043-4e0a-a560-4e6ae2a9f89a"
        
        try:
            # Récupérer le document
            response = requests.get(f"{BASE_URL}/ocr/document/{document_id}")
            if response.status_code != 200:
                self.log_result("Document Retrieval", False, f"Erreur {response.status_code}")
                return
            
            document = response.json()
            texte_extrait = document.get("texte_extrait", "")
            donnees_parsees = document.get("donnees_parsees", {})
            z_analysis = donnees_parsees.get("z_analysis", {})
            
            print(f"\n📄 TEXTE EXTRAIT ({len(texte_extrait)} caractères):")
            print("-" * 50)
            lines = texte_extrait.split('\n')
            for i, line in enumerate(lines[:25], 1):  # Afficher les 25 premières lignes
                print(f"{i:2d}: {repr(line)}")
            
            # Analyse des catégories détectées
            self.analyze_categories(z_analysis)
            
            # Analyse des productions détectées
            self.analyze_productions(z_analysis)
            
            # Analyse des faux positifs
            self.analyze_false_positives(z_analysis)
            
            # Analyse de la logique séquentielle
            self.analyze_sequential_logic(z_analysis)
            
            # Recommandations d'amélioration
            self.provide_recommendations(z_analysis)
            
        except Exception as e:
            self.log_result("OCR Analysis", False, f"Exception: {str(e)}")

    def analyze_categories(self, z_analysis):
        """Analyse les catégories détectées"""
        print(f"\n📊 ANALYSE DES CATÉGORIES DÉTECTÉES")
        print("-" * 50)
        
        categories_detectees = z_analysis.get("categories_detectees", [])
        print(f"Nombre total de catégories détectées: {len(categories_detectees)}")
        
        # Grouper par famille
        by_family = {}
        for cat in categories_detectees:
            family = cat.get("family", "Autres")
            if family not in by_family:
                by_family[family] = []
            by_family[family].append(cat)
        
        for family, items in by_family.items():
            print(f"\n🏷️ Famille '{family}' ({len(items)} items):")
            for item in items[:5]:  # Afficher les 5 premiers
                print(f"   - {item.get('nom')} (x{item.get('quantite')}) - {item.get('prix_total')}€")
                print(f"     Raw: {item.get('raw_line')}")
        
        # Problèmes identifiés
        problems = []
        
        # Problème 1: Items qui devraient être des productions sont classés comme catégories
        individual_items = ["Salade Caesar", "Tartare saumon", "Soupe du jour", 
                           "Steak frites", "Poisson grillé", "Pasta truffe", 
                           "Tiramisu", "Tarte citron"]
        
        misclassified = []
        for cat in categories_detectees:
            if any(item in cat.get("nom", "") for item in individual_items):
                misclassified.append(cat.get("nom"))
        
        if misclassified:
            problems.append(f"Items classés comme catégories au lieu de productions: {misclassified}")
        
        # Problème 2: Mauvaise classification des familles
        wrong_family = []
        for cat in categories_detectees:
            nom = cat.get("nom", "")
            family = cat.get("family", "")
            
            if "Salade" in nom or "Tartare" in nom or "Soupe" in nom:
                if family != "Entrées":
                    wrong_family.append(f"{nom} classé en '{family}' au lieu de 'Entrées'")
            elif "Steak" in nom or "Poisson" in nom or "Pasta" in nom:
                if family != "Plats":
                    wrong_family.append(f"{nom} classé en '{family}' au lieu de 'Plats'")
            elif "Tiramisu" in nom or "Tarte" in nom:
                if family != "Desserts":
                    wrong_family.append(f"{nom} classé en '{family}' au lieu de 'Desserts'")
        
        if wrong_family:
            problems.append(f"Mauvaise classification des familles: {wrong_family}")
        
        if problems:
            self.log_result("Analyse Catégories", False, f"{len(problems)} problèmes identifiés", problems)
        else:
            self.log_result("Analyse Catégories", True, "Classification correcte")

    def analyze_productions(self, z_analysis):
        """Analyse les productions détectées"""
        print(f"\n🍽️ ANALYSE DES PRODUCTIONS DÉTECTÉES")
        print("-" * 50)
        
        productions_detectees = z_analysis.get("productions_detectees", [])
        print(f"Nombre total de productions détectées: {len(productions_detectees)}")
        
        if len(productions_detectees) == 0:
            self.log_result("Productions Détection", False, 
                          "PROBLÈME CRITIQUE: Aucune production détectée - La logique de distinction catégorie/production ne fonctionne pas")
            
            print("\n🔍 ANALYSE DU PROBLÈME:")
            print("La fonction ne distingue pas entre:")
            print("- Catégories: x25) Entrees 850,00")
            print("- Productions:   x8) Salade Caesar 184,00 (indentées)")
            print("\nLa logique séquentielle nécessite cette distinction pour fonctionner correctement.")
        else:
            self.log_result("Productions Détection", True, f"{len(productions_detectees)} productions détectées")

    def analyze_false_positives(self, z_analysis):
        """Analyse les faux positifs"""
        print(f"\n🚫 ANALYSE DES FAUX POSITIFS")
        print("-" * 50)
        
        categories_detectees = z_analysis.get("categories_detectees", [])
        
        # Mots-clés qui ne devraient jamais être des productions
        forbidden_keywords = ["tva", "total", "sous-total", "remise", "service", "heure", "solde", "caisse"]
        
        false_positives = []
        for cat in categories_detectees:
            nom = cat.get("nom", "").lower()
            for keyword in forbidden_keywords:
                if keyword in nom:
                    false_positives.append({
                        "nom": cat.get("nom"),
                        "family": cat.get("family"),
                        "raw_line": cat.get("raw_line"),
                        "keyword": keyword
                    })
        
        if false_positives:
            self.log_result("Faux Positifs", False, f"{len(false_positives)} faux positifs détectés")
            for fp in false_positives:
                print(f"   ❌ '{fp['nom']}' (famille: {fp['family']}) - contient '{fp['keyword']}'")
                print(f"      Raw: {fp['raw_line']}")
        else:
            self.log_result("Faux Positifs", True, "Aucun faux positif détecté")

    def analyze_sequential_logic(self, z_analysis):
        """Analyse la logique séquentielle"""
        print(f"\n🔄 ANALYSE DE LA LOGIQUE SÉQUENTIELLE")
        print("-" * 50)
        
        category_zones = z_analysis.get("category_zones", {})
        entrees_end_line = z_analysis.get("entrees_end_line")
        desserts_start_line = z_analysis.get("desserts_start_line")
        
        print(f"Zones de catégories détectées: {len(category_zones)}")
        print(f"Fin des entrées: ligne {entrees_end_line}")
        print(f"Début des desserts: ligne {desserts_start_line}")
        
        if category_zones:
            print("\n📍 ZONES DÉTECTÉES:")
            for zone_name, zone_range in list(category_zones.items())[:5]:
                print(f"   {zone_name}: lignes {zone_range[0]} à {zone_range[1]}")
        
        # Vérifier la logique de zone ciblée pour les plats
        if entrees_end_line is not None and desserts_start_line is not None:
            if desserts_start_line > entrees_end_line:
                zone_plats_size = desserts_start_line - entrees_end_line - 1
                self.log_result("Zone Plats", True, 
                              f"Zone plats correctement délimitée: {zone_plats_size} lignes entre entrées et desserts")
            else:
                self.log_result("Zone Plats", False, "Zone plats mal délimitée")
        else:
            self.log_result("Zone Plats", False, "Impossible de délimiter la zone plats")

    def analyze_plats_section_specifically(self, z_analysis):
        """Analyse spécifique de la section Plats pour les faux positifs"""
        print(f"\n🍖 ANALYSE SPÉCIFIQUE SECTION PLATS")
        print("-" * 50)
        
        categories_detectees = z_analysis.get("categories_detectees", [])
        
        # Items qui devraient être dans la section Plats
        expected_plats = ["Steak frites", "Poisson grillé", "Pasta truffe"]
        
        # Items qui ne devraient PAS être dans la section Plats
        forbidden_in_plats = ["TVA", "Total HT", "Remise", "Service", "Entrees", "Desserts"]
        
        plats_items = [cat for cat in categories_detectees if cat.get("family") == "Plats"]
        autres_items_in_plats = [cat for cat in categories_detectees 
                               if cat.get("family") == "Autres" and 
                               any(plat in cat.get("nom", "") for plat in expected_plats)]
        
        print(f"Items classés en famille 'Plats': {len(plats_items)}")
        for item in plats_items:
            print(f"   - {item.get('nom')} (ligne {item.get('line_number')})")
        
        print(f"Items de plats classés en 'Autres': {len(autres_items_in_plats)}")
        for item in autres_items_in_plats:
            print(f"   - {item.get('nom')} (ligne {item.get('line_number')})")
        
        # Vérifier les faux positifs spécifiquement dans les plats
        false_positives_in_plats = []
        for item in plats_items:
            nom = item.get("nom", "")
            if any(forbidden in nom for forbidden in forbidden_in_plats):
                false_positives_in_plats.append(nom)
        
        if false_positives_in_plats:
            self.log_result("Faux Positifs Plats", False, 
                          f"Faux positifs dans section Plats: {false_positives_in_plats}")
        else:
            self.log_result("Faux Positifs Plats", True, "Pas de faux positifs dans section Plats")

    def provide_recommendations(self, z_analysis):
        """Fournit des recommandations d'amélioration"""
        print(f"\n💡 RECOMMANDATIONS D'AMÉLIORATION")
        print("-" * 50)
        
        recommendations = []
        
        # Recommandation 1: Distinction catégorie/production
        productions_count = len(z_analysis.get("productions_detectees", []))
        if productions_count == 0:
            recommendations.append({
                "priority": "CRITIQUE",
                "issue": "Distinction catégorie/production",
                "description": "La fonction ne distingue pas les catégories (x25) Entrees) des productions indentées (  x8) Salade Caesar)",
                "solution": "Modifier la logique pour détecter l'indentation et classer correctement les items"
            })
        
        # Recommandation 2: Classification des familles
        categories_detectees = z_analysis.get("categories_detectees", [])
        autres_count = len([cat for cat in categories_detectees if cat.get("family") == "Autres"])
        if autres_count > 10:
            recommendations.append({
                "priority": "HAUTE",
                "issue": "Classification des familles",
                "description": f"{autres_count} items classés en 'Autres' au lieu de leur vraie famille",
                "solution": "Améliorer les patterns de reconnaissance pour Entrées, Plats, Desserts"
            })
        
        # Recommandation 3: Filtrage des faux positifs
        false_positives = [cat for cat in categories_detectees 
                         if any(keyword in cat.get("nom", "").lower() 
                               for keyword in ["tva", "total", "heure", "solde"])]
        if false_positives:
            recommendations.append({
                "priority": "HAUTE",
                "issue": "Filtrage des faux positifs",
                "description": f"{len(false_positives)} faux positifs détectés (TVA, totaux, etc.)",
                "solution": "Renforcer le filtrage des mots-clés interdits avant classification"
            })
        
        # Recommandation 4: Logique séquentielle
        entrees_end_line = z_analysis.get("entrees_end_line")
        desserts_start_line = z_analysis.get("desserts_start_line")
        if entrees_end_line is None or desserts_start_line is None:
            recommendations.append({
                "priority": "MOYENNE",
                "issue": "Logique séquentielle",
                "description": "Zones de catégories non correctement délimitées",
                "solution": "Améliorer la détection des zones pour l'extraction ciblée"
            })
        
        print(f"Nombre de recommandations: {len(recommendations)}")
        for i, rec in enumerate(recommendations, 1):
            print(f"\n{i}. [{rec['priority']}] {rec['issue']}")
            print(f"   Problème: {rec['description']}")
            print(f"   Solution: {rec['solution']}")
        
        if recommendations:
            critical_count = len([r for r in recommendations if r['priority'] == 'CRITIQUE'])
            high_count = len([r for r in recommendations if r['priority'] == 'HAUTE'])
            
            if critical_count > 0:
                self.log_result("Recommandations", False, 
                              f"{critical_count} problèmes critiques, {high_count} problèmes haute priorité")
            elif high_count > 0:
                self.log_result("Recommandations", False, 
                              f"{high_count} problèmes haute priorité nécessitent des corrections")
            else:
                self.log_result("Recommandations", True, "Améliorations mineures suggérées")
        else:
            self.log_result("Recommandations", True, "Fonction OCR optimale")

    def run_analysis(self):
        """Lance l'analyse complète"""
        print("🔍 ANALYSE DÉTAILLÉE DE LA FONCTION OCR OPTIMISÉE")
        print("=" * 80)
        
        self.analyze_current_ocr_behavior()
        
        # Résumé final
        self.print_summary()

    def print_summary(self):
        """Affiche le résumé de l'analyse"""
        print("\n" + "=" * 80)
        print("📋 RÉSUMÉ DE L'ANALYSE OCR")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["success"]])
        failed_tests = total_tests - passed_tests
        
        print(f"Total des vérifications: {total_tests}")
        print(f"Vérifications réussies: {passed_tests}")
        print(f"Vérifications échouées: {failed_tests}")
        
        if failed_tests > 0:
            print(f"\n❌ PROBLÈMES IDENTIFIÉS ({failed_tests}):")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['test']}: {result['message']}")
        
        print(f"\n🎯 CONCLUSION:")
        if failed_tests == 0:
            print("✅ FONCTION OCR OPTIMISÉE FONCTIONNE CORRECTEMENT")
        elif failed_tests <= 2:
            print("⚠️ FONCTION OCR NÉCESSITE DES AMÉLIORATIONS MINEURES")
        else:
            print("❌ FONCTION OCR NÉCESSITE DES CORRECTIONS IMPORTANTES")
            print("\nLes problèmes principaux identifiés doivent être corrigés pour éviter les faux positifs.")

if __name__ == "__main__":
    print("🚀 Lancement de l'analyse détaillée de la fonction OCR optimisée")
    
    analyzer = OCRAnalysisTest()
    analyzer.run_analysis()