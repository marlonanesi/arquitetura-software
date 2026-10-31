// Três tipos de tráfego ao mesmo tempo:
//   cotacao  (depende da API de mapas), notificar (depende do serviço de notificação) e
//   tracking (não depende de ninguém: mostra o dano colateral).
// Variável: DURACAO (padrão 40s)
import http from 'k6/http';
import { check } from 'k6';

const BASE = 'http://cotacao:8000';
const DURACAO = __ENV.DURACAO || '40s';

function cenario(exec, taxa) {
  return {
    executor: 'constant-arrival-rate',
    exec,
    rate: taxa,
    timeUnit: '1s',
    duration: DURACAO,
    preAllocatedVUs: 50,
    maxVUs: 400,
  };
}

export const options = {
  scenarios: {
    cotacao: cenario('cotacao', 20),
    notificar: cenario('notificar', 15),
    tracking: cenario('tracking', 20),
  },
  thresholds: {
    // Os thresholds existem para o k6 mostrar cada tipo de tráfego separado no resumo.
    'http_req_duration{endpoint:cotacao}': ['p(95)<100000'],
    'http_req_duration{endpoint:notificar}': ['p(95)<100000'],
    'http_req_duration{endpoint:tracking}': ['p(95)<100000'],
    'http_req_failed{endpoint:cotacao}': ['rate<2'],
    'http_req_failed{endpoint:notificar}': ['rate<2'],
    'http_req_failed{endpoint:tracking}': ['rate<2'],
  },
  summaryTrendStats: ['avg', 'p(95)', 'max'],
};

const opcoes = (endpoint) => ({ timeout: '5s', tags: { endpoint } });

export function cotacao() {
  const r = http.get(`${BASE}/cotacao/E-${Math.floor(Math.random() * 1000)}`, opcoes('cotacao'));
  check(r, { 'cotacao 200': (x) => x.status === 200 });
}

export function notificar() {
  const r = http.post(`${BASE}/entregas/E-${Math.floor(Math.random() * 1000)}/notificar`, null, opcoes('notificar'));
  check(r, { 'notificar 2xx': (x) => x.status === 200 || x.status === 202 });
}

export function tracking() {
  const r = http.get(`${BASE}/tracking/E-${Math.floor(Math.random() * 1000)}`, opcoes('tracking'));
  check(r, { 'tracking 200': (x) => x.status === 200 });
}
