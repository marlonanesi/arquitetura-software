// Carga constante sobre o fluxo de cotação. Variáveis: TAXA (req/s, padrão 10), DURACAO (padrão 60s)
import http from 'k6/http';

const DESTINOS = ['SP', 'RJ', 'MG', 'PR', 'BA'];

export const options = {
  dns: { ttl: '0s' }, // sem cache de DNS: os contêineres podem ser recriados durante a carga
  scenarios: {
    carga: {
      executor: 'constant-arrival-rate',
      rate: parseInt(__ENV.TAXA || '10'),
      timeUnit: '1s',
      duration: __ENV.DURACAO || '60s',
      preAllocatedVUs: 30,
      maxVUs: 200,
    },
  },
};

export default function () {
  const destino = DESTINOS[Math.floor(Math.random() * DESTINOS.length)];
  http.get(`http://cotacao:8000/cotacao?destino=${destino}`, { timeout: '20s' });
}
