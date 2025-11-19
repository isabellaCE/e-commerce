import sqlite3
import os

DB_PATH = os.path.join('database', 'ecommerce.db')
DB_SCHEMA = os.path.join('database', 'script-database.sql')

def conectar_db():
  try:
    conexao = sqlite3.connect(DB_PATH)
    conexao.row_factory = sqlite3.Row
    return conexao
  except sqlite3.Error as e:
    raise sqlite3.Error(f"Erro ao conectar ao banco de dados: {e}")


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

