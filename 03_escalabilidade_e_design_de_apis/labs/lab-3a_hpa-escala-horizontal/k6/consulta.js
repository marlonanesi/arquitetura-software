// Carga em /consulta (depende do "banco" de capacidade fixa de ~50/s). Variáveis: TAXA (padrão 80), DURACAO (padrão 45s)
import http from 'k6/http';
import { check } from 'k6';

export const options = {
  dns: { ttl: '0s' },
  scenarios: {
    carga: {
      executor: 'constant-arrival-rate',
      rate: parseInt(__ENV.TAXA || '80'), timeUnit: '1s', duration: __ENV.DURACAO || '45s',
      preAllocatedVUs: 200, maxVUs: 800,
    },
  },
  summaryTrendStats: ['avg', 'p(95)', 'max'],
};

export default function () {
  const r = http.get('http://tracking/consulta', { timeout: '10s' });
  check(r, { 'status 200': (x) => x.status === 200 });
}
