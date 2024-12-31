#!/bin/bash
declare -a RESULT_COUNT
declare -a RESULT_IMAGE
declare -a RESULT_SEVERITY

i=0

# Diretórios e Configuração
CONFIG_FILE="config.yml"
if [[ ! -f "$CONFIG_FILE" ]]; then
    echo "Erro: Arquivo config.yml não encontrado."
    exit 1
fi

OUTPUT_DIR=$(grep 'vulnerabilities:' "$CONFIG_FILE" | awk '{print $2}' | tr -d '"')
SEVERITY=$(grep 'severity:' "$CONFIG_FILE" | awk '{print $2}' | tr -d '"')

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

function scan(){
    mkdir -p "$OUTPUT_DIR"
    IMAGES=$($CONTAINER_TOOL images --format "{{.Repository}}:{{.Tag}}" | grep -v "<none>")

    if [[ -z "$IMAGES" ]]; then
        echo "Nenhuma imagem encontrada no $CONTAINER_TOOL."
        exit 0
    fi

    for IMAGE in $IMAGES; do
        echo "Escaneando imagem: $IMAGE"

        IMAGE_NAME=$(echo "$IMAGE" | tr '/:' '_')
        TIMESTAMP=$(date +%Y%m%d_%H%M%S)
        OUTPUT_FILE="${OUTPUT_DIR}/${IMAGE_NAME}_${TIMESTAMP}.json"

        # Executa o scan do Trivy
        if trivy image -q --severity "$SEVERITY" --format json "$IMAGE" > "$OUTPUT_FILE"; then
            ((i++))
            if grep -q "$SEVERITY" "$OUTPUT_FILE"; then
                RESULT_COUNT[i]=$(grep "$SEVERITY" "$OUTPUT_FILE" | wc -l | tr -d " ")
                RESULT_IMAGE[i]=$IMAGE_NAME
                RESULT_SEVERITY[i]=$SEVERITY
            else
                rm -f "$OUTPUT_FILE"
            fi
        else
            echo "Erro ao escanear a imagem: $IMAGE"
            rm -f "$OUTPUT_FILE"
        fi

    done
}

function show(){
    echo -e "\n"
    echo -e "\033[1;34mResumo do Scan de Vulnerabilidades\033[0m"
    printf "+-%-30s-+-%-10s-+-%-5s-+\n" "------------------------------" "----------" "-----"
    printf "| %-30s | %-10s | %5s |\n" "Imagem" "Tipo" "Quant"
    printf "+-%-30s-+-%-10s-+-%-5s-+\n" "------------------------------" "----------" "-----"
    for idx in "${!RESULT_IMAGE[@]}"; do
        if [[ "${RESULT_SEVERITY[$idx]}" == "CRITICAL" ]]; then
            printf "| %-30s | \033[1;31m%-10s\033[0m | %5s |\n" "${RESULT_IMAGE[$idx]}" "${RESULT_SEVERITY[$idx]}" "${RESULT_COUNT[$idx]}"
        else
            printf "| %-30s | %-10s | %5s |\n" "${RESULT_IMAGE[$idx]}" "${RESULT_SEVERITY[$idx]}" "${RESULT_COUNT[$idx]}"
        fi
    done
    printf "+-%-30s-+-%-10s-+-%-5s-+\n" "------------------------------" "----------" "-----"
}

scan
show
