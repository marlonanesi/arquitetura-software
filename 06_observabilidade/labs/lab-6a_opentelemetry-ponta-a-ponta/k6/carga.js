// Carga leve e constante, só para gerar métricas e traces. Variável: DURACAO (padrão 30s)
import http from 'k6/http';

export const options = {
  dns: { ttl: '0s' }, // sem cache de DNS: os contêineres podem ser recriados durante a carga
  scenarios: {
    carga: { executor: 'constant-arrival-rate', rate: 3, timeUnit: '1s', duration: __ENV.DURACAO || '30s', preAllocatedVUs: 20, maxVUs: 60 },
  },
};

export default function () {
  http.get('http://cotacao:8000/cotacao?destino=SP', { timeout: '20s' });
}
