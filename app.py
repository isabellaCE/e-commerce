from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from models.model import conectar_db, criar_banco
from models.auth import hash_senha, verificar_senha
import sqlite3
from functools import wraps
import os

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'sua-chave-secreta-mude-em-producao')

criar_banco()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'cliente_id' not in session:
            flash('Por favor, faça login para continuar.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


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

@app.route('/logout')
def logout():
    session.clear()
    flash('Você foi desconectado.', 'info')
    return redirect(url_for('index'))


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

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
