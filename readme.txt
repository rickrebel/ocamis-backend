#README:

tener instalado python3

instalar pip

# Instalar venv
python3 -m venv desabasto

Iniciar venv

pip install -r requirementes

# Iniciar redis en local
sudo service redis-server start
redis-cli

Iniciar ngrok para recibir los resultados de AWS Lambda
ngrok start desabasto-api
