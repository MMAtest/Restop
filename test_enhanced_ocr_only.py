#!/usr/bin/env python3
"""
Test spécifique pour les nouvelles APIs Enhanced OCR Parsing - Version 3 Feature #2
"""

import requests
import json
import base64
from PIL import Image, ImageDraw, ImageFont
import io
from datetime import datetime

# Configuration
BASE_URL = "https://smart-inventory-63.preview.emergentagent.com/api"
HEADERS = {"Content-Type": "application/json"}

def create_mock_base64_image(text_content):
    """Créer une image base64 simulée avec du texte pour les tests OCR"""
    from PIL import Image, ImageDraw, ImageFont
    import io
    
    # Créer une image blanche
    img = Image.new('RGB', (400, 200), color='white')
    draw = ImageDraw.Draw(img)
    
    # Ajouter le texte (utiliser une police par défaut)
    try:
        # Essayer d'utiliser une police par défaut
        font = ImageFont.load_default()
    except:
        font = None
    
    # Diviser le texte en lignes et les dessiner
    lines = text_content.strip().split('\n')
    y_offset = 10
    for line in lines:
        if line.strip():
            draw.text((10, y_offset), line.strip(), fill='black', font=font)
            y_offset += 20
    
    # Convertir en base64
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    
    return base64.b64encode(buffer.getvalue()).decode()

def test_enhanced_ocr_apis():
    """Test des nouvelles APIs Enhanced OCR"""
    print("🆕 TEST VERSION 3 ENHANCED OCR PARSING APIs")
    print("=" * 60)
    
    # Créer un document OCR de test
    enhanced_z_report_text = """
    RAPPORT Z - Service Soir - 06/01/2025
    
    === BAR ===
    (x3) Vin rouge Côtes du Rhône
    (x2) Kir Royal
    
    === ENTRÉES ===
    (x4) Supions en persillade de Mamie
    (x2) Salade de tomates anciennes
    
    === PLATS ===
    (x3) Linguine aux palourdes & sauce à l'ail
    (x2) Rigatoni à la truffe fraîche de Forcalquier
    (x1) Bœuf Wellington à la truffe
    
    === DESSERTS ===
    (x2) Tiramisu maison
    (x1) Tarte aux figues
    
    TOTAL CA: 285.50€
    Couverts: 12
    """
    
    # Créer et uploader le document de test
    mock_image_base64 = create_mock_base64_image(enhanced_z_report_text)
    test_document_id = None
    
    print("\n--- Upload Document Test ---")
    try:
        files = {
            'file': ('enhanced_z_report_test.jpg', base64.b64decode(mock_image_base64), 'image/jpeg')
        }
        data = {'document_type': 'z_report'}
        
        response = requests.post(f"{BASE_URL}/ocr/upload-document", files=files, data=data)
        if response.status_code == 200 or response.status_code == 201:
            result = response.json()
            test_document_id = result.get("document_id")
            print(f"✅ Document créé: {test_document_id[:8]}...")
        else:
            print(f"❌ Erreur upload: {response.status_code} - {response.text}")
            return
    except Exception as e:
        print(f"❌ Exception upload: {str(e)}")
        return
    
    # Test 1: POST /api/ocr/parse-z-report-enhanced
    print("\n--- Test Enhanced Z Report Parsing ---")
    try:
        response = requests.post(f"{BASE_URL}/ocr/parse-z-report-enhanced?document_id={test_document_id}", 
                               headers=HEADERS)
        if response.status_code == 200:
            structured_data = response.json()
            print(f"✅ Enhanced parsing réussi")
            print(f"   - Service: {structured_data.get('service', 'N/A')}")
            print(f"   - Date: {structured_data.get('report_date', 'N/A')}")
            print(f"   - Total CA: {structured_data.get('grand_total_sales', 'N/A')}€")
            
            categories = structured_data.get("items_by_category", {})
            for category, items in categories.items():
                print(f"   - {category}: {len(items)} item(s)")
        else:
            print(f"❌ Erreur parsing: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Exception parsing: {str(e)}")
    
    # Test 2: GET /api/ocr/z-report-preview/{document_id}
    print("\n--- Test Z Report Preview ---")
    if test_document_id:
        try:
            response = requests.get(f"{BASE_URL}/ocr/z-report-preview/{test_document_id}")
            if response.status_code == 200:
                preview_data = response.json()
                print(f"✅ Preview réussi")
                print(f"   - Preview only: {preview_data.get('preview_only')}")
                print(f"   - Can apply: {preview_data.get('can_apply')}")
                
                validation_result = preview_data.get("validation_result", {})
                deductions = validation_result.get("proposed_deductions", [])
                print(f"   - Déductions proposées: {len(deductions)}")
            else:
                print(f"❌ Erreur preview: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"❌ Exception preview: {str(e)}")
    
    # Test 3: POST /api/ocr/calculate-stock-deductions
    print("\n--- Test Stock Deductions Calculation ---")
    try:
        test_structured_data = {
            "report_date": "06/01/2025",
            "service": "Soir",
            "items_by_category": {
                "Plats": [
                    {"name": "Linguine aux palourdes", "quantity_sold": 3, "category": "Plats"},
                    {"name": "Supions en persillade", "quantity_sold": 4, "category": "Plats"}
                ]
            },
            "grand_total_sales": 285.50,
            "raw_items": []
        }
        
        response = requests.post(f"{BASE_URL}/ocr/calculate-stock-deductions", 
                               json=test_structured_data, headers=HEADERS)
        if response.status_code == 200:
            validation_result = response.json()
            print(f"✅ Calcul déductions réussi")
            print(f"   - Can validate: {validation_result.get('can_validate')}")
            print(f"   - Total deductions: {validation_result.get('total_deductions')}")
            print(f"   - Warnings: {len(validation_result.get('warnings', []))}")
            print(f"   - Errors: {len(validation_result.get('errors', []))}")
            
            deductions = validation_result.get("proposed_deductions", [])
            for deduction in deductions:
                print(f"   - Recette: {deduction.get('recipe_name')} (x{deduction.get('quantity_sold')})")
        else:
            print(f"❌ Erreur calcul déductions: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Exception calcul déductions: {str(e)}")
    
    # Test 4: POST /api/ocr/validate-z-report (preview mode)
    print("\n--- Test Z Report Validation (Preview) ---")
    if test_document_id:
        try:
            response = requests.post(f"{BASE_URL}/ocr/validate-z-report?document_id={test_document_id}&apply_deductions=false", 
                                   headers=HEADERS)
            if response.status_code == 200:
                validation_response = response.json()
                print(f"✅ Validation preview réussie")
                print(f"   - Applied: {validation_response.get('applied')}")
                print(f"   - Document ID: {validation_response.get('document_id', 'N/A')[:8]}...")
            else:
                print(f"❌ Erreur validation: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"❌ Exception validation: {str(e)}")
    
    print("\n" + "=" * 60)
    print("✅ Tests Enhanced OCR terminés")

if __name__ == "__main__":
    test_enhanced_ocr_apis()