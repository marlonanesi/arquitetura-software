"""Adaptador de ENTRADA (driving adapter): a linha de comando.

Traduz argumentos de terminal em chamadas aos casos de uso. Outro adaptador de entrada (uma API HTTP,
uma fila) chamaria os mesmos casos de uso, sem mudar o domínio.

Uso:
  python -m confirmacao.cli demo
  python -m confirmacao.cli criar E-100 "Rua das Flores, 100"
  python -m confirmacao.cli iniciar E-100
  python -m confirmacao.cli confirmar E-100 -23.5614 -46.6559
  python -m confirmacao.cli mostrar E-100
"""
import sys

from confirmacao import fabrica
from confirmacao.dominio.entrega import ErroDeDominio
from confirmacao.dominio.geo import Coordenada


def mostrar(entrega) -> None:
    print(f"{entrega.id} | {entrega.endereco} | {entrega.status.value} | confirmada_em={entrega.confirmada_em}")


def demo(app: dict) -> None:
    print("1. registrar e iniciar a rota")
    app["registrar"].executar("E-100", "Rua das Flores, 100")
    mostrar(app["iniciar_rota"].executar("E-100"))
    print("2. tentar confirmar a 2 km do destino (a regra de negocio recusa)")
    try:
        app["confirmar"].executar("E-100", Coordenada(-23.5430, -46.6559))
    except ErroDeDominio as erro:
        print(f"   recusada: {erro}")
    print("3. confirmar no endereco")
    mostrar(app["confirmar"].executar("E-100", Coordenada(-23.5614, -46.6559)))


def main(argv: list[str]) -> int:
    app = fabrica.montar()
    comando, args = (argv[0] if argv else "demo"), argv[1:]
    try:
        if comando == "demo":
            demo(app)
        elif comando == "criar":
            mostrar(app["registrar"].executar(args[0], args[1]))
        elif comando == "iniciar":
            mostrar(app["iniciar_rota"].executar(args[0]))
        elif comando == "confirmar":
            mostrar(app["confirmar"].executar(args[0], Coordenada(float(args[1]), float(args[2]))))
        elif comando == "mostrar":
            entrega = app["repositorio"].obter(args[0])
            print("nao encontrada" if entrega is None else "", end="")
            if entrega is not None:
                mostrar(entrega)
        else:
            print(__doc__)
            return 2
    except ErroDeDominio as erro:
        print(f"recusado pelo dominio: {erro}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
