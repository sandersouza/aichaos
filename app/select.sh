#!/bin/bash
CONFIG_FILE="config.yml"
OUTPUT_DIR=$(grep -E '^ *vulnerabilities:' "$CONFIG_FILE" | awk '{print $2}' | tr -d '"')
SEVERITY=$(grep -E '^ *severity:' "$CONFIG_FILE" | awk '{print $2}' | tr -d '"')

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

    local image_id=$(echo "$selected_image" | awk '{print $1}')
    echo $image_id
}

main() {
    local container_tool=$(detect_container_tool)
    local image_id=$(list_and_select_image $container_tool)

    if [[ -n "$image_id" ]]; then
        mkdir -p "$OUTPUT_DIR"
        trivy image -q --severity "$SEVERITY" --format json "$image_id" | jq -r '.Results[]?.Vulnerabilities[]?.VulnerabilityID // empty' > "$OUTPUT_DIR/$image_id.txt"
        $container_tool inspect "$image_id" > "$OUTPUT_DIR/$image_id.json"
    fi
}

main