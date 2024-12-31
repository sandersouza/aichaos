#!/bin/bash
# Diretórios e Configuração
CONFIG_FILE="config.yml"
if [[ ! -f "$CONFIG_FILE" ]]; then
    echo "Erro: Arquivo config.yml não encontrado."
    exit 1
fi

# Extrair diretórios e severidade do config.yml
VULNE_DIR=$(grep 'vulnerabilities:' "$CONFIG_FILE" | awk '{print $2}' | tr -d '"')
CHAOS_DIR=$(grep 'chaosexperiments:' "$CONFIG_FILE" | awk '{print $2}' | tr -d '"')
rm -rf "$CHAOS_DIR" "$VULNE_DIR" build chaoslib.egg-info

echo "Ambiente limpo."
