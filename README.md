![AICHAOS](banner.png)
# AI CHAOS Project
## Dependências
- [x] Docker ou PODMAN ( Breve analise da imagem .tar )
- [x] Tokens disponíveis no OpenAI / ChatGPT
- [x] trivy
- [x] Python 3+

## Trivy ( Vulnerability Scanner )
O **Trivy** é uma ferramenta de código aberto usada para **detecção de vulnerabilidades em segurança e configuração incorreta**. Ele é amplamente utilizado em ambientes DevOps e CI/CD para identificar problemas em imagens de contêiner, arquivos de configuração de infraestrutura como código (IaC), dependências de aplicativos e repositórios de código.

### Principais recursos do Trivy:
1. **Detecção de vulnerabilidades**:
   - Identifica vulnerabilidades em pacotes de software e bibliotecas.
   - Suporta imagens de contêiner, como as usadas no Docker e no Kubernetes.

2. **Verificação de IaC**:
   - Analisa arquivos de infraestrutura como código, como Terraform, Kubernetes YAML e arquivos CloudFormation, para identificar configurações inseguras.

3. **Análise de dependências**:
   - Examina os gerenciadores de dependências (como `npm`, `pip`, `gem`, etc.) para localizar vulnerabilidades em bibliotecas de terceiros.

4. **Verificação de arquivos binários**:
   - Escaneia executáveis e binários para detectar problemas de segurança.

5. **Integração fácil**:
   - Funciona bem com pipelines de CI/CD, como Jenkins, GitHub Actions e GitLab CI.
   - Pode ser integrado a ferramentas de desenvolvimento para validação contínua.

## Modo de uso provisório
### Gerar relatório de vulnerabilidades de imagen existentes
Seleciona a imagen desejada para SCAN.
```
$ select.sh
```

O comando irá gerar um diretório ( vulnerabilities ),  contendo arquivos JSON com a lista de vulnerabilidades da imagem selecionada.

### Execute a geração de scripts para teste de Chaos
O script à seguir, faz um parser nos arquivos, captura as vulnerabilidades e usa o modelo gpt-4o-mini ou gpt-3.5-turbo para classifica-las e gerar scripts de testes para o Chaos Monkey.

```
$ generate.py
```

