"""Tradução entre o modelo do legado e o modelo novo (a ACL da migração de dados, lab 8C).

legado -> novo: devolve a entrega limpa, ou levanta ErroDeTraducao (o registro vai para a quarentena)
novo -> legado: escreve no formato que o legado entende, para o dual-write
"""
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

STATUS = {"1": "aguardando_coleta", "2": "em_rota", "3": "entregue", "9": "cancelada"}
CODIGO_STATUS = {v: k for k, v in STATUS.items()}
TRANSPORTADORAS = {"TRANSRAPIDA LTDA": "transrapida", "VELOZ EXPRESS S/A": "veloz", "LOG BOREAL ME": "boreal"}
NOME_LEGADO = {v: k for k, v in TRANSPORTADORAS.items()}


class ErroDeTraducao(Exception):
    pass


def do_legado(cod_ent: str, st: str, dt_prev: str, vlr: str, transp: str) -> dict:
    status = STATUS.get(str(st).strip())
    if status is None:
        raise ErroDeTraducao(f"status invalido: {st!r}")
    for formato in ("%d/%m/%Y", "%Y-%m-%d"):
        try:
            previsao = datetime.strptime(dt_prev.strip(), formato).date()
            break
        except ValueError:
            continue
    else:
        raise ErroDeTraducao(f"data invalida: {dt_prev!r}")
    texto = vlr.strip().replace(".", "").replace(",", ".") if "," in vlr else vlr.strip()
    try:
        centavos = int((Decimal(texto) * 100).to_integral_value())
    except InvalidOperation:
        raise ErroDeTraducao(f"valor invalido: {vlr!r}")
    transportadora = TRANSPORTADORAS.get(transp.strip().upper())
    if transportadora is None:
        raise ErroDeTraducao(f"transportadora desconhecida: {transp!r}")
    return {"id": cod_ent, "status": status, "previsao": previsao, "valor_centavos": centavos, "transportadora_id": transportadora}


def para_legado(e: dict) -> tuple:
    reais, centavos = divmod(e["valor_centavos"], 100)
    previsao: date = e["previsao"] if isinstance(e["previsao"], date) else date.fromisoformat(e["previsao"])
    return (e["id"], CODIGO_STATUS[e["status"]], previsao.strftime("%d/%m/%Y"), f"{reais},{centavos:02d}", NOME_LEGADO[e["transportadora_id"]])


def forma_canonica(e: dict) -> str:
    """Texto estável usado para comparar uma entrega nos dois bancos."""
    return f"{e['id']}|{e['status']}|{e['previsao'].isoformat()}|{e['valor_centavos']}|{e['transportadora_id']}"
