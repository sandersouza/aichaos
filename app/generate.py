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
REPORTS_DIR = config["dir"]["vulnerabilities"]
OUTPUT_DIR = config["dir"]["exploits"]
GPTMODEL = config["gpt"]["model"]
os.makedirs(OUTPUT_DIR, exist_ok=True)

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

def generate_exploit(cve):
    message = (
                f"Se a {cve} for apenas explorável por camada ou protocolo de rede, não dê explicações apenas escreva #ONLYNET;"
                "se não possuir informações sobre a CVE apenas escreva #NOINFO."
                "Caso contrário, crie script que teste se a mesma é explorável em um servidor local de testes controlado."
              )
    
    prompt = f"{message}"

    try:
        response = openai.ChatCompletion.create(
            messages=[{
                "role": "user",
                "content": prompt
            }],
            model=GPTMODEL,
        )
        content = response['choices'][0]['message']['content'].strip()

        if "#ONLYNET" in content:
            print(f"{cve} somente explorável por camada ou protocolo de rede.")
            return None, None
        elif "#NOINFO" in content:
            print(f"{cve} sem informações disponíveis.")
            return None, None
        else:
            code_block = extract_code_block(content)
            filename = None
            for line in content.split('\n'):
                if line.startswith("#Filename:"):
                    filename = line.split(":")[1].strip()
                    break
            return code_block, filename

    except openai.error.OpenAIError as e:
        print(f"Erro ao analisar a CVE '{cve}': {e}")
        return None, None

def process_vulnerabilities():
    for file_name in os.listdir(REPORTS_DIR):
        if file_name.endswith(".txt"):
            file_path = os.path.join(REPORTS_DIR, file_name)
            print(f"Processando arquivo de vulnerabilidades: {file_path}.\n")

            with open(file_path, "r") as file:
                cves = file.read().splitlines()

            image_id = os.path.splitext(file_name)[0]
            image_output_dir = os.path.join(OUTPUT_DIR, image_id)
            os.makedirs(image_output_dir, exist_ok=True)

            for cve in cves:
                exploit_script, filename = generate_exploit(cve)
                if exploit_script and filename:
                    base_name, extension = os.path.splitext(filename)
                    exploit_file_path = os.path.join(image_output_dir, filename)

                    unique_exploit_path = get_unique_filepath(exploit_file_path)
                    with open(unique_exploit_path, "w") as exploit_file:
                        exploit_file.write(exploit_script)

                    # Tornar o script executável
                    st = os.stat(unique_exploit_path)
                    os.chmod(unique_exploit_path, st.st_mode | stat.S_IEXEC)

                    print(f"Exploit gerado: {unique_exploit_path}")

if __name__ == "__main__":
    openai.api_key = API_KEY
    process_vulnerabilities()
