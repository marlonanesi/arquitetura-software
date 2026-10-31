from app.compartilhado.db import COL_STATUS


def inserir(conn, codigo: str, destino: str) -> int:
    row = conn.execute(
        f"INSERT INTO entregas (codigo, destino, {COL_STATUS}) VALUES (%s, %s, 'criada') RETURNING id",
        (codigo, destino),
    ).fetchone()
    return row[0]


def atualizar_status(conn, entrega_id: int, novo: str) -> None:
    conn.execute(f"UPDATE entregas SET {COL_STATUS} = %s WHERE id = %s", (novo, entrega_id))


def obter(conn, entrega_id: int):
    return conn.execute(
        f"SELECT id, codigo, destino, {COL_STATUS} FROM entregas WHERE id = %s", (entrega_id,)
    ).fetchone()
