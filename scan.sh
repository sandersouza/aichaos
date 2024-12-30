#!/bin/bash

OUTPUT_DIR="trivy_reports"
SEVERITY="${SEVERITY:-CRITICAL}"  # Permite definir a severidade via variável de ambiente

# Verifica se o Trivy está instalado
if ! command -v trivy &> /dev/null; then
    echo "Erro: Trivy não está instalado. Instale com 'brew install aquasecurity/trivy/trivy'."
    exit 1
fi

# Detecta o uso de Docker ou Podman
if command -v podman &> /dev/null; then
    CONTAINER_TOOL="podman"
elif command -v docker &> /dev/null; then
    CONTAINER_TOOL="docker"
else
    echo "Erro: Nem Podman nem Docker estão instalados. Instale uma dessas ferramentas."
    exit 1
fi

mkdir -p "$OUTPUT_DIR"
IMAGES=$($CONTAINER_TOOL images --format "{{.Repository}}:{{.Tag}}" | grep -v "<none>")

if [[ -z "$IMAGES" ]]; then
    echo "Nenhuma imagem encontrada no $CONTAINER_TOOL."
    exit 0
fi

echo -e "Iniciando o scan de imagens com severidade $SEVERITY...\n"

for IMAGE in $IMAGES; do
    echo "Escaneando imagem: $IMAGE"

    IMAGE_NAME=$(echo "$IMAGE" | tr '/:' '_')
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    OUTPUT_FILE="${OUTPUT_DIR}/${IMAGE_NAME}_${TIMESTAMP}.json"

    # Executa o scan do Trivy
    if trivy image -q --severity "$SEVERITY" --format json "$IMAGE" > "$OUTPUT_FILE"; then
        if grep -q "$SEVERITY" "$OUTPUT_FILE"; then
            echo -e "Relatório salvo em: $OUTPUT_FILE\n"
        else
            echo -e "Nenhuma vulnerabilidade $SEVERITY encontrada para a imagem: $IMAGE\n"
            rm -f "$OUTPUT_FILE"
        fi
    else
        echo "Erro ao escanear a imagem: $IMAGE"
        rm -f "$OUTPUT_FILE"
    fi
done

echo "Scan concluído. Relatórios disponíveis no diretório: $OUTPUT_DIR"
