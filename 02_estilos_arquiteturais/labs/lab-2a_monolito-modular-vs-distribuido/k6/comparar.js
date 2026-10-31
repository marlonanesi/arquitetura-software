// Mesma carga nas duas implementações. Variáveis: TAXA (por alvo, padrão 30/s) e DURACAO (padrão 20s).
import http from 'k6/http';
import { check } from 'k6';

export const options = {
  scenarios: {
    modular: { executor: 'constant-arrival-rate', exec: 'modular', rate: parseInt(__ENV.TAXA || '30'), timeUnit: '1s', duration: __ENV.DURACAO || '20s', preAllocatedVUs: 30, maxVUs: 100 },
    distribuido: { executor: 'constant-arrival-rate', exec: 'distribuido', rate: parseInt(__ENV.TAXA || '30'), timeUnit: '1s', duration: __ENV.DURACAO || '20s', preAllocatedVUs: 30, maxVUs: 100 },
  },
  thresholds: {
    'http_req_duration{alvo:modular}': ['avg>=0'],
    'http_req_duration{alvo:distribuido}': ['avg>=0'],
    'http_req_failed{alvo:modular}': ['rate>=0'],
    'http_req_failed{alvo:distribuido}': ['rate>=0'],
  },
};

const cabecalhos = { headers: { 'Content-Type': 'application/json' } };
let n = 0;

function pedir(alvo, url) {
  const corpo = JSON.stringify({ codigo: `${alvo}-${__VU}-${n++}`, destino: 'Rua das Flores, 100' });
  const r = http.post(url, corpo, { ...cabecalhos, tags: { alvo } });
  check(r, { 'status 201': (x) => x.status === 201 });
}

export function modular() { pedir('modular', 'http://monolito:8000/entregas'); }
export function distribuido() { pedir('distribuido', 'http://entregas:8000/entregas'); }

export function handleSummary(data) {
  const linha = (alvo) => {
    const d = data.metrics[`http_req_duration{alvo:${alvo}}`].values;
    const f = data.metrics[`http_req_failed{alvo:${alvo}}`].values.rate * 100;
    return `${alvo.padEnd(12)} mediana=${d['med'].toFixed(0).padStart(4)} ms  p95=${d['p(95)'].toFixed(0).padStart(4)} ms  erros=${f.toFixed(2)}%`;
  };
  return { stdout: `\n===== LATENCIA DE POST /entregas (mesma carga) =====\n${linha('modular')}\n${linha('distribuido')}\n` };
}
