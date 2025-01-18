#!/bin/bash
declare -A RMDIR

CONFIG_FILE="config.yml"
if [[ ! -f "$CONFIG_FILE" ]]; then
    echo "Erro: Arquivo config.yml não encontrado."
    exit 1
fi

# Extrair diretórios e severidade do config.yml
RMDIR[0]=$(grep 'vulnerabilities:' "$CONFIG_FILE" | awk '{print $2}' | tr -d '"')
RMDIR[1]=$(grep 'postmortem:' "$CONFIG_FILE" | awk '{print $2}' | tr -d '"')
RMDIR[2]=$(grep 'exploits:' "$CONFIG_FILE" | awk '{print $2}' | tr -d '"')
RMDIR[3]=$(grep 'temp:' "$CONFIG_FILE" | awk '{print $2}' | tr -d '"')

# Iterar pelos diretórios e limpar
for DIR in "${RMDIR[@]}"; do
    rm -rf "$DIR"
    echo "Deletando conteúdo do diretório $DIR."
done

echo "Ambiente limpo."
