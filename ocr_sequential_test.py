#!/usr/bin/env python3
"""
Test spécifique pour la fonction OCR optimisée pour éviter les faux positifs dans la catégorie Plats
Test de la nouvelle logique séquentielle selon les spécifications détaillées
"""

import requests
import json
from datetime import datetime
import sys
import os

# Configuration
BASE_URL = "https://ocr-manager.preview.emergentagent.com/api"
HEADERS = {"Content-Type": "application/json"}

class OCRSequentialTestSuite:
    def __init__(self):
        self.test_results = []
        self.document_id = None
        
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

    def create_test_ocr_text(self):
        """Crée le texte OCR de test avec structure séquentielle problématique"""
        return """RAPPORT DE CLOTURE
Date: 01/09/2025
Heure: 22:59:38

VENTES PAR CATEGORIES

x25) Entrees 850,00
  x8) Salade Caesar 184,00
  x12) Tartare saumon 420,00
  x5) Soupe du jour 75,00

TVA 10% sur total: 85,00
Sous-total HT: 765,00
Service 15%: 127,75

x45) Plats principaux 2400,00
  x12) Steak frites 420,00
  x8) Poisson grillé 288,00
  x15) Pasta truffe 690,00

TVA 20% restaurant: 480,00
Total HT plats: 1920,00
Remise groupe: -50,00

x18) Desserts 324,00
  x12) Tiramisu 144,00
  x6) Tarte citron 96,00

SOLDE DE CAISSE
Nombre de couverts: 122,00
Total TTC: 3574,00"""

    def create_test_pdf(self, text_content):
        """Crée un PDF de test avec le contenu texte"""
        try:
            from reportlab.pdfgen import canvas
            from reportlab.lib.pagesizes import letter
            import io
            
            buffer = io.BytesIO()
            p = canvas.Canvas(buffer, pagesize=letter)
            
            # Ajouter le texte ligne par ligne
            lines = text_content.split('\n')
            y_position = 750
            
            for line in lines:
                if y_position < 50:  # Nouvelle page si nécessaire
                    p.showPage()
                    y_position = 750
                p.drawString(50, y_position, line)
                y_position -= 15
            
            p.save()
            buffer.seek(0)
            return buffer.getvalue()
            
        except ImportError:
            # Fallback: créer un PDF minimal avec une autre méthode
            return self.create_minimal_pdf(text_content)
    
    def create_minimal_pdf(self, text_content):
        """Crée un PDF minimal sans reportlab"""
        # Créer un PDF très basique avec le contenu
        pdf_header = b"%PDF-1.4\n"
        pdf_content = f"""1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj

2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj

3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj

4 0 obj
<<
/Length {len(text_content) + 50}
>>
stream
BT
/F1 12 Tf
50 750 Td
({text_content.replace(chr(10), ') Tj T* (')}) Tj
ET
endstream
endobj

xref
0 5
0000000000 65535 f 
0000000010 00000 n 
0000000053 00000 n 
0000000110 00000 n 
0000000205 00000 n 
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
{300 + len(text_content)}
%%EOF"""
        
        return pdf_header + pdf_content.encode('utf-8')

    def test_sequential_logic_extraction(self):
        """Test de la nouvelle logique séquentielle"""
        print("\n=== TEST LOGIQUE SÉQUENTIELLE OCR ===")
        
        # Créer le texte OCR de test
        test_text = self.create_test_ocr_text()
        
        # Créer un PDF de test
        try:
            pdf_content = self.create_test_pdf(test_text)
            
            # Upload du PDF
            files = {
                'file': ('test_sequential_z_report.pdf', pdf_content, 'application/pdf')
            }
            data = {'document_type': 'z_report'}
            
            response = requests.post(f"{BASE_URL}/ocr/upload-document", files=files, data=data)
            if response.status_code in [200, 201]:
                result = response.json()
                self.document_id = result.get("document_id")
                
                if self.document_id:
                    self.log_result("Document Upload", True, f"Document PDF créé avec ID: {self.document_id}")
                    
                    # Tester l'analyse avec la fonction analyze_z_report_categories
                    self.test_analyze_z_report_categories()
                else:
                    self.log_result("Document Upload", False, "Pas d'ID de document retourné")
            else:
                self.log_result("Document Upload", False, f"Erreur {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_result("Document Upload", False, f"Exception: {str(e)}")
            
    def test_direct_analysis(self):
        """Test direct de la fonction analyze_z_report_categories"""
        print("\n=== TEST DIRECT ANALYZE_Z_REPORT_CATEGORIES ===")
        
        test_text = self.create_test_ocr_text()
        
        # Créer un document temporaire pour tester
        try:
            # Créer un document simple avec le texte
            doc_data = {
                "type_document": "z_report",
                "nom_fichier": "test_direct.txt",
                "texte_extrait": test_text,
                "statut": "traite"
            }
            
            # Créer le document via l'API
            response = requests.post(f"{BASE_URL}/ocr/documents", json=doc_data, headers=HEADERS)
            if response.status_code in [200, 201]:
                result = response.json()
                self.document_id = result.get("id")
                
                if self.document_id:
                    self.log_result("Direct Document Creation", True, f"Document direct créé: {self.document_id}")
                    self.test_analyze_z_report_categories()
                else:
                    self.log_result("Direct Document Creation", False, "Pas d'ID retourné")
            else:
                # Si l'API de création directe n'existe pas, simuler l'analyse
                self.log_result("Direct Document Creation", False, f"API non disponible: {response.status_code}")
                self.simulate_analysis_test(test_text)
                
        except Exception as e:
            self.log_result("Direct Document Creation", False, f"Exception: {str(e)}")
            self.simulate_analysis_test(test_text)
    
    def simulate_analysis_test(self, test_text):
        """Simule le test d'analyse en testant les patterns directement"""
        print("\n=== SIMULATION TEST ANALYSE ===")
        
        # Tester les patterns de base que la fonction devrait détecter
        lines = test_text.split('\n')
        
        # Test 1: Détection des catégories
        import re
        category_pattern = re.compile(r"^x?(\d+)\)\s*([^0-9]+?)\s+([0-9]+(?:[,\.][0-9]{2}))$", re.IGNORECASE)
        
        categories_found = []
        for line in lines:
            line_clean = line.strip()
            match = category_pattern.match(line_clean)
            if match:
                quantity = int(match.group(1))
                name = match.group(2).strip()
                amount = float(match.group(3).replace(',', '.'))
                categories_found.append((name, quantity, amount))
        
        expected_categories = [
            ("Entrees", 25, 850.0),
            ("Plats principaux", 45, 2400.0),
            ("Desserts", 18, 324.0)
        ]
        
        if len(categories_found) == 3:
            self.log_result("Pattern Catégories", True, f"3 catégories détectées: {[c[0] for c in categories_found]}")
        else:
            self.log_result("Pattern Catégories", False, f"{len(categories_found)} catégories détectées")
        
        # Test 2: Détection des productions
        production_pattern = re.compile(r"^\s*\(?x?(\d+)\)?\s*([^0-9]+?)\s+([0-9]+(?:[,\.][0-9]{2}))$", re.IGNORECASE)
        
        productions_found = []
        for line in lines:
            if line.startswith(' ') or line.startswith('\t'):  # Lignes indentées
                line_clean = line.strip()
                match = production_pattern.match(line_clean)
                if match:
                    quantity = int(match.group(1))
                    name = match.group(2).strip()
                    amount = float(match.group(3).replace(',', '.'))
                    productions_found.append((name, quantity, amount))
        
        expected_productions = 8  # 3 entrées + 3 plats + 2 desserts
        if len(productions_found) == expected_productions:
            self.log_result("Pattern Productions", True, f"{len(productions_found)} productions détectées")
        else:
            self.log_result("Pattern Productions", False, f"{len(productions_found)} productions au lieu de {expected_productions}")
        
        # Test 3: Vérification du filtrage des faux positifs
        forbidden_keywords = ["tva", "total", "sous-total", "remise", "service"]
        false_positives = []
        
        for name, _, _ in productions_found:
            name_lower = name.lower()
            for keyword in forbidden_keywords:
                if keyword in name_lower:
                    false_positives.append(f"{name} (contient '{keyword}')")
        
        if len(false_positives) == 0:
            self.log_result("Simulation Filtrage", True, "Aucun faux positif dans la simulation")
        else:
            self.log_result("Simulation Filtrage", False, f"Faux positifs: {false_positives}")
        
        # Test 4: Vérification des données principales
        date_found = any("01/09/2025" in line for line in lines)
        heure_found = any("22:59:38" in line for line in lines)
        couverts_found = any("122" in line and "couverts" in line.lower() for line in lines)
        total_found = any("3574" in line for line in lines)
        
        if date_found:
            self.log_result("Simulation Date", True, "Date 01/09/2025 trouvée")
        else:
            self.log_result("Simulation Date", False, "Date non trouvée")
        
        if heure_found:
            self.log_result("Simulation Heure", True, "Heure 22:59:38 trouvée")
        else:
            self.log_result("Simulation Heure", False, "Heure non trouvée")
        
        if couverts_found:
            self.log_result("Simulation Couverts", True, "Nombre de couverts 122 trouvé")
        else:
            self.log_result("Simulation Couverts", False, "Nombre de couverts non trouvé")
        
        if total_found:
            self.log_result("Simulation Total", True, "Total TTC 3574 trouvé")
        else:
            self.log_result("Simulation Total", False, "Total TTC non trouvé")
        
    def simulate_specific_validations(self, productions_found):
        """Simule les validations spécifiques demandées"""
        print("\n--- Simulation Validations Spécifiques ---")
        
        # Classifier les productions par type (basé sur le contexte dans le texte)
        test_text = self.create_test_ocr_text()
        lines = test_text.split('\n')
        
        # Trouver les sections
        entrees_section = False
        plats_section = False
        desserts_section = False
        
        entrees_productions = []
        plats_productions = []
        desserts_productions = []
        
        for i, line in enumerate(lines):
            line_clean = line.strip().lower()
            
            # Détecter les sections
            if "entrees" in line_clean and "x" in line_clean:
                entrees_section = True
                plats_section = False
                desserts_section = False
                continue
            elif "plats" in line_clean and "x" in line_clean:
                entrees_section = False
                plats_section = True
                desserts_section = False
                continue
            elif "desserts" in line_clean and "x" in line_clean:
                entrees_section = False
                plats_section = False
                desserts_section = True
                continue
            
            # Classifier les productions selon la section
            if line.startswith(' ') or line.startswith('\t'):  # Production indentée
                for name, quantity, amount in productions_found:
                    if name in line:
                        if entrees_section:
                            entrees_productions.append((name, quantity, amount))
                        elif plats_section:
                            plats_productions.append((name, quantity, amount))
                        elif desserts_section:
                            desserts_productions.append((name, quantity, amount))
        
        # ✅ Entrées : 3 productions détectées
        expected_entrees = ["Salade Caesar", "Tartare saumon", "Soupe du jour"]
        entrees_names = [name for name, _, _ in entrees_productions]
        
        if len(entrees_productions) == 3:
            has_all_entrees = all(any(expected in name for name in entrees_names) for expected in ["Salade", "Tartare", "Soupe"])
            if has_all_entrees:
                self.log_result("✅ Simulation Entrées", True, "3 productions entrées (Salade, Tartare, Soupe)")
            else:
                self.log_result("✅ Simulation Entrées", False, f"Productions entrées: {entrees_names}")
        else:
            self.log_result("✅ Simulation Entrées", False, f"{len(entrees_productions)} productions au lieu de 3")
        
        # ✅ Plats : 3 productions uniquement - PAS de TVA/totaux
        expected_plats = ["Steak frites", "Poisson grillé", "Pasta truffe"]
        plats_names = [name for name, _, _ in plats_productions]
        
        # Vérifier qu'aucun nom de plat ne contient des mots interdits
        forbidden_in_plats = ["tva", "total", "remise", "service", "ht", "ttc"]
        clean_plats = all(not any(forbidden in name.lower() for forbidden in forbidden_in_plats) 
                         for name in plats_names)
        
        if len(plats_productions) == 3 and clean_plats:
            has_all_plats = all(any(expected in name for name in plats_names) for expected in ["Steak", "Poisson", "Pasta"])
            if has_all_plats:
                self.log_result("✅ Simulation Plats", True, "3 productions plats uniquement (Steak, Poisson, Pasta) - PAS de TVA/totaux")
            else:
                self.log_result("✅ Simulation Plats", False, f"Productions plats: {plats_names}")
        else:
            self.log_result("✅ Simulation Plats", False, 
                          f"{len(plats_productions)} productions, clean: {clean_plats}, noms: {plats_names}")
        
        # ✅ Desserts : 2 productions détectées
        expected_desserts = ["Tiramisu", "Tarte citron"]
        desserts_names = [name for name, _, _ in desserts_productions]
        
        if len(desserts_productions) == 2:
            has_all_desserts = all(any(expected in name for name in desserts_names) for expected in ["Tiramisu", "Tarte"])
            if has_all_desserts:
                self.log_result("✅ Simulation Desserts", True, "2 productions desserts (Tiramisu, Tarte)")
            else:
                self.log_result("✅ Simulation Desserts", False, f"Productions desserts: {desserts_names}")
        else:
            self.log_result("✅ Simulation Desserts", False, f"{len(desserts_productions)} productions au lieu de 2")
        
        # ✅ Filtrage global
        all_production_names = [name.lower() for name, _, _ in productions_found]
        global_forbidden = ["tva", "sous-total", "remise", "service", "total ht", "total ttc"]
        
        found_forbidden = []
        for forbidden in global_forbidden:
            if any(forbidden in name for name in all_production_names):
                found_forbidden.append(forbidden)
        
        if len(found_forbidden) == 0:
            self.log_result("✅ Simulation Filtrage Global", True, "TVA, sous-totaux, remises exclus des productions")
        else:
            self.log_result("✅ Simulation Filtrage Global", False, f"Mots-clés non filtrés: {found_forbidden}")

    def test_validation_requirements(self):
        """Test des vérifications spécifiques demandées"""
        print("\n=== VÉRIFICATIONS SPÉCIFIQUES ===")
        
        if self.document_id:
            # Si on a un document, utiliser l'API
            try:
                parse_response = requests.post(f"{BASE_URL}/ocr/parse-z-report-enhanced?document_id={self.document_id}", 
                                             headers=HEADERS)
                
                if parse_response.status_code == 200:
                    analysis_result = parse_response.json()
                    self.validate_api_results(analysis_result)
                else:
                    self.log_result("API Validation", False, f"Erreur API {parse_response.status_code}")
                    self.fallback_validation()
            except Exception as e:
                self.log_result("API Validation", False, f"Exception: {str(e)}")
                self.fallback_validation()
        else:
            # Fallback: validation simulée
            self.fallback_validation()
    
    def validate_api_results(self, analysis_result):
        """Valide les résultats de l'API"""
        productions_detectees = analysis_result.get("productions_detectees", [])
        
        # Grouper par famille
        productions_by_family = {}
        for prod in productions_detectees:
            family = prod.get("family", "Autres")
            if family not in productions_by_family:
                productions_by_family[family] = []
            productions_by_family[family].append(prod)
        
        # Validations comme dans la version originale
        # ... (code de validation identique à la version précédente)
        
    def fallback_validation(self):
        """Validation de fallback sans API"""
        print("Utilisation de la validation de fallback...")
        
        # Utiliser la simulation pour valider
        test_text = self.create_test_ocr_text()
        
        # Tester les patterns directement
        import re
        production_pattern = re.compile(r"^\s*\(?x?(\d+)\)?\s*([^0-9]+?)\s+([0-9]+(?:[,\.][0-9]{2}))$", re.IGNORECASE)
        
        lines = test_text.split('\n')
        productions_found = []
        
        for line in lines:
            if line.startswith(' ') or line.startswith('\t'):
                line_clean = line.strip()
                match = production_pattern.match(line_clean)
                if match:
                    quantity = int(match.group(1))
                    name = match.group(2).strip()
                    amount = float(match.group(3).replace(',', '.'))
                    productions_found.append((name, quantity, amount))
        
        self.simulate_specific_validations(productions_found)

    def test_analyze_z_report_categories(self):
        """Test spécifique de la fonction analyze_z_report_categories optimisée"""
        print("\n=== TEST ANALYZE_Z_REPORT_CATEGORIES OPTIMISÉE ===")
        
        if not self.document_id:
            self.log_result("Analyze Z Report", False, "Pas de document ID disponible")
            return
        
        try:
            # Récupérer le document pour obtenir le texte extrait
            doc_response = requests.get(f"{BASE_URL}/ocr/document/{self.document_id}")
            if doc_response.status_code != 200:
                self.log_result("Get Document", False, f"Erreur {doc_response.status_code}")
                return
            
            document = doc_response.json()
            texte_extrait = document.get("texte_extrait", "")
            
            if not texte_extrait:
                self.log_result("Text Extraction", False, "Pas de texte extrait disponible")
                return
            
            self.log_result("Text Extraction", True, f"Texte extrait: {len(texte_extrait)} caractères")
            
            # Tester l'analyse directe avec le texte
            # Nous devons appeler une fonction qui utilise analyze_z_report_categories
            # Utilisons parse-z-report-enhanced qui devrait utiliser cette fonction
            
            parse_response = requests.post(f"{BASE_URL}/ocr/parse-z-report-enhanced?document_id={self.document_id}", 
                                         headers=HEADERS)
            
            if parse_response.status_code == 200:
                analysis_result = parse_response.json()
                
                # Test 1: Vérification de l'extraction des données principales
                self.test_main_data_extraction(analysis_result)
                
                # Test 2: Vérification de la détection des catégories
                self.test_category_detection(analysis_result)
                
                # Test 3: Vérification de la détection des productions (le plus important)
                self.test_production_detection(analysis_result)
                
                # Test 4: Vérification du filtrage des faux positifs
                self.test_false_positive_filtering(analysis_result)
                
                # Test 5: Vérification de la zone ciblée pour les plats
                self.test_targeted_zone_extraction(analysis_result)
                
            else:
                self.log_result("Parse Z Report Enhanced", False, 
                              f"Erreur {parse_response.status_code}: {parse_response.text}")
                
        except Exception as e:
            self.log_result("Analyze Z Report Categories", False, f"Exception: {str(e)}")

    def test_main_data_extraction(self, analysis_result):
        """Test extraction des données principales"""
        print("\n--- Test Extraction Données Principales ---")
        
        # Vérifier la date de clôture
        date_cloture = analysis_result.get("date_cloture")
        if date_cloture == "01/09/2025":
            self.log_result("Date Clôture", True, f"Date extraite: {date_cloture}")
        else:
            self.log_result("Date Clôture", False, f"Date incorrecte: {date_cloture}")
        
        # Vérifier l'heure de clôture
        heure_cloture = analysis_result.get("heure_cloture")
        if heure_cloture == "22:59:38":
            self.log_result("Heure Clôture", True, f"Heure extraite: {heure_cloture}")
        else:
            self.log_result("Heure Clôture", False, f"Heure incorrecte: {heure_cloture}")
        
        # Vérifier le nombre de couverts
        nombre_couverts = analysis_result.get("nombre_couverts")
        if nombre_couverts == 122.0:
            self.log_result("Nombre Couverts", True, f"Couverts extraits: {nombre_couverts}")
        else:
            self.log_result("Nombre Couverts", False, f"Couverts incorrects: {nombre_couverts}")
        
        # Vérifier le total TTC
        total_ttc = analysis_result.get("total_ttc")
        if total_ttc == 3574.0:
            self.log_result("Total TTC", True, f"Total TTC extrait: {total_ttc}€")
        else:
            self.log_result("Total TTC", False, f"Total TTC incorrect: {total_ttc}")

    def test_category_detection(self, analysis_result):
        """Test détection des catégories"""
        print("\n--- Test Détection Catégories ---")
        
        categories_detectees = analysis_result.get("categories_detectees", [])
        
        # Vérifier qu'on a exactement 3 catégories (Entrées, Plats, Desserts)
        expected_categories = ["Entrees", "Plats principaux", "Desserts"]
        found_categories = [cat.get("nom", "") for cat in categories_detectees]
        
        if len(categories_detectees) == 3:
            self.log_result("Nombre Catégories", True, f"3 catégories détectées: {found_categories}")
        else:
            self.log_result("Nombre Catégories", False, 
                          f"{len(categories_detectees)} catégories au lieu de 3: {found_categories}")
        
        # Vérifier les quantités et montants des catégories
        for cat in categories_detectees:
            nom = cat.get("nom", "")
            quantite = cat.get("quantite", 0)
            prix_total = cat.get("prix_total", 0)
            
            if "Entrees" in nom:
                if quantite == 25 and prix_total == 850.0:
                    self.log_result("Catégorie Entrées", True, f"x{quantite}) {nom} {prix_total}")
                else:
                    self.log_result("Catégorie Entrées", False, 
                                  f"Valeurs incorrectes: x{quantite}) {prix_total}")
            
            elif "Plats" in nom:
                if quantite == 45 and prix_total == 2400.0:
                    self.log_result("Catégorie Plats", True, f"x{quantite}) {nom} {prix_total}")
                else:
                    self.log_result("Catégorie Plats", False, 
                                  f"Valeurs incorrectes: x{quantite}) {prix_total}")
            
            elif "Desserts" in nom:
                if quantite == 18 and prix_total == 324.0:
                    self.log_result("Catégorie Desserts", True, f"x{quantite}) {nom} {prix_total}")
                else:
                    self.log_result("Catégorie Desserts", False, 
                                  f"Valeurs incorrectes: x{quantite}) {prix_total}")

    def test_production_detection(self, analysis_result):
        """Test détection des productions individuelles"""
        print("\n--- Test Détection Productions ---")
        
        productions_detectees = analysis_result.get("productions_detectees", [])
        
        # Vérifier qu'on a exactement 8 productions (3 entrées + 3 plats + 2 desserts)
        expected_count = 8
        if len(productions_detectees) == expected_count:
            self.log_result("Nombre Productions", True, f"{len(productions_detectees)} productions détectées")
        else:
            self.log_result("Nombre Productions", False, 
                          f"{len(productions_detectees)} productions au lieu de {expected_count}")
        
        # Vérifier les productions par famille
        productions_by_family = {}
        for prod in productions_detectees:
            family = prod.get("family", "Autres")
            if family not in productions_by_family:
                productions_by_family[family] = []
            productions_by_family[family].append(prod)
        
        # Test Entrées: 3 productions attendues
        entrees_productions = productions_by_family.get("Entrées", [])
        expected_entrees = ["Salade Caesar", "Tartare saumon", "Soupe du jour"]
        
        if len(entrees_productions) == 3:
            self.log_result("Productions Entrées", True, f"3 productions entrées détectées")
            
            # Vérifier les noms et quantités
            for prod in entrees_productions:
                nom = prod.get("nom", "")
                quantite = prod.get("quantite", 0)
                
                if "Salade Caesar" in nom and quantite == 8:
                    self.log_result("Salade Caesar", True, f"x{quantite}) {nom}")
                elif "Tartare saumon" in nom and quantite == 12:
                    self.log_result("Tartare saumon", True, f"x{quantite}) {nom}")
                elif "Soupe du jour" in nom and quantite == 5:
                    self.log_result("Soupe du jour", True, f"x{quantite}) {nom}")
        else:
            self.log_result("Productions Entrées", False, 
                          f"{len(entrees_productions)} productions entrées au lieu de 3")
        
        # Test Plats: 3 productions attendues (CRITIQUE - pas de TVA/totaux)
        plats_productions = productions_by_family.get("Plats", [])
        expected_plats = ["Steak frites", "Poisson grillé", "Pasta truffe"]
        
        if len(plats_productions) == 3:
            self.log_result("Productions Plats", True, f"3 productions plats détectées")
            
            # Vérifier qu'aucune production ne contient des mots-clés interdits
            forbidden_keywords = ["tva", "total", "remise", "service", "ht", "ttc"]
            clean_productions = True
            
            for prod in plats_productions:
                nom = prod.get("nom", "").lower()
                if any(keyword in nom for keyword in forbidden_keywords):
                    clean_productions = False
                    self.log_result("Filtrage Plats", False, 
                                  f"Production contient mot-clé interdit: {prod.get('nom')}")
            
            if clean_productions:
                self.log_result("Filtrage Plats", True, "Aucun faux positif dans les plats")
            
            # Vérifier les productions spécifiques
            for prod in plats_productions:
                nom = prod.get("nom", "")
                quantite = prod.get("quantite", 0)
                
                if "Steak frites" in nom and quantite == 12:
                    self.log_result("Steak frites", True, f"x{quantite}) {nom}")
                elif "Poisson grillé" in nom and quantite == 8:
                    self.log_result("Poisson grillé", True, f"x{quantite}) {nom}")
                elif "Pasta truffe" in nom and quantite == 15:
                    self.log_result("Pasta truffe", True, f"x{quantite}) {nom}")
        else:
            self.log_result("Productions Plats", False, 
                          f"{len(plats_productions)} productions plats au lieu de 3")
        
        # Test Desserts: 2 productions attendues
        desserts_productions = productions_by_family.get("Desserts", [])
        
        if len(desserts_productions) == 2:
            self.log_result("Productions Desserts", True, f"2 productions desserts détectées")
            
            for prod in desserts_productions:
                nom = prod.get("nom", "")
                quantite = prod.get("quantite", 0)
                
                if "Tiramisu" in nom and quantite == 12:
                    self.log_result("Tiramisu", True, f"x{quantite}) {nom}")
                elif "Tarte citron" in nom and quantite == 6:
                    self.log_result("Tarte citron", True, f"x{quantite}) {nom}")
        else:
            self.log_result("Productions Desserts", False, 
                          f"{len(desserts_productions)} productions desserts au lieu de 2")

    def test_false_positive_filtering(self, analysis_result):
        """Test du filtrage des faux positifs"""
        print("\n--- Test Filtrage Faux Positifs ---")
        
        productions_detectees = analysis_result.get("productions_detectees", [])
        
        # Mots-clés qui ne doivent PAS apparaître dans les productions
        forbidden_keywords = [
            "tva", "total", "sous-total", "remise", "service", "pourboire",
            "ht", "ttc", "solde", "caisse", "espece", "carte", "cheque"
        ]
        
        false_positives = []
        for prod in productions_detectees:
            nom = prod.get("nom", "").lower()
            for keyword in forbidden_keywords:
                if keyword in nom:
                    false_positives.append(f"{prod.get('nom')} (contient '{keyword}')")
        
        if len(false_positives) == 0:
            self.log_result("Filtrage Faux Positifs", True, "Aucun faux positif détecté")
        else:
            self.log_result("Filtrage Faux Positifs", False, 
                          f"Faux positifs détectés: {false_positives}")
        
        # Vérifier spécifiquement que les patterns de pourcentage sont ignorés
        percentage_patterns = []
        for prod in productions_detectees:
            nom = prod.get("nom", "")
            if "%" in nom or "10%" in nom or "20%" in nom or "15%" in nom:
                percentage_patterns.append(nom)
        
        if len(percentage_patterns) == 0:
            self.log_result("Filtrage Pourcentages", True, "Patterns de pourcentage ignorés")
        else:
            self.log_result("Filtrage Pourcentages", False, 
                          f"Patterns de pourcentage détectés: {percentage_patterns}")

    def test_targeted_zone_extraction(self, analysis_result):
        """Test de l'extraction ciblée par zone pour les plats"""
        print("\n--- Test Zone Ciblée Plats ---")
        
        # Vérifier les zones de catégories
        category_zones = analysis_result.get("category_zones", {})
        entrees_end_line = analysis_result.get("entrees_end_line")
        desserts_start_line = analysis_result.get("desserts_start_line")
        
        if category_zones:
            self.log_result("Category Zones", True, f"Zones détectées: {list(category_zones.keys())}")
        else:
            self.log_result("Category Zones", False, "Aucune zone de catégorie détectée")
        
        if entrees_end_line is not None:
            self.log_result("Entrées End Line", True, f"Fin entrées ligne: {entrees_end_line}")
        else:
            self.log_result("Entrées End Line", False, "Ligne de fin des entrées non détectée")
        
        if desserts_start_line is not None:
            self.log_result("Desserts Start Line", True, f"Début desserts ligne: {desserts_start_line}")
        else:
            self.log_result("Desserts Start Line", False, "Ligne de début des desserts non détectée")
        
        # Vérifier que la zone des plats est bien délimitée
        if entrees_end_line is not None and desserts_start_line is not None:
            if desserts_start_line > entrees_end_line:
                self.log_result("Zone Plats Délimitée", True, 
                              f"Zone plats: lignes {entrees_end_line+1} à {desserts_start_line-1}")
            else:
                self.log_result("Zone Plats Délimitée", False, 
                              "Zone plats mal délimitée")

    def test_validation_requirements(self):
        """Test des vérifications spécifiques demandées"""
        print("\n=== VÉRIFICATIONS SPÉCIFIQUES ===")
        
        if not self.document_id:
            self.log_result("Validation Requirements", False, "Pas de document pour validation")
            return
        
        try:
            # Récupérer les données analysées
            parse_response = requests.post(f"{BASE_URL}/ocr/parse-z-report-enhanced?document_id={self.document_id}", 
                                         headers=HEADERS)
            
            if parse_response.status_code != 200:
                self.log_result("Get Analysis Data", False, f"Erreur {parse_response.status_code}")
                return
            
            analysis_result = parse_response.json()
            productions_detectees = analysis_result.get("productions_detectees", [])
            
            # Grouper par famille
            productions_by_family = {}
            for prod in productions_detectees:
                family = prod.get("family", "Autres")
                if family not in productions_by_family:
                    productions_by_family[family] = []
                productions_by_family[family].append(prod)
            
            # ✅ **Entrées** : 3 productions détectées (Salade, Tartare, Soupe)
            entrees = productions_by_family.get("Entrées", [])
            if len(entrees) == 3:
                entrees_names = [p.get("nom", "") for p in entrees]
                has_salade = any("Salade" in name for name in entrees_names)
                has_tartare = any("Tartare" in name for name in entrees_names)
                has_soupe = any("Soupe" in name for name in entrees_names)
                
                if has_salade and has_tartare and has_soupe:
                    self.log_result("✅ Entrées Validation", True, 
                                  "3 productions détectées (Salade, Tartare, Soupe)")
                else:
                    self.log_result("✅ Entrées Validation", False, 
                                  f"Productions manquantes dans: {entrees_names}")
            else:
                self.log_result("✅ Entrées Validation", False, 
                              f"{len(entrees)} productions au lieu de 3")
            
            # ✅ **Plats** : 3 productions uniquement (Steak, Poisson, Pasta) - PAS de TVA/totaux
            plats = productions_by_family.get("Plats", [])
            if len(plats) == 3:
                plats_names = [p.get("nom", "") for p in plats]
                has_steak = any("Steak" in name for name in plats_names)
                has_poisson = any("Poisson" in name for name in plats_names)
                has_pasta = any("Pasta" in name for name in plats_names)
                
                # Vérifier qu'aucun nom ne contient TVA/total
                clean_names = all(not any(keyword in name.lower() for keyword in ["tva", "total", "remise"]) 
                                for name in plats_names)
                
                if has_steak and has_poisson and has_pasta and clean_names:
                    self.log_result("✅ Plats Validation", True, 
                                  "3 productions uniquement (Steak, Poisson, Pasta) - PAS de TVA/totaux")
                else:
                    self.log_result("✅ Plats Validation", False, 
                                  f"Problème dans: {plats_names}, clean: {clean_names}")
            else:
                self.log_result("✅ Plats Validation", False, 
                              f"{len(plats)} productions au lieu de 3")
            
            # ✅ **Desserts** : 2 productions détectées (Tiramisu, Tarte)
            desserts = productions_by_family.get("Desserts", [])
            if len(desserts) == 2:
                desserts_names = [p.get("nom", "") for p in desserts]
                has_tiramisu = any("Tiramisu" in name for name in desserts_names)
                has_tarte = any("Tarte" in name for name in desserts_names)
                
                if has_tiramisu and has_tarte:
                    self.log_result("✅ Desserts Validation", True, 
                                  "2 productions détectées (Tiramisu, Tarte)")
                else:
                    self.log_result("✅ Desserts Validation", False, 
                                  f"Productions manquantes dans: {desserts_names}")
            else:
                self.log_result("✅ Desserts Validation", False, 
                              f"{len(desserts)} productions au lieu de 2")
            
            # ✅ **Filtrage** : TVA, sous-totaux, remises exclus des productions
            all_productions_names = [p.get("nom", "").lower() for p in productions_detectees]
            filtered_keywords = ["tva", "sous-total", "remise", "service", "total ht", "total ttc"]
            
            found_filtered = []
            for keyword in filtered_keywords:
                if any(keyword in name for name in all_productions_names):
                    found_filtered.append(keyword)
            
            if len(found_filtered) == 0:
                self.log_result("✅ Filtrage Validation", True, 
                              "TVA, sous-totaux, remises exclus des productions")
            else:
                self.log_result("✅ Filtrage Validation", False, 
                              f"Mots-clés non filtrés: {found_filtered}")
            
            # ✅ **Zone ciblée** : Productions plats extraites entre fin entrées et début desserts
            entrees_end_line = analysis_result.get("entrees_end_line")
            desserts_start_line = analysis_result.get("desserts_start_line")
            category_zones = analysis_result.get("category_zones", {})
            
            if entrees_end_line is not None and desserts_start_line is not None and category_zones:
                self.log_result("✅ Zone Ciblée Validation", True, 
                              f"Productions plats extraites entre lignes {entrees_end_line} et {desserts_start_line}")
            else:
                self.log_result("✅ Zone Ciblée Validation", False, 
                              "Zone ciblée non correctement délimitée")
                
        except Exception as e:
            self.log_result("Validation Requirements", False, f"Exception: {str(e)}")

    def run_all_tests(self):
        """Exécute tous les tests"""
        print("🎯 DÉBUT DES TESTS OCR SÉQUENTIEL - ÉVITER FAUX POSITIFS PLATS")
        print("=" * 80)
        
        # Test 1: Logique séquentielle
        self.test_sequential_logic_extraction()
        
        # Test 2: Vérifications spécifiques
        self.test_validation_requirements()
        
        # Résumé des résultats
        self.print_summary()

    def print_summary(self):
        """Affiche le résumé des tests"""
        print("\n" + "=" * 80)
        print("📊 RÉSUMÉ DES TESTS OCR SÉQUENTIEL")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["success"]])
        failed_tests = total_tests - passed_tests
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Total des tests: {total_tests}")
        print(f"Tests réussis: {passed_tests}")
        print(f"Tests échoués: {failed_tests}")
        print(f"Taux de réussite: {success_rate:.1f}%")
        
        if failed_tests > 0:
            print(f"\n❌ TESTS ÉCHOUÉS ({failed_tests}):")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['test']}: {result['message']}")
        
        print(f"\n🎯 CONCLUSION:")
        if success_rate >= 90:
            print("✅ FONCTION OCR OPTIMISÉE VALIDÉE - Faux positifs évités avec succès!")
        elif success_rate >= 75:
            print("⚠️ FONCTION OCR PARTIELLEMENT VALIDÉE - Quelques améliorations nécessaires")
        else:
            print("❌ FONCTION OCR NON VALIDÉE - Corrections importantes requises")

if __name__ == "__main__":
    print("🚀 Lancement des tests OCR séquentiel pour éviter les faux positifs dans la catégorie Plats")
    
    test_suite = OCRSequentialTestSuite()
    test_suite.run_all_tests()
    
    # Retourner le code de sortie approprié
    failed_tests = len([r for r in test_suite.test_results if not r["success"]])
    sys.exit(0 if failed_tests == 0 else 1)