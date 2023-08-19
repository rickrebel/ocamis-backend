#README:

tener instalado python3

instalar pip

Revisar que las variables de entorno se escribieron adecuadamente (Si se trabaja en Windows)

#Tener dos carpetas separadas (para una mejor organización), 
#una para los entornos virtuales, y otro para los sistemas/proyectos

# Instalar venv
#Crear en ambiente virtual, en este caso llamado 'ocamis' en la carpeta env
python3 -m venv ocamis

#Iniciar venv en la carpeta del env
.\ocamis\Scripts\Activate.ps1

#Instalar los paquetes requeridos para el sistema en la carpeta dev\ocamis. 
#Esto viene en el archivo requirements.txt
pip install -r requirements.txt

#Es posible que lance un error similar a 'ERROR: Could not build wheels for 
#psycopg2, psycopg2-binary, which is required to install pyproject.toml-based 
#projects' o uno similar a 'error: Microsoft Visual C++ 14.0 or greater is required. 
#Get it with "Microsoft C++ Build Tools": 
#https://visualstudio.microsoft.com/visual-cpp-build-tools/'
#Para el primer error se pueden ejecutar los siguientes comandos:
#pip uninstall psycopg2
#pip list --outdated
#pip install --upgrade wheel
#pip install --upgrade setuptools
#pip install psycopg2
#Para el segundo error, es necesario ingresar al enlace proporcionado e instalar el 
#componente faltante: una versión >= Microsoft Visual C++ 14.0

#Una vez terminado, se habrán instalado los paquetes necesarios para el sistema, 
#detallados en requirements.txt

# Iniciar redis en local
sudo service redis-server start
redis-cli

Iniciar ngrok para recibir los resultados de AWS Lambda
ngrok start desabasto-api
