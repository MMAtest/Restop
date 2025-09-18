#!/usr/bin/env python3
"""
Test critique de la fonction OCR optimisée avec analyse d'un document existant
Validation des problèmes identifiés dans la détection d'indentation
"""

import requests
import json
from datetime import datetime
import sys

# Configuration
BASE_URL = "https://restop-manager.preview.emergentagent.com/api"
HEADERS = {"Content-Type": "application/json"}

class OCRCriticalAnalysisTest:
    def __init__(self):
        self.test_results = []
        self.total_tests = 0
        self.passed_tests = 0
        self.critical_issues = []
        
    def log_result(self, test_name, success, message="", details=None, is_critical=False):
        """Enregistre le résultat d'un test"""
        result = {
            "test": test_name,
            "success": success,
            "message": message,
            "details": details,
            "is_critical": is_critical,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        self.total_tests += 1
        if success:
            self.passed_tests += 1
        elif is_critical:
            self.critical_issues.append(result)
            
        status = "✅ PASS" if success else ("🔥 CRITICAL" if is_critical else "❌ FAIL")
        print(f"{status} - {test_name}: {message}")
        if details and not success:
            print(f"   Détails: {details}")

    def test_existing_document_analysis(self):
        """Test d'analyse d'un document existant avec problèmes identifiés"""
        print("\n🎯 === ANALYSE CRITIQUE DOCUMENT EXISTANT ===")
        print("Test du document ID: 42cd9f45-a043-4e0a-a560-4e6ae2a9f89a")
        
        document_id = "42cd9f45-a043-4e0a-a560-4e6ae2a9f89a"
        
        try:
            # Récupérer le document existant
            response = requests.get(f"{BASE_URL}/ocr/document/{document_id}")
            
            if response.status_code == 200:
                document = response.json()
                self.log_result("Récupération Document", True, f"Document récupéré avec succès")
                
                # Analyser le texte extrait
                self.analyze_extracted_text(document)
                
                # Analyser les données parsées
                self.analyze_parsed_data_critical(document)
                
            else:
                self.log_result("Récupération Document", False, 
                              f"Erreur {response.status_code}: {response.text}", is_critical=True)
                
        except Exception as e:
            self.log_result("Test Document Existant", False, f"Exception: {str(e)}", is_critical=True)

    def analyze_extracted_text(self, document):
        """Analyser le texte extrait pour comprendre la structure"""
        print("\n📄 ANALYSE DU TEXTE EXTRAIT:")
        
        texte_extrait = document.get("texte_extrait", "")
        if not texte_extrait:
            self.log_result("Texte Extrait", False, "Pas de texte extrait", is_critical=True)
            return
        
        lines = texte_extrait.split('\n')
        print(f"📊 Nombre de lignes: {len(lines)}")
        
        # Analyser la structure d'indentation dans le texte
        categories_lines = []
        productions_lines = []
        
        for i, line in enumerate(lines):
            line_stripped = line.strip()
            
            # Détecter les lignes avec pattern x25) Entrees 850,00
            if line_stripped.startswith('x') and ')' in line_stripped:
                # Vérifier l'indentation
                indent_level = len(line) - len(line.lstrip(' \t'))
                
                if indent_level == 0:
                    categories_lines.append((i, line_stripped, "catégorie"))
                elif indent_level > 0:
                    productions_lines.append((i, line_stripped, "production"))
        
        print(f"\n🔍 STRUCTURE DÉTECTÉE DANS LE TEXTE:")
        print(f"   Lignes catégories (indent=0): {len(categories_lines)}")
        print(f"   Lignes productions (indent>0): {len(productions_lines)}")
        
        # Afficher quelques exemples
        if categories_lines:
            print(f"\n📂 EXEMPLES CATÉGORIES:")
            for i, (line_num, line_text, type_item) in enumerate(categories_lines[:5]):
                print(f"   Ligne {line_num}: {line_text}")
        
        if productions_lines:
            print(f"\n🍽️ EXEMPLES PRODUCTIONS:")
            for i, (line_num, line_text, type_item) in enumerate(productions_lines[:5]):
                print(f"   Ligne {line_num}: {line_text}")
        
        # Vérifications critiques
        expected_categories = 3  # Entrees, Plats principaux, Desserts
        expected_productions = 8  # 3 entrées + 3 plats + 2 desserts
        
        if len(categories_lines) >= expected_categories:
            self.log_result("Catégories dans Texte", True, 
                          f"{len(categories_lines)} catégories détectées dans le texte")
        else:
            self.log_result("Catégories dans Texte", False, 
                          f"Seulement {len(categories_lines)} catégories détectées, attendu: {expected_categories}")
        
        if len(productions_lines) >= expected_productions:
            self.log_result("Productions dans Texte", True, 
                          f"{len(productions_lines)} productions détectées dans le texte")
        else:
            self.log_result("Productions dans Texte", False, 
                          f"Seulement {len(productions_lines)} productions détectées, attendu: {expected_productions}",
                          is_critical=True)

    def analyze_parsed_data_critical(self, document):
        """Analyse critique des données parsées"""
        print("\n🔥 ANALYSE CRITIQUE DES DONNÉES PARSÉES:")
        
        donnees_parsees = document.get("donnees_parsees", {})
        if not donnees_parsees:
            self.log_result("Données Parsées Disponibles", False, "Pas de données parsées", is_critical=True)
            return
        
        # Analyser z_analysis spécifiquement
        z_analysis = donnees_parsees.get("z_analysis", {})
        if not z_analysis:
            self.log_result("Z Analysis Disponible", False, "Pas de z_analysis", is_critical=True)
            return
        
        # PROBLÈME CRITIQUE 1: Détection des productions
        self.check_productions_detection_critical(z_analysis)
        
        # PROBLÈME CRITIQUE 2: Classification des familles
        self.check_family_classification_critical(z_analysis)
        
        # PROBLÈME CRITIQUE 3: Distinction catégories vs productions
        self.check_category_vs_production_distinction(z_analysis)
        
        # Vérifications supplémentaires
        self.check_sequential_logic_critical(z_analysis)

    def check_productions_detection_critical(self, z_analysis):
        """Vérification critique de la détection des productions"""
        print("\n🔥 PROBLÈME CRITIQUE 1: DÉTECTION DES PRODUCTIONS")
        
        productions_detectees = z_analysis.get("productions_detectees", [])
        total_productions = z_analysis.get("total_productions", 0)
        
        print(f"   Productions détectées: {len(productions_detectees)}")
        print(f"   Total productions: {total_productions}")
        
        # Vérification critique: doit détecter au moins 8 productions
        expected_productions = 8
        if len(productions_detectees) >= expected_productions:
            self.log_result("CRITIQUE - Nombre Productions", True, 
                          f"{len(productions_detectees)} productions détectées")
        else:
            self.log_result("CRITIQUE - Nombre Productions", False, 
                          f"SEULEMENT {len(productions_detectees)} productions détectées au lieu de {expected_productions}",
                          is_critical=True)
        
        # Vérifier les productions attendues spécifiques
        expected_production_names = [
            "Salade Caesar", "Tartare saumon", "Soupe du jour",
            "Steak frites", "Poisson grillé", "Pasta truffe",
            "Tiramisu", "Tarte citron"
        ]
        
        found_productions = [p.get("nom", "") for p in productions_detectees]
        
        for expected_name in expected_production_names:
            found = any(expected_name.lower() in prod_name.lower() for prod_name in found_productions)
            if found:
                self.log_result(f"Production {expected_name}", True, "Détectée correctement")
            else:
                self.log_result(f"Production {expected_name}", False, 
                              f"NON DÉTECTÉE - Absent des productions", is_critical=True)

    def check_family_classification_critical(self, z_analysis):
        """Vérification critique de la classification des familles"""
        print("\n🔥 PROBLÈME CRITIQUE 2: CLASSIFICATION DES FAMILLES")
        
        analysis = z_analysis.get("analysis", {})
        
        # Vérifier la répartition par familles
        families_data = {}
        for family in ["Bar", "Entrées", "Plats", "Desserts", "Autres"]:
            family_info = analysis.get(family, {})
            articles = family_info.get("articles", 0)
            ca = family_info.get("ca", 0)
            details = family_info.get("details", [])
            
            families_data[family] = {
                "articles": articles,
                "ca": ca,
                "details_count": len(details)
            }
            
            print(f"   {family}: {articles} articles, {ca}€ CA, {len(details)} détails")
        
        # PROBLÈME CRITIQUE: Trop d'items dans "Autres"
        autres_articles = families_data["Autres"]["articles"]
        total_articles = sum(f["articles"] for f in families_data.values())
        
        if total_articles > 0:
            autres_percentage = (autres_articles / total_articles) * 100
            print(f"   Pourcentage dans 'Autres': {autres_percentage:.1f}%")
            
            if autres_percentage > 50:
                self.log_result("CRITIQUE - Classification Familles", False, 
                              f"{autres_percentage:.1f}% des items classés en 'Autres' - TROP ÉLEVÉ",
                              is_critical=True)
            else:
                self.log_result("CRITIQUE - Classification Familles", True, 
                              f"{autres_percentage:.1f}% des items classés en 'Autres'")
        
        # Vérifier que les familles principales ont des articles
        expected_families = ["Entrées", "Plats", "Desserts"]
        for family in expected_families:
            articles = families_data[family]["articles"]
            if articles > 0:
                self.log_result(f"Famille {family} - Articles", True, f"{articles} articles")
            else:
                self.log_result(f"Famille {family} - Articles", False, 
                              f"AUCUN article dans {family}", is_critical=True)

    def check_category_vs_production_distinction(self, z_analysis):
        """Vérification de la distinction catégories vs productions"""
        print("\n🔥 PROBLÈME CRITIQUE 3: DISTINCTION CATÉGORIES VS PRODUCTIONS")
        
        categories_detectees = z_analysis.get("categories_detectees", [])
        productions_detectees = z_analysis.get("productions_detectees", [])
        
        print(f"   Catégories détectées: {len(categories_detectees)}")
        print(f"   Productions détectées: {len(productions_detectees)}")
        
        # Analyser les catégories détectées
        individual_items_as_categories = []
        
        for category in categories_detectees:
            nom = category.get("nom", "")
            
            # Ces items devraient être des productions, pas des catégories
            individual_item_names = [
                "Salade Caesar", "Tartare saumon", "Soupe du jour",
                "Steak frites", "Poisson grillé", "Pasta truffe",
                "Tiramisu", "Tarte citron"
            ]
            
            if any(item_name.lower() in nom.lower() for item_name in individual_item_names):
                individual_items_as_categories.append(nom)
        
        if len(individual_items_as_categories) > 0:
            self.log_result("CRITIQUE - Items Individuels comme Catégories", False, 
                          f"{len(individual_items_as_categories)} items individuels traités comme catégories: {individual_items_as_categories}",
                          is_critical=True)
        else:
            self.log_result("CRITIQUE - Items Individuels comme Catégories", True, 
                          "Aucun item individuel traité comme catégorie")
        
        # Vérifier que les vraies catégories sont détectées
        true_categories = ["Entrees", "Plats principaux", "Desserts"]
        found_true_categories = []
        
        for category in categories_detectees:
            nom = category.get("nom", "")
            for true_cat in true_categories:
                if true_cat.lower() in nom.lower():
                    found_true_categories.append(true_cat)
                    break
        
        if len(found_true_categories) >= 3:
            self.log_result("CRITIQUE - Vraies Catégories Détectées", True, 
                          f"{len(found_true_categories)} vraies catégories détectées")
        else:
            self.log_result("CRITIQUE - Vraies Catégories Détectées", False, 
                          f"Seulement {len(found_true_categories)} vraies catégories détectées sur 3",
                          is_critical=True)

    def check_sequential_logic_critical(self, z_analysis):
        """Vérification de la logique séquentielle"""
        print("\n🔍 VÉRIFICATION LOGIQUE SÉQUENTIELLE:")
        
        entrees_end_line = z_analysis.get("entrees_end_line")
        desserts_start_line = z_analysis.get("desserts_start_line")
        
        print(f"   Fin entrées ligne: {entrees_end_line}")
        print(f"   Début desserts ligne: {desserts_start_line}")
        
        if entrees_end_line is not None and desserts_start_line is not None:
            if entrees_end_line < desserts_start_line:
                zone_plats = desserts_start_line - entrees_end_line
                self.log_result("Logique Séquentielle", True, 
                              f"Zone plats de {zone_plats} lignes entre entrées et desserts")
            else:
                self.log_result("Logique Séquentielle", False, 
                              f"Ordre incorrect: entrées={entrees_end_line}, desserts={desserts_start_line}")
        else:
            self.log_result("Logique Séquentielle", False, 
                          f"Bornes non définies correctement")

    def run_all_tests(self):
        """Exécuter tous les tests critiques"""
        print("🔥 DÉMARRAGE ANALYSE CRITIQUE FONCTION OCR")
        print("=" * 80)
        print("Test des problèmes identifiés dans la détection d'indentation")
        print("Document de test: 42cd9f45-a043-4e0a-a560-4e6ae2a9f89a")
        print("=" * 80)
        
        start_time = datetime.now()
        
        # Test principal
        self.test_existing_document_analysis()
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Résumé des résultats
        print("\n" + "=" * 80)
        print("🔥 RÉSUMÉ ANALYSE CRITIQUE OCR")
        print("=" * 80)
        
        success_rate = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        critical_count = len(self.critical_issues)
        
        print(f"✅ Tests réussis: {self.passed_tests}/{self.total_tests} ({success_rate:.1f}%)")
        print(f"🔥 Problèmes critiques: {critical_count}")
        print(f"⏱️  Durée totale: {duration:.2f}s")
        
        # Détail des problèmes critiques
        if self.critical_issues:
            print(f"\n🔥 PROBLÈMES CRITIQUES IDENTIFIÉS ({len(self.critical_issues)}):")
            for issue in self.critical_issues:
                print(f"   🔥 {issue['test']}: {issue['message']}")
        
        # Détail des échecs non critiques
        failed_tests = [r for r in self.test_results if not r["success"] and not r.get("is_critical", False)]
        if failed_tests:
            print(f"\n❌ AUTRES ÉCHECS ({len(failed_tests)}):")
            for test in failed_tests:
                print(f"   - {test['test']}: {test['message']}")
        
        # Conclusion critique
        print("\n🎯 CONCLUSION CRITIQUE:")
        if critical_count == 0:
            print("✅ FONCTION OCR OPTIMISÉE - PROBLÈMES RÉSOLUS")
            print("   Tous les problèmes critiques d'indentation ont été corrigés")
        elif critical_count <= 2:
            print("⚠️  FONCTION OCR OPTIMISÉE - PARTIELLEMENT CORRIGÉE")
            print("   Quelques problèmes critiques persistent mais amélioration notable")
        else:
            print("❌ FONCTION OCR OPTIMISÉE - PROBLÈMES CRITIQUES PERSISTENT")
            print("   Les problèmes d'indentation ne sont PAS résolus")
            print("   Corrections importantes nécessaires avant mise en production")
        
        # Recommandations spécifiques
        print("\n📋 RECOMMANDATIONS:")
        if critical_count > 0:
            print("   1. Corriger la logique de détection d'indentation (indent_level)")
            print("   2. Améliorer la distinction catégories vs productions")
            print("   3. Optimiser la classification des familles")
            print("   4. Tester avec le texte de référence fourni dans la demande")
        else:
            print("   ✅ Fonction OCR optimisée opérationnelle")
            print("   ✅ Tests de régression recommandés")
        
        return critical_count == 0

if __name__ == "__main__":
    print("🔥 ANALYSE CRITIQUE - FONCTION OCR OPTIMISÉE")
    print("Test des problèmes critiques de détection d'indentation")
    print("Validation des corrections apportées à analyze_z_report_categories")
    print()
    
    test_suite = OCRCriticalAnalysisTest()
    success = test_suite.run_all_tests()
    
    # Code de sortie
    sys.exit(0 if success else 1)