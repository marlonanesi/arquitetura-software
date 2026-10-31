# Diagrama: Contexto

> Gerado a partir de workspace.dsl. Não edite à mão.

```mermaid
graph LR
  linkStyle default fill:#ffffff

  subgraph diagram ["System Context View: LunaLog"]
    style diagram fill:#ffffff,stroke:#ffffff

    1["<div style='font-weight: bold'>Lojista</div><div style='font-size: 70%; margin-top: 0px'>[Person]</div><div style='font-size: 80%; margin-top:10px'>Contrata entregas e acompanha<br />os pedidos dos clientes.</div>"]
    style 1 fill:#1f3a5f,stroke:#152842,color:#ffffff
    2["<div style='font-weight: bold'>Motorista</div><div style='font-size: 70%; margin-top: 0px'>[Person]</div><div style='font-size: 80%; margin-top:10px'>Executa as entregas e<br />confirma cada uma pelo<br />aplicativo.</div>"]
    style 2 fill:#1f3a5f,stroke:#152842,color:#ffffff
    3["<div style='font-weight: bold'>Operador de logística</div><div style='font-size: 70%; margin-top: 0px'>[Person]</div><div style='font-size: 80%; margin-top:10px'>Monitora a operação e trata<br />as exceções.</div>"]
    style 3 fill:#1f3a5f,stroke:#152842,color:#ffffff
    4["<div style='font-weight: bold'>Google Maps</div><div style='font-size: 70%; margin-top: 0px'>[Software System]</div><div style='font-size: 80%; margin-top:10px'>Geocodificação de endereços e<br />cálculo de rotas.</div>"]
    style 4 fill:#8a8a8a,stroke:#606060,color:#ffffff
    5["<div style='font-weight: bold'>Gateway de pagamento</div><div style='font-size: 70%; margin-top: 0px'>[Software System]</div><div style='font-size: 80%; margin-top:10px'>Cobrança dos serviços de<br />entrega.</div>"]
    style 5 fill:#8a8a8a,stroke:#606060,color:#ffffff
    6["<div style='font-weight: bold'>APIs das transportadoras</div><div style='font-size: 70%; margin-top: 0px'>[Software System]</div><div style='font-size: 80%; margin-top:10px'>Parceiros que recebem e<br />executam parte das entregas.</div>"]
    style 6 fill:#8a8a8a,stroke:#606060,color:#ffffff
    7["<div style='font-weight: bold'>LunaLog</div><div style='font-size: 70%; margin-top: 0px'>[Software System]</div><div style='font-size: 80%; margin-top:10px'>Planeja rotas, rastreia<br />entregas e notifica os<br />clientes em tempo real.</div>"]
    style 7 fill:#2e5c8a,stroke:#204060,color:#ffffff

    1-. "<div>Acompanha pedidos</div><div style='font-size: 70%'>[HTTPS]</div>" .->7
    3-. "<div>Monitora a operação</div><div style='font-size: 70%'>[HTTPS]</div>" .->7
    2-. "<div>Confirma entregas</div><div style='font-size: 70%'>[Aplicativo móvel]</div>" .->7
    7-. "<div>Consulta rotas e geocodifica</div><div style='font-size: 70%'>[HTTPS]</div>" .->4
    7-. "<div>Avisa sobre a entrega</div><div style='font-size: 70%'>[SMS, e-mail]</div>" .->1
    7-. "<div>Cobra pelo serviço</div><div style='font-size: 70%'>[HTTPS]</div>" .->5
    7-. "<div>Repassa entregas parceiras</div><div style='font-size: 70%'>[HTTPS]</div>" .->6

  end```
