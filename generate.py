#!./venv/bin/python

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
    "Você é um especialista em Metasploit Framework. "
    "O título do relatório será 'Relatório de vulnerabilidade - {CVE}', onde {CVE} precisa ser a CVE especificada. "
    "Os links que forem gerados como referência deverão ser separados em TÍTULO e o LINK deve estar completo (https://xyz.com) entre parênteses. "
    "Irei lhe passar uma CVE, se existir módulo para ela no Metasploit, gere um RC, senão faça um relatório explicando com a extensão .md, e no formato Markdown."
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
        match = re.search(r"```(.*?)```", content, re.DOTALL)
        if match:
            rc_content = match.group(1).strip()
            return rc_content
        else:
            return None
    except Exception as e:
        print(f"Erro ao extrair script RC: {e}")
        return None

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
        rc_content = extract_rc_from_response(content)

        if rc_content:
            return rc_content, None
        else:
            return None, content

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
            os.makedirs(image_output_dir, exist_ok=True)

            # Save the image name in image.txt
            image_txt_path = os.path.join(image_output_dir, "image.txt")
            with open(image_txt_path, "w") as image_file:
                image_file.write(image_name)

            for cve in cves:
                base_name = sanitize_filename(cve)
                exploit_file_path = os.path.join(image_output_dir, f"{base_name}.rc")
                postmortem_file_path = os.path.join(POSTMORTEM_DIR, f"{base_name}.md")

                rc_content, report_content = analyze_vulnerability(cve)

                if rc_content:
                    unique_exploit_path = get_unique_filepath(exploit_file_path)
                    with open(unique_exploit_path, "w") as exploit_file:
                        exploit_file.write(rc_content)
                    print(f"Exploit gerado: {unique_exploit_path}")

                elif report_content:
                    unique_postmortem_path = get_unique_filepath(postmortem_file_path)
                    with open(unique_postmortem_path, "w") as report_file:
                        report_file.write(report_content)
                    print(f"Relatório gerado: {unique_postmortem_path}")

if __name__ == "__main__":
    openai.api_key = API_KEY
    process_vulnerabilities()
