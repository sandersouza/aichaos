#!/bin/bash -e

CONFIG_FILE="config.yml"
if [[ ! -f "$CONFIG_FILE" ]]; then
    echo "Erro: Arquivo config.yml não encontrado."
    exit 1
fi

OUTPUT_DIR=$(grep 'chaosexperiments:' "$CONFIG_FILE" | awk '{print $2}' | tr -d '"')
REPORTS_DIR=$(grep 'reports:' "$CONFIG_FILE" | awk '{print $2}' | tr -d '"')

if ! command -v docker &> /dev/null; then
    echo "Erro: Docker não está instalado. Instale o Docker antes de continuar."
    exit 1
fi

ACCEPT_ALL=false

function ask_user() {
    local experiment_name=$1

    if $ACCEPT_ALL; then
        return 0
    fi

    while true; do
        echo
        echo "Deseja executar o experimento '$experiment_name'?"
        echo "[1] Executar este experimento"
        echo "[2] Executar todos os experimentos automaticamente"
        echo "[3] Cancelar este experimento"
        echo -n "Escolha uma opção (1, 2 ou 3): "
        read -r user_input
        case "$user_input" in
            1)
                return 0
                ;;
            2)
                ACCEPT_ALL=true
                return 0
                ;;
            3)
                return 1
                ;;
            *)
                echo "Opção inválida. Por favor, escolha 1, 2 ou 3."
                ;;
        esac
    done
}

function extract_image_from_info() {
    local info_file=$1
    local image=$(grep '"image"' "$info_file" | awk -F': ' '{print $2}' | tr -d '",')
    local tag=$(grep '"tag"' "$info_file" | awk -F': ' '{print $2}' | tr -d '",')
    echo "${image}:${tag}"
}

function run_container() {
    local image_name=$1
    local container_name="chaos_test_$(echo "$image_name" | tr '/:' '_')"

    if docker ps -a --format "{{.Names}}" | grep -q "^${container_name}$"; then
        echo "O contêiner $container_name já existe. Removendo antes de criar um novo..."
        docker rm -f "$container_name" > /dev/null 2>&1
    fi

    echo "Baixando a imagem: $image_name"
    docker pull "$image_name" > /dev/null 2>&1

    if [[ $? -ne 0 ]]; then
        echo "Erro ao baixar a imagem: $image_name"
        return 1
    fi

    echo "Iniciando o contêiner: $container_name"
    docker run -d --name "$container_name" "$image_name" sh -c "while :; do sleep 1; done" > /dev/null 2>&1

    if [[ $? -ne 0 ]]; then
        echo "Erro ao iniciar o container para a imagem: $image_name"
        return 1
    fi

    echo "$container_name"
}

function execute_experiment() {
    local experiment_file="$1"
    local container_name="$2"
    local image_name="$3"

    local experiment_name=$(basename "$experiment_file" .json)

    if ! ask_user "$experiment_name"; then
        echo "Experimento '$experiment_name' cancelado pelo usuário."
        return
    fi

    local report_path="$REPORTS_DIR/$image_name/$experiment_name.log"
    mkdir -p "$REPORTS_DIR/$image_name"

    echo "Executando experimento: $experiment_name"

    experiment_file=$(realpath "$experiment_file")

    # Executar o experimento com Chaos Toolkit
    chaos run "$experiment_file" > "$report_path" 2>&1

    if [[ $? -eq 0 ]]; then
        generate_postmortem "$report_path" "$experiment_name" "sucesso"
    else
        generate_postmortem "$report_path" "$experiment_name" "falha"
    fi
}

function generate_postmortem() {
    local log_path=$1
    local experiment_name=$2
    local status=$3

    local summary="Experimento: $experiment_name\nResultado: $status\nResumo: O experimento foi executado com $status."
    echo -e "$summary" >> "$log_path"
}

function process_experiments() {
    if [[ ! -d "$OUTPUT_DIR" ]]; then
        echo "Erro: Diretório de experimentos não encontrado ($OUTPUT_DIR)."
        exit 1
    fi

    for image_dir in "$OUTPUT_DIR"/*; do
        if [[ -d "$image_dir" ]]; then
            local info_file="$image_dir/info.json"

            if [[ ! -f "$info_file" ]]; then
                echo "Erro: Arquivo info.json não encontrado no diretório: $image_dir"
                continue
            fi

            local full_image_name=$(extract_image_from_info "$info_file")
            local container_name=$(run_container "$full_image_name")

            if [[ -z "$container_name" ]]; then
                echo "Erro ao iniciar o container para a imagem: $full_image_name"
                continue
            fi

            for experiment_file in "$image_dir"/*.json; do
                if [[ -f "$experiment_file" && "$(basename "$experiment_file")" != "info.json" ]]; then
                    execute_experiment "$experiment_file" "$container_name" "$full_image_name"
                fi
            done

            echo "Finalizando container: $container_name"
            docker rm -f "$container_name" > /dev/null 2>&1
        fi
    done
}

process_experiments
