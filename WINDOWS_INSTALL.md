# Installation sur Windows

## Problème avec le CLI pdfanalysis-app

Sur Windows, si la commande `pdfanalysis-app` ne fonctionne pas après l'installation, voici les solutions:

### Solution 1: Vérifier le PATH (Recommandé)

Après installation avec pip, vérifiez que le dossier Scripts de votre environnement Python est dans le PATH:

```cmd
# Pour un environnement virtuel
set PATH=%PATH%;%VIRTUAL_ENV%\Scripts

# Pour conda
set PATH=%PATH%;%CONDA_PREFIX%\Scripts
```

Pour ajouter de manière permanente:
1. Cherchez "Variables d'environnement" dans le menu Démarrer
2. Modifiez la variable PATH
3. Ajoutez: `C:\Users\VotreNom\Anaconda3\Scripts` (ou le chemin de votre environnement)

### Solution 2: Réinstaller proprement

```cmd
# Désinstaller
pip uninstall pdfanalysis

# Nettoyer le cache
pip cache purge

# Réinstaller
pip install --no-cache-dir .
```

### Solution 3: Utiliser le fichier .bat

Si le .exe ne fonctionne pas, utilisez:
```cmd
pdfanalysis-app.bat
```

### Solution 4: Lancer directement avec Python

```cmd
python -m pdfanalysis.app_pdf_analysis
```

ou

```cmd
streamlit run pdfanalysis/app_pdf_analysis.py
```

### Solution 5: Vérifier l'installation

Pour vérifier que le script est bien installé:

```cmd
# Voir où est installé le script
where pdfanalysis-app

# Lister les scripts installés par pip
pip show -f pdfanalysis | findstr Scripts
```

## Installation recommandée

### Avec conda (Recommandé pour Windows)

```cmd
# Créer un environnement
conda create -n pdfanalysis python=3.10
conda activate pdfanalysis

# Installer depuis le dossier du projet
cd C:\chemin\vers\PDFanalysis_streamlit
pip install -e .

# Vérifier l'installation
pdfanalysis-app --help
```

### Avec pip et venv

```cmd
# Créer un environnement virtuel
python -m venv venv

# Activer l'environnement
venv\Scripts\activate

# Installer
pip install -e .

# Lancer
pdfanalysis-app
```

## Dépannage

### Erreur: "pdfanalysis-app n'est pas reconnu"

1. Vérifiez que l'environnement est activé
2. Vérifiez le PATH (voir Solution 1)
3. Essayez de relancer le terminal en tant qu'administrateur

### Erreur: "No module named 'app_pdf_analysis'"

Le module n'est pas dans le PYTHONPATH. Assurez-vous que:
- L'installation a bien été faite avec `pip install .` ou `pip install pdfanalysis`
- Le fichier `app_pdf_analysis.py` est présent dans le dossier `pdfanalysis/`

### Le .exe existe mais ne lance rien

Essayez de lancer depuis PowerShell ou cmd en tant qu'administrateur:
```powershell
# PowerShell
& pdfanalysis-app

# Ou avec le chemin complet
& "$env:CONDA_PREFIX\Scripts\pdfanalysis-app.exe"
```
