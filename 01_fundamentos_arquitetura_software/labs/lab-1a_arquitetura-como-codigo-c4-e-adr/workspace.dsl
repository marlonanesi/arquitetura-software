workspace "LunaLog" "Modelo C4 da plataforma de logística e rastreamento de entregas da LunaLog." {

    !identifiers hierarchical

    configuration {
        scope softwaresystem
    }

    model {
        lojista = person "Lojista" "Contrata entregas e acompanha os pedidos dos clientes."
        motorista = person "Motorista" "Executa as entregas e confirma cada uma pelo aplicativo."
        operador = person "Operador de logística" "Monitora a operação e trata as exceções."

        maps = softwareSystem "Google Maps" "Geocodificação de endereços e cálculo de rotas." "Externo"
        pagamentos = softwareSystem "Gateway de pagamento" "Cobrança dos serviços de entrega." "Externo"
        transportadoras = softwareSystem "APIs das transportadoras" "Parceiros que recebem e executam parte das entregas." "Externo"

        lunalog = softwareSystem "LunaLog" "Planeja rotas, rastreia entregas e notifica os clientes em tempo real." {
            !docs docs
            !adrs adrs madr

            painel = container "Painel Web" "Operação e acompanhamento dos pedidos." "React" "Navegador"
            app = container "Aplicativo do Motorista" "Lista de entregas, rota e confirmação." "React Native" "Mobile"
            gateway = container "API Gateway" "Autenticação, limite de taxa e roteamento das chamadas." "Kong"

            rastreamento = container "Serviço de Rastreamento" "Recebe eventos das entregas e mantém o estado atual de cada uma." "Python, FastAPI" {
                !adrs adrs/rastreamento madr

                controlador = component "Controlador de Eventos" "Recebe as confirmações e eventos de GPS." "FastAPI router"
                estado = component "Gestor de Estado da Entrega" "Aplica as regras de transição de estado." "Python"
                repositorio = component "Repositório de Entregas" "Lê e grava o estado das entregas." "Python"
                publicador = component "Publicador de Eventos" "Publica as mudanças de estado para os demais serviços." "Python"
            }
            roteirizacao = container "Serviço de Roteirização" "Calcula a melhor sequência de paradas de cada motorista." "Python"
            notificacao = container "Serviço de Notificação" "Avisa o destinatário por SMS, e-mail e WhatsApp." "Python"
            eventos = container "Barramento de Eventos" "Transporta os eventos de entrega entre os serviços." "Kafka" "Fila"
            banco = container "Banco de Entregas" "Estado das entregas e histórico." "PostgreSQL" "Banco"
        }

        lojista -> lunalog.painel "Acompanha pedidos" "HTTPS"
        operador -> lunalog.painel "Monitora a operação" "HTTPS"
        motorista -> lunalog.app "Confirma entregas" "Aplicativo móvel"

        lunalog.painel -> lunalog.gateway "Chama a API" "HTTPS"
        lunalog.app -> lunalog.gateway "Chama a API" "HTTPS"
        lunalog.gateway -> lunalog.rastreamento "Encaminha eventos e consultas" "HTTPS/JSON"
        lunalog.gateway -> lunalog.roteirizacao "Solicita rotas" "HTTPS/JSON"

        lunalog.rastreamento.controlador -> lunalog.rastreamento.estado "Valida a transição" "Chamada de função"
        lunalog.rastreamento.estado -> lunalog.rastreamento.repositorio "Grava o novo estado" "Chamada de função"
        lunalog.rastreamento.estado -> lunalog.rastreamento.publicador "Anuncia a mudança" "Chamada de função"
        lunalog.rastreamento.repositorio -> lunalog.banco "Lê e grava" "SQL"
        lunalog.rastreamento.publicador -> lunalog.eventos "Publica eventos" "Kafka"

        lunalog.eventos -> lunalog.notificacao "Entrega eventos" "Kafka"
        lunalog.roteirizacao -> maps "Consulta rotas e geocodifica" "HTTPS"
        lunalog.notificacao -> lojista "Avisa sobre a entrega" "SMS, e-mail"
        lunalog -> pagamentos "Cobra pelo serviço" "HTTPS"
        lunalog -> transportadoras "Repassa entregas parceiras" "HTTPS"
    }

    views {
        systemContext lunalog "Contexto" "Nível 1: a LunaLog, quem a usa e de quem ela depende." {
            include *
            autoLayout lr
        }

        container lunalog "Containers" "Nível 2: o que existe dentro da LunaLog." {
            include *
            autoLayout lr
        }

        component lunalog.rastreamento "Componentes-Rastreamento" "Nível 3: por dentro do Serviço de Rastreamento." {
            include *
            autoLayout lr
        }

        dynamic lunalog "Confirmar-entrega" "Fluxo: o motorista confirma uma entrega." {
            motorista -> lunalog.app "Confirma a entrega"
            lunalog.app -> lunalog.gateway "POST /entregas/{id}/confirmacao"
            lunalog.gateway -> lunalog.rastreamento "Encaminha a confirmação"
            lunalog.rastreamento -> lunalog.banco "Grava o novo estado"
            lunalog.rastreamento -> lunalog.eventos "Publica EntregaConfirmada"
            lunalog.eventos -> lunalog.notificacao "Entrega o evento"
            autoLayout lr
        }

        styles {
            element "Person" {
                shape Person
                background #1f3a5f
                color #ffffff
            }
            element "Software System" {
                background #2e5c8a
                color #ffffff
            }
            element "Externo" {
                background #8a8a8a
                color #ffffff
            }
            element "Container" {
                background #3f7cac
                color #ffffff
            }
            element "Component" {
                background #7fb2d8
                color #0b1b2b
            }
            element "Banco" {
                shape Cylinder
            }
            element "Fila" {
                shape Pipe
            }
            element "Navegador" {
                shape WebBrowser
            }
            element "Mobile" {
                shape MobileDevicePortrait
            }
        }
    }
}
