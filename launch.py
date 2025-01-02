import os
import sys
import venv
import subprocess

def setup_venv():
    venv_path = "venv"
    
    # Créer l'environnement virtuel s'il n'existe pas
    if not os.path.exists(venv_path):
        print("Création de l'environnement virtuel...")
        venv.create(venv_path, with_pip=True)
    
    # Déterminer le chemin de l'exécutable python
    if sys.platform == "win32":
        python_path = os.path.join(venv_path, "Scripts", "python")
    else:
        python_path = os.path.join(venv_path, "bin", "python")

    # Installer les dépendances
    print("Installation des dépendances...")
    subprocess.run([python_path, "-m", "pip", "install", "-r", "requirements.txt"])
    
    # Lancer l'application
    print("Lancement de l'application...")
    subprocess.run([python_path, "FDP2imgPrevie.py"])

if __name__ == "__main__":
    setup_venv() 