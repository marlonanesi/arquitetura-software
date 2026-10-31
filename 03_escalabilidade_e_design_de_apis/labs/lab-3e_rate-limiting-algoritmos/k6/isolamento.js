// Um parceiro com bug (loop de retry sem espera) e um parceiro normal, ao mesmo tempo.
// ESCOPO=cliente: um limite por chave de API.  ESCOPO=global: um limite único para todos.
// Mede, para cada parceiro, quantas requisições foram aceitas e quantas receberam 429.
import http from 'k6/http';
import { Counter } from 'k6/metrics';

const ESCOPO = __ENV.ESCOPO || 'cliente';
const ok = { bugado: new Counter('ok_bugado'), normal: new Counter('ok_normal') };
const bloqueado = { bugado: new Counter('bloq_bugado'), normal: new Counter('bloq_normal') };

export const options = {
  scenarios: {
    bugado: { executor: 'constant-arrival-rate', exec: 'bugado', rate: 100, timeUnit: '1s', duration: '15s', preAllocatedVUs: 50, maxVUs: 200 },
    normal: { executor: 'constant-arrival-rate', exec: 'normal', rate: 1, timeUnit: '1s', duration: '15s', preAllocatedVUs: 5, maxVUs: 10 },
  },
};

function chamar(parceiro) {
  const r = http.get(`http://lb/bucket?escopo=${ESCOPO}`, { headers: { 'X-Api-Key': `parceiro-${parceiro}` } });
  if (r.status === 200) ok[parceiro].add(1);
  else if (r.status === 429) bloqueado[parceiro].add(1);
}
export function bugado() { chamar('bugado'); }
export function normal() { chamar('normal'); }

export function handleSummary(data) {
  const v = (m) => (data.metrics[m] ? data.metrics[m].values.count : 0);
  const linha = (p) => {
    const a = v(`ok_${p}`), b = v(`bloq_${p}`);
    return `${p.padEnd(8)} enviadas=${String(a + b).padStart(5)}  aceitas=${String(a).padStart(4)}  bloqueadas(429)=${String(b).padStart(5)}  (${((b / Math.max(a + b, 1)) * 100).toFixed(0)}% bloqueadas)`;
  };
  return { stdout: `\n===== ISOLAMENTO (escopo=${ESCOPO}) =====\n${linha('bugado')}\n${linha('normal')}\n` };
}
