#!/bin/bash

echo "Instalando Google Chrome..."

# Baixando e adicionando chave do repositório
wget -qO - https://dl.google.com/linux/linux_signing_key.pub | sudo gpg --dearmor -o /usr/share/keyrings/google-chrome-keyring.gpg

# Adicionando repositório do Google Chrome
echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-chrome-keyring.gpg] http://dl.google.com/linux/chrome/deb/ stable main" | sudo tee /etc/apt/sources.list.d/google-chrome.list

# Atualizando pacotes e instalando Google Chrome
sudo apt update && sudo apt install -y google-chrome-stable

# Instalando ChromeDriver (compatível com a versão instalada do Chrome)
CHROME_VERSION=$(google-chrome --version | awk '{print $3}')
CHROMEDRIVER_VERSION=$(curl -s "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_$CHROME_VERSION")
wget -q "https://chromedriver.storage.googleapis.com/${CHROMEDRIVER_VERSION}/chromedriver_linux64.zip" -O chromedriver.zip
unzip chromedriver.zip
chmod +x chromedriver
sudo mv chromedriver /usr/local/bin/

echo "Instalação concluída!"