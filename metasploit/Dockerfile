# Use uma imagem base do Ubuntu Slim
FROM ubuntu:20.04

# Configurar variáveis de ambiente
ENV LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    DEBIAN_FRONTEND=noninteractive \
    TZ=Etc/UTC

# Atualizar pacotes e instalar dependências
RUN apt-get update && apt-get install -y \
    curl \
    gnupg2 \
    postgresql \
    git \
    build-essential \
    libreadline-dev \
    libssl-dev \
    zlib1g-dev \
    libpq-dev \
    libsqlite3-dev \
    ruby-full \
    tzdata \
    && apt-get clean

# Instalar o Metasploit Framework
RUN curl https://raw.githubusercontent.com/rapid7/metasploit-omnibus/master/config/templates/metasploit-framework-wrappers/msfupdate.erb > msfinstall && \
    chmod 755 msfinstall && \
    ./msfinstall

# Criar um usuário não root (boa prática de segurança)
RUN useradd -m -s /bin/bash msf
USER msf
WORKDIR /home/msf

# Expor porta para comunicação
EXPOSE 4444

# Comando padrão ao iniciar o container
CMD ["msfconsole", "-q"]
