------------------------------------------------------
-- UTILIZADO PARA CRIAR O DIAGRAMA RELACIONAL
-- https://erd.dbdesigner.net/
------------------------------------------------------


-- TABELA DE CLIENTES
CREATE TABLE clientes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    senha_hash TEXT NOT NULL,
    telefone TEXT
);

-- TABELA DE PRODUTOS
CREATE TABLE produtos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    descricao TEXT,
    preco NUMERIC(10,2) NOT NULL,
    estoque INTEGER NOT NULL DEFAULT 0
);

-- TABELA DE PEDIDOS (APÓS FINALIZAÇÃO)
CREATE TABLE pedidos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cliente_id INTEGER NOT NULL,
    data DATETIME DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'pendente',
    FOREIGN KEY (cliente_id) REFERENCES clientes(id)
);

-- ITENS DE CADA PEDIDO
CREATE TABLE itens_pedido (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pedido_id INTEGER NOT NULL,
    produto_id INTEGER NOT NULL,
    quantidade INTEGER NOT NULL,
    preco_unitario NUMERIC(10,2) NOT NULL,
    FOREIGN KEY (pedido_id) REFERENCES pedidos(id),
    FOREIGN KEY (produto_id) REFERENCES produtos(id)
);

-- PAGAMENTO ASSOCIADO A PEDIDOS
CREATE TABLE pagamentos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pedido_id INTEGER NOT NULL,
    tipo TEXT,                  -- ex: 'cartao', 'pix', 'boleto'
    valor NUMERIC(10,2) NOT NULL,
    status TEXT DEFAULT 'aguardando',
    FOREIGN KEY (pedido_id) REFERENCES pedidos(id)
);

-- CARRINHO DE COMPRAS TEMPORÁRIO (sem FKs)
CREATE TABLE carrinho_compras (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cliente_id INTEGER,             -- pode ser NULL para visitante
    produto_id INTEGER,
    nome_produto TEXT,              -- desnormalizado para exibição
    preco_unitario NUMERIC(10,2),
    quantidade INTEGER NOT NULL,
    criado_em DATETIME DEFAULT CURRENT_TIMESTAMP
);
