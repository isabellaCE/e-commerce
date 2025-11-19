# E-commerce - Trabalho Final

Aplicação web de comércio eletrônico simplificada desenvolvida com Python e Flask.

## 🚀 Funcionalidades

- ✅ Cadastro e login de clientes com hash de senha
- ✅ Catálogo de produtos
- ✅ Carrinho de compras (funciona sem login)
- ✅ Checkout e criação de pedidos
- ✅ Atualização automática de estoque
- ✅ Gestão de pagamentos
- ✅ Tratamento de erros

## 📋 Requisitos

- Python 3.8+
- Flask
- SQLite

## 🔧 Instalação

1. Clone o repositório ou navegue até a pasta do projeto

2. Instale as dependências:
```bash
pip install -r requirements.txt
```

3. Inicialize o banco de dados:
```bash
python app.py
```

## 🏃 Executando Localmente

```bash
python app.py
```

A aplicação estará disponível em `http://localhost:5000`

## 🌐 Deploy na AWS EC2

### 1. Preparar a instância EC2

- Crie uma instância EC2 (Ubuntu recomendado)
- Configure o Security Group para permitir:
  - SSH (porta 22)
  - HTTP (porta 80)
  - Porta customizada (8000) ou configure um reverse proxy

### 2. Conectar e configurar

```bash
# Conecte via SSH
ssh -i sua-chave.pem ubuntu@seu-ip-ec2

# Atualize o sistema
sudo apt update && sudo apt upgrade -y

# Instale Python e pip
sudo apt install python3 python3-pip python3-venv -y

# Clone ou faça upload do projeto
# ...

# Crie o ambiente virtual
python3 -m venv venv
source venv/bin/activate

# Instale dependências
pip install -r requirements.txt
```

### 3. Executar com Gunicorn

```bash
# Ative o ambiente virtual
source venv/bin/activate

# Execute com Gunicorn
gunicorn -c gunicorn_config.py app:app

# Ou diretamente:
gunicorn --bind 0.0.0.0:8000 app:app
```

### 4. Configurar como serviço (opcional)

Crie um arquivo `/etc/systemd/system/ecommerce.service`:

```ini
[Unit]
Description=E-commerce Gunicorn daemon
After=network.target

[Service]
User=ubuntu
Group=ubuntu
WorkingDirectory=/home/ubuntu/e-commerce
ExecStart=/home/ubuntu/e-commerce/venv/bin/gunicorn -c gunicorn_config.py app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

Ative o serviço:
```bash
sudo systemctl enable ecommerce
sudo systemctl start ecommerce
sudo systemctl status ecommerce
```

## 📁 Estrutura do Projeto

```
e-commerce/
├── app.py                 # Aplicação Flask principal
├── models/                # Modelos e lógica de negócio
│   ├── model.py          # Conexão e criação do banco
│   └── auth.py           # Autenticação e hash de senha
├── routes/               # Rotas (organização futura)
├── templates/            # Templates HTML
│   ├── base.html
│   ├── index.html
│   ├── login.html
│   ├── registrar.html
│   ├── produto_detalhes.html
│   ├── carrinho.html
│   ├── checkout.html
│   └── pedido_detalhes.html
├── static/               # Arquivos estáticos
│   └── css/
│       └── style.css
├── database/             # Scripts SQL
│   └── script-database.sql
├── requirements.txt      # Dependências Python
├── gunicorn_config.py    # Configuração Gunicorn
└── popular_banco.py     # Script para popular dados
```

## 🔐 Segurança

- Senhas são armazenadas com hash SHA-256 + salt
- Sessões Flask para autenticação
- Validação de dados de entrada
- Tratamento de erros SQL

## 📝 Rotas da Aplicação

- `/` - Página inicial (catálogo)
- `/produto/<id>` - Detalhes do produto
- `/carrinho` - Carrinho de compras
- `/checkout` - Finalização de pedido (requer login)
- `/pedido/<id>` - Detalhes do pedido (requer login)
- `/login` - Login
- `/registrar` - Cadastro
- `/logout` - Logout

## 👥 Autores

Trabalho Final - Desenvolvimento de Aplicações Web Backend

## 📄 Licença

Este projeto foi desenvolvido para fins educacionais.
