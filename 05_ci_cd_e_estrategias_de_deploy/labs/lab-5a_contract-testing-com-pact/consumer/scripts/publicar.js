// Publica o contrato gerado pelo teste do consumidor no Pact Broker.
// Em um pipeline real, isto é uma etapa do CI do portal, depois dos testes.
const fs = require('node:fs');
const path = require('node:path');

const broker = process.env.PACT_BROKER_URL;
const versao = process.env.CONSUMER_VERSION || '1.0.0';
const arquivo = path.join(process.env.PACT_DIR || '/pacts', 'portal-transportadora-tracking-api.json');

async function main() {
  const contrato = fs.readFileSync(arquivo, 'utf-8');
  const url = `${broker}/pacts/provider/tracking-api/consumer/portal-transportadora/version/${versao}`;
  const r = await fetch(url, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: contrato });
  if (!r.ok) throw new Error(`falha ao publicar: HTTP ${r.status} ${await r.text()}`);
  console.log(`Contrato publicado: portal-transportadora ${versao} -> tracking-api`);
}

main().catch((e) => {
  console.error(e.message);
  process.exit(1);
});
