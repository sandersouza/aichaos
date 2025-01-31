#!python3
import os
import openai
import yaml
import stat
import requests
import json

CONFIG_FILE = "config.yml"

def load_config():
    try:
        with open(CONFIG_FILE, "r") as config_file:
            return yaml.safe_load(config_file)
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
GPTMODEL = config["gpt"]["model"]
REPORTS_DIR = config["dir"]["vulnerabilities"]

SYSTEM_MESSAGE_CONTENT = (
    "Gere um postmortem / relatório no formarto markdown, com as informações da CVE, e detalhes da vulnerabilidade."
    "O postmortem deve conter a explanação detalhada da vulnerabilidade, assim como o script para exploração da mesma."
)

def extract_code_block(content):
    lines = content.split('\n')
    code_block = []
    inside_code_block = False

    for line in lines:
        if line.strip().startswith("```"):
            inside_code_block = not inside_code_block
            continue
        if inside_code_block:
            code_block.append(line)

    return '\n'.join(code_block)

def write_report(content, filename):
    with open(filename, "w") as file:
        file.write(content)

def generate_report():
    prompt = f"Essa é a CVE explorável:cve-2023-45283\n{SYSTEM_MESSAGE_CONTENT}\n"

    print(f"Gerando report...")
    response = openai.ChatCompletion.create(
        model=GPTMODEL,
        messages=[
            {"role": "user", "content": prompt}
        ],
    )
    
    content = response['choices'][0]['message']['content'].strip()
    print(f"{content}")

    with open(f"{REPORTS_DIR}/report.md", "w") as file:
        file.write(content)

if __name__ == "__main__":
    openai.api_key = API_KEY
    generate_report()