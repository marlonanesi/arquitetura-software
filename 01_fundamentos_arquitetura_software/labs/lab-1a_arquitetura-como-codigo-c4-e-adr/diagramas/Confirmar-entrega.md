# Diagrama: Confirmar-entrega

> Gerado a partir de workspace.dsl. Não edite à mão.

```mermaid
graph LR
  linkStyle default fill:#ffffff

  subgraph diagram ["Dynamic View: LunaLog"]
    style diagram fill:#ffffff,stroke:#ffffff

    subgraph 7 ["LunaLog"]
      style 7 fill:#ffffff,stroke:#204060,color:#204060

      10["<div style='font-weight: bold'>API Gateway</div><div style='font-size: 70%; margin-top: 0px'>[Container: Kong]</div><div style='font-size: 80%; margin-top:10px'>Autenticação, limite de taxa<br />e roteamento das chamadas.</div>"]
      style 10 fill:#3f7cac,stroke:#2c5678,color:#ffffff
      11["<div style='font-weight: bold'>Serviço de Rastreamento</div><div style='font-size: 70%; margin-top: 0px'>[Container: Python, FastAPI]</div><div style='font-size: 80%; margin-top:10px'>Recebe eventos das entregas e<br />mantém o estado atual de cada<br />uma.</div>"]
      style 11 fill:#3f7cac,stroke:#2c5678,color:#ffffff
      17["<div style='font-weight: bold'>Serviço de Notificação</div><div style='font-size: 70%; margin-top: 0px'>[Container: Python]</div><div style='font-size: 80%; margin-top:10px'>Avisa o destinatário por SMS,<br />e-mail e WhatsApp.</div>"]
      style 17 fill:#3f7cac,stroke:#2c5678,color:#ffffff
      18["<div style='font-weight: bold'>Barramento de Eventos</div><div style='font-size: 70%; margin-top: 0px'>[Container: Kafka]</div><div style='font-size: 80%; margin-top:10px'>Transporta os eventos de<br />entrega entre os serviços.</div>"]
      style 18 fill:#3f7cac,stroke:#2c5678,color:#ffffff
      19[("<div style='font-weight: bold'>Banco de Entregas</div><div style='font-size: 70%; margin-top: 0px'>[Container: PostgreSQL]</div><div style='font-size: 80%; margin-top:10px'>Estado das entregas e<br />histórico.</div>")]
      style 19 fill:#3f7cac,stroke:#2c5678,color:#ffffff
      9["<div style='font-weight: bold'>Aplicativo do Motorista</div><div style='font-size: 70%; margin-top: 0px'>[Container: React Native]</div><div style='font-size: 80%; margin-top:10px'>Lista de entregas, rota e<br />confirmação.</div>"]
      style 9 fill:#3f7cac,stroke:#2c5678,color:#ffffff
    end

    2["<div style='font-weight: bold'>Motorista</div><div style='font-size: 70%; margin-top: 0px'>[Person]</div><div style='font-size: 80%; margin-top:10px'>Executa as entregas e<br />confirma cada uma pelo<br />aplicativo.</div>"]
    style 2 fill:#1f3a5f,stroke:#152842,color:#ffffff

    2-. "<div>1. Confirma a entrega</div><div style='font-size: 70%'>[Aplicativo móvel]</div>" .->9
    9-. "<div>2. POST<br />/entregas/{id}/confirmacao</div><div style='font-size: 70%'>[HTTPS]</div>" .->10
    10-. "<div>3. Encaminha a confirmação</div><div style='font-size: 70%'>[HTTPS/JSON]</div>" .->11
    11-. "<div>4. Grava o novo estado</div><div style='font-size: 70%'>[SQL]</div>" .->19
    11-. "<div>5. Publica EntregaConfirmada</div><div style='font-size: 70%'>[Kafka]</div>" .->18
    18-. "<div>6. Entrega o evento</div><div style='font-size: 70%'>[Kafka]</div>" .->17

  end```
