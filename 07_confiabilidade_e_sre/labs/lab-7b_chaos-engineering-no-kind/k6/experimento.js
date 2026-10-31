// Tráfego de estado estacionário contra os dois fretes ao mesmo tempo.
// Variáveis: TAXA (por alvo, padrão 20/s), DURACAO (padrão 60s), ABORTAR=sim (liga a condição de abortar).
//
// As hipóteses viram thresholds: erros < 1% e p95 < 800 ms. O resultado diz se cada alvo as confirmou.
import http from 'k6/http';
import { check } from 'k6';
import { Counter } from 'k6/metrics';

const degradadas = {
  fragil: new Counter('degradadas_fragil'),
  protegido: new Counter('degradadas_protegido'),
};
const abortar = (__ENV.ABORTAR || 'nao') === 'sim';

export const options = {
  dns: { ttl: '0s' },
  noConnectionReuse: true,   // cada requisição abre conexão nova: o Service distribui por conexão
  scenarios: {
    fragil: {
      executor: 'constant-arrival-rate', exec: 'fragil',
      rate: parseInt(__ENV.TAXA || '20'), timeUnit: '1s', duration: __ENV.DURACAO || '60s',
      preAllocatedVUs: 60, maxVUs: 300,
    },
    protegido: {
      executor: 'constant-arrival-rate', exec: 'protegido',
      rate: parseInt(__ENV.TAXA || '20'), timeUnit: '1s', duration: __ENV.DURACAO || '60s',
      preAllocatedVUs: 60, maxVUs: 300,
    },
  },
  thresholds: {
    'http_req_failed{alvo:fragil}': ['rate<0.01'],
    'http_req_duration{alvo:fragil}': ['p(95)<800'],
    // A condição de abortar vale só para o alvo protegido: se ele violar a hipótese, o experimento para.
    'http_req_failed{alvo:protegido}': [{ threshold: 'rate<0.01', abortOnFail: abortar, delayAbortEval: '5s' }],
    'http_req_duration{alvo:protegido}': ['p(95)<800'],
    'http_reqs{alvo:fragil}': ['count>=0'],
    'http_reqs{alvo:protegido}': ['count>=0'],
  },
};

function chamar(alvo) {
  const r = http.get(`http://frete-${alvo}:8000/cotacao`, { timeout: '6s', tags: { alvo } });
  check(r, { 'status 200': (x) => x.status === 200 });
  if (r.status === 200 && r.headers['X-Origem'] === 'tabela-local') degradadas[alvo].add(1);
}

export function fragil() { chamar('fragil'); }
export function protegido() { chamar('protegido'); }

function fmt(n, casas) { return n.toFixed(casas); }

export function handleSummary(data) {
  const linha = (alvo) => {
    const reqs = data.metrics[`http_reqs{alvo:${alvo}}`].values.count;
    const falhas = data.metrics[`http_req_failed{alvo:${alvo}}`].values.rate * 100;
    const p95 = data.metrics[`http_req_duration{alvo:${alvo}}`].values['p(95)'];
    const deg = data.metrics[`degradadas_${alvo}`] ? data.metrics[`degradadas_${alvo}`].values.count : 0;
    const veredito = (falhas < 1 && p95 < 800) ? 'HIPOTESE CONFIRMADA' : 'HIPOTESE REFUTADA';
    return `${alvo.padEnd(10)} requisicoes=${String(reqs).padStart(5)}  erros=${fmt(falhas, 2).padStart(6)}%  ` +
           `p95=${fmt(p95, 0).padStart(5)} ms  degradadas=${fmt(reqs ? deg / reqs * 100 : 0, 1).padStart(5)}%  ${veredito}`;
  };
  return { stdout: `\n===== RESULTADO DO EXPERIMENTO =====\n${linha('fragil')}\n${linha('protegido')}\n` };
}
