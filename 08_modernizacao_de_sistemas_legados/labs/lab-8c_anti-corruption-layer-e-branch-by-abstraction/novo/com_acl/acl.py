"""A ANTI-CORRUPTION LAYER: o único lugar que conhece o modelo do legado.

Traduz nos dois sentidos:
  para_dominio(dados_do_legado) -> Entrega      (leitura)
  para_legado(Entrega)          -> dados do legado   (escrita)

Se o legado mudar de formato, o conserto é neste arquivo. O domínio, a API e os testes de negócio
do serviço novo não sabem que o legado existe. Quando o legado não puder ser traduzido, a ACL
falha de forma CLARA (ErroDeTraducao), em vez de deixar um dado estranho entrar no domínio.
"""
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from dominio import Entrega, StatusEntrega, Transportadora


class ErroDeTraducao(Exception):
    """O legado devolveu algo que a ACL não sabe traduzir."""


STATUS_DO_LEGADO = {
    "1": StatusEntrega.AGUARDANDO_COLETA, "2": StatusEntrega.EM_ROTA, "3": StatusEntrega.ENTREGUE, "9": StatusEntrega.CANCELADA,
    "AGUARDANDO_COLETA": StatusEntrega.AGUARDANDO_COLETA, "EM_ROTA": StatusEntrega.EM_ROTA,
    "ENTREGUE": StatusEntrega.ENTREGUE, "CANCELADA": StatusEntrega.CANCELADA,
}
CODIGO_DO_STATUS = {StatusEntrega.AGUARDANDO_COLETA: 1, StatusEntrega.EM_ROTA: 2, StatusEntrega.ENTREGUE: 3, StatusEntrega.CANCELADA: 9}

TRANSPORTADORAS = {
    "TRANSRAPIDA LTDA": Transportadora("transrapida", "TransRápida"),
    "VELOZ EXPRESS S/A": Transportadora("veloz", "Veloz Express"),
    "LOG BOREAL ME": Transportadora("boreal", "Logística Boreal"),
}
NOME_NO_LEGADO = {t.id: nome for nome, t in TRANSPORTADORAS.items()}


def _status(bruto) -> StatusEntrega:
    chave = str(bruto).strip().upper()
    if chave not in STATUS_DO_LEGADO:
        raise ErroDeTraducao(f"status desconhecido no legado: {bruto!r}")
    return STATUS_DO_LEGADO[chave]


def _data(bruto) -> date:
    texto = str(bruto).strip()
    for formato in ("%d/%m/%Y", "%Y-%m-%d"):                 # o legado tem os dois, em entregas diferentes
        try:
            return datetime.strptime(texto, formato).date()
        except ValueError:
            continue
    raise ErroDeTraducao(f"data em formato desconhecido no legado: {bruto!r}")


def _centavos(bruto) -> int:
    texto = str(bruto).strip()
    if "," in texto:                                           # "1.250,50": ponto de milhar, vírgula decimal
        texto = texto.replace(".", "").replace(",", ".")
    try:
        return int((Decimal(texto) * 100).to_integral_value())
    except InvalidOperation:
        raise ErroDeTraducao(f"valor invalido no legado: {bruto!r}")


def _transportadora(bruto) -> Transportadora:
    nome = str(bruto).strip().upper()
    if nome not in TRANSPORTADORAS:
        raise ErroDeTraducao(f"transportadora desconhecida no legado: {bruto!r}")
    return TRANSPORTADORAS[nome]


def para_dominio(d: dict) -> Entrega:
    try:
        return Entrega(id=d["COD_ENT"], status=_status(d["ST"]), previsao=_data(d["DT_PREV"]),
                       valor_centavos=_centavos(d["VLR"]), transportadora=_transportadora(d["TRANSP"]))
    except KeyError as erro:
        raise ErroDeTraducao(f"campo ausente na resposta do legado: {erro}")


def para_legado(e: Entrega) -> dict:
    reais, centavos = divmod(e.valor_centavos, 100)
    return {"COD_ENT": e.id, "ST": CODIGO_DO_STATUS[e.status], "DT_PREV": e.previsao.strftime("%d/%m/%Y"),
            "VLR": f"{reais},{centavos:02d}", "TRANSP": NOME_NO_LEGADO[e.transportadora.id]}
