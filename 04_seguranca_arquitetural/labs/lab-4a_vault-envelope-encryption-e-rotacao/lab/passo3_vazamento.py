"""Passo 3: o dia em que a chave vaza. Chave em variável de ambiente x envelope encryption com Vault.

Cenário da aula 4.4: a chave foi parar em um commit público e é preciso trocá-la.
  A. chave única em variável de ambiente: é preciso LER, DECIFRAR, CIFRAR e GRAVAR todos os dados de novo.
  B. envelope encryption: rotaciona a KEK e faz REWRAP das DEKs; o dado cifrado não é tocado.
Variáveis: N (registros, padrão 2000) e TAMANHO (bytes por registro, padrão 50000).
"""
import os
import time

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from comum import ROOT_TOKEN, APP_TOKEN, b64, banco, vault

N = int(os.environ.get("N", "2000"))
TAMANHO = int(os.environ.get("TAMANHO", "50000"))
dado_exemplo = os.urandom(TAMANHO)

with banco() as conn:
    conn.execute("DROP TABLE IF EXISTS lote_a, lote_b")
    conn.execute("CREATE TABLE lote_a (id int PRIMARY KEY, dado bytea, nonce bytea)")
    conn.execute("CREATE TABLE lote_b (id int PRIMARY KEY, dado bytea, nonce bytea, dek_cifrada text)")

    # ---------------- A. chave única em variável de ambiente ----------------
    chave_vazada = os.urandom(32)
    preparo = []
    for i in range(N):
        nonce = os.urandom(12)
        preparo.append((i, AESGCM(chave_vazada).encrypt(nonce, dado_exemplo, None), nonce))
    conn.cursor().executemany("INSERT INTO lote_a VALUES (%s, %s, %s)", preparo)

    inicio = time.time()
    chave_nova = os.urandom(32)
    linhas = conn.execute("SELECT id, dado, nonce FROM lote_a").fetchall()
    atualizados = []
    for id_, dado, nonce in linhas:
        claro = AESGCM(chave_vazada).decrypt(bytes(nonce), bytes(dado), None)
        novo_nonce = os.urandom(12)
        atualizados.append((AESGCM(chave_nova).encrypt(novo_nonce, claro, None), novo_nonce, id_))
    with conn.transaction():
        conn.cursor().executemany("UPDATE lote_a SET dado = %s, nonce = %s WHERE id = %s", atualizados)
    tempo_a = time.time() - inicio

    # ---------------- B. envelope encryption com Vault ----------------
    deks = [os.urandom(32) for _ in range(N)]
    embrulhadas = vault("POST", "transit/encrypt/kek", APP_TOKEN,
                        {"batch_input": [{"plaintext": b64(d)} for d in deks]})["data"]["batch_results"]
    preparo = []
    for i in range(N):
        nonce = os.urandom(12)
        preparo.append((i, AESGCM(deks[i]).encrypt(nonce, dado_exemplo, None), nonce, embrulhadas[i]["ciphertext"]))
    conn.cursor().executemany("INSERT INTO lote_b VALUES (%s, %s, %s, %s)", preparo)

    inicio = time.time()
    vault("POST", "transit/keys/kek/rotate", ROOT_TOKEN)
    linhas = conn.execute("SELECT id, dek_cifrada FROM lote_b").fetchall()
    novos = vault("POST", "transit/rewrap/kek", ROOT_TOKEN,
                  {"batch_input": [{"ciphertext": dek} for _, dek in linhas]})["data"]["batch_results"]
    with conn.transaction():
        conn.cursor().executemany("UPDATE lote_b SET dek_cifrada = %s WHERE id = %s",
                                  [(novo["ciphertext"], id_) for (id_, _), novo in zip(linhas, novos)])
    tempo_b = time.time() - inicio

    mb = N * TAMANHO / 1_000_000
    print(f"{N} registros de {TAMANHO / 1000:.0f} KB ({mb:.0f} MB de dados cifrados)\n")
    print(f"A. chave em variavel de ambiente: recriptografar tudo   {tempo_a:7.2f} s  ({mb:.0f} MB lidos, decifrados, cifrados e gravados)")
    print(f"B. envelope encryption: rotacao + rewrap das DEKs       {tempo_b:7.2f} s  (so {N} DEKs pequenas; o dado nao foi tocado)")
    print(f"\nB e cerca de {tempo_a / tempo_b:.0f}x mais rapido. E a diferenca cresce com o volume de dados:")
    print("o custo de A e proporcional ao TAMANHO dos dados; o de B, ao NUMERO de registros (e o Vault faz em lote).")
