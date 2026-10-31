// Cliente da API de tracking usado pelo portal da transportadora.
// Repare no que o portal USA da resposta: id, status e previsao_entrega.
// Esse é o contrato que o consumidor realmente precisa, nada além disso.

async function consultarEntrega(baseUrl, id) {
  const resposta = await fetch(`${baseUrl}/entregas/${id}`, {
    headers: { Accept: 'application/json' },
  });
  if (resposta.status === 404) return null;
  if (!resposta.ok) throw new Error(`tracking-api respondeu ${resposta.status}`);

  const dados = await resposta.json();
  return {
    id: dados.id,
    status: dados.status,
    previsaoEntrega: new Date(dados.previsao_entrega),
  };
}

module.exports = { consultarEntrega };
