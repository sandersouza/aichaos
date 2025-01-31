#!/bin/bash
# Default FZF Options
export FZF_DEFAULT_OPTS='--layout=reverse --border --ansi --preview-window=80% --info=inline --tmux 80% --prompt="Select an item: "'

navigate_and_select_exploit() {
    while true; do
        DIRECTORIES=$(find . -type d -mindepth 1 -maxdepth 1 | sed 's|^\./||' | xargs -n1 -I{} echo "\033[1;31m{}\033[0m")
        FILES=$(find . -type f -mindepth 1 -maxdepth 1 -name "*.rc" -exec basename {} \; | sort)

        if [ -z "$DIRECTORIES" ]; then
            items="..\n$FILES"
        elif [ -z "$FILES" ]; then
            items="..\n$DIRECTORIES"
        else
            items="..\n$DIRECTORIES\n$FILES"
        fi

        SELECTED_ITEM=$(echo -e "$items" | fzf --preview="[ -f {} ] && cat {} || ls -1 {}")

        if [[ -z "$SELECTED_ITEM" ]]; then
            echo "No selection made. Exiting."
            exit 0
        fi

        SELECTED_ITEM=$(echo "$SELECTED_ITEM" | sed -r 's/\x1b\\[[0-9;]*m//g')

        if [ -d "$SELECTED_ITEM" ]; then
            cd "$SELECTED_ITEM"
        elif [ -f "$SELECTED_ITEM" ]; then
            echo "Selected file: $SELECTED_ITEM"
            confirm_selection $SELECTED_ITEM
            return
        fi
    done
}

confirm_selection() {
    local file=$1
    echo "Deseja executar o script '$file'?"
    local confirmation=$(echo -e "Sim\nNão" | fzf --prompt="Confirmação: " --layout=reverse --border --ansi)

    if [[ "$confirmation" == "Sim" ]]; then
        EXPLOIT_DIR=$(dirname "$file")
        IMAGE_FILE="$EXPLOIT_DIR/image.txt"

        if [[ ! -f "$IMAGE_FILE" ]]; then
            echo "Erro: Arquivo 'image.txt' não encontrado no diretório do exploit selecionado."
            exit 1
        fi

        TARGET_CONTAINER=$(cat "$IMAGE_FILE")

        if [[ -z "$TARGET_CONTAINER" ]]; then
            echo "Erro: Nenhum nome de imagem especificado em 'image.txt'."
            exit 1
        fi
    else
        echo "Operação cancelada pelo usuário."
        exit 0
    fi
}

start_target_container() {
    CONTAINER_NAME="chaos_$(echo "$TARGET_CONTAINER" | awk -F':' '{print $1}')"
    echo "Instanciando container $CONTAINER_NAME... aguarde."
    echo $CONTAINER_NAME
    echo $TARGET_CONTAINER
    docker run --name "$CONTAINER_NAME" "$TARGET_CONTAINER" sh -c "while :; do sleep 1; done" -d > /dev/null 2>&1 &
}

start_metasploit_container() {
    METASPLOIT_CONTAINER="metasploit_runner"
    echo "Preparando o container do Metasploit..."
    docker rm -f "$METASPLOIT_CONTAINER" > /dev/null 2>&1
    docker run -d --name "$METASPLOIT_CONTAINER" \
        --network container:"$CONTAINER_NAME" \
        -v "$(realpath "$SELECTED_ITEM"):/opt/exploit.rc" \
        metasploit
}

execute_exploit() {
    echo "Executando o script de exploit..."
    docker exec "$METASPLOIT_CONTAINER" msfconsole -r /opt/exploit.rc > exploit_report.log
    echo "Exploit concluído. Relatório salvo em exploit_report.log"
}

cleanup() {
    echo "Finalizando containers..."
    docker rm -f "$CONTAINER_NAME" > /dev/null 2>&1
    docker rm -f "$METASPLOIT_CONTAINER" > /dev/null 2>&1
}

main() {
    clear
    CONFIG_FILE="config.yml"
    EXPLOIT_DIR=$(grep 'exploits:' "$CONFIG_FILE" | awk '{print $2}' | tr -d '"')
    cd $EXPLOIT_DIR

    navigate_and_select_exploit
    start_target_container
    execute_exploit
    cleanup
}

main