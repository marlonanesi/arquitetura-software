// Verificação do PROVEDOR: executa os contratos dos consumidores contra a API real.
// É isto que roda no CI do time da tracking-api antes de qualquer mudança ir para produção.
//
// MODO=arquivo (padrão): lê o contrato da pasta local /pacts
// MODO=broker          : busca os contratos no Pact Broker e publica o resultado lá
const path = require('node:path');
const { Verifier } = require('@pact-foundation/pact');
const { criarApp, prepararEntrega, removerEntrega, CONTRATO } = require('../src/app');

const PORTA = 8100;
const MODO = process.env.MODO || 'arquivo';
const servidor = criarApp().listen(PORTA);

function opcoesDeOrigem() {
  if (MODO === 'broker') {
    return {
      pactBrokerUrl: process.env.PACT_BROKER_URL,
      consumerVersionSelectors: [{ latest: true }],
      publishVerificationResult: true,
      providerVersion: process.env.PROVIDER_VERSION || '1.0.0',
    };
  }
  const pasta = process.env.PACT_DIR || path.resolve(__dirname, '../../pacts');
  return { pactUrls: [path.join(pasta, 'portal-transportadora-tracking-api.json')] };
}

async function main() {
  console.log(`\nVerificando os contratos contra a tracking-api (CONTRATO=${CONTRATO}, MODO=${MODO})\n`);
  try {
    await new Verifier({
      provider: 'tracking-api',
      providerBaseUrl: `http://localhost:${PORTA}`,
      ...opcoesDeOrigem(),
      // Cada "given" do contrato do consumidor corresponde a um estado que o provedor sabe preparar.
      stateHandlers: {
        'a entrega E-100 existe': async () => prepararEntrega('E-100'),
        'a entrega E-404 não existe': async () => removerEntrega('E-404'),
      },
      logLevel: 'warn',
    }).verifyProvider();
    console.log('\nRESULTADO: contrato respeitado. A mudança pode seguir para produção.\n');
  } catch (erro) {
    console.error('\nRESULTADO: contrato QUEBRADO. A mudança não deve ir para produção.\n');
    process.exitCode = 1;
  } finally {
    servidor.close();
  }
}

main();
