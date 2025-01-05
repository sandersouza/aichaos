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
OUTPUT_DIR = config["dir"]["exploits"]

os.makedirs(OUTPUT_DIR, exist_ok=True)

SYSTEM_MESSAGE_CONTENT = (
    "Você é um especialista em Metasploit Framework." 
    "Crie um script de exploit no formato .rc baseado nas vulnerabilidades críticas que lhe serão enviadas." 
    "Certifique-se de gerar scripts válidos e funcionais, evitando placeholders fictícios como 'http://your-service/...'."
    "O exploit sempre será executado localmente no container/pod que contém a vulnerabilidade, portanto use socket ou localhost."
    "Seguem algumas dicas do próprio metasploit:"
    "- Metasploit tip: You can pivot connections over sessions started with the ssh_login modules"
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

def extract_rc_from_response(content):
    try:
        # Captura o conteúdo entre ``` e ```
        match = re.search(r"```(.*?)```", content, re.DOTALL)
        if match:
            rc_content = match.group(1).strip()
            return rc_content
        else:
            print("Nenhum script RC válido encontrado no conteúdo gerado.")
            return None
    except Exception as e:
        print(f"Erro ao extrair script RC: {e}")
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
        rc_content = extract_rc_from_response(content)

        if rc_content:
            return rc_content
        else:
            return None

    except openai.error.OpenAIError as e:
        print(f"Erro ao gerar script RC para '{vulnerability.get('Title', 'Título não disponível')}': {e}")
        return None

def save_info_file(image_dir, image_name, image_id, tag, severity, cve, description):
    info_data = {
        "image_name": image_name,
        "image_id": image_id,
        "severity": severity,
        "cve": cve,
        "description": description
    }

    info_file_path = os.path.join(image_dir, "info.json")
    with open(info_file_path, "w") as info_file:
        json.dump(info_data, info_file, indent=4)

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

            image_name = data.get("ArtifactName", "unknown")
            image_id = data.get("Metadata", {}).get("ImageID", "unknown")
            tag = image_name.split(":")[-1] if ":" in image_name else "latest"
            image_dir = os.path.join(OUTPUT_DIR, sanitize_filename(image_name))
            os.makedirs(image_dir, exist_ok=True)

            vulnerabilities = data.get("Results", [])
            for result in vulnerabilities:
                vulns = result.get("Vulnerabilities", [])
                for vulnerability in vulns:
                    if vulnerability.get("Severity", "").upper() == "CRITICAL":
                        exploit_content = analyze_vulnerability(vulnerability)
                        exploit_content = exploit_content.replace("plaintext", "")
                        if exploit_content:
                            exploit_title = sanitize_filename(vulnerability.get("Title", "exploit"))
                            exploit_file_path = os.path.join(image_dir, f"{exploit_title}.rc")
                            unique_file_path = get_unique_filepath(exploit_file_path)

                            with open(unique_file_path, "w") as exploit_file:
                                exploit_file.write(exploit_content)

                            print(f"Exploit gerado e salvo: {unique_file_path}")

                            # Salvar arquivo info.json
                            cve = vulnerability.get("VulnerabilityID", "unknown")
                            description = vulnerability.get("Description", "Sem descrição disponível.")
                            save_info_file(image_dir, image_name, image_id, tag, "CRITICAL", cve, description)

if __name__ == "__main__":
    openai.api_key = API_KEY
    process_reports()
