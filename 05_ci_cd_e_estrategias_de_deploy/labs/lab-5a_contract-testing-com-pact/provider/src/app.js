// API de tracking da LunaLog (provedor).
//
// A variável CONTRATO simula versões diferentes da API, para vermos o que o contrato
// do consumidor pega e o que ele deixa passar:
//
//   original          : a versão atual
//   aditivo           : adiciona um campo novo (motorista)             -> compatível
//   remove-nao-usado  : remove campos internos que ninguém consome     -> compatível
//   quebra-renomeia   : renomeia previsao_entrega para eta             -> QUEBRA o portal
//   quebra-tipo       : previsao_entrega passa de texto ISO a número   -> QUEBRA o portal
const express = require('express');

const CONTRATO = process.env.CONTRATO || 'original';

const entregas = new Map();

function representar(e) {
  const base = { id: e.id, status: e.status };
  const internos = { custo_interno: e.custo, observacoes_internas: e.observacoes };
  switch (CONTRATO) {
    case 'aditivo':
      return { ...base, ...internos, previsao_entrega: e.previsao, motorista: { nome: 'Carlos' } };
    case 'remove-nao-usado':
      return { ...base, previsao_entrega: e.previsao };
    case 'quebra-renomeia':
      return { ...base, ...internos, eta: e.previsao };
    case 'quebra-tipo':
      return { ...base, ...internos, previsao_entrega: Date.parse(e.previsao) };
    case 'original':
    default:
      return { ...base, ...internos, previsao_entrega: e.previsao };
  }
}

function criarApp() {
  const app = express();

  app.get('/entregas/:id', (req, res) => {
    const entrega = entregas.get(req.params.id);
    if (!entrega) return res.status(404).json({ erro: 'entrega nao encontrada' });
    res.json(representar(entrega));
  });

  return app;
}

// Dados que os "estados" dos contratos preparam antes de cada verificação.
function prepararEntrega(id) {
  entregas.set(id, {
    id,
    status: 'em_rota',
    previsao: '2026-11-03T18:00:00Z',
    custo: 31.9,
    observacoes: 'cliente pediu entrega após as 17h',
  });
}

function removerEntrega(id) {
  entregas.delete(id);
}

module.exports = { criarApp, prepararEntrega, removerEntrega, CONTRATO };
