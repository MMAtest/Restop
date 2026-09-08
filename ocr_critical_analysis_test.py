#!/usr/bin/env python3
"""
Test critique de la fonction OCR optimisée - Analyse des résultats existants
Basé sur le document ID: a99b0cb4-9543-4fc1-9262-5b43260e7863 avec la structure exacte de la review request
"""

import requests
import json
from datetime import datetime
import sys

# Configuration
BASE_URL = "https://ocr-joker-1.preview.emergentagent.com/api"
HEADERS = {"Content-Type": "application/json"}

class OCRCriticalAnalysisTest:
    def __init__(self):
        self.test_results = []
        self.document_id = "a99b0cb4-9543-4fc1-9262-5b43260e7863"
        
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

    def analyze_existing_document(self):
        """Analyser le document existant avec la structure exacte de la review request"""
        print("\n=== ANALYSE CRITIQUE DOCUMENT EXISTANT - STRUCTURE REVIEW REQUEST ===")
        
        try:
            # Récupérer le document existant
            response = requests.get(f"{BASE_URL}/ocr/document/{self.document_id}")
            
            if response.status_code != 200:
                self.log_result("Récupération document", False, f"Erreur {response.status_code}")
                return
            
            document = response.json()
            texte_extrait = document.get("texte_extrait", "")
            donnees_parsees = document.get("donnees_parsees", {})
            z_analysis = donnees_parsees.get("z_analysis", {})
            
            print(f"📄 Document analysé: {document.get('nom_fichier')}")
            print(f"📝 Texte extrait: {len(texte_extrait)} caractères")
            
            # Test 1: Vérifier la structure du texte extrait
            self.verify_text_structure(texte_extrait)
            
            # Test 2: Analyser les résultats de z_analysis
            self.analyze_z_analysis_results(z_analysis)
            
            # Test 3: Vérifier les critères de succès spécifiques
            self.verify_success_criteria(z_analysis)
            
            # Test 4: Identifier les problèmes critiques
            self.identify_critical_issues(z_analysis)
            
        except Exception as e:
            self.log_result("Analyse document existant", False, f"Exception: {str(e)}")

    def verify_text_structure(self, texte_extrait):
        """Vérifier la structure du texte extrait"""
        print("\n--- Analyse structure texte extrait ---")
        
        # Vérifier la présence des éléments attendus
        expected_elements = [
            "RAPPORT DE CLOTURE",
            "Date: 01/09/2025", 
            "Heure: 22:59:38",
            "x25) Entrees 850,00",
            "x45) Plats principaux 2400,00",
            "x18) Desserts 324,00",
            "Nombre de couverts: 122,00",
            "Total TTC: 3574,00"
        ]
        
        elements_found = 0
        for element in expected_elements:
            if element in texte_extrait:
                elements_found += 1
            else:
                self.log_result(f"Élément manquant", False, f"'{element}' non trouvé dans le texte")
        
        if elements_found == len(expected_elements):
            self.log_result("Structure texte extrait", True, f"Tous les éléments attendus présents ({elements_found}/{len(expected_elements)})")
        else:
            self.log_result("Structure texte extrait", False, f"Éléments manquants: {len(expected_elements) - elements_found}")
        
        # Vérifier la présence d'indentation
        lines_with_indentation = [line for line in texte_extrait.split('\n') if line.startswith('  ')]
        if len(lines_with_indentation) > 0:
            self.log_result("Indentation préservée", True, f"{len(lines_with_indentation)} lignes avec indentation détectées")
        else:
            self.log_result("Indentation préservée", False, "Aucune ligne avec indentation détectée")

    def analyze_z_analysis_results(self, z_analysis):
        """Analyser les résultats de z_analysis"""
        print("\n--- Analyse résultats z_analysis ---")
        
        if not z_analysis:
            self.log_result("z_analysis présent", False, "Aucune analyse z_analysis trouvée")
            return
        
        # Vérifier les données principales
        date_cloture = z_analysis.get("date_cloture")
        heure_cloture = z_analysis.get("heure_cloture")
        nombre_couverts = z_analysis.get("nombre_couverts")
        total_ttc = z_analysis.get("total_ttc")
        
        if date_cloture == "01/09/2025":
            self.log_result("Date clôture", True, f"Date correcte: {date_cloture}")
        else:
            self.log_result("Date clôture", False, f"Date incorrecte: {date_cloture}")
        
        if heure_cloture == "22:59:38":
            self.log_result("Heure clôture", True, f"Heure correcte: {heure_cloture}")
        else:
            self.log_result("Heure clôture", False, f"Heure incorrecte: {heure_cloture}")
        
        if nombre_couverts == 122:
            self.log_result("Nombre couverts", True, f"Couverts corrects: {nombre_couverts}")
        else:
            self.log_result("Nombre couverts", False, f"Couverts incorrects: {nombre_couverts}")
        
        if total_ttc == 3574:
            self.log_result("Total TTC", True, f"Total correct: {total_ttc}€")
        else:
            self.log_result("Total TTC", False, f"Total incorrect: {total_ttc}€")

    def verify_success_criteria(self, z_analysis):
        """Vérifier les critères de succès spécifiques de la review request"""
        print("\n--- Vérification critères de succès spécifiques ---")
        
        categories_detectees = z_analysis.get("categories_detectees", [])
        productions_detectees = z_analysis.get("productions_detectees", [])
        
        # Critère 1: 3 CATÉGORIES attendues
        expected_categories = ["Entrees", "Plats principaux", "Desserts"]
        actual_categories = []
        
        for cat in categories_detectees:
            if cat.get("type") == "categorie" and cat.get("nom") in expected_categories:
                actual_categories.append(cat.get("nom"))
        
        unique_categories = list(set(actual_categories))
        if len(unique_categories) == 3:
            self.log_result("✅ CRITÈRE 1: 3 catégories", True, f"3 catégories détectées: {unique_categories}")
        else:
            self.log_result("❌ CRITÈRE 1: 3 catégories", False, f"Seulement {len(unique_categories)} catégories uniques détectées: {unique_categories}")
        
        # Critère 2: 8 PRODUCTIONS attendues avec bonne classification
        expected_productions = [
            {"nom": "Salade Caesar", "famille": "Entrées"},
            {"nom": "Tartare saumon", "famille": "Entrées"},
            {"nom": "Soupe du jour", "famille": "Entrées"},
            {"nom": "Steak frites", "famille": "Plats"},
            {"nom": "Poisson grillé", "famille": "Plats"},
            {"nom": "Pasta truffe", "famille": "Plats"},
            {"nom": "Tiramisu", "famille": "Desserts"},
            {"nom": "Tarte citron", "famille": "Desserts"}
        ]
        
        productions_found = 0
        correctly_classified = 0
        
        for expected_prod in expected_productions:
            found = False
            for actual_prod in productions_detectees:
                if expected_prod["nom"] in actual_prod.get("nom", ""):
                    found = True
                    productions_found += 1
                    if actual_prod.get("family") == expected_prod["famille"]:
                        correctly_classified += 1
                    break
            
            if not found:
                self.log_result(f"Production manquante", False, f"{expected_prod['nom']} non trouvée dans productions_detectees")
        
        if productions_found == 8:
            self.log_result("✅ CRITÈRE 2a: 8 productions", True, f"8 productions détectées")
        else:
            self.log_result("❌ CRITÈRE 2a: 8 productions", False, f"Seulement {productions_found}/8 productions détectées")
        
        if correctly_classified == 8:
            self.log_result("✅ CRITÈRE 2b: Classification correcte", True, f"8/8 productions correctement classifiées")
        else:
            self.log_result("❌ CRITÈRE 2b: Classification correcte", False, f"Seulement {correctly_classified}/8 productions correctement classifiées")
        
        # Critère 3: Logique séquentielle pour plats
        entrees_end_line = z_analysis.get("entrees_end_line")
        desserts_start_line = z_analysis.get("desserts_start_line")
        
        if entrees_end_line is not None and desserts_start_line is not None:
            if entrees_end_line < desserts_start_line:
                self.log_result("✅ CRITÈRE 3: Logique séquentielle", True, 
                              f"Zone plats définie: ligne {entrees_end_line} → {desserts_start_line}")
            else:
                self.log_result("❌ CRITÈRE 3: Logique séquentielle", False, 
                              f"Ordre incorrect: entrées fin {entrees_end_line}, desserts début {desserts_start_line}")
        else:
            self.log_result("❌ CRITÈRE 3: Logique séquentielle", False, "Bornes séquentielles non définies")

    def identify_critical_issues(self, z_analysis):
        """Identifier les problèmes critiques selon la review request"""
        print("\n--- Identification problèmes critiques ---")
        
        categories_detectees = z_analysis.get("categories_detectees", [])
        productions_detectees = z_analysis.get("productions_detectees", [])
        analysis = z_analysis.get("analysis", {})
        
        # PROBLÈME CRITIQUE 1: Distinction catégories/productions
        categories_count = len(categories_detectees)
        productions_count = len(productions_detectees)
        
        # Selon la structure attendue: 3 catégories + 8 productions = 11 items au total
        # Mais la fonction semble traiter tout comme catégories
        if categories_count > 3:
            self.log_result("🔥 PROBLÈME CRITIQUE 1", False, 
                          f"Fonction ne distingue PAS catégories/productions: {categories_count} catégories détectées au lieu de 3")
        else:
            self.log_result("✅ PROBLÈME CRITIQUE 1 RÉSOLU", True, "Distinction catégories/productions correcte")
        
        if productions_count < 8:
            self.log_result("🔥 PROBLÈME CRITIQUE 1b", False, 
                          f"Seulement {productions_count} productions détectées au lieu de 8")
        else:
            self.log_result("✅ PRODUCTIONS DÉTECTÉES", True, f"{productions_count} productions détectées")
        
        # PROBLÈME CRITIQUE 2: Classification des familles
        autres_items = analysis.get("Autres", {}).get("details", [])
        autres_count = len(autres_items)
        
        if autres_count > 0:
            percentage_autres = (autres_count / (categories_count + productions_count)) * 100 if (categories_count + productions_count) > 0 else 0
            self.log_result("🔥 PROBLÈME CRITIQUE 2", False, 
                          f"Mauvaise classification: {autres_count} items en 'Autres' ({percentage_autres:.1f}%)")
            
            # Lister les items mal classés
            for item in autres_items[:5]:  # Montrer les 5 premiers
                self.log_result("Item mal classé", False, f"{item.get('name')} classé en 'Autres'")
        else:
            self.log_result("✅ PROBLÈME CRITIQUE 2 RÉSOLU", True, "Aucun item mal classé en 'Autres'")
        
        # PROBLÈME CRITIQUE 3: Indentation et détection
        # Vérifier si les productions ont bien un indent_level > 0
        productions_with_indent = [p for p in productions_detectees if p.get("indent_level", 0) > 0]
        if len(productions_with_indent) == len(productions_detectees):
            self.log_result("✅ INDENTATION PRODUCTIONS", True, "Toutes les productions ont une indentation correcte")
        else:
            self.log_result("🔥 PROBLÈME CRITIQUE 3", False, 
                          f"Indentation incorrecte: {len(productions_with_indent)}/{len(productions_detectees)} productions avec indentation")

    def run_comprehensive_analysis(self):
        """Exécuter l'analyse complète"""
        print("🔥 ANALYSE CRITIQUE - FONCTION OCR OPTIMISÉE ÉVITER FAUX POSITIFS PLATS")
        print("=" * 80)
        print(f"📋 Document testé: {self.document_id}")
        print(f"📋 Structure attendue selon review request:")
        print(f"   - x25) Entrees 850,00 = CATÉGORIE")
        print(f"   - Indentés sous catégorie = PRODUCTIONS")
        print(f"   - Logique séquentielle: Entrées → Plats → Desserts")
        print("=" * 80)
        
        # Analyse principale
        self.analyze_existing_document()
        
        # Résumé des résultats
        self.print_critical_summary()

    def print_critical_summary(self):
        """Afficher le résumé critique"""
        print("\n" + "=" * 80)
        print("🔥 RÉSUMÉ CRITIQUE - PROBLÈMES IDENTIFIÉS")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"📊 Total des tests: {total_tests}")
        print(f"✅ Réussis: {passed_tests}")
        print(f"❌ Échoués: {failed_tests}")
        print(f"📈 Taux de réussite: {success_rate:.1f}%")
        
        # Problèmes critiques identifiés
        critical_issues = [result for result in self.test_results if not result["success"] and "CRITIQUE" in result["test"]]
        
        if critical_issues:
            print(f"\n🔥 PROBLÈMES CRITIQUES IDENTIFIÉS ({len(critical_issues)}):")
            for issue in critical_issues:
                print(f"  ❌ {issue['test']}: {issue['message']}")
        
        # Tests échoués non-critiques
        other_failures = [result for result in self.test_results if not result["success"] and "CRITIQUE" not in result["test"]]
        
        if other_failures:
            print(f"\n⚠️ AUTRES PROBLÈMES ({len(other_failures)}):")
            for failure in other_failures[:10]:  # Montrer les 10 premiers
                print(f"  ❌ {failure['test']}: {failure['message']}")
        
        # Conclusion selon les critères de la review request
        print(f"\n🎯 CONCLUSION SELON REVIEW REQUEST:")
        
        # Vérifier si les critères principaux sont remplis
        criteria_met = 0
        total_criteria = 5
        
        categories_ok = any("CRITÈRE 1" in r["test"] and r["success"] for r in self.test_results)
        productions_ok = any("CRITÈRE 2a" in r["test"] and r["success"] for r in self.test_results)
        classification_ok = any("CRITÈRE 2b" in r["test"] and r["success"] for r in self.test_results)
        sequential_ok = any("CRITÈRE 3" in r["test"] and r["success"] for r in self.test_results)
        no_false_positives = not any("CRITIQUE 2" in r["test"] and not r["success"] for r in self.test_results)
        
        if categories_ok:
            criteria_met += 1
            print(f"  ✅ 3 CATÉGORIES détectées correctement")
        else:
            print(f"  ❌ 3 CATÉGORIES non détectées correctement")
        
        if productions_ok:
            criteria_met += 1
            print(f"  ✅ 8 PRODUCTIONS détectées correctement")
        else:
            print(f"  ❌ 8 PRODUCTIONS non détectées correctement")
        
        if classification_ok:
            criteria_met += 1
            print(f"  ✅ Classification familiale correcte")
        else:
            print(f"  ❌ Classification familiale incorrecte")
        
        if sequential_ok:
            criteria_met += 1
            print(f"  ✅ Logique séquentielle fonctionnelle")
        else:
            print(f"  ❌ Logique séquentielle défaillante")
        
        if no_false_positives:
            criteria_met += 1
            print(f"  ✅ Aucun faux positif dans catégorie Plats")
        else:
            print(f"  ❌ Faux positifs détectés dans catégorie Plats")
        
        print(f"\n📊 CRITÈRES REMPLIS: {criteria_met}/{total_criteria} ({criteria_met/total_criteria*100:.1f}%)")
        
        if criteria_met >= 4:
            print(f"\n🎉 FONCTION OCR OPTIMISÉE: LARGEMENT FONCTIONNELLE")
            print(f"   Le problème des faux positifs dans les Plats est en grande partie résolu")
        elif criteria_met >= 2:
            print(f"\n⚠️ FONCTION OCR OPTIMISÉE: PARTIELLEMENT FONCTIONNELLE")
            print(f"   Des améliorations sont encore nécessaires")
        else:
            print(f"\n💥 FONCTION OCR OPTIMISÉE: NON FONCTIONNELLE")
            print(f"   Des corrections majeures sont requises")
        
        return criteria_met >= 4

if __name__ == "__main__":
    test_suite = OCRCriticalAnalysisTest()
    success = test_suite.run_comprehensive_analysis()
    
    if success:
        print(f"\n🎉 ANALYSE TERMINÉE - Fonction largement fonctionnelle")
        sys.exit(0)
    else:
        print(f"\n💥 ANALYSE TERMINÉE - Corrections nécessaires")
        sys.exit(1)