import os
import sys
import venv
import subprocess
import platform
import time

def is_venv():
    return hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)

def wait_for_venv(python_path, max_attempts=10):
    """Attend que l'environnement virtuel soit prêt"""
    for i in range(max_attempts):
        if os.path.exists(python_path):
            time.sleep(1)  # Attendre que les fichiers soient complètement écrits
            return True
        time.sleep(1)
    return False

def setup_venv():
    venv_path = "venv"
    
    # Déterminer les chemins selon la plateforme
    if platform.system() == "Windows":
        python_path = os.path.join(venv_path, "Scripts", "python.exe")
        pip_path = os.path.join(venv_path, "Scripts", "pip.exe")
    else:
        python_path = os.path.join(venv_path, "bin", "python")
        pip_path = os.path.join(venv_path, "bin", "pip")

    # Si nous ne sommes pas dans un environnement virtuel
    if not is_venv():
        if not os.path.exists(venv_path):
            print("Création de l'environnement virtuel...")
            venv.create(venv_path, with_pip=True)
            
            if not wait_for_venv(python_path):
                print("Erreur: La création de l'environnement virtuel a échoué")
                sys.exit(1)
            
            # Mise à jour de pip dans le nouvel environnement
            try:
                subprocess.run([python_path, "-m", "ensurepip", "--upgrade"], check=True)
                subprocess.run([python_path, "-m", "pip", "install", "--upgrade", "pip"], check=True)
            except subprocess.CalledProcessError as e:
                print(f"Erreur lors de la configuration de pip: {e}")
                sys.exit(1)
        
        print("Relancement dans l'environnement virtuel...")
        if not os.path.exists(python_path):
            print(f"Erreur: L'environnement virtuel semble corrompu. Essayez de supprimer le dossier {venv_path} et relancez le script.")
            sys.exit(1)
            
        try:
            subprocess.run([python_path, __file__], check=True)
            sys.exit(0)
        except subprocess.CalledProcessError as e:
            print(f"Erreur lors du relancement dans l'environnement virtuel: {e}")
            sys.exit(1)

    # Le reste du code s'exécute uniquement dans l'environnement virtuel
    if not os.path.exists("requirements.txt"):
        print("Erreur: Le fichier requirements.txt n'a pas été trouvé.")
        sys.exit(1)

    print("Installation des dépendances...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Erreur lors de l'installation des dépendances: {e}")
        sys.exit(1)

    if not os.path.exists("FDP2imgPrevie.py"):
        print("Erreur: Le fichier FDP2imgPrevie.py n'a pas été trouvé.")
        sys.exit(1)

    print("Lancement de l'application...")
    try:
        subprocess.run([sys.executable, "FDP2imgPrevie.py"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Erreur lors du lancement de l'application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    setup_venv()