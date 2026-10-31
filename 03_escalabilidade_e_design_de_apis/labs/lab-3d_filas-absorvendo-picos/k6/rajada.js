// Rajada de confirmações. Variáveis: ALVO (direto ou fila), TAXA (requisições por segundo, padrão 800),
// DURACAO (padrão 10s). O resumo diz quantas foram aceitas, quantas falharam e a latência.
import http from 'k6/http';
import { Counter } from 'k6/metrics';

const aceitas = new Counter('aceitas');
const recusadas = new Counter('recusadas');
const ALVO = __ENV.ALVO || 'direto';
let n = 0;

export const options = {
  scenarios: {
    rajada: {
      executor: 'constant-arrival-rate',
      rate: parseInt(__ENV.TAXA || '800'), timeUnit: '1s', duration: __ENV.DURACAO || '10s',
      preAllocatedVUs: 200, maxVUs: 1500,
    },
  },
  summaryTrendStats: ['avg', 'med', 'p(95)'],
};

export default function () {
  const codigo = `${ALVO}-${__VU}-${__ITER}-${Date.now() % 100000}`;
  const r = http.post(`http://api:8000/confirmacoes/${ALVO}`, JSON.stringify({ codigo }),
    { headers: { 'Content-Type': 'application/json' }, timeout: '10s' });
  if (r.status === 201 || r.status === 202) aceitas.add(1); else recusadas.add(1);
}

export function handleSummary(data) {
  const total = data.metrics.http_reqs.values.count;
  const ok = data.metrics.aceitas ? data.metrics.aceitas.values.count : 0;
  const d = data.metrics.http_req_duration.values;
  return { stdout: `\n===== RAJADA (${ALVO}) =====\n` +
    `enviadas=${total}  aceitas=${ok} (${(ok / total * 100).toFixed(1)}%)  recusadas=${total - ok}\n` +
    `latencia: mediana=${d.med.toFixed(0)} ms  p95=${d['p(95)'].toFixed(0)} ms\n` };
}
