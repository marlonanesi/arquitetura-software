"""Caso de uso: registrar uma entrega, atribuir a rota e avisar o destinatário."""
from app.entregas import repositorio
from app.notificacao import api as notificacao
from app.roteirizacao import api as roteirizacao


def registrar(conn, codigo: str, destino: str) -> dict:
    entrega_id = repositorio.inserir(conn, codigo, destino)
    rota = roteirizacao.atribuir_rota(conn, entrega_id, destino)
    repositorio.atualizar_status(conn, entrega_id, "roteirizada")
    notificacao.avisar_destinatario(conn, entrega_id, canal="sms")
    return {"id": entrega_id, "codigo": codigo, "status": "roteirizada", "motorista": rota["motorista"]}
