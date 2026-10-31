const { criarApp, prepararEntrega, CONTRATO } = require('./app');

prepararEntrega('E-100');
criarApp().listen(8000, () => console.log(`tracking-api (contrato=${CONTRATO}) em http://localhost:8000`));
