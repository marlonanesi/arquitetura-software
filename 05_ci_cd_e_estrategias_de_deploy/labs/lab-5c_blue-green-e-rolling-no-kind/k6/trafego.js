// Tráfego contínuo sobre o Service. Variáveis: ALVO (padrão "app"), TAXA (padrão 30/s), DURACAO (padrão 90s).
// O resumo mostra quantas respostas vieram de cada versão e quantas falharam.
import http from 'k6/http';
import { check } from 'k6';
import { Counter } from 'k6/metrics';

// As métricas precisam ser declaradas aqui, no contexto de inicialização.
const respostas = {
  '1.0.0': new Counter('respostas_da_versao_1_0_0'),
  '2.0.0': new Counter('respostas_da_versao_2_0_0'),
  '3.0.0-quebrada': new Counter('respostas_da_versao_3_0_0_quebrada'),
};

export const options = {
  dns: { ttl: '0s' },
  noConnectionReuse: true,   // cada requisição abre uma conexão nova: o Service balanceia por conexão
  scenarios: {
    trafego: {
      executor: 'constant-arrival-rate',
      rate: parseInt(__ENV.TAXA || '30'), timeUnit: '1s', duration: __ENV.DURACAO || '90s',
      preAllocatedVUs: 50, maxVUs: 200,
    },
  },
  summaryTrendStats: ['avg', 'p(95)'],
};

export default function () {
  const r = http.get(`http://${__ENV.ALVO || 'app'}/`, { timeout: '3s' });
  const ok = check(r, { 'status 200': (x) => x.status === 200 });
  if (ok && respostas[r.headers['X-Versao']]) {
    respostas[r.headers['X-Versao']].add(1);
  }
}
