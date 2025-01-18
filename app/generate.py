#!python3

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
POSTMORTEM_DIR = config["dir"]["postmortem"]

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(POSTMORTEM_DIR, exist_ok=True)

SYSTEM_MESSAGE_CONTENT = (
    "Você é um especialista em Metasploit, todos os scripts serão executados localmente, e seu usuário tem acesso irrestrito inclusive ao ROOT."
    "Irei lhe passar uma CVE, se existir módulo para ela no Metasploit, gere um script (.rc), não precisa dar explicaçõe e coloque no início o comentário #SCRIPT."
    "Senão gere relatório da CVE em latex usando a formatação estilo markdown. Inclua os links referenciais, dicas de mitigação e coloque no início a tag #POSTMORTEM."
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

def extract_tagged_content(content):
    script_match = re.search(r"#SCRIPT\s+'''(.*?)'''", content, re.DOTALL)
    if script_match:
        return "script", script_match.group(1).strip()

    postmortem_match = re.search(r"#POSTMORTEM\s+(.*)", content, re.DOTALL)
    if postmortem_match:
        return "postmortem", postmortem_match.group(1).strip()

    return None, content

def analyze_vulnerability(cve):
    prompt = f"Existe módulo para {cve}? Caso exista, gere o script RC. Caso contrário, forneça um relatório sobre a vulnerabilidade."

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
        content_type, sanitized_content = extract_tagged_content(content)

        if content_type is None:
            print(f"[WARNING] Tag inválida ou ausente para {cve}. Conteúdo: {content}")

        return content_type, sanitized_content

    except openai.error.OpenAIError as e:
        print(f"Erro ao analisar a CVE '{cve}': {e}")
        return None, None

def process_vulnerabilities():
    for file_name in os.listdir(REPORTS_DIR):
        if file_name.endswith("-cve.txt"):
            file_path = os.path.join(REPORTS_DIR, file_name)

            with open(file_path, "r") as file:
                cves = file.read().splitlines()

            image_name = cves.pop(0)  # First line is the image name
            sanitized_image_name = sanitize_filename(image_name)
            image_output_dir = os.path.join(OUTPUT_DIR, sanitized_image_name)
            postmortem_output_dir = os.path.join(POSTMORTEM_DIR, sanitized_image_name)
            os.makedirs(image_output_dir, exist_ok=True)
            os.makedirs(postmortem_output_dir, exist_ok=True)

            # Save the image name in image.txt
            image_txt_path = os.path.join(image_output_dir, "image.txt")
            with open(image_txt_path, "w") as image_file:
                image_file.write(image_name)

            for cve in cves:
                base_name = sanitize_filename(cve)
                exploit_file_path = os.path.join(image_output_dir, f"{base_name}.rc")
                postmortem_file_path = os.path.join(postmortem_output_dir, f"{base_name}.md")

                content_type, sanitized_content = analyze_vulnerability(cve)

                if content_type == "script":
                    unique_exploit_path = get_unique_filepath(exploit_file_path)
                    with open(unique_exploit_path, "w") as exploit_file:
                        exploit_file.write(sanitized_content)
                    print(f"Exploit gerado: {unique_exploit_path}")

                elif content_type == "postmortem":
                    unique_postmortem_path = get_unique_filepath(postmortem_file_path)
                    with open(unique_postmortem_path, "w") as report_file:
                        report_file.write(sanitized_content)
                    print(f"Relatório gerado: {unique_postmortem_path}")

                else:
                    print(f"[INFO] Nenhuma ação realizada para a CVE '{cve}' - Sem tag válida no conteúdo.")

if __name__ == "__main__":
    openai.api_key = API_KEY
    process_vulnerabilities()
