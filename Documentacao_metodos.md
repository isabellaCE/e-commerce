# Documentação Detalhada dos Métodos - E-commerce

Este documento explica detalhadamente cada método e função dos arquivos principais do projeto.

---

## 📄 app.py - Aplicação Flask Principal

### Configuração Inicial

```1:11:app.py
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from models.model import conectar_db, criar_banco
from models.auth import hash_senha, verificar_senha
import sqlite3
from functools import wraps
import os

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'sua-chave-secreta-mude-em-producao')

criar_banco()
```

**Explicação:**

- Cria instância do Flask
- Define `SECRET_KEY` para sessões (usa variável de ambiente ou valor padrão)
- Chama `criar_banco()` na inicialização para garantir que o banco existe

---

### `login_required(f)` - Decorador de Autenticação

```13:20:app.py
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'cliente_id' not in session:
            flash('Por favor, faça login para continuar.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function
```

**Propósito:** Protege rotas que exigem autenticação.

**Parâmetros:**

- `f`: Função a ser decorada

**Retorno:** Função decorada que verifica autenticação antes de executar

**Funcionamento:**

1. `@wraps(f)`: Preserva metadados da função original (nome, docstring)
2. Verifica se `'cliente_id'` existe na sessão
3. Se não existir: exibe mensagem e redireciona para login
4. Se existir: executa a função original com `*args, **kwargs`

**Conceitos:**

- Decorador Python
- Closure (função interna acessa variáveis externas)
- `*args, **kwargs` para passar argumentos dinamicamente

**Uso:**

```python
@app.route('/checkout')
@login_required
def checkout():
    # Esta rota só é acessível se o usuário estiver logado
```

---

### `login()` - Autenticação de Usuário

```23:106:app.py
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        senha = request.form.get('senha')
      
        if not email or not senha:
            flash('Por favor, preencha todos os campos.', 'danger')
            return render_template('login.html')
      
        conexao = conectar_db()
        cursor = conexao.cursor()
      
        try:
            cursor.execute('SELECT id, nome, email, senha_hash FROM clientes WHERE email = ?', (email,))
            cliente = cursor.fetchone()
          
            if cliente and verificar_senha(senha, cliente['senha_hash']):
                cliente_id = cliente['id']
                session['cliente_id'] = cliente_id
                session['cliente_nome'] = cliente['nome']
                session['cliente_email'] = cliente['email']
              
                try:
                    cursor.execute('''
                        SELECT id, produto_id, nome_produto, preco_unitario, quantidade
                        FROM carrinho_compras
                        WHERE cliente_id IS NULL
                    ''')
                    itens_visitante = cursor.fetchall()
                  
                    if itens_visitante:
                        for item_visitante in itens_visitante:
                            item_id_visitante = item_visitante['id']
                            produto_id = item_visitante['produto_id']
                            quantidade_visitante = item_visitante['quantidade']
                          
                            cursor.execute('''
                                SELECT id, quantidade FROM carrinho_compras
                                WHERE cliente_id = ? AND produto_id = ?
                            ''', (cliente_id, produto_id))
                            item_existente = cursor.fetchone()
                          
                            if item_existente:
                                nova_quantidade = item_existente['quantidade'] + quantidade_visitante
                              
                                cursor.execute('SELECT estoque FROM produtos WHERE id = ?', (produto_id,))
                                produto = cursor.fetchone()
                              
                                if produto and nova_quantidade <= produto['estoque']:
                                    cursor.execute('''
                                        UPDATE carrinho_compras
                                        SET quantidade = ?
                                        WHERE id = ?
                                    ''', (nova_quantidade, item_existente['id']))
                                else:
                                    pass
                              
                                cursor.execute('''
                                    DELETE FROM carrinho_compras
                                    WHERE id = ?
                                ''', (item_id_visitante,))
                            else:
                                cursor.execute('''
                                    UPDATE carrinho_compras
                                    SET cliente_id = ?
                                    WHERE id = ?
                                ''', (cliente_id, item_id_visitante))
                      
                        conexao.commit()
                except sqlite3.Error as e:
                    conexao.rollback()
                    pass
              
                flash(f'Bem-vindo, {cliente["nome"]}!', 'success')
                return redirect(url_for('index'))
            else:
                flash('Email ou senha incorretos.', 'danger')
        except sqlite3.Error as e:
            flash(f'Erro ao fazer login: {e}', 'danger')
        finally:
            conexao.close()
  
    return render_template('login.html')
```

**Rota:** `/login` (GET e POST)

**Propósito:** Autentica usuário e migra carrinho de visitante.

**Fluxo GET:**

- Renderiza template de login

**Fluxo POST:**

1. Validação de campos:

   - Obtém `email` e `senha` do formulário
   - Se vazios, exibe erro e retorna template
2. Busca no banco:

   - Conecta ao banco
   - Busca cliente por email
   - Usa prepared statement (`?`) para evitar SQL injection
3. Verificação de senha:

   - Chama `verificar_senha()` para comparar hash
   - Se válido, cria sessão
4. Criação de sessão:

   - Armazena `cliente_id`, `cliente_nome`, `cliente_email` na sessão
   - Sessão persiste entre requisições via cookies
5. Migração de carrinho (se houver itens de visitante):

   - Busca itens com `cliente_id IS NULL`
   - Para cada item:
     - Verifica se usuário já tem o produto no carrinho
     - Se sim: soma quantidades (valida estoque) e atualiza
     - Se não: transfere item para `cliente_id` do usuário
     - Remove item de visitante após migração
   - Commit da transação
6. Resposta:

   - Mensagem de boas-vindas
   - Redireciona para index

**Tratamento de erros:**

- Try/except para erros SQL
- Rollback em caso de erro na migração
- Finally fecha conexão

**Conceitos:**

- Prepared statements
- Transações SQL
- Migração de estado (carrinho visitante → usuário)
- Sessões Flask

---

### `registrar()` - Cadastro de Novo Usuário

```108:144:app.py
@app.route('/registrar', methods=['GET', 'POST'])
def registrar():
    if request.method == 'POST':
        nome = request.form.get('nome')
        email = request.form.get('email')
        senha = request.form.get('senha')
        telefone = request.form.get('telefone', '')
      
        if not nome or not email or not senha:
            flash('Por favor, preencha todos os campos obrigatórios.', 'danger')
            return render_template('registrar.html')
      
        conexao = conectar_db()
        cursor = conexao.cursor()
      
        try:
            cursor.execute('SELECT id FROM clientes WHERE email = ?', (email,))
            if cursor.fetchone():
                flash('Este email já está cadastrado.', 'danger')
                return render_template('registrar.html')
          
            senha_hash = hash_senha(senha)
            cursor.execute(
                'INSERT INTO clientes (nome, email, senha_hash, telefone) VALUES (?, ?, ?, ?)',
                (nome, email, senha_hash, telefone)
            )
            conexao.commit()
          
            flash('Cadastro realizado com sucesso! Faça login para continuar.', 'success')
            return redirect(url_for('login'))
        except sqlite3.Error as e:
            flash(f'Erro ao cadastrar: {e}', 'danger')
            conexao.rollback()
        finally:
            conexao.close()
  
    return render_template('registrar.html')
```

**Rota:** `/registrar` (GET e POST)

**Propósito:** Cria novo usuário no sistema.

**Fluxo GET:**

- Renderiza template de registro

**Fluxo POST:**

1. Validação:

   - Obtém dados do formulário
   - `telefone` é opcional (default: `''`)
   - Valida campos obrigatórios
2. Verificação de email único:

   - Busca cliente por email
   - Se existir, exibe erro e retorna
3. Hash da senha:

   - Chama `hash_senha()` para gerar hash com salt
   - Senha nunca armazenada em texto plano
4. Inserção:

   - Insere novo cliente
   - Commit da transação
5. Resposta:

   - Mensagem de sucesso
   - Redireciona para login

**Tratamento de erros:**

- Try/except para erros SQL
- Rollback em caso de erro
- Finally fecha conexão

**Conceitos:**

- Validação de dados
- Unicidade de email (constraint UNIQUE)
- Hash de senhas
- Transações SQL

---

### `logout()` - Encerramento de Sessão

```146:150:app.py
@app.route('/logout')
def logout():
    session.clear()
    flash('Você foi desconectado.', 'info')
    return redirect(url_for('index'))
```

**Rota:** `/logout` (GET)

**Propósito:** Encerra a sessão do usuário.

**Funcionamento:**

1. `session.clear()`: Remove todos os dados da sessão
2. Exibe mensagem informativa
3. Redireciona para página inicial

**Conceitos:**

- Gerenciamento de sessão
- Limpeza de estado

---

### `index()` - Página Inicial (Catálogo)

```153:167:app.py
@app.route('/')
def index():
    conexao = conectar_db()
    cursor = conexao.cursor()
  
    try:
        cursor.execute('SELECT id, nome, descricao, preco, estoque FROM produtos WHERE estoque > 0 ORDER BY nome')
        produtos = cursor.fetchall()
    except sqlite3.Error as e:
        flash(f'Erro ao carregar produtos: {e}', 'danger')
        produtos = []
    finally:
        conexao.close()
  
    return render_template('index.html', produtos=produtos)
```

**Rota:** `/` (GET)

**Propósito:** Exibe catálogo de produtos disponíveis.

**Funcionamento:**

1. Conecta ao banco
2. Consulta SQL:
   - Seleciona produtos com `estoque > 0`
   - Ordena por nome
3. Tratamento de erros:
   - Se erro, define `produtos = []` e exibe mensagem
4. Renderiza template com lista de produtos

**Conceitos:**

- Consultas SQL com filtros
- Tratamento de exceções
- Renderização de templates

---

### `produto_detalhes(id)` - Detalhes de um Produto

```169:187:app.py
@app.route('/produto/<int:id>')
def produto_detalhes(id):
    conexao = conectar_db()
    cursor = conexao.cursor()
  
    try:
        cursor.execute('SELECT id, nome, descricao, preco, estoque FROM produtos WHERE id = ?', (id,))
        produto = cursor.fetchone()
      
        if not produto:
            flash('Produto não encontrado.', 'danger')
            return redirect(url_for('index'))
    except sqlite3.Error as e:
        flash(f'Erro ao carregar produto: {e}', 'danger')
        return redirect(url_for('index'))
    finally:
        conexao.close()
  
    return render_template('produto_detalhes.html', produto=produto)
```

**Rota:** `/produto/<int:id>` (GET)

**Propósito:** Exibe detalhes de um produto específico.

**Parâmetros:**

- `id`: ID do produto (convertido para int pelo Flask)

**Funcionamento:**

1. Busca produto por ID
2. Validação:
   - Se não encontrado, exibe erro e redireciona
3. Renderiza template com dados do produto

**Conceitos:**

- Conversão de tipos em rotas (`<int:id>`)
- Validação de existência
- Tratamento de erros

---

### `carrinho()` - Gerenciamento do Carrinho

```190:333:app.py
@app.route('/carrinho', methods=['GET', 'POST'])
def carrinho():
    conexao = conectar_db()
    cursor = conexao.cursor()
  
    if request.method == 'POST':
        acao = request.form.get('acao')
        produto_id = request.form.get('produto_id')
        quantidade = request.form.get('quantidade', type=int)
      
        if acao == 'adicionar':
            cursor.execute('SELECT id, nome, preco, estoque FROM produtos WHERE id = ?', (produto_id,))
            produto = cursor.fetchone()
          
            if not produto:
                flash('Produto não encontrado.', 'danger')
                return redirect(url_for('index'))
          
            if quantidade > produto['estoque']:
                flash(f'Quantidade solicitada ({quantidade}) excede o estoque disponível ({produto["estoque"]}).', 'danger')
                return redirect(url_for('produto_detalhes', id=produto_id))
          
            cliente_id = session.get('cliente_id')
          
            if cliente_id:
                cursor.execute(
                    'SELECT id, quantidade FROM carrinho_compras WHERE cliente_id = ? AND produto_id = ?',
                    (cliente_id, produto_id)
                )
            else:
                session_id = session.get('session_id', '')
                cursor.execute(
                    'SELECT id, quantidade FROM carrinho_compras WHERE cliente_id IS NULL AND produto_id = ?',
                    (produto_id,)
                )
          
            item_existente = cursor.fetchone()
          
            if item_existente:
                nova_quantidade = item_existente['quantidade'] + quantidade
                if nova_quantidade > produto['estoque']:
                    flash(f'Quantidade total ({nova_quantidade}) excede o estoque disponível ({produto["estoque"]}).', 'danger')
                    return redirect(url_for('produto_detalhes', id=produto_id))
              
                cursor.execute(
                    'UPDATE carrinho_compras SET quantidade = ? WHERE id = ?',
                    (nova_quantidade, item_existente['id'])
                )
            else:
                if cliente_id:
                    cursor.execute(
                        'INSERT INTO carrinho_compras (cliente_id, produto_id, nome_produto, preco_unitario, quantidade) VALUES (?, ?, ?, ?, ?)',
                        (cliente_id, produto_id, produto['nome'], produto['preco'], quantidade)
                    )
                else:
                    cursor.execute(
                        'INSERT INTO carrinho_compras (cliente_id, produto_id, nome_produto, preco_unitario, quantidade) VALUES (NULL, ?, ?, ?, ?)',
                        (produto_id, produto['nome'], produto['preco'], quantidade)
                    )
          
            conexao.commit()
            flash('Produto adicionado ao carrinho!', 'success')
            return redirect(url_for('carrinho'))
      
        elif acao == 'remover':
            item_id = request.form.get('item_id')
            cliente_id = session.get('cliente_id')
          
            if cliente_id:
                cursor.execute('DELETE FROM carrinho_compras WHERE id = ? AND cliente_id = ?', (item_id, cliente_id))
            else:
                cursor.execute('DELETE FROM carrinho_compras WHERE id = ? AND cliente_id IS NULL', (item_id,))
          
            conexao.commit()
            flash('Item removido do carrinho.', 'info')
            return redirect(url_for('carrinho'))
      
        elif acao == 'atualizar':
            item_id = request.form.get('item_id')
            nova_quantidade = request.form.get('quantidade', type=int)
          
            if nova_quantidade <= 0:
                flash('Quantidade deve ser maior que zero.', 'danger')
                return redirect(url_for('carrinho'))
          
            cursor.execute('SELECT produto_id, quantidade FROM carrinho_compras WHERE id = ?', (item_id,))
            item = cursor.fetchone()
          
            if item:
                cursor.execute('SELECT estoque FROM produtos WHERE id = ?', (item['produto_id'],))
                produto = cursor.fetchone()
              
                if nova_quantidade > produto['estoque']:
                    flash(f'Quantidade solicitada excede o estoque disponível ({produto["estoque"]}).', 'danger')
                    return redirect(url_for('carrinho'))
              
                cliente_id = session.get('cliente_id')
                if cliente_id:
                    cursor.execute(
                        'UPDATE carrinho_compras SET quantidade = ? WHERE id = ? AND cliente_id = ?',
                        (nova_quantidade, item_id, cliente_id)
                    )
                else:
                    cursor.execute(
                        'UPDATE carrinho_compras SET quantidade = ? WHERE id = ? AND cliente_id IS NULL',
                        (nova_quantidade, item_id)
                    )
              
                conexao.commit()
                flash('Quantidade atualizada!', 'success')
          
            return redirect(url_for('carrinho'))
  
    cliente_id = session.get('cliente_id')
  
    try:
        if cliente_id:
            cursor.execute('''
                SELECT c.id, c.produto_id, c.nome_produto, c.preco_unitario, c.quantidade,
                       (c.preco_unitario * c.quantidade) as subtotal
                FROM carrinho_compras c
                WHERE c.cliente_id = ?
                ORDER BY c.criado_em DESC
            ''', (cliente_id,))
        else:
            cursor.execute('''
                SELECT c.id, c.produto_id, c.nome_produto, c.preco_unitario, c.quantidade,
                       (c.preco_unitario * c.quantidade) as subtotal
                FROM carrinho_compras c
                WHERE c.cliente_id IS NULL
                ORDER BY c.criado_em DESC
            ''')
      
        itens = cursor.fetchall()
      
        total = sum(item['subtotal'] for item in itens)
    except sqlite3.Error as e:
        flash(f'Erro ao carregar carrinho: {e}', 'danger')
        itens = []
        total = 0
    finally:
        conexao.close()
  
    return render_template('carrinho.html', itens=itens, total=total)
```

**Rota:** `/carrinho` (GET e POST)

**Propósito:** Gerencia o carrinho de compras (adicionar, remover, atualizar, visualizar).

#### Ação: `adicionar` (POST)

**Funcionamento:**

1. Validação do produto:

   - Busca produto por ID
   - Se não encontrado, redireciona
2. Validação de estoque:

   - Verifica se quantidade solicitada <= estoque
   - Se exceder, exibe erro e redireciona
3. Verificação de item existente:

   - Se usuário logado: busca por `cliente_id` e `produto_id`
   - Se visitante: busca por `cliente_id IS NULL` e `produto_id`
4. Lógica de adição:

   - Se item existe: soma quantidades (valida estoque novamente) e atualiza
   - Se não existe: insere novo item
   - Suporta usuário logado e visitante
5. Commit e resposta:

   - Salva alterações
   - Mensagem de sucesso
   - Redireciona para carrinho

#### Ação: `remover` (POST)

**Funcionamento:**

1. Obtém `item_id` do formulário
2. Remove item do carrinho:
   - Se logado: remove com `cliente_id`
   - Se visitante: remove com `cliente_id IS NULL`
3. Commit e redireciona

#### Ação: `atualizar` (POST)

**Funcionamento:**

1. Validação:
   - Quantidade deve ser > 0
2. Busca item e produto:
   - Obtém dados do item
   - Verifica estoque atual do produto
3. Validação de estoque:
   - Nova quantidade não pode exceder estoque
4. Atualização:
   - Atualiza quantidade no carrinho
   - Diferencia usuário logado e visitante
5. Commit e redireciona

#### Visualização (GET)

**Funcionamento:**

1. Identifica usuário:
   - Obtém `cliente_id` da sessão (pode ser None)
2. Consulta SQL:
   - Se logado: busca itens com `cliente_id = ?`
   - Se visitante: busca itens com `cliente_id IS NULL`
   - Calcula subtotal por item (`preco_unitario * quantidade`)
   - Ordena por data de criação (mais recentes primeiro)
3. Cálculo do total:
   - Soma todos os subtotais usando list comprehension
4. Renderiza template com itens e total

**Conceitos:**

- CRUD (Create, Read, Update, Delete)
- Validação de estoque
- Suporte a usuários anônimos
- Cálculos em SQL e Python
- Prepared statements com condições dinâmicas

---

### `checkout()` - Finalização de Pedido

```335:430:app.py
@app.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    conexao = conectar_db()
    cursor = conexao.cursor()
    cliente_id = session['cliente_id']
  
    if request.method == 'POST':
        tipo_pagamento = request.form.get('tipo_pagamento')
      
        if not tipo_pagamento:
            flash('Selecione um método de pagamento.', 'danger')
            return redirect(url_for('checkout'))
      
        try:
            cursor.execute('''
                SELECT produto_id, nome_produto, preco_unitario, quantidade
                FROM carrinho_compras
                WHERE cliente_id = ?
            ''', (cliente_id,))
            itens_carrinho = cursor.fetchall()
          
            if not itens_carrinho:
                flash('Seu carrinho está vazio.', 'warning')
                return redirect(url_for('carrinho'))
          
            for item in itens_carrinho:
                cursor.execute('SELECT estoque FROM produtos WHERE id = ?', (item['produto_id'],))
                produto = cursor.fetchone()
              
                if not produto or produto['estoque'] < item['quantidade']:
                    flash(f'Produto "{item["nome_produto"]}" sem estoque suficiente.', 'danger')
                    return redirect(url_for('carrinho'))
          
            total = sum(item['preco_unitario'] * item['quantidade'] for item in itens_carrinho)
          
            cursor.execute(
                'INSERT INTO pedidos (cliente_id, status) VALUES (?, ?)',
                (cliente_id, 'pendente')
            )
            pedido_id = cursor.lastrowid
          
            for item in itens_carrinho:
                cursor.execute(
                    'INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario) VALUES (?, ?, ?, ?)',
                    (pedido_id, item['produto_id'], item['quantidade'], item['preco_unitario'])
                )
              
                cursor.execute(
                    'UPDATE produtos SET estoque = estoque - ? WHERE id = ?',
                    (item['quantidade'], item['produto_id'])
                )
          
            cursor.execute(
                'INSERT INTO pagamentos (pedido_id, tipo, valor, status) VALUES (?, ?, ?, ?)',
                (pedido_id, tipo_pagamento, total, 'aguardando')
            )
          
            cursor.execute('DELETE FROM carrinho_compras WHERE cliente_id = ?', (cliente_id,))
          
            conexao.commit()
            flash(f'Pedido #{pedido_id} criado com sucesso!', 'success')
            return redirect(url_for('pedido_detalhes', id=pedido_id))
          
        except sqlite3.Error as e:
            flash(f'Erro ao processar pedido: {e}', 'danger')
            conexao.rollback()
            return redirect(url_for('carrinho'))
        finally:
            conexao.close()
  
    try:
        cursor.execute('''
            SELECT c.id, c.produto_id, c.nome_produto, c.preco_unitario, c.quantidade,
                   (c.preco_unitario * c.quantidade) as subtotal
            FROM carrinho_compras c
            WHERE c.cliente_id = ?
        ''', (cliente_id,))
        itens = cursor.fetchall()
      
        if not itens:
            flash('Seu carrinho está vazio.', 'warning')
            return redirect(url_for('carrinho'))
      
        total = sum(item['subtotal'] for item in itens)
      
        cursor.execute('SELECT nome, email, telefone FROM clientes WHERE id = ?', (cliente_id,))
        cliente = cursor.fetchone()
      
    except sqlite3.Error as e:
        flash(f'Erro ao carregar checkout: {e}', 'danger')
        return redirect(url_for('carrinho'))
    finally:
        conexao.close()
  
    return render_template('checkout.html', itens=itens, total=total, cliente=cliente)
```

**Rota:** `/checkout` (GET e POST) - **Requer autenticação**

**Propósito:** Finaliza pedido, criando registro permanente e atualizando estoque.

#### Processamento de Pedido (POST)

**Funcionamento:**

1. Validação de pagamento:

   - Verifica se método de pagamento foi selecionado
2. Validação do carrinho:

   - Busca itens do carrinho
   - Se vazio, redireciona
3. Validação de estoque (última verificação):

   - Para cada item, verifica estoque disponível
   - Se algum produto sem estoque, cancela e redireciona
   - **Importante:** Validação dupla (no carrinho e no checkout)
4. Cálculo do total:

   - Soma `preco_unitario * quantidade` de todos os itens
5. Criação do pedido (transação):

   - **a) Cria pedido:**

     - Insere em `pedidos` com status 'pendente'
     - Obtém `pedido_id` com `cursor.lastrowid`
   - **b) Cria itens do pedido:**

     - Para cada item do carrinho, insere em `itens_pedido`
     - Armazena preço unitário (preserva preço histórico)
   - **c) Atualiza estoque:**

     - Decrementa estoque de cada produto
     - `estoque = estoque - quantidade`
   - **d) Cria pagamento:**

     - Insere em `pagamentos` com status 'aguardando'
   - **e) Limpa carrinho:**

     - Remove todos os itens do carrinho do cliente
6. Commit da transação:

   - Todas as operações são atômicas
   - Se qualquer erro ocorrer, rollback reverte tudo
7. Resposta:

   - Mensagem de sucesso com número do pedido
   - Redireciona para detalhes do pedido

**Tratamento de erros:**

- Try/except captura erros SQL
- Rollback reverte todas as mudanças
- Redireciona para carrinho em caso de erro

#### Visualização (GET)

**Funcionamento:**

1. Busca itens do carrinho:
   - Calcula subtotal por item
2. Validação:
   - Se carrinho vazio, redireciona
3. Cálculo do total:
   - Soma subtotais
4. Busca dados do cliente:
   - Nome, email, telefone para exibição
5. Renderiza template:
   - Exibe resumo do pedido
   - Formulário de seleção de pagamento
   - Dados do cliente

**Conceitos:**

- Transações atômicas
- Integridade referencial
- Validação dupla de estoque
- Preservação de preço histórico
- Operações em cascata (pedido → itens → estoque → pagamento)

---

### `pedido_detalhes(id)` - Visualização de Pedido

```432:473:app.py
@app.route('/pedido/<int:id>')
@login_required
def pedido_detalhes(id):
    conexao = conectar_db()
    cursor = conexao.cursor()
    cliente_id = session['cliente_id']
  
    try:
        cursor.execute('''
            SELECT p.id, p.data, p.status, c.nome as cliente_nome
            FROM pedidos p
            JOIN clientes c ON p.cliente_id = c.id
            WHERE p.id = ? AND p.cliente_id = ?
        ''', (id, cliente_id))
        pedido = cursor.fetchone()
      
        if not pedido:
            flash('Pedido não encontrado.', 'danger')
            return redirect(url_for('index'))
      
        cursor.execute('''
            SELECT ip.quantidade, ip.preco_unitario, 
                   (ip.quantidade * ip.preco_unitario) as subtotal,
                   pr.nome as produto_nome
            FROM itens_pedido ip
            JOIN produtos pr ON ip.produto_id = pr.id
            WHERE ip.pedido_id = ?
        ''', (id,))
        itens = cursor.fetchall()
      
        cursor.execute('SELECT tipo, valor, status FROM pagamentos WHERE pedido_id = ?', (id,))
        pagamento = cursor.fetchone()
      
        total = sum(item['subtotal'] for item in itens)
      
    except sqlite3.Error as e:
        flash(f'Erro ao carregar pedido: {e}', 'danger')
        return redirect(url_for('index'))
    finally:
        conexao.close()
  
    return render_template('pedido_detalhes.html', pedido=pedido, itens=itens, pagamento=pagamento, total=total)
```

**Rota:** `/pedido/<int:id>` (GET) - **Requer autenticação**

**Propósito:** Exibe detalhes completos de um pedido específico.

**Parâmetros:**

- `id`: ID do pedido

**Funcionamento:**

1. Busca dados do pedido:

   - JOIN entre `pedidos` e `clientes`
   - Filtra por `pedido_id` E `cliente_id` (segurança: usuário só vê seus pedidos)
   - Se não encontrado, redireciona
2. Busca itens do pedido:

   - JOIN entre `itens_pedido` e `produtos`
   - Calcula subtotal por item
   - Obtém nome do produto
3. Busca informações de pagamento:

   - Tipo, valor e status do pagamento
4. Cálculo do total:

   - Soma subtotais dos itens
5. Renderiza template:

   - Dados do pedido
   - Lista de itens
   - Informações de pagamento
   - Total

**Segurança:**

- Validação dupla: `p.id = ? AND p.cliente_id = ?`
- Impede acesso a pedidos de outros usuários

**Conceitos:**

- JOINs SQL (INNER JOIN)
- Segurança: validação de propriedade
- Agregações (soma de subtotais)
- Relacionamentos entre tabelas

---

## 📄 models/auth.py - Módulo de Autenticação

### `hash_senha(senha)` - Geração de Hash de Senha

```4:7:models/auth.py
def hash_senha(senha):
	salt = secrets.token_hex(16)
	senha_hash = hashlib.sha256((senha + salt).encode()).hexdigest()
	return f"{salt}:{senha_hash}"
```

**Propósito:** Gera hash seguro de uma senha usando SHA-256 com salt.

**Parâmetros:**

- `senha` (str): Senha em texto plano

**Retorno:** String no formato `"salt:hash"`

**Funcionamento:**

1. Geração de salt:

   - `secrets.token_hex(16)`: Gera 16 bytes aleatórios em hexadecimal (32 caracteres)
   - Salt único para cada senha
2. Criação do hash:

   - Concatena senha + salt
   - Converte para bytes (`.encode()`)
   - Aplica SHA-256
   - Converte hash para hexadecimal (`.hexdigest()`)
3. Retorno:

   - Formato: `"salt:hash"`
   - Permite recuperar salt na verificação

**Exemplo:**

```python
hash_senha("minhasenha123")
# Retorna: "a1b2c3d4e5f6...:9f8e7d6c5b4a3..."
```

**Conceitos:**

- Hash unidirecional (não pode ser revertido)
- Salt (previne rainbow tables)
- SHA-256 (algoritmo criptográfico)
- Encoding (string → bytes)

---

### `verificar_senha(senha, senha_hash_armazenada)` - Verificação de Senha

```9:15:models/auth.py
def verificar_senha(senha, senha_hash_armazenada):
	try:
		salt, hash_armazenado = senha_hash_armazenada.split(':')
		hash_calculado = hashlib.sha256((senha + salt).encode()).hexdigest()
		return hash_calculado == hash_armazenado
	except:
		return False
```

**Propósito:** Verifica se uma senha corresponde ao hash armazenado.

**Parâmetros:**

- `senha` (str): Senha fornecida pelo usuário
- `senha_hash_armazenada` (str): Hash armazenado no formato `"salt:hash"`

**Retorno:** `True` se senha correta, `False` caso contrário

**Funcionamento:**

1. Extração do salt e hash:

   - Divide string por `:` usando `split(':')`
   - Obtém `salt` e `hash_armazenado`
2. Cálculo do hash:

   - Concatena senha fornecida + salt extraído
   - Aplica SHA-256 (mesmo processo de `hash_senha()`)
3. Comparação:

   - Compara hash calculado com hash armazenado
   - Retorna `True` se iguais, `False` se diferentes
4. Tratamento de erros:

   - Try/except captura erros (formato inválido, etc.)
   - Retorna `False` em caso de erro

**Exemplo:**

```python
hash_armazenado = "a1b2c3...:9f8e7d..."
verificar_senha("minhasenha123", hash_armazenado)  # True
verificar_senha("senhaerrada", hash_armazenado)    # False
```

**Conceitos:**

- Comparação de hashes
- Parsing de strings
- Tratamento de exceções
- Segurança: nunca compara senhas diretamente, apenas hashes

**Por que usar salt?**

- Sem salt: mesma senha gera mesmo hash → vulnerável a rainbow tables
- Com salt: mesma senha gera hashes diferentes → mais seguro

---

## 📄 models/model.py - Módulo de Banco de Dados

### `conectar_db()` - Conexão com Banco de Dados

```7:13:models/model.py
def conectar_db():
  try:
    conexao = sqlite3.connect(DB_PATH)
    conexao.row_factory = sqlite3.Row
    return conexao
  except sqlite3.Error as e:
    raise sqlite3.Error(f"Erro ao conectar ao banco de dados: {e}")
```

**Propósito:** Cria e configura conexão com o banco de dados SQLite.

**Retorno:** Objeto de conexão SQLite

**Funcionamento:**

1. Criação da conexão:

   - `sqlite3.connect(DB_PATH)`: Conecta ao arquivo do banco
   - Cria arquivo se não existir
2. Configuração de `row_factory`:

   - `sqlite3.Row`: Retorna linhas como objetos que permitem acesso por nome
   - Permite: `row['campo']` ao invés de `row[0]`
   - Mais legível e menos propenso a erros
3. Tratamento de erros:

   - Captura `sqlite3.Error`
   - Relança com mensagem descritiva

**Exemplo de uso:**

```python
conexao = conectar_db()
cursor = conexao.cursor()
cursor.execute('SELECT nome FROM produtos WHERE id = ?', (1,))
produto = cursor.fetchone()
print(produto['nome'])  # Acesso por nome (graças ao row_factory)
```

**Conceitos:**

- Factory pattern (função que cria objetos)
- Configuração de conexão
- Tratamento de exceções
- `row_factory` para acesso nomeado

---

### `criar_banco()` - Inicialização do Banco de Dados

```16:37:models/model.py
def criar_banco():
  if not os.path.exists(DB_SCHEMA):
    raise FileNotFoundError(f"Arquivo SQL não encontrado: {DB_SCHEMA}")
  
  conexao = conectar_db()
  
  try:
    with open(DB_SCHEMA, 'r', encoding='utf-8') as arquivo:
      script_sql = arquivo.read()
  
    script_sql = script_sql.replace('CREATE TABLE', 'CREATE TABLE IF NOT EXISTS')
  
    conexao.executescript(script_sql)
    conexao.commit()
  
    popular_produtos()
  
  except sqlite3.Error as e:
    conexao.rollback()
    raise
  finally:
    conexao.close()
```

**Propósito:** Cria todas as tabelas do banco de dados se não existirem.

**Funcionamento:**

1. Validação do arquivo SQL:

   - Verifica se `script-database.sql` existe
   - Se não existir, lança `FileNotFoundError`
2. Leitura do script SQL:

   - Abre arquivo em modo leitura com encoding UTF-8
   - Lê todo o conteúdo
3. Modificação do script:

   - Substitui `CREATE TABLE` por `CREATE TABLE IF NOT EXISTS`
   - Permite executar múltiplas vezes sem erro
   - Evita erro se tabelas já existirem
4. Execução do script:

   - `executescript()`: Executa múltiplos comandos SQL
   - Útil para scripts com várias instruções
5. Commit:

   - Confirma criação das tabelas
6. Popular produtos:

   - Chama `popular_produtos()` para inserir dados iniciais
7. Tratamento de erros:

   - Try/except captura erros SQL
   - Rollback reverte mudanças
   - Finally fecha conexão

**Conceitos:**

- Manipulação de arquivos
- Processamento de strings (replace)
- Execução de scripts SQL
- Idempotência (pode executar múltiplas vezes)
- Context managers (`with`)

---

### `popular_produtos()` - Inserção de Dados Iniciais

```40:80:models/model.py
def popular_produtos():
  conexao = conectar_db()
  cursor = conexao.cursor()
  
  produtos = [
    ('Notebook Dell Inspiron 15', 'Notebook com processador Intel Core i5, 8GB RAM, 256GB SSD', 2499.90, 10),
    ('Mouse Logitech MX Master 3', 'Mouse sem fio ergonômico com sensor de alta precisão', 399.90, 25),
    ('Teclado Mecânico RGB', 'Teclado mecânico com switches azuis e iluminação RGB', 599.90, 15),
    ('Monitor LG UltraWide 29"', 'Monitor ultrawide Full HD IPS de 29 polegadas', 1299.90, 8),
    ('Webcam Logitech C920', 'Webcam Full HD 1080p com microfone estéreo', 499.90, 20),
    ('Headset HyperX Cloud II', 'Headset gamer com som surround 7.1 e microfone removível', 699.90, 12),
    ('SSD Samsung 1TB', 'SSD NVMe M.2 de 1TB com velocidade de leitura até 3500MB/s', 599.90, 30),
    ('Placa de Vídeo RTX 3060', 'Placa de vídeo NVIDIA GeForce RTX 3060 12GB', 2499.90, 5),
    ('Smartphone Samsung Galaxy S23', 'Smartphone Android com tela AMOLED 6.1", 128GB, câmera tripla 50MP', 3299.90, 15),
    ('Tablet iPad Air 10.9"', 'Tablet Apple com chip M1, 64GB, tela Retina, suporte para Apple Pencil', 4299.90, 7),
    ('Smartwatch Apple Watch Series 9', 'Relógio inteligente com GPS, monitoramento de saúde e tela sempre ligada', 2999.90, 12),
    ('Fone de Ouvido AirPods Pro', 'Fones Bluetooth com cancelamento ativo de ruído e áudio espacial', 1899.90, 20),
    ('Caixa de Som JBL Charge 5', 'Caixa de som Bluetooth à prova d\'água com bateria de 20 horas', 899.90, 18),
    ('Roteador Wi-Fi 6 TP-Link Archer AX50', 'Roteador dual-band com Wi-Fi 6, velocidade até 3Gbps', 699.90, 14),
    ('HD Externo Seagate 2TB', 'HD externo portátil USB 3.0 de 2TB para backup e armazenamento', 449.90, 25),
    ('Impressora Multifuncional HP', 'Impressora jato de tinta com scanner, copiadora e Wi-Fi', 599.90, 10),
    ('Câmera Canon EOS R50', 'Câmera mirrorless com lente 18-45mm, 24.2MP, gravação 4K', 4499.90, 6),
    ('Drone DJI Mini 3', 'Drone compacto com câmera 4K, 30 minutos de voo, peso inferior a 250g', 3299.90, 8),
    ('Mousepad Gamer RGB', 'Mousepad gamer com iluminação RGB, superfície de controle e base antiderrapante', 199.90, 30),
    ('Hub USB-C 7 em 1', 'Hub USB-C com HDMI, USB 3.0, leitor de cartão SD, carregamento pass-through', 249.90, 22),
  ]
  
  try:
    cursor.execute('SELECT COUNT(*) FROM produtos')
    count = cursor.fetchone()[0]
  
    if count == 0:
      cursor.executemany(
        'INSERT INTO produtos (nome, descricao, preco, estoque) VALUES (?, ?, ?, ?)',
        produtos
      )
      conexao.commit()
  except sqlite3.Error as e:
    conexao.rollback()
  finally:
    conexao.close()
```

**Propósito:** Insere produtos de exemplo no banco se a tabela estiver vazia.

**Funcionamento:**

1. Preparação de dados:

   - Lista de tuplas com 20 produtos
   - Cada tupla: `(nome, descricao, preco, estoque)`
2. Verificação de dados existentes:

   - `SELECT COUNT(*)`: Conta produtos existentes
   - `fetchone()[0]`: Obtém o primeiro valor (contagem)
3. Inserção condicional:

   - Se `count == 0`: tabela vazia, insere produtos
   - Se `count > 0`: já tem dados, não insere (evita duplicação)
4. Inserção em lote:

   - `executemany()`: Executa INSERT para cada tupla da lista
   - Mais eficiente que múltiplos `execute()`
   - Usa mesmo prepared statement para todos
5. Commit:

   - Confirma inserções
6. Tratamento de erros:

   - Try/except captura erros
   - Rollback reverte mudanças
   - Finally fecha conexão

**Conceitos:**

- Inserção em lote (`executemany`)
- Verificação de existência (COUNT)
- Idempotência (só insere se vazio)
- Tuplas para dados estruturados
- Performance: uma query para múltiplas inserções

**Por que verificar se está vazio?**

- Evita duplicar dados em execuções subsequentes
- Permite reexecutar `criar_banco()` sem problemas
- Mantém dados existentes intactos

---

## Resumo dos Conceitos Aplicados

### Padrões de Projeto

- **Decorator Pattern**: `@login_required`, `@app.route`
- **Factory Pattern**: `conectar_db()`
- **Template Method**: Estrutura comum em rotas (GET/POST)

### Segurança

- **Prepared Statements**: Prevenção de SQL Injection
- **Hash com Salt**: Proteção de senhas
- **Validação de Propriedade**: Usuário só acessa seus dados
- **Sessões Seguras**: Cookies assinados

### Banco de Dados

- **Transações**: Atomicidade de operações
- **Integridade Referencial**: Foreign Keys
- **JOINs**: Relacionamentos entre tabelas
- **Agregações**: Cálculos em SQL

### Python

- **Context Managers**: `with` para arquivos
- **List Comprehensions**: Cálculos de totais
- **Exception Handling**: Try/except/finally
- **Closures**: Decoradores

### Flask

- **Roteamento**: `@app.route`
- **Sessões**: `session`
- **Flash Messages**: Mensagens temporárias
- **Templates**: Jinja2
