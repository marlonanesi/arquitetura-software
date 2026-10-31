// 30 requisições por segundo durante 45 s. Aos 10 s, a API de mapas sofre uma falha de 8 s.
// Variáveis: POLITICA (sem-retry | retry-imediato | backoff-jitter | completo), DURACAO (padrão 45s)
import http from 'k6/http';
import { check } from 'k6';

const POLITICA = __ENV.POLITICA || 'sem-retry';

export const options = {
  dns: { ttl: '0s' },
  scenarios: {
    carga: {
      executor: 'constant-arrival-rate',
      rate: 30, timeUnit: '1s', duration: __ENV.DURACAO || '45s',
      preAllocatedVUs: 100, maxVUs: 600,
    },
    // O gatilho do incidente: a API de mapas fica fora do ar por 8 segundos.
    gatilho: { executor: 'per-vu-iterations', vus: 1, iterations: 1, startTime: '10s', exec: 'gatilho' },
  },
  summaryTrendStats: ['avg', 'p(95)', 'max'],
};

export function setup() {
  http.post('http://mapas:8000/reiniciar');
  http.post(`http://cotacao:8000/config?politica=${POLITICA}`);
}

export default function () {
  const r = http.get(`http://cotacao:8000/cotacao/E-${Math.floor(Math.random() * 1000)}`, { timeout: '8s' });
  check(r, { 'status 200': (x) => x.status === 200 });
}

export function gatilho() {
  http.post('http://mapas:8000/falha?segundos=8');
}
