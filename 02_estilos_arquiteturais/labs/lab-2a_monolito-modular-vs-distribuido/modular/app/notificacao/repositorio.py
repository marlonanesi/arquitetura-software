def registrar(conn, entrega_id: int, canal: str) -> None:
    conn.execute("INSERT INTO notificacoes (entrega_id, canal) VALUES (%s, %s)", (entrega_id, canal))
