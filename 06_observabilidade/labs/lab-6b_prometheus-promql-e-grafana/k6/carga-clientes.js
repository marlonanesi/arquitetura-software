// Carga em que cada requisição é de um cliente diferente (até 5 mil clientes).
// Usada para mostrar a explosão de cardinalidade quando cliente_id vira rótulo de métrica.
// Variáveis: TAXA (padrão 40), DURACAO (padrão 60s)
import http from 'k6/http';

export const options = {
  dns: { ttl: '0s' }, // sem cache de DNS: os contêineres podem ser recriados durante a carga
  scenarios: {
    carga: {
      executor: 'constant-arrival-rate',
      rate: parseInt(__ENV.TAXA || '40'),
      timeUnit: '1s',
      duration: __ENV.DURACAO || '60s',
      preAllocatedVUs: 50,
      maxVUs: 300,
    },
  },
};

export default function () {
  const cliente = 'c' + (1 + Math.floor(Math.random() * 5000));
  http.get(`http://cotacao:8000/cotacao?destino=SP&cliente=${cliente}`, { timeout: '20s' });
}
