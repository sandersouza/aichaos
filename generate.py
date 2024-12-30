#!./venv/bin/python3
import os
import json
import openai
import yaml

# Diretórios
REPORTS_DIR = os.getenv("REPORTS_DIR", "trivy_reports")
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "chaos_experiments")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Carregar a chave da API do arquivo config.yml
def load_api_key(config_file="config.yml"):
    try:
        with open(config_file, "r") as file:
            config = yaml.safe_load(file)
        return config["token"]["OPENAI_API_KEY"]
    except FileNotFoundError:
        print("Erro: Arquivo config.yml não encontrado.")
        return None
    except KeyError:
        print("Erro: Chave 'OPENAI_API_KEY' não encontrada no config.yml.")
        return None
    except Exception as e:
        print(f"Erro ao carregar o arquivo de configuração: {e}")
        return None

def initialize_prompt():
    return """
    Uso Chaos Monkey para execução de chaos no meu ambiente. Todo experimento deve usar a sintaxe do Chaos Monkey.
    Analise as vulnerabilidades abaixo e crie experimentos individuais para cada uma no formato JSON, sem explicações adicionais.
    """

def sanitize_filename(filename):
    """Sanitiza o nome do arquivo, removendo caracteres problemáticos."""
    return filename.replace(":", "").replace(" ", "_").replace("/", "_").replace(".", "_").replace("\\", "_").lower()

def get_image_info_from_report(file_path):
    """Recupera informações da imagem a partir do arquivo JSON gerado pelo scan.sh."""
    try:
        with open(file_path, "r") as file:
            data = json.load(file)
            artifact_name = data.get("ArtifactName", "")
            metadata = data.get("Metadata", {})
            image_id = metadata.get("ImageID", "")
            created_at = data.get("CreatedAt", "")
            size = metadata.get("Size", "")

            # Separar nome e tag da ArtifactName
            if ":" in artifact_name:
                image_name, tag = artifact_name.split(":", 1)
            else:
                image_name, tag = artifact_name, ""

            return {
                "image": image_name,
                "_id": image_id,
                "tag": tag,
                "created": created_at,
                "size": size
            }
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Erro ao processar o arquivo {file_path}: {e}")
        return None

def analyze_vulnerability(vulnerability, base_prompt):
    """Gera o experimento baseado na vulnerabilidade."""
    prompt = f"{base_prompt}\n    - Título: {vulnerability.get('Title', 'Título não disponível')}\n    - Descrição: {vulnerability.get('Description', 'Descrição não disponível')}"
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Você é um assistente especializado em criar experimentos de Chaos Engineering para o Chaos Monkey."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000,
            temperature=0.7
        )
        return response['choices'][0]['message']['content'].strip()
    except openai.error.OpenAIError as e:
        print(f"Erro ao gerar experimento para '{vulnerability.get('Title', 'Título não disponível')}': {e}")
        return None

def process_reports():
    """Processa todos os relatórios de vulnerabilidades e gera experimentos."""
    base_prompt = initialize_prompt()

    for file_name in os.listdir(REPORTS_DIR):
        if file_name.endswith(".json"):
            file_path = os.path.join(REPORTS_DIR, file_name)

            try:
                with open(file_path, "r") as file:
                    data = json.load(file)
            except json.JSONDecodeError as e:
                print(f"Erro ao ler o arquivo {file_path}: {e}")
                continue

            image_info = get_image_info_from_report(file_path)
            if not image_info:
                print(f"Não foi possível extrair informações da imagem para {file_path}.")
                continue

            image_name = sanitize_filename(image_info["image"])
            image_dir = os.path.join(OUTPUT_DIR, image_name)
            os.makedirs(image_dir, exist_ok=True)

            # Gerar o arquivo info.json com informações da imagem
            info_file_path = os.path.join(image_dir, "info.json")
            with open(info_file_path, "w") as info_file:
                json.dump(image_info, info_file, indent=4)

            vulnerabilities = data.get("Results", [])
            for result in vulnerabilities:
                vulns = result.get("Vulnerabilities", [])
                for vulnerability in vulns:
                    if vulnerability.get("Severity", "").upper() == "CRITICAL":
                        experiment_content = analyze_vulnerability(vulnerability, base_prompt)
                        if experiment_content:
                            experiment_title = sanitize_filename(vulnerability.get("Title", "experiment"))
                            experiment_file_path = os.path.join(image_dir, f"{experiment_title}.txt")
                            
                            # Conteúdo do experimento não modificado
                            with open(experiment_file_path, "w") as experiment_file:
                                experiment_file.write(experiment_content)
                            print(f"Experimento gerado: {experiment_file_path}")

if __name__ == "__main__":
    # Carregar chave da API
    api_key = load_api_key()
    if not api_key:
        print("Erro: não foi possível carregar a chave da API do OpenAI.")
        exit(1)

    # Configurar a chave da API para o OpenAI
    openai.api_key = api_key

    # Processar os relatórios
    process_reports()
