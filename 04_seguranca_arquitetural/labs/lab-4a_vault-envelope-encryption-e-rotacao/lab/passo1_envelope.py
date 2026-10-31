"""Passo 1: envelope encryption. O dado é cifrado com uma DEK própria, e a DEK é cifrada pela KEK do Vault."""
from comum import banco, cifrar_com_envelope, decifrar_com_envelope

REGISTROS = {
    "ENT-001": "CPF 123.456.789-00 | Av. Paulista, 1000",
    "ENT-002": "CPF 987.654.321-00 | Rua das Flores, 100",
    "ENT-003": "CPF 111.222.333-44 | Rua do Ouvidor, 50",
}

with banco() as conn:
    conn.execute("TRUNCATE registros RESTART IDENTITY")
    for codigo, texto in REGISTROS.items():
        cifrado, nonce, dek_cifrada = cifrar_com_envelope(texto.encode(), codigo.encode())
        conn.execute("INSERT INTO registros (codigo, dado, nonce, dek_cifrada) VALUES (%s, %s, %s, %s)",
                     (codigo, cifrado, nonce, dek_cifrada))

    print("O QUE O BANCO GUARDA (um atacante com acesso ao banco veria apenas isto):\n")
    for codigo, dado, dek_cifrada in conn.execute("SELECT codigo, dado, dek_cifrada FROM registros ORDER BY id"):
        print(f"  {codigo}  dado={bytes(dado)[:14].hex()}...  dek_cifrada={dek_cifrada[:34]}...")

    print("\nO QUE A APLICACAO LE (com o token dela, que pode pedir ao Vault a decifragem):\n")
    for codigo, dado, nonce, dek_cifrada in conn.execute("SELECT codigo, dado, nonce, dek_cifrada FROM registros ORDER BY id"):
        texto = decifrar_com_envelope(bytes(dado), bytes(nonce), dek_cifrada, codigo.encode())
        print(f"  {codigo}  {texto.decode()}")
