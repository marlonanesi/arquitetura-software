"""Passo 2: rotação da KEK e rewrap, sem recriptografar os dados.

1. rotaciona a chave mestra (nova versão v2)
2. registros novos já usam a v2; os antigos continuam legíveis (a v1 ainda existe)
3. rewrap: o Vault reembrulha as DEKs antigas na v2, sem entregar a DEK em claro e sem tocar no dado
4. retira a v1 (min_decryption_version=2): uma cópia antiga de DEK deixa de ser decifrável
"""
import hashlib

from comum import (ErroDoVault, ROOT_TOKEN, banco, cifrar_com_envelope, decifrar_com_envelope,
                   versao_da_dek, vault)


def resumo(conn):
    contagem = {}
    for (dek,) in conn.execute("SELECT dek_cifrada FROM registros"):
        contagem[versao_da_dek(dek)] = contagem.get(versao_da_dek(dek), 0) + 1
    return contagem


def impressao_dos_dados(conn):
    h = hashlib.sha256()
    for (dado,) in conn.execute("SELECT dado FROM registros ORDER BY id"):
        h.update(bytes(dado))
    return h.hexdigest()[:16]


with banco() as conn:
    copia_antiga = conn.execute("SELECT dek_cifrada FROM registros ORDER BY id LIMIT 1").fetchone()[0]
    print(f"antes:   DEKs por versao da chave mestra: {resumo(conn)}")
    print(f"         (guardei uma copia de uma DEK v1, como se estivesse em um backup antigo: {copia_antiga[:28]}...)\n")

    # 1. rotação
    nova = vault("POST", "transit/keys/kek/rotate", ROOT_TOKEN)["data"]["latest_version"]
    print(f"1. kek rotacionada: versao atual = v{nova}")

    # 2. um registro novo usa a versão nova; os antigos continuam legíveis
    cifrado, nonce, dek = cifrar_com_envelope(b"CPF 555.666.777-88 | Av. Brasil, 200", b"ENT-004")
    conn.execute("INSERT INTO registros (codigo, dado, nonce, dek_cifrada) VALUES (%s, %s, %s, %s)",
                 ("ENT-004", cifrado, nonce, dek))
    print(f"2. registro novo ENT-004 gravado com DEK {versao_da_dek(dek)}; DEKs por versao: {resumo(conn)}")
    for codigo, dado, nonce, dek_cifrada in conn.execute("SELECT codigo, dado, nonce, dek_cifrada FROM registros ORDER BY id"):
        decifrar_com_envelope(bytes(dado), bytes(nonce), dek_cifrada, codigo.encode())
    print("   todos os registros (v1 e v2) continuam legiveis\n")

    # 3. rewrap em lote: as DEKs v1 passam para v2; o dado cifrado não é tocado
    antes = impressao_dos_dados(conn)
    linhas = conn.execute("SELECT id, dek_cifrada FROM registros").fetchall()
    resposta = vault("POST", "transit/rewrap/kek", ROOT_TOKEN,
                     {"batch_input": [{"ciphertext": dek} for _, dek in linhas]})["data"]["batch_results"]
    for (id_, _), novo in zip(linhas, resposta):
        conn.execute("UPDATE registros SET dek_cifrada = %s WHERE id = %s", (novo["ciphertext"], id_))
    print(f"3. rewrap de {len(linhas)} DEKs: {resumo(conn)}")
    print(f"   impressao dos dados cifrados: antes={antes} depois={impressao_dos_dados(conn)}  (identica: o dado nao foi recriptografado)\n")

    # 4. aposentar a versão antiga da chave
    vault("POST", "transit/keys/kek/config", ROOT_TOKEN, {"min_decryption_version": nova})
    print(f"4. min_decryption_version = {nova}: a v1 foi aposentada")
    try:
        vault("POST", "transit/decrypt/kek", ROOT_TOKEN, {"ciphertext": copia_antiga})
        print("   ERRO: a copia antiga ainda foi decifrada")
    except ErroDoVault as erro:
        print(f"   a copia antiga da DEK v1 (do backup) nao decifra mais: {erro}")
    for codigo, dado, nonce, dek_cifrada in conn.execute("SELECT codigo, dado, nonce, dek_cifrada FROM registros ORDER BY id"):
        decifrar_com_envelope(bytes(dado), bytes(nonce), dek_cifrada, codigo.encode())
    print("   e os registros atuais (todos v2) continuam legiveis")
