# 🚀 Guia de Deploy na AWS EC2

## Passo a Passo Completo

### 1. Preparar a Instância EC2

1. Acesse o AWS Console e crie uma instância EC2
2. Escolha Ubuntu Server (versão mais recente)
3. Configure o Security Group:
   - **SSH (22)** - Para acesso remoto
   - **HTTP (80)** - Para acesso web (se usar Nginx)
   - **Custom TCP (8000)** - Para Gunicorn diretamente

### 2. Conectar à Instância

```bash
ssh -i sua-chave.pem ubuntu@seu-ip-publico
```

### 3. Atualizar o Sistema

```bash
sudo apt update && sudo apt upgrade -y
```

### 4. Instalar Dependências do Sistema

```bash
sudo apt install python3 python3-pip python3-venv git -y
```

### 5. Fazer Upload do Projeto

**Opção A - Via Git:**
```bash
git clone seu-repositorio.git
cd e-commerce
```

**Opção B - Via SCP (do seu computador local):**
```bash
scp -i sua-chave.pem -r /caminho/local/e-commerce ubuntu@seu-ip:/home/ubuntu/
```

### 6. Configurar o Ambiente Python

```bash
cd e-commerce
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 7. Inicializar o Banco de Dados

```bash
python popular_banco.py
```

### 8. Testar Localmente na EC2

```bash
# Ainda com venv ativado
python app.py
```

Teste em outro terminal:
```bash
curl http://localhost:5000
```

### 9. Configurar Gunicorn

```bash
# Com venv ativado
gunicorn -c gunicorn_config.py app:app
```

### 10. Criar Serviço Systemd (Opcional mas Recomendado)

Crie o arquivo de serviço:
```bash
sudo nano /etc/systemd/system/ecommerce.service
```

Cole o seguinte conteúdo (ajuste os caminhos):
```ini
[Unit]
Description=E-commerce Gunicorn daemon
After=network.target

[Service]
User=ubuntu
Group=ubuntu
WorkingDirectory=/home/ubuntu/e-commerce
Environment="PATH=/home/ubuntu/e-commerce/venv/bin"
ExecStart=/home/ubuntu/e-commerce/venv/bin/gunicorn -c gunicorn_config.py app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

Ative e inicie o serviço:
```bash
sudo systemctl daemon-reload
sudo systemctl enable ecommerce
sudo systemctl start ecommerce
sudo systemctl status ecommerce
```

### 11. Verificar Logs

```bash
# Logs do serviço
sudo journalctl -u ecommerce -f

# Logs do Gunicorn (se configurado)
tail -f /var/log/ecommerce/access.log
```

### 12. Configurar Firewall (UFW)

```bash
sudo ufw allow 22/tcp
sudo ufw allow 8000/tcp
sudo ufw enable
sudo ufw status
```

### 13. Acessar a Aplicação

Acesse no navegador:
```
http://seu-ip-publico:8000
```

## 🔧 Configuração com Nginx (Opcional - Produção)

Para usar na porta 80 com Nginx:

1. Instale Nginx:
```bash
sudo apt install nginx -y
```

2. Configure o Nginx:
```bash
sudo nano /etc/nginx/sites-available/ecommerce
```

Cole:
```nginx
server {
    listen 80;
    server_name seu-dominio.com ou seu-ip;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

3. Ative o site:
```bash
sudo ln -s /etc/nginx/sites-available/ecommerce /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## 🔐 Segurança Adicional

1. **Altere a SECRET_KEY do Flask:**
```bash
export SECRET_KEY="sua-chave-secreta-muito-forte-aqui"
```

2. **Configure variáveis de ambiente:**
```bash
nano ~/.bashrc
# Adicione:
export SECRET_KEY="sua-chave"
```

3. **Use HTTPS (recomendado):**
   - Configure certificado SSL com Let's Encrypt
   - Ou use AWS Certificate Manager com Load Balancer

## 📝 Comandos Úteis

```bash
# Reiniciar serviço
sudo systemctl restart ecommerce

# Ver status
sudo systemctl status ecommerce

# Ver logs
sudo journalctl -u ecommerce -n 50

# Parar serviço
sudo systemctl stop ecommerce

# Desabilitar serviço
sudo systemctl disable ecommerce
```

## ✅ Checklist de Deploy

- [ ] Instância EC2 criada e acessível
- [ ] Security Group configurado
- [ ] Projeto enviado para EC2
- [ ] Ambiente virtual criado
- [ ] Dependências instaladas
- [ ] Banco de dados inicializado
- [ ] Gunicorn testado
- [ ] Serviço systemd configurado (opcional)
- [ ] Firewall configurado
- [ ] Aplicação acessível via navegador
- [ ] Logs funcionando

## 🆘 Troubleshooting

**Erro de conexão:**
- Verifique Security Group
- Verifique firewall (UFW)
- Verifique se Gunicorn está rodando

**Erro 500:**
- Verifique logs: `sudo journalctl -u ecommerce -n 100`
- Verifique permissões do banco de dados
- Verifique variáveis de ambiente

**Aplicação não inicia:**
- Verifique se o venv está ativado
- Verifique se todas as dependências estão instaladas
- Verifique caminhos no arquivo de serviço

