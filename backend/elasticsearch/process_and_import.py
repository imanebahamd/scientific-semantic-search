#!/usr/bin/env python3
"""
Script maître pour le pipeline de données dans Docker.
Exécute le nettoyage, l'enrichissement et l'importation.
"""
import subprocess
import sys
import os

def run_script(script_name, args=""):
    """Exécute un script Python et retourne True en cas de succès."""
    script_path = f"/app/data/scripts/{script_name}"
    if os.path.exists(script_path):
        print(f"▶ Exécution de {script_name}...")
        result = subprocess.run([sys.executable, script_path] + args.split(), capture_output=True, text=True)
        if result.returncode == 0:
            print(f"  ✅ {script_name} terminé avec succès")
            return True
        else:
            print(f"  ❌ Erreur avec {script_name}: {result.stderr}")
            return False
    else:
        print(f"  ⚠ Script non trouvé: {script_path}")
        return False

def main():
    print("🚀 DÉMARRAGE DU PIPELINE DE DONNÉES DOCKER")
    print("=" * 50)

    # 1. Nettoyer les données (depuis les fichiers .json et .xml bruts)
    if not run_script("clean_data.py"):
        print("Le nettoyage a échoué, poursuite avec les données existantes...")

    # 2. Enrichir les données nettoyées
    if not run_script("enhance_data.py"):
        print("L'enrichissement a échoué, poursuite avec les données nettoyées...")

    # 3. Exécuter l'importateur principal (pointant vers le fichier enrichi)
    print("▶ Exécution de l'importateur principal...")
    os.chdir("/app/backend/elasticsearch")
    result = subprocess.run([sys.executable, "data_importer.py"], capture_output=True, text=True)
    if result.returncode == 0:
        print("✅ Importateur principal terminé avec succès")
        print(result.stdout)
    else:
        print("❌ L'importateur principal a échoué")
        print(result.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
