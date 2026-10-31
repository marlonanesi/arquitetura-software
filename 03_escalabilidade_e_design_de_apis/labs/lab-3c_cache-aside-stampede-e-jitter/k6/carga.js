// Carga de consultas de tarifa.
// Variáveis: ESTRATEGIA (sem-cache | ttl-fixo | ttl-jitter | jitter-lock), PERFIL (quente | uniforme),
//            TAXA (requisições por segundo), DURACAO (ex.: 40s)
import http from 'k6/http';
import { check } from 'k6';

const BASE = 'http://app:8000';
const ESTRATEGIA = __ENV.ESTRATEGIA || 'ttl-fixo';
const PERFIL = __ENV.PERFIL || 'quente';
const TAXA = parseInt(__ENV.TAXA || '300');

export const options = {
  scenarios: {
    carga: {
      executor: 'constant-arrival-rate',
      rate: TAXA,
      timeUnit: '1s',
      duration: __ENV.DURACAO || '40s',
      preAllocatedVUs: 100,
      maxVUs: 600,
    },
  },
  summaryTrendStats: ['avg', 'med', 'p(95)', 'p(99)', 'max'],
};

export function setup() {
  // No perfil uniforme, as 200 rotas são pré-carregadas juntas: com TTL fixo, expiram juntas.
  const aquecer = PERFIL === 'uniforme';
  http.post(`${BASE}/admin/reiniciar?estrategia=${ESTRATEGIA}&aquecer=${aquecer}`);
}

export default function () {
  let n;
  if (PERFIL === 'quente') {
    // 90% das consultas são para 5 rotas repetidas (o padrão do pico de checkout)
    n = Math.random() < 0.9 ? 1 + Math.floor(Math.random() * 5) : 1 + Math.floor(Math.random() * 200);
  } else {
    n = 1 + Math.floor(Math.random() * 200);
  }
  const rota = 'R' + String(n).padStart(3, '0');
  const r = http.get(`${BASE}/tarifa/${rota}?estrategia=${ESTRATEGIA}`, { timeout: '5s' });
  check(r, { 'status 200': (x) => x.status === 200 });
}
