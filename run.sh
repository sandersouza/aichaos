#!/bin/bash

# Nome do contêiner alvo
TARGET_CONTAINER=$1
EXPLOIT_SCRIPT=$2
CONTAINER_NAME="chaos_$( echo $TARGET_CONTAINER | awk -F':' '{print $1}')"

if [ -z "$TARGET_CONTAINER" ] || [ -z "$EXPLOIT_SCRIPT" ]; then
    echo "Uso: $0 <container-alvo> <caminho-do-exploit>"
    exit 1
fi

echo "Instanciando container $CONTAINER_NAME... aguarde."
docker run --name $CONTAINER_NAME $TARGET_CONTAINER sh -c "while :; do sleep 1; done" -d > /dev/null 2>&1 &

# Cria e sobe o contêiner Metasploit
METASPLOIT_CONTAINER="metasploit_runner"
docker rm -f "$METASPLOIT_CONTAINER" > /dev/null 2>&1
docker run -d --name "$METASPLOIT_CONTAINER" \
    --network container:"$CONTAINER_NAME" \
    -v "$(realpath $EXPLOIT_SCRIPT):/opt/exploit.rc" \
    metasploit

# Executa o script RC no Metasploit
echo "Executando o script de exploit..."
docker exec "$METASPLOIT_CONTAINER" msfconsole -r /opt/exploit.rc > exploit_report.log

# Exibe o relatório
echo "Exploit concluído. Relatório salvo em exploit_report.log"

# Finaliza o contêiner do Metasploit
docker rm -f "$CONTAINER_NAME"
docker rm -f "$METASPLOIT_CONTAINER"
