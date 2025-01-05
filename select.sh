#!/bin/bash
CONFIG_FILE="config.yml"
OUTPUT_DIR=$(grep 'vulnerabilities:' "$CONFIG_FILE" | awk '{print $2}' | tr -d '"')
SEVERITY=$(grep 'severity:' "$CONFIG_FILE" | awk '{print $2}' | tr -d '"')

detect_container_tool() {
    if command -v docker &>/dev/null; then
        echo "docker"
    elif command -v podman &>/dev/null; then
        echo "podman"
    else
        echo "Nenhum gerenciador de containers encontrado. Instale o Docker ou Podman antes de continuar."
        exit 1
    fi
}

list_and_select_image() {
    local container_tool=$1
    local IMAGES=$($container_tool images --format "{{.ID}}\t{{.Repository}}:{{.Tag}}")
    if [[ -z "$IMAGES" ]]; then
        echo "Nenhuma imagem encontrada no $container_tool."
        exit 0
    fi

    local selected_image=$(echo "$IMAGES" | fzf --prompt="Selecione uma imagem: " --layout=reverse --border --ansi)

    if [[ -z "$selected_image" ]]; then
        echo "Nenhuma imagem selecionada. Saindo."
        exit 0
    fi

    echo $selected_image
}

function vulnerability_scan(){
    local IMAGE_NAME=$1
    local OUTPUT_FILE="${OUTPUT_DIR}/${IMAGE_NAME}.json"

    mkdir -p "$OUTPUT_DIR"

    echo -e "Scanning $IMAGE_NAME... wait."
    result=$( trivy image -q --severity "$SEVERITY" --format json "$IMAGE_NAME" )
    if [ -z "$result" ]; then 
        "No vulnerabilities found. Have a good day sir!"
    else
        echo "$result" > "$OUTPUT_FILE"
        echo -e "Vulnerability report generated."
    fi
}

clear
CONTAINER_TOOL=$(detect_container_tool)
image=$(list_and_select_image "$CONTAINER_TOOL")
vulnerability_scan $( echo $image | awk '{print $2}' )
rm -rf exploits ; ./generate.py