// Pergunta ao Pact Broker: esta versão pode ir para produção?
// A resposta sai da matriz de compatibilidade (quem foi verificado contra quem).
// Uso: node scripts/can-i-deploy.js <participante> <versao>
const broker = process.env.PACT_BROKER_URL;
const [participante, versao] = process.argv.slice(2);

async function main() {
  const params = new URLSearchParams();
  params.append('q[][pacticipant]', participante);
  params.append('q[][version]', versao);
  params.append('latestby', 'cvp');
  const r = await fetch(`${broker}/matrix?${params}`, { headers: { Accept: 'application/hal+json' } });
  if (!r.ok) throw new Error(`broker respondeu HTTP ${r.status}`);
  const { summary, matrix = [] } = await r.json();

  console.log(`\nCan I deploy ${participante} ${versao}?\n`);
  for (const linha of matrix) {
    const res = linha.verificationResult?.success;
    const estado = res === true ? 'verificado com sucesso' : res === false ? 'verificação FALHOU' : 'sem verificação';
    console.log(`  ${linha.consumer.name} ${linha.consumer.version.number} -> ${linha.provider.name} ${linha.provider.version?.number ?? '?'}: ${estado}`);
  }
  console.log(`\nResposta: ${summary.deployable ? 'SIM, pode seguir para produção' : 'NÃO, há verificação falhando ou ausente'}\n`);
  process.exit(summary.deployable ? 0 : 1);
}

main().catch((e) => {
  console.error(e.message);
  process.exit(2);
});
