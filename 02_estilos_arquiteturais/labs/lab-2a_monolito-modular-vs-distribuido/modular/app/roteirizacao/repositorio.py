def inserir_rota(conn, entrega_id: int, sequencia: int, motorista: str) -> None:
    conn.execute(
        "INSERT INTO rotas (entrega_id, sequencia, motorista) VALUES (%s, %s, %s)",
        (entrega_id, sequencia, motorista),
    )
