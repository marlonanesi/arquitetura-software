// Teste do CONSUMIDOR: descreve o que o portal espera da API de tracking.
// Ao rodar, o Pact sobe um servidor falso que responde exatamente isso e,
// se o cliente passar no teste, grava o contrato em ../pacts.
const { test } = require('node:test');
const assert = require('node:assert');
const path = require('node:path');
const { PactV4, MatchersV3 } = require('@pact-foundation/pact');
const { consultarEntrega } = require('../src/clienteTracking');

const { like, regex } = MatchersV3;

const pact = new PactV4({
  consumer: 'portal-transportadora',
  provider: 'tracking-api',
  dir: process.env.PACT_DIR || path.resolve(__dirname, '../../pacts'),
  logLevel: 'warn',
});

test('consulta uma entrega que existe', async () => {
  await pact
    .addInteraction()
    .given('a entrega E-100 existe')
    .uponReceiving('uma consulta de entrega existente')
    .withRequest('GET', '/entregas/E-100', (req) => req.headers({ Accept: 'application/json' }))
    .willRespondWith(200, (res) =>
      res.headers({ 'Content-Type': 'application/json' }).jsonBody({
        // like(): o contrato exige o TIPO, não o valor exato
        id: like('E-100'),
        status: like('em_rota'),
        // regex(): data e hora no formato ISO 8601 (o padrão precisa casar o valor inteiro)
        previsao_entrega: regex(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(Z|[+-]\d{2}:\d{2})$/, '2026-11-03T18:00:00Z'),
      })
    )
    .executeTest(async (mockServer) => {
      const entrega = await consultarEntrega(mockServer.url, 'E-100');
      assert.strictEqual(entrega.id, 'E-100');
      assert.strictEqual(entrega.status, 'em_rota');
      assert.ok(entrega.previsaoEntrega instanceof Date && !Number.isNaN(entrega.previsaoEntrega.getTime()));
    });
});

test('consulta uma entrega que não existe', async () => {
  await pact
    .addInteraction()
    .given('a entrega E-404 não existe')
    .uponReceiving('uma consulta de entrega inexistente')
    .withRequest('GET', '/entregas/E-404', (req) => req.headers({ Accept: 'application/json' }))
    .willRespondWith(404)
    .executeTest(async (mockServer) => {
      const entrega = await consultarEntrega(mockServer.url, 'E-404');
      assert.strictEqual(entrega, null);
    });
});
