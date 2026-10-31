"""O modelo de ameaças da LunaLog como CÓDIGO (pytm, da OWASP).

O mesmo sistema em duas variantes, escolhidas pela variável VARIANTE:
  inseguro   como ele nasceu: controles ausentes
  seguro     depois do redesign: controles presentes

O pytm gera, a partir deste arquivo:
  --dfd      o diagrama de fluxo de dados (formato Graphviz)
  --json     o modelo com a lista de ameaças que ele deduz dos controles declarados
  --list     os tipos de ameaça que ele conhece
"""
import os

from pytm import TM, Actor, Boundary, Data, Dataflow, Datastore, Lambda, Server, Classification

variante = os.environ.get("VARIANTE", "inseguro")
ok = variante == "seguro"          # True: o controle existe; False: não existe

tm = TM(f"LunaLog Entregas ({variante})")
tm.description = "Confirmação de entregas por motoristas, com notificação do destinatário."
tm.isOrdered = True
tm.mergeResponses = True

internet = Boundary("Internet")
interna = Boundary("Rede interna")

motorista = Actor("Motorista")
motorista.inBoundary = internet
operador = Actor("Operador")
operador.inBoundary = internet
destinatario = Actor("Destinatario")
destinatario.inBoundary = internet

cpf = Data("CPF e endereco do destinatario", classification=Classification.RESTRICTED, isPII=True,
           isStored=True, isDestEncryptedAtRest=ok, isSourceEncryptedAtRest=ok)
posicao = Data("Posicao GPS da confirmacao", classification=Classification.SENSITIVE, isStored=True)
credencial = Data("Credenciais de login", classification=Classification.SECRET, isCredentials=True)

def controles(elemento, **valores):
    """Declara os controles que o elemento implementa. O pytm deduz as ameaças a partir deles."""
    for nome, valor in valores.items():
        setattr(elemento.controls, nome, valor)


api = Server("API de entregas")
api.inBoundary = interna
api.port = 8000
api.protocol = "HTTP"
controles(api,
          isHardened=ok,
          hasAccessControl=ok,                  # F4 e F5: autorizacao no servidor
          authorizesSource=ok,
          implementsPOLP=ok,                    # F8: privilegio minimo
          sanitizesInput=ok,                    # F3: consultas parametrizadas
          usesParameterizedInput=ok,
          validatesInput=ok,                    # F6: valida a posicao informada
          checksInputBounds=ok,
          encodesOutput=ok,
          authenticatesSource=ok,               # F1 e F2: segredo fora do codigo, token com expiracao
          implementsAuthenticationScheme=ok,
          implementsNonce=ok,                   # F6: o horario do aparelho barra a repeticao
          usesStrongSessionIdentifiers=ok,
          verifySessionIdentifiers=ok,
          providesIntegrity=ok,
          definesConnectionTimeout=ok,
          handlesResourceConsumption=False)     # ameaca residual: ainda sem limite de taxa (lab 3E)

notificacao = Server("Servico de notificacao")
notificacao.inBoundary = interna
controles(notificacao,
          isHardened=ok,
          hasAccessControl=ok,                  # F8: credencial de banco com privilegio minimo
          implementsPOLP=ok,
          sanitizesInput=True, usesParameterizedInput=True, validatesInput=True, encodesOutput=True,
          checksInputBounds=True, authenticatesSource=ok, implementsAuthenticationScheme=ok,
          authorizesSource=ok, providesIntegrity=ok, definesConnectionTimeout=ok,
          usesStrongSessionIdentifiers=True, verifySessionIdentifiers=True, implementsNonce=True)

banco = Datastore("PostgreSQL")
banco.inBoundary = interna
banco.isSQL = True
banco.isShared = not ok          # banco compartilhado, com uma credencial administradora para todos
banco.storesPII = True
banco.storesSensitiveData = True
banco.maxClassification = Classification.RESTRICTED
controles(banco,
          isEncrypted=ok, isHardened=ok, hasAccessControl=ok, authorizesSource=ok, implementsPOLP=ok,
          validatesInput=True, sanitizesInput=True, encodesOutput=True, checksInputBounds=True,
          authenticatesSource=True, implementsAuthenticationScheme=True, providesIntegrity=ok,
          definesConnectionTimeout=ok, usesStrongSessionIdentifiers=True, verifySessionIdentifiers=True, implementsNonce=True)

d1 = Dataflow(motorista, api, "Login e confirmacao de entrega")
d1.protocol = "HTTPS" if ok else "HTTP"
d1.dstPort = 8000
d1.data = [credencial, posicao]
controles(d1, isEncrypted=ok, authenticatesDestination=ok, checksDestinationRevocation=ok, implementsAuthenticationScheme=ok, providesIntegrity=ok, usesEncryptionAlgorithm="AES" if ok else "")

d2 = Dataflow(operador, api, "Consulta de entregas e relatorios")
d2.protocol = "HTTPS" if ok else "HTTP"
d2.dstPort = 8000
d2.data = [cpf]
controles(d2, isEncrypted=ok, authenticatesDestination=ok, implementsAuthenticationScheme=ok, providesIntegrity=ok, usesEncryptionAlgorithm="AES" if ok else "")

d3 = Dataflow(api, banco, "SQL")
d3.protocol = "PostgreSQL"
d3.dstPort = 5432
d3.data = [cpf, posicao]
controles(d3, isEncrypted=ok, authenticatesDestination=ok, implementsAuthenticationScheme=True, providesIntegrity=ok, usesEncryptionAlgorithm="AES" if ok else "")

d4 = Dataflow(notificacao, banco, "Le entregas concluidas e grava avisos")
d4.protocol = "PostgreSQL"
d4.dstPort = 5432
d4.data = [cpf]
controles(d4, isEncrypted=ok, authenticatesDestination=ok, implementsAuthenticationScheme=True, providesIntegrity=ok, usesEncryptionAlgorithm="AES" if ok else "")

d5 = Dataflow(notificacao, destinatario, "Aviso de entrega (SMS)")
d5.protocol = "HTTPS"
d5.dstPort = 443
controles(d5, isEncrypted=True, authenticatesDestination=True, providesIntegrity=True, usesEncryptionAlgorithm="AES")

tm.process()
