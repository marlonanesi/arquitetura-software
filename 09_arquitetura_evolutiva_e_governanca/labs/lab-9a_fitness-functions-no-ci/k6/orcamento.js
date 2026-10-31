// FITNESS FUNCTION DE DESEMPENHO: o orçamento de latência da API, como thresholds do k6.
// Se a latência passar do orçamento, o k6 sai com código diferente de zero e o pipeline falha.
import http from 'k6/http';
import { check } from 'k6';

export const options = {
  dns: { ttl: '0s' },
  scenarios: {
    orcamento: { executor: 'constant-arrival-rate', rate: 50, timeUnit: '1s', duration: '8s', preAllocatedVUs: 50, maxVUs: 200 },
  },
  thresholds: {
    http_req_duration: ['p(95)<150'],   // 95% das requisições em menos de 150 ms
    http_req_failed: ['rate<0.01'],     // menos de 1% de erro
  },
};

export default function () {
  const r = http.get(`http://${__ENV.ALVO}:8000/frete?peso_kg=10&distancia_km=100`);
  check(r, { 'status 200': (x) => x.status === 200 });
}
