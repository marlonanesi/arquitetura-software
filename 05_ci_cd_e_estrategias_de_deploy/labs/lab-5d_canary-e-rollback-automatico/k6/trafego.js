// Tráfego contínuo sobre o Service "app". Variáveis: TAXA (padrão 40/s), DURACAO (padrão 150s).
// O resumo mostra a taxa de falhas e quantas respostas vieram de cada versão.
import http from 'k6/http';
import { check } from 'k6';
import { Counter } from 'k6/metrics';

const respostas = {
  '1.0.0': new Counter('respostas_da_versao_1_0_0'),
  '2.0.0': new Counter('respostas_da_versao_2_0_0'),
  '3.0.0-defeito': new Counter('respostas_da_versao_3_0_0_defeito'),
};
const erros = new Counter('erros_5xx');

export const options = {
  dns: { ttl: '0s' },
  noConnectionReuse: true,   // cada requisição abre conexão nova: o Service distribui por conexão
  scenarios: {
    trafego: {
      executor: 'constant-arrival-rate',
      rate: parseInt(__ENV.TAXA || '40'), timeUnit: '1s', duration: __ENV.DURACAO || '150s',
      preAllocatedVUs: 50, maxVUs: 200,
    },
  },
  summaryTrendStats: ['avg', 'p(95)'],
};

export default function () {
  const r = http.get('http://app/', { timeout: '3s' });
  const ok = check(r, { 'status 200': (x) => x.status === 200 });
  if (ok && respostas[r.headers['X-Versao']]) respostas[r.headers['X-Versao']].add(1);
  if (r.status >= 500) erros.add(1);
}
