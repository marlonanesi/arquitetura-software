# Diagrama: Componentes-Rastreamento

> Gerado a partir de workspace.dsl. Não edite à mão.

```mermaid
graph LR
  linkStyle default fill:#ffffff

  subgraph diagram ["Component View: LunaLog - Serviço de Rastreamento"]
    style diagram fill:#ffffff,stroke:#ffffff

    subgraph 7 ["LunaLog"]
      style 7 fill:#ffffff,stroke:#204060,color:#204060

      subgraph 11 ["Serviço de Rastreamento"]
        style 11 fill:#ffffff,stroke:#2c5678,color:#2c5678

        12["<div style='font-weight: bold'>Controlador de Eventos</div><div style='font-size: 70%; margin-top: 0px'>[Component: FastAPI router]</div><div style='font-size: 80%; margin-top:10px'>Recebe as confirmações e<br />eventos de GPS.</div>"]
        style 12 fill:#7fb2d8,stroke:#587c97,color:#0b1b2b
        13["<div style='font-weight: bold'>Gestor de Estado da Entrega</div><div style='font-size: 70%; margin-top: 0px'>[Component: Python]</div><div style='font-size: 80%; margin-top:10px'>Aplica as regras de transição<br />de estado.</div>"]
        style 13 fill:#7fb2d8,stroke:#587c97,color:#0b1b2b
        14["<div style='font-weight: bold'>Repositório de Entregas</div><div style='font-size: 70%; margin-top: 0px'>[Component: Python]</div><div style='font-size: 80%; margin-top:10px'>Lê e grava o estado das<br />entregas.</div>"]
        style 14 fill:#7fb2d8,stroke:#587c97,color:#0b1b2b
        15["<div style='font-weight: bold'>Publicador de Eventos</div><div style='font-size: 70%; margin-top: 0px'>[Component: Python]</div><div style='font-size: 80%; margin-top:10px'>Publica as mudanças de estado<br />para os demais serviços.</div>"]
        style 15 fill:#7fb2d8,stroke:#587c97,color:#0b1b2b
      end

      18["<div style='font-weight: bold'>Barramento de Eventos</div><div style='font-size: 70%; margin-top: 0px'>[Container: Kafka]</div><div style='font-size: 80%; margin-top:10px'>Transporta os eventos de<br />entrega entre os serviços.</div>"]
      style 18 fill:#3f7cac,stroke:#2c5678,color:#ffffff
      19[("<div style='font-weight: bold'>Banco de Entregas</div><div style='font-size: 70%; margin-top: 0px'>[Container: PostgreSQL]</div><div style='font-size: 80%; margin-top:10px'>Estado das entregas e<br />histórico.</div>")]
      style 19 fill:#3f7cac,stroke:#2c5678,color:#ffffff
    end

    12-. "<div>Valida a transição</div><div style='font-size: 70%'>[Chamada de função]</div>" .->13
    13-. "<div>Grava o novo estado</div><div style='font-size: 70%'>[Chamada de função]</div>" .->14
    13-. "<div>Anuncia a mudança</div><div style='font-size: 70%'>[Chamada de função]</div>" .->15
    14-. "<div>Lê e grava</div><div style='font-size: 70%'>[SQL]</div>" .->19
    15-. "<div>Publica eventos</div><div style='font-size: 70%'>[Kafka]</div>" .->18

  end```
