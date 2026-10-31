// Carga em /cotacao (consome CPU). Variáveis: TAXA (padrão 40 req/s), DURACAO (padrão 120s)
import http from 'k6/http';
import { check } from 'k6';

export const options = {
  dns: { ttl: '0s' },
  scenarios: {
    carga: {
      executor: 'constant-arrival-rate',
      rate: parseInt(__ENV.TAXA || '40'), timeUnit: '1s', duration: __ENV.DURACAO || '120s',
      preAllocatedVUs: 100, maxVUs: 400,
    },
  },
  summaryTrendStats: ['avg', 'p(95)', 'max'],
};

export default function () {
  const r = http.get('http://tracking/cotacao', { timeout: '10s' });
  check(r, { 'status 200': (x) => x.status === 200 });
}
