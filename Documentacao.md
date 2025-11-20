Documentação do projeto:

# Documentação Técnica - Sistema E-commerce

## 1. Visão Geral do Projeto

Este projeto é uma aplicação web de comércio eletrônico desenvolvida em Python utilizando o framework Flask. O sistema permite que usuários naveguem por um catálogo de produtos, adicionem itens ao carrinho de compras, realizem pedidos e acompanhem seus pedidos. O sistema suporta tanto usuários autenticados quanto visitantes anônimos.

### Funcionalidades Principais:

- Sistema de autenticação (cadastro e login)
- Catálogo de produtos com estoque
- Carrinho de compras (funciona para visitantes e usuários logados)
- Processo de checkout e criação de pedidos
- Gestão de pagamentos
- Visualização de detalhes de pedidos
- Atualização automática de estoque


## 2. Arquitetura e Estrutura do Projeto

### 2.1 Estrutura de Diretórios

```
e-commerce/
├── app.py                      # Aplicação Flask principal (rotas e lógica)
├── models/                     # Módulos de modelo e lógica de negócio
│   ├── model.py               # Gerenciamento de banco de dados
│   └── auth.py                # Autenticação e hash de senhas
├── templates/                  # Templates HTML (Jinja2)
│   ├── base.html              # Template base com layout comum
│   ├── index.html             # Página inicial (catálogo)
│   ├── login.html             # Página de login
│   ├── registrar.html         # Página de cadastro
│   ├── produto-detalhes.html   # Detalhes de um produto
│   ├── carrinho.html          # Carrinho de compras
│   ├── checkout.html          # Finalização de pedido
│   └── pedido-detalhes.html    # Detalhes de um pedido
├── static/                     # Arquivos estáticos
│   └── css/
│       └── style.css          # Estilos CSS
├── database/                   # Scripts de banco de dados
│   └── script-database.sql    # Schema do banco de dados
├── requirements.txt            # Dependências Python
└── gunicorn-config.py         # Configuração para produção (Gunicorn)
```


### 2.2 Padrão Arquitetural

O projeto segue o padrão **MVC (Model-View-Controller)** de forma simplificada:

- **Model**: `models/model.py` e `models/auth.py` - Lógica de dados e autenticação
- **View**: Templates HTML em `templates/` - Apresentação
- **Controller**: `app.py` - Rotas e lógica de controle

---

## 3. Principais Conceitos e Tecnologias Utilizadas

### 3.1 Flask Framework

**Flask** é um microframework web em Python que fornece:

- Sistema de roteamento (`@app.route`)
- Renderização de templates (Jinja2)
- Gerenciamento de sessões
- Sistema de mensagens flash
- Tratamento de requisições HTTP

**Exemplo no código:**

```python
@app.route('/')
def index():
    # Lógica da rota
    return render_template('index.html', produtos=produtos)
```

### 3.2 SQLite Database

**SQLite** é um banco de dados relacional embutido, ideal para aplicações pequenas e médias:

- Não requer servidor separado
- Arquivo único (`ecommerce.db`)
- Suporta SQL padrão
- Transações ACID

**Conexão no código:**

```python
def conectar_db():
    conexao = sqlite3.connect(DB_PATH)
    conexao.row_factory = sqlite3.Row  # Retorna dicionários
    return conexao
```

### 3.3 Autenticação e Segurança

#### Hash de Senhas

O sistema utiliza **SHA-256 com salt** para armazenar senhas de forma segura:

**Conceito de Salt:**

- Salt é uma string aleatória única para cada senha
- Impede ataques de rainbow table
- Mesma senha gera hashes diferentes

**Implementação:**

```python
def hash_senha(senha):
    salt = secrets.token_hex(16)  # Gera salt aleatório
    senha_hash = hashlib.sha256((senha + salt).encode()).hexdigest()
    return f"{salt}:{senha_hash}"  # Armazena salt e hash juntos
```

#### Sessões Flask

- Armazenam dados do usuário logado (`session['cliente_id']`)
- Utilizam cookies assinados criptograficamente
- Requer `SECRET_KEY` configurada

#### Decorador de Autenticação

```python
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'cliente_id' not in session:
            flash('Por favor, faça login para continuar.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function
```

### 3.4 Jinja2 Templates

**Jinja2** é o motor de templates do Flask, permitindo:

- Herança de templates (`{% extends %}`)
- Blocos de conteúdo (`{% block %}`)
- Estruturas de controle (`{% if %}`, `{% for %}`)
- Filtros e funções

**Exemplo:**

```html
{% if session.cliente_id %}
    <span>Olá, {{ session.cliente_nome }}!</span>
{% else %}
    <a href="{{ url_for('login') }}">Login</a>
{% endif %}
```

### 3.5 Gerenciamento de Estado

#### Sessões para Usuários Logados

- Dados armazenados no servidor (cookies assinados)
- Persistem entre requisições
- Seguras (criptografadas)

#### Carrinho para Visitantes

- Armazenado no banco com `cliente_id = NULL`
- Migrado para o usuário após login
- Permite continuidade da experiência

---

## 4. Estrutura do Banco de Dados

### 4.1 Modelo Relacional

O banco possui 6 tabelas principais:

1. **clientes**: Informações dos usuários
2. **produtos**: Catálogo de produtos
3. **pedidos**: Pedidos finalizados
4. **itens_pedido**: Itens de cada pedido
5. **pagamentos**: Informações de pagamento
6. **carrinho_compras**: Carrinho temporário

### 4.2 Relacionamentos

```
clientes (1) ──── (N) pedidos
pedidos (1) ──── (N) itens_pedido
produtos (1) ──── (N) itens_pedido
pedidos (1) ──── (1) pagamentos
clientes (1) ──── (N) carrinho_compras (pode ser NULL para visitantes)
```

### 4.3 Chaves Estrangeiras

- `pedidos.cliente_id` → `clientes.id`
- `itens_pedido.pedido_id` → `pedidos.id`
- `itens_pedido.produto_id` → `produtos.id`
- `pagamentos.pedido_id` → `pedidos.id`

### 4.4 Desnormalização no Carrinho

A tabela `carrinho_compras` armazena `nome_produto` e `preco_unitario` desnormalizados para:

- Performance (evita JOINs)
- Preservar preço histórico
- Funcionar mesmo se produto for deletado

---

## 5. Explicação Detalhada dos Componentes

### 5.1 app.py - Aplicação Principal

#### Inicialização

```python
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'sua-chave-secreta-mude-em-producao')
criar_banco()  # Cria tabelas se não existirem
```

#### Rotas de Autenticação

**`/login` (GET/POST)**

- GET: Exibe formulário de login
- POST: Valida credenciais
  - Busca cliente no banco
  - Verifica hash da senha
  - Cria sessão
  - Migra carrinho de visitante para usuário (se houver)

**`/registrar` (GET/POST)**

- GET: Exibe formulário de cadastro
- POST: Cria novo cliente
  - Valida email único
  - Gera hash da senha
  - Insere no banco

**`/logout`**

- Limpa sessão
- Redireciona para home

#### Rotas de Produtos

**`/` (index)**

- Lista produtos com estoque > 0
- Ordena por nome
- Renderiza catálogo

**`/produto/<id>`**

- Exibe detalhes de um produto
- Valida existência
- Mostra estoque disponível

#### Rotas de Carrinho

**`/carrinho` (GET/POST)**

**Ações POST:**

- `adicionar`: Adiciona produto ao carrinho

  - Valida estoque
  - Incrementa quantidade se já existe
  - Suporta usuário logado e visitante
- `remover`: Remove item do carrinho
- `atualizar`: Atualiza quantidade

  - Valida estoque disponível
  - Valida quantidade > 0

**GET:**

- Lista itens do carrinho
- Calcula total
- Diferencia entre usuário logado e visitante

#### Rotas de Pedidos

**`/checkout` (GET/POST) - Requer login**

**POST:**

- Valida carrinho não vazio
- Valida estoque de todos os itens
- Cria pedido
- Cria itens do pedido
- Atualiza estoque dos produtos
- Cria registro de pagamento
- Limpa carrinho
- Redireciona para detalhes do pedido

**GET:**

- Exibe resumo do pedido
- Mostra dados do cliente
- Formulário de seleção de pagamento

**`/pedido/<id>` - Requer login**

- Exibe detalhes completos do pedido
- Lista itens com subtotais
- Mostra informações de pagamento
- Valida que pedido pertence ao usuário logado

### 5.2 models/model.py - Gerenciamento de Banco

#### `conectar_db()`

- Cria conexão SQLite
- Configura `row_factory` para retornar dicionários
- Facilita acesso: `row['campo']` ao invés de `row[0]`

#### `criar_banco()`

- Verifica existência do schema SQL
- Lê e executa script SQL
- Modifica `CREATE TABLE` para `CREATE TABLE IF NOT EXISTS`
- Chama `popular_produtos()` para dados iniciais

#### `popular_produtos()`

- Insere 20 produtos de exemplo
- Só insere se tabela estiver vazia
- Utiliza `executemany()` para performance

### 5.3 models/auth.py - Autenticação

#### `hash_senha(senha)`

- Gera salt aleatório (32 caracteres hex)
- Concatena senha + salt
- Aplica SHA-256
- Retorna formato: `salt:hash`

#### `verificar_senha(senha, senha_hash_armazenada)`

- Separa salt e hash armazenados
- Recalcula hash com senha fornecida
- Compara hashes
- Retorna True/False

---

## 6. Fluxos de Funcionamento

### 6.1 Fluxo de Compra (Usuário Logado)

1. Usuário navega pelo catálogo (`/`)
2. Clica em produto → vê detalhes (`/produto/<id>`)
3. Adiciona ao carrinho → POST `/carrinho` (ação: adicionar)
4. Visualiza carrinho → GET `/carrinho`
5. Ajusta quantidades se necessário
6. Clica em "Finalizar Compra" → GET `/checkout`
7. Seleciona método de pagamento → POST `/checkout`
8. Sistema cria pedido, atualiza estoque, limpa carrinho
9. Redireciona para `/pedido/<id>` com confirmação

### 6.2 Fluxo de Compra (Visitante)

1. Visitante navega e adiciona produtos (mesmo fluxo)
2. Carrinho armazenado com `cliente_id = NULL`
3. Ao tentar fazer checkout → redirecionado para login
4. Após login → carrinho migrado automaticamente
5. Continua checkout normalmente

### 6.3 Migração de Carrinho no Login

Quando usuário faz login:

1. Sistema busca itens com `cliente_id IS NULL`
2. Para cada item de visitante:
   - Verifica se usuário já tem o produto no carrinho
   - Se sim: soma quantidades (valida estoque)
   - Se não: transfere item para `cliente_id` do usuário
3. Remove itens de visitante após migração

---

## 7. Tratamento de Erros e Validações

### 7.1 Validações de Entrada

- **Campos obrigatórios**: Verificados antes de processar
- **Email único**: Verificado no cadastro
- **Estoque**: Validado ao adicionar/atualizar carrinho
- **Quantidade**: Deve ser > 0

### 7.2 Tratamento de Exceções SQL

```python
try:
    # Operações SQL
except sqlite3.Error as e:
    flash(f'Erro: {e}', 'danger')
    conexao.rollback()  # Reverte transação
finally:
    conexao.close()  # Sempre fecha conexão
```

### 7.3 Mensagens Flash

Sistema de mensagens temporárias:

- `success`: Operação bem-sucedida
- `danger`: Erro
- `warning`: Aviso
- `info`: Informação

---

## 8. Segurança Implementada

### 8.1 Proteção de Senhas

- Hash SHA-256 com salt único
- Senhas nunca armazenadas em texto plano
- Salt aleatório impede rainbow tables

### 8.2 Proteção de Rotas

- Decorador `@login_required` protege rotas sensíveis
- Verificação de propriedade (pedidos só do usuário logado)

### 8.3 SQL Injection

- Uso de **prepared statements** (`?` placeholders)
- Nunca concatena strings em SQL
- Exemplo: `cursor.execute('SELECT * FROM produtos WHERE id = ?', (id,))`

### 8.4 Sessões Seguras

- Cookies assinados criptograficamente
- `SECRET_KEY` deve ser forte em produção
- Dados sensíveis não expostos no cliente

---

## 9. Conceitos de Banco de Dados Aplicados

### 9.1 Transações

- Operações críticas envolvidas em transações
- `commit()` confirma mudanças
- `rollback()` reverte em caso de erro
- Exemplo: Criação de pedido (pedido + itens + pagamento + estoque)

### 9.2 Integridade Referencial

- Foreign Keys garantem consistência
- Pedidos sempre têm cliente válido
- Itens sempre referenciam produtos existentes

### 9.3 Normalização

- Tabelas normalizadas (exceto carrinho por design)
- Evita redundância de dados
- Facilita manutenção

### 9.4 Índices Implícitos

- SQLite cria índices automáticos para PRIMARY KEY
- Melhora performance de buscas

---

## 10. Tecnologias e Bibliotecas

### 10.1 Dependências Principais

**Flask 3.0.0**

- Framework web minimalista
- Roteamento, templates, sessões

**Gunicorn 21.2.0**

- Servidor WSGI para produção
- Suporta múltiplos workers
- Mais robusto que servidor de desenvolvimento do Flask

### 10.2 Bibliotecas Padrão Python

- **sqlite3**: Interface para SQLite
- **hashlib**: Funções de hash (SHA-256)
- **secrets**: Geração de valores aleatórios seguros
- **functools**: Decoradores (`wraps`)
- **os**: Variáveis de ambiente, caminhos

---

## 11. Melhorias e Considerações Futuras

### 11.1 Possíveis Melhorias

1. **Sistema de Admin**: Painel para gerenciar produtos
2. **Histórico de Pedidos**: Lista de pedidos do cliente
3. **Busca e Filtros**: Buscar produtos por nome/categoria
4. **Categorias**: Organizar produtos por categoria
5. **Imagens**: Upload e exibição de imagens de produtos
6. **API REST**: Endpoints JSON para integração
7. **Testes**: Testes unitários e de integração
8. **Logging**: Sistema de logs estruturado
9. **Cache**: Cache de consultas frequentes
10. **Paginação**: Paginar listagem de produtos

### 11.2 Considerações de Produção

- Usar variável de ambiente para `SECRET_KEY`
- Configurar HTTPS
- Implementar rate limiting
- Adicionar backup automático do banco
- Monitoramento e logs
- Usar banco mais robusto (PostgreSQL) para escala

---

## 12. Resumo dos Conceitos Técnicos

### Conceitos de Programação Web

- **HTTP Methods**: GET (leitura), POST (envio de dados)
- **Sessions**: Manutenção de estado entre requisições
- **Cookies**: Armazenamento no cliente
- **Templates**: Separação de lógica e apresentação

### Conceitos de Banco de Dados

- **SQL**: Linguagem de consulta estruturada
- **Relacionamentos**: 1:N, 1:1
- **Transações**: Atomicidade de operações
- **ACID**: Propriedades de transações

### Conceitos de Segurança

- **Hash**: Função unidirecional
- **Salt**: Valor aleatório para hash
- **Prepared Statements**: Prevenção de SQL Injection
- **Autenticação**: Verificação de identidade
- **Autorização**: Controle de acesso

### Conceitos de Arquitetura

- **MVC**: Separação de responsabilidades
- **Separation of Concerns**: Cada módulo tem função específica
- **DRY (Don't Repeat Yourself)**: Reutilização de código

---

## Conclusão

Este projeto demonstra a aplicação prática de diversos conceitos fundamentais de desenvolvimento web:

- Framework web (Flask)
- Banco de dados relacional (SQLite)
- Autenticação e segurança
- Templates e renderização
- Gerenciamento de estado (sessões)
- Tratamento de erros
- Arquitetura de software
