"""Passo 4: revogar o acesso de uma aplicação. Sem o token, a decifragem falha, mesmo com os dados e a DEK em mãos."""
from comum import APP_TOKEN, ErroDoVault, ROOT_TOKEN, banco, decifrar_com_envelope, vault

with banco() as conn:
    codigo, dado, nonce, dek_cifrada = conn.execute(
        "SELECT codigo, dado, nonce, dek_cifrada FROM registros ORDER BY id LIMIT 1").fetchone()

    print("1. com o token da aplicacao:")
    print(f"   {decifrar_com_envelope(bytes(dado), bytes(nonce), dek_cifrada, codigo.encode(), APP_TOKEN).decode()}\n")

    print("2. a aplicacao tenta rotacionar a chave (nao esta na politica dela):")
    try:
        vault("POST", "transit/keys/kek/rotate", APP_TOKEN)
    except ErroDoVault as erro:
        print(f"   negado: {erro}\n")

    print("3. o administrador revoga o token da aplicacao (por exemplo, apos um incidente):")
    vault("POST", "auth/token/revoke", ROOT_TOKEN, {"token": APP_TOKEN})
    try:
        decifrar_com_envelope(bytes(dado), bytes(nonce), dek_cifrada, codigo.encode(), APP_TOKEN)
    except ErroDoVault as erro:
        print(f"   a decifragem falha: {erro}")
    print("   os dados e a DEK cifrada continuam no banco, mas sem a permissao no Vault eles sao opacos.\n")

    print("4. o administrador cria um token novo para a aplicacao, mesma politica:")
    vault("POST", "auth/token/create", ROOT_TOKEN, {"id": APP_TOKEN, "policies": ["app"], "ttl": "24h"})
    print(f"   {decifrar_com_envelope(bytes(dado), bytes(nonce), dek_cifrada, codigo.encode(), APP_TOKEN).decode()}")
