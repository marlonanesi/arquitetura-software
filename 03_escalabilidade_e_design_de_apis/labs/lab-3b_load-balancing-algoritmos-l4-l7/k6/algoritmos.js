// Mesma carga em cada algoritmo, um depois do outro: 30 usuários simultâneos (modelo fechado) por 12 s.
// Mostra, por balanceador: quantas requisições foram atendidas, a latência e a distribuição por instância.
import http from 'k6/http';
import { Counter } from 'k6/metrics';

const BALANCEADORES = {
  rr: 'http://haproxy:8301/',
  leastconn: 'http://haproxy:8302/',
  source: 'http://haproxy:8303/',
  peso: 'http://haproxy:8304/',
};
const INSTANCIAS = ['a', 'b', 'c'];
const DURACAO = parseInt(__ENV.DURACAO || '12');
const contadores = {};
const scenarios = {};
const thresholds = {};
Object.keys(BALANCEADORES).forEach((lb, i) => {
  INSTANCIAS.forEach((inst) => { contadores[`${lb}_${inst}`] = new Counter(`dist_${lb}_${inst}`); });
  scenarios[lb] = {
    executor: 'constant-vus', vus: 30, duration: `${DURACAO}s`,
    startTime: `${i * (DURACAO + 3)}s`, exec: 'carga', env: { LB: lb },
  };
  thresholds[`http_req_duration{lb:${lb}}`] = ['avg>=0'];
  thresholds[`http_reqs{lb:${lb}}`] = ['count>=0'];
});

export const options = { scenarios, thresholds, summaryTrendStats: ['avg', 'med', 'p(95)'] };

export function carga() {
  const lb = __ENV.LB;
  const r = http.get(BALANCEADORES[lb], { tags: { lb }, timeout: '10s' });
  const inst = r.headers['X-Instancia'];
  if (inst && contadores[`${lb}_${inst}`]) contadores[`${lb}_${inst}`].add(1);
}

export function handleSummary(data) {
  const linhas = Object.keys(BALANCEADORES).map((lb) => {
    const n = data.metrics[`http_reqs{lb:${lb}}`].values.count;
    const d = data.metrics[`http_req_duration{lb:${lb}}`].values;
    const dist = INSTANCIAS.map((inst) => {
      const m = data.metrics[`dist_${lb}_${inst}`];
      const c = m ? m.values.count : 0;
      return `${inst}=${String(Math.round((c / n) * 100)).padStart(3)}%`;
    }).join(' ');
    return `${lb.padEnd(10)} req=${String(n).padStart(5)} (${(n / DURACAO).toFixed(0).padStart(3)}/s)  media=${d.avg.toFixed(0).padStart(4)} ms  p95=${d['p(95)'].toFixed(0).padStart(4)} ms  | ${dist}`;
  });
  return { stdout: `\n===== ALGORITMOS (30 usuarios simultaneos, ${DURACAO}s cada) =====\n${linhas.join('\n')}\n` };
}
