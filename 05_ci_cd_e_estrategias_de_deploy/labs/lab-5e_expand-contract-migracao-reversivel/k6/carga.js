// Tráfego contínuo sobre as duas versões da aplicação ao mesmo tempo.
// PESO_V2 (0 a 100): percentual das requisições enviadas à v2. Simula o avanço de um deploy gradual.
//   PESO_V2=0   -> só a v1 (antes do deploy)
//   PESO_V2=50  -> as duas versões convivendo (meio do deploy)
//   PESO_V2=100 -> só a v2 (deploy concluído)
// Variável: DURACAO (padrão 15s)
import http from 'k6/http';
import { check } from 'k6';

const PESO_V2 = parseInt(__ENV.PESO_V2 || '0');
const TOTAL = 5000; // entregas existentes no banco

export const options = {
  scenarios: {
    trafego: {
      executor: 'constant-arrival-rate',
      rate: 40,
      timeUnit: '1s',
      duration: __ENV.DURACAO || '15s',
      preAllocatedVUs: 20,
      maxVUs: 100,
    },
  },
  thresholds: {
    // Existem só para o k6 mostrar o resultado de cada versão separado no resumo.
    'http_req_failed{versao:v1}': ['rate<2'],
    'http_req_failed{versao:v2}': ['rate<2'],
  },
  summaryTrendStats: ['avg', 'p(95)'],
};

export default function () {
  const usaV2 = Math.random() * 100 < PESO_V2;
  const versao = usaV2 ? 'v2' : 'v1';
  const base = usaV2 ? 'http://app-v2:8000' : 'http://app-v1:8000';
  const opcoes = { tags: { versao } };
  const id = 1 + Math.floor(Math.random() * TOTAL);
  const sorteio = Math.random();

  let r;
  if (sorteio < 0.5) {
    r = http.get(`${base}/entregas/${id}`, opcoes);
  } else if (sorteio < 0.8) {
    r = http.post(`${base}/entregas`, JSON.stringify({ cliente: `Cliente novo ${versao}` }),
      { ...opcoes, headers: { 'Content-Type': 'application/json' } });
  } else {
    r = http.patch(`${base}/entregas/${id}/cliente`, JSON.stringify({ cliente: `Cliente atualizado ${versao}` }),
      { ...opcoes, headers: { 'Content-Type': 'application/json' } });
  }
  check(r, { 'status 2xx': (x) => x.status >= 200 && x.status < 300 });
}
