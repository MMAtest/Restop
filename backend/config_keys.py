"""
Configuration des cles API pour la production
Les cles sont chargees depuis les variables d'environnement
"""
import os

EMERGENT_LLM_KEY = os.environ.get("EMERGENT_LLM_KEY", "")
