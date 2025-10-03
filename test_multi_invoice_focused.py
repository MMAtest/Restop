#!/usr/bin/env python3
"""
Test ciblé pour la fonctionnalité multi-factures OCR
Focus sur les fonctions detect_multiple_invoices() et check_invoice_quality()
"""

import requests
import json
from datetime import datetime

# Configuration
BASE_URL = "https://ocrstockpro.preview.emergentagent.com/api"
HEADERS = {"Content-Type": "application/json"}
METRO_PDF_URL = "https://customer-assets.emergentagent.com/job_ocrstockpro/artifacts/dbb8qsl7_METRO.pdf"

def test_metro_pdf_with_correct_type():
    """Test METRO.pdf avec le bon type de document"""
    print("🎯 TEST METRO.PDF AVEC TYPE FACTURE_FOURNISSEUR")
    print("=" * 60)
    
    # Télécharger METRO.pdf
    try:
        print("📥 Téléchargement METRO.pdf...")
        response = requests.get(METRO_PDF_URL, timeout=30)
        if response.status_code != 200:
            print(f"❌ Erreur téléchargement: {response.status_code}")
            return
        
        metro_content = response.content
        print(f"✅ Fichier téléchargé: {len(metro_content)} bytes")
        
        # Upload avec le bon type de document
        files = {
            'file': ('METRO.pdf', metro_content, 'application/pdf')
        }
        data = {'document_type': 'facture_fournisseur'}  # Type correct !
        
        print("🔄 Upload avec document_type=facture_fournisseur...")
        upload_response = requests.post(f"{BASE_URL}/ocr/upload-document", files=files, data=data)
        
        print(f"📊 Status Code: {upload_response.status_code}")
        
        if upload_response.status_code in [200, 201]:
            result = upload_response.json()
            print("✅ Upload réussi!")
            
            # Analyser la réponse
            print("\n📋 ANALYSE DE LA RÉPONSE:")
            print("-" * 40)
            
            # Vérifier les champs multi-invoice
            multi_invoice = result.get("multi_invoice")
            print(f"multi_invoice: {multi_invoice}")
            
            total_detected = result.get("total_detected", 0)
            print(f"total_detected: {total_detected}")
            
            successfully_processed = result.get("successfully_processed", 0)
            print(f"successfully_processed: {successfully_processed}")
            
            rejected_count = result.get("rejected_count", 0)
            print(f"rejected_count: {rejected_count}")
            
            document_ids = result.get("document_ids", [])
            print(f"document_ids: {len(document_ids)} documents créés")
            
            rejected_invoices = result.get("rejected_invoices", [])
            print(f"rejected_invoices: {len(rejected_invoices)} factures rejetées")
            
            processing_summary = result.get("processing_summary", [])
            print(f"processing_summary: {len(processing_summary)} messages")
            
            message = result.get("message", "")
            print(f"message: {message}")
            
            file_type = result.get("file_type", "")
            print(f"file_type: {file_type}")
            
            has_quality_issues = result.get("has_quality_issues", False)
            print(f"has_quality_issues: {has_quality_issues}")
            
            # Si c'est une réponse multi-invoice, analyser les détails
            if multi_invoice:
                print("\n🎉 MULTI-INVOICE DÉTECTÉ!")
                print("-" * 40)
                
                if total_detected == 14:
                    print("✅ Nombre correct de documents détectés (14)")
                else:
                    print(f"⚠️ Nombre inattendu: {total_detected} au lieu de 14")
                
                if document_ids:
                    print(f"✅ {len(document_ids)} documents créés en base")
                    
                    # Vérifier le premier document
                    first_doc_id = document_ids[0]
                    doc_response = requests.get(f"{BASE_URL}/ocr/document/{first_doc_id}")
                    if doc_response.status_code == 200:
                        doc_data = doc_response.json()
                        print(f"✅ Premier document récupéré: {doc_data.get('nom_fichier', 'N/A')}")
                        
                        # Vérifier les métadonnées de séparation
                        separation_info = doc_data.get("donnees_parsees", {}).get("separation_info", {})
                        if separation_info:
                            print("✅ Métadonnées de séparation présentes:")
                            for key, value in separation_info.items():
                                print(f"   {key}: {value}")
                        else:
                            print("❌ Métadonnées de séparation manquantes")
                
                if rejected_invoices:
                    print(f"⚠️ {len(rejected_invoices)} factures rejetées:")
                    for rejected in rejected_invoices:
                        print(f"   - Facture {rejected.get('index', 'N/A')}: {rejected.get('reason', 'N/A')}")
                        print(f"     Qualité: {rejected.get('quality_score', 'N/A')}")
                
                if processing_summary:
                    print("\n📝 Résumé du traitement:")
                    for summary in processing_summary:
                        print(f"   {summary}")
                        
            else:
                print("\n❌ MULTI-INVOICE NON DÉTECTÉ")
                print("Possible causes:")
                print("- Extraction de texte échouée")
                print("- Patterns de détection non matchés")
                print("- Logique de détection défaillante")
                
                # Vérifier si c'est une réponse de facture unique
                if "document_id" in result:
                    print(f"📄 Traité comme facture unique: {result.get('document_id')}")
                    
                    # Récupérer le document pour voir le texte extrait
                    doc_response = requests.get(f"{BASE_URL}/ocr/document/{result['document_id']}")
                    if doc_response.status_code == 200:
                        doc_data = doc_response.json()
                        texte_extrait = doc_data.get("texte_extrait", "")
                        print(f"📝 Texte extrait: {len(texte_extrait)} caractères")
                        
                        if len(texte_extrait) < 500:
                            print("⚠️ Texte très court - possible problème d'extraction")
                            print(f"Aperçu: {texte_extrait[:200]}...")
                        else:
                            print("✅ Texte extrait semble correct")
                            # Chercher des patterns METRO dans le texte
                            if "METRO" in texte_extrait.upper():
                                print("✅ Pattern METRO trouvé dans le texte")
                            else:
                                print("❌ Pattern METRO non trouvé")
        else:
            print(f"❌ Erreur upload: {upload_response.status_code}")
            print(f"Réponse: {upload_response.text}")
            
    except Exception as e:
        print(f"❌ Exception: {str(e)}")

def test_simple_multi_invoice_simulation():
    """Test avec un contenu simulé multi-factures"""
    print("\n🧪 TEST SIMULATION MULTI-FACTURES")
    print("=" * 60)
    
    # Créer un contenu simulé avec plusieurs factures
    multi_invoice_text = """
METRO FRANCE FACTURE N°12345
Date: 01/01/2025
Fournisseur: METRO Cash & Carry
Total: 150.00 EUR
NET A PAYER: 150.00 EUR

---

LE DIAMANT DU TERROIR
BON DE LIVRAISON N°67890
Date: 02/01/2025
Produits de qualité
Total TTC: 89.50 EUR

---

GFD LERDA INVOICE ABC123
Date: 03/01/2025
Spécialités italiennes
MONTANT TOTAL: 245.75 EUR
"""
    
    # Créer un "PDF" simulé avec ce contenu
    simulated_pdf = multi_invoice_text.encode('utf-8')
    
    try:
        files = {
            'file': ('multi_factures_test.pdf', simulated_pdf, 'application/pdf')
        }
        data = {'document_type': 'facture_fournisseur'}
        
        print("🔄 Upload contenu multi-factures simulé...")
        response = requests.post(f"{BASE_URL}/ocr/upload-document", files=files, data=data)
        
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code in [200, 201]:
            result = response.json()
            print("✅ Upload réussi!")
            
            # Analyser la réponse
            multi_invoice = result.get("multi_invoice")
            total_detected = result.get("total_detected", 0)
            
            print(f"multi_invoice: {multi_invoice}")
            print(f"total_detected: {total_detected}")
            
            if multi_invoice and total_detected >= 2:
                print("🎉 Simulation multi-factures réussie!")
            else:
                print("❌ Simulation échouée - traité comme facture unique")
                
        else:
            print(f"❌ Erreur: {response.status_code}")
            print(f"Réponse: {response.text}")
            
    except Exception as e:
        print(f"❌ Exception: {str(e)}")

def cleanup_test_documents():
    """Nettoie les documents de test"""
    print("\n🧹 NETTOYAGE DES DOCUMENTS DE TEST")
    print("=" * 60)
    
    try:
        # Récupérer tous les documents
        response = requests.get(f"{BASE_URL}/ocr/documents")
        if response.status_code == 200:
            documents = response.json()
            
            # Filtrer les documents de test
            test_docs = [doc for doc in documents if 
                        "METRO.pdf" in doc.get("nom_fichier", "") or 
                        "multi_factures_test.pdf" in doc.get("nom_fichier", "") or
                        "Facture" in doc.get("nom_fichier", "")]
            
            print(f"📋 {len(test_docs)} documents de test trouvés")
            
            for doc in test_docs:
                doc_id = doc.get("id")
                nom_fichier = doc.get("nom_fichier", "N/A")
                
                try:
                    delete_response = requests.delete(f"{BASE_URL}/ocr/document/{doc_id}")
                    if delete_response.status_code == 200:
                        print(f"✅ Supprimé: {nom_fichier}")
                    else:
                        print(f"❌ Erreur suppression {nom_fichier}: {delete_response.status_code}")
                except Exception as e:
                    print(f"❌ Exception suppression {nom_fichier}: {str(e)}")
        else:
            print(f"❌ Erreur récupération documents: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Exception nettoyage: {str(e)}")

if __name__ == "__main__":
    print("🎯 TEST CIBLÉ MULTI-INVOICE OCR")
    print("=" * 80)
    
    # Test principal avec METRO.pdf
    test_metro_pdf_with_correct_type()
    
    # Test de simulation
    test_simple_multi_invoice_simulation()
    
    # Nettoyage
    cleanup_test_documents()
    
    print("\n🎯 TESTS TERMINÉS")