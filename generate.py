#!./venv/bin/python3
import os
import json
import openai
import yaml
import re

def load_config(config_file="config.yml"):
    try:
        with open(config_file, "r") as file:
            config = yaml.safe_load(file)
        return config
    except FileNotFoundError:
        print("Erro: Arquivo config.yml não encontrado.")
        return None
    except yaml.YAMLError as e:
        print(f"Erro ao carregar o arquivo de configuração: {e}")
        return None

config = load_config()
if not config:
    exit(1)

API_KEY = config["token"]["OPENAI_API_KEY"]
REPORTS_DIR = config["dir"]["vulnerabilities"]
OUTPUT_DIR = config["dir"]["chaosexperiments"]

os.makedirs(OUTPUT_DIR, exist_ok=True)

SYSTEM_MESSAGE_CONTENT = (
    "Você é um especialista em criação de experimentos de chaos usando a ferramenta Chaos Toolkit 1.19.0 ( chaos, version 1.19.0 ). "
    "Crie experimentos válidos no formato JSON focador nas vulnerabilidades críticas. Não inclua URLs fictícias como 'http://your-service/...', "
    "e caso não tenha opção não o crie. Certifique-se de adicionar um `steady-state-hypothesis` com `tolerance` válido. "
    "Não gere experimentos que necessitem de ajustes manuais. Não adicione comentários ou instruções, gere somente os scripts."
    "Não use funções customizadas, use apenas as features default."
)

def sanitize_filename(filename):
    return filename.replace(":", "").replace(" ", "_").replace("/", "_").replace(".", "_").replace("\\", "_").lower()

def get_unique_filepath(base_path):
    if not os.path.exists(base_path):
        return base_path

    base, ext = os.path.splitext(base_path)
    counter = 1
    new_path = f"{base}_{counter}{ext}"
    while os.path.exists(new_path):
        counter += 1
        new_path = f"{base}_{counter}{ext}"

    return new_path

def extract_json_from_response(content):
    try:
        # Captura o conteúdo entre ```json e ```
        match = re.search(r"```json(.*?)```", content, re.DOTALL)
        if match:
            json_content = match.group(1).strip()
            return json_content
        else:
            print("Nenhum JSON válido encontrado no conteúdo gerado.")
            return None
    except Exception as e:
        print(f"Erro ao extrair JSON: {e}")
        return None

def analyze_vulnerability(vulnerability):
    prompt = f"{SYSTEM_MESSAGE_CONTENT}\n- Título: {vulnerability.get('Title', 'Título não disponível')}\n- Descrição: {vulnerability.get('Description', 'Descrição não disponível')}"

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_MESSAGE_CONTENT},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000,
            temperature=0.7
        )

        content = response['choices'][0]['message']['content'].strip()
        json_content = extract_json_from_response(content)

        print(f"{json_content}")

        if json_content:
            try:
                parsed_content = json.loads(json_content)
                return json.dumps(parsed_content, indent=4)
            except json.JSONDecodeError:
                print(f"Erro: O JSON extraído não é válido para '{vulnerability.get('Title', 'Título não disponível')}'.")
                return None
        else:
            return None

    except openai.error.OpenAIError as e:
        print(f"Erro ao gerar experimento para '{vulnerability.get('Title', 'Título não disponível')}': {e}")
        return None

def process_reports():
    for file_name in os.listdir(REPORTS_DIR):
        if file_name.endswith(".json"):
            file_path = os.path.join(REPORTS_DIR, file_name)

            try:
                with open(file_path, "r") as file:
                    data = json.load(file)
            except json.JSONDecodeError as e:
                print(f"Erro ao ler o arquivo {file_path}: {e}")
                continue

            image_name = sanitize_filename(data.get("ArtifactName", "unknown"))
            image_dir = os.path.join(OUTPUT_DIR, image_name)
            os.makedirs(image_dir, exist_ok=True)

            vulnerabilities = data.get("Results", [])
            for result in vulnerabilities:
                vulns = result.get("Vulnerabilities", [])
                for vulnerability in vulns:
                    if vulnerability.get("Severity", "").upper() == "CRITICAL":
                        experiment_content = analyze_vulnerability(vulnerability)
                        if experiment_content:
                            experiment_title = sanitize_filename(vulnerability.get("Title", "experiment"))
                            experiment_file_path = os.path.join(image_dir, f"{experiment_title}.json")
                            unique_file_path = get_unique_filepath(experiment_file_path)

                            with open(unique_file_path, "w") as experiment_file:
                                experiment_file.write(experiment_content)
                            print(f"Experimento gerado e salvo: {unique_file_path}")

if __name__ == "__main__":
    openai.api_key = API_KEY
    process_reports()
