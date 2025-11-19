import hashlib
import secrets

def hash_senha(senha):
	salt = secrets.token_hex(16)
	senha_hash = hashlib.sha256((senha + salt).encode()).hexdigest()
	return f"{salt}:{senha_hash}"

def verificar_senha(senha, senha_hash_armazenada):
	try:
		salt, hash_armazenado = senha_hash_armazenada.split(':')
		hash_calculado = hashlib.sha256((senha + salt).encode()).hexdigest()
		return hash_calculado == hash_armazenado
	except:
		return False

