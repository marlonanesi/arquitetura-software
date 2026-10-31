# Diagrama: Containers

> Gerado a partir de workspace.dsl. Não edite à mão.

```mermaid
graph LR
  linkStyle default fill:#ffffff

  subgraph diagram ["Container View: LunaLog"]
    style diagram fill:#ffffff,stroke:#ffffff

    1["<div style='font-weight: bold'>Lojista</div><div style='font-size: 70%; margin-top: 0px'>[Person]</div><div style='font-size: 80%; margin-top:10px'>Contrata entregas e acompanha<br />os pedidos dos clientes.</div>"]
    style 1 fill:#1f3a5f,stroke:#152842,color:#ffffff
    2["<div style='font-weight: bold'>Motorista</div><div style='font-size: 70%; margin-top: 0px'>[Person]</div><div style='font-size: 80%; margin-top:10px'>Executa as entregas e<br />confirma cada uma pelo<br />aplicativo.</div>"]
    style 2 fill:#1f3a5f,stroke:#152842,color:#ffffff
    3["<div style='font-weight: bold'>Operador de logística</div><div style='font-size: 70%; margin-top: 0px'>[Person]</div><div style='font-size: 80%; margin-top:10px'>Monitora a operação e trata<br />as exceções.</div>"]
    style 3 fill:#1f3a5f,stroke:#152842,color:#ffffff
    4["<div style='font-weight: bold'>Google Maps</div><div style='font-size: 70%; margin-top: 0px'>[Software System]</div><div style='font-size: 80%; margin-top:10px'>Geocodificação de endereços e<br />cálculo de rotas.</div>"]
    style 4 fill:#8a8a8a,stroke:#606060,color:#ffffff

    subgraph 7 ["LunaLog"]
      style 7 fill:#ffffff,stroke:#204060,color:#204060

      10["<div style='font-weight: bold'>API Gateway</div><div style='font-size: 70%; margin-top: 0px'>[Container: Kong]</div><div style='font-size: 80%; margin-top:10px'>Autenticação, limite de taxa<br />e roteamento das chamadas.</div>"]
      style 10 fill:#3f7cac,stroke:#2c5678,color:#ffffff
      11["<div style='font-weight: bold'>Serviço de Rastreamento</div><div style='font-size: 70%; margin-top: 0px'>[Container: Python, FastAPI]</div><div style='font-size: 80%; margin-top:10px'>Recebe eventos das entregas e<br />mantém o estado atual de cada<br />uma.</div>"]
      style 11 fill:#3f7cac,stroke:#2c5678,color:#ffffff
      16["<div style='font-weight: bold'>Serviço de Roteirização</div><div style='font-size: 70%; margin-top: 0px'>[Container: Python]</div><div style='font-size: 80%; margin-top:10px'>Calcula a melhor sequência de<br />paradas de cada motorista.</div>"]
      style 16 fill:#3f7cac,stroke:#2c5678,color:#ffffff
      17["<div style='font-weight: bold'>Serviço de Notificação</div><div style='font-size: 70%; margin-top: 0px'>[Container: Python]</div><div style='font-size: 80%; margin-top:10px'>Avisa o destinatário por SMS,<br />e-mail e WhatsApp.</div>"]
      style 17 fill:#3f7cac,stroke:#2c5678,color:#ffffff
      18["<div style='font-weight: bold'>Barramento de Eventos</div><div style='font-size: 70%; margin-top: 0px'>[Container: Kafka]</div><div style='font-size: 80%; margin-top:10px'>Transporta os eventos de<br />entrega entre os serviços.</div>"]
      style 18 fill:#3f7cac,stroke:#2c5678,color:#ffffff
      19[("<div style='font-weight: bold'>Banco de Entregas</div><div style='font-size: 70%; margin-top: 0px'>[Container: PostgreSQL]</div><div style='font-size: 80%; margin-top:10px'>Estado das entregas e<br />histórico.</div>")]
      style 19 fill:#3f7cac,stroke:#2c5678,color:#ffffff
      8["<div style='font-weight: bold'>Painel Web</div><div style='font-size: 70%; margin-top: 0px'>[Container: React]</div><div style='font-size: 80%; margin-top:10px'>Operação e acompanhamento dos<br />pedidos.</div>"]
      style 8 fill:#3f7cac,stroke:#2c5678,color:#ffffff
      9["<div style='font-weight: bold'>Aplicativo do Motorista</div><div style='font-size: 70%; margin-top: 0px'>[Container: React Native]</div><div style='font-size: 80%; margin-top:10px'>Lista de entregas, rota e<br />confirmação.</div>"]
      style 9 fill:#3f7cac,stroke:#2c5678,color:#ffffff
    end

    1-. "<div>Acompanha pedidos</div><div style='font-size: 70%'>[HTTPS]</div>" .->8
    3-. "<div>Monitora a operação</div><div style='font-size: 70%'>[HTTPS]</div>" .->8
    2-. "<div>Confirma entregas</div><div style='font-size: 70%'>[Aplicativo móvel]</div>" .->9
    8-. "<div>Chama a API</div><div style='font-size: 70%'>[HTTPS]</div>" .->10
    9-. "<div>Chama a API</div><div style='font-size: 70%'>[HTTPS]</div>" .->10
    10-. "<div>Encaminha eventos e consultas</div><div style='font-size: 70%'>[HTTPS/JSON]</div>" .->11
    10-. "<div>Solicita rotas</div><div style='font-size: 70%'>[HTTPS/JSON]</div>" .->16
    11-. "<div>Lê e grava</div><div style='font-size: 70%'>[SQL]</div>" .->19
    11-. "<div>Publica eventos</div><div style='font-size: 70%'>[Kafka]</div>" .->18
    18-. "<div>Entrega eventos</div><div style='font-size: 70%'>[Kafka]</div>" .->17
    16-. "<div>Consulta rotas e geocodifica</div><div style='font-size: 70%'>[HTTPS]</div>" .->4
    17-. "<div>Avisa sobre a entrega</div><div style='font-size: 70%'>[SMS, e-mail]</div>" .->1

  end```
