-- Dois bancos com o mesmo esquema: "inseguro" (como o sistema nasceu) e "seguro" (depois do redesign).
-- Todos os usuários, senhas e CPFs são fictícios.
CREATE DATABASE inseguro;
CREATE DATABASE seguro;

-- =====================================================================================
\c inseguro
-- Senhas em texto puro e um único usuário administrador de banco para todos os serviços.
CREATE TABLE usuarios (id serial PRIMARY KEY, nome text UNIQUE NOT NULL, senha text NOT NULL, papel text NOT NULL);
INSERT INTO usuarios (nome, senha, papel) VALUES ('ana', 'ana123', 'operador'), ('bruno', 'bruno123', 'motorista'), ('carla', 'carla123', 'motorista');
CREATE TABLE entregas (
  id serial PRIMARY KEY, codigo text NOT NULL, destinatario text NOT NULL, cpf text NOT NULL, endereco text NOT NULL,
  dest_lat double precision NOT NULL, dest_lon double precision NOT NULL,
  motorista_id int REFERENCES usuarios(id), status text NOT NULL DEFAULT 'em_rota',
  conf_lat double precision, conf_lon double precision);
INSERT INTO entregas (codigo, destinatario, cpf, endereco, dest_lat, dest_lon, motorista_id, status) VALUES
  ('E-1001', 'Marina Souza',  '123.456.789-00', 'Av. Paulista, 1000',   -23.561400, -46.655900, 2, 'em_rota'),
  ('E-1002', 'Paulo Lima',    '987.654.321-00', 'Rua Augusta, 300',     -23.553000, -46.652000, 3, 'em_rota'),
  ('E-1003', 'Lucia Ferraz',  '111.222.333-44', 'Rua do Ouvidor, 50',   -23.548000, -46.634000, 2, 'em_rota');
CREATE TABLE notificacoes (id serial PRIMARY KEY, entrega_id int NOT NULL, enviada_em timestamptz NOT NULL DEFAULT now());

-- =====================================================================================
\c seguro
CREATE TABLE usuarios (id serial PRIMARY KEY, nome text UNIQUE NOT NULL, senha_hash text NOT NULL, papel text NOT NULL);
INSERT INTO usuarios (nome, senha_hash, papel) VALUES
  ('ana', 'scrypt$ae840c7e1b734aac4053420e14022a23$6d33966be2120ad4fdd7559538d9cc71066a66cee89a96074012d42822493ee0', 'operador'),
  ('bruno', 'scrypt$c7ed85543a85a75f00058098a563c1b7$dde2579d6c083a9c737646c43f24cec0fb8f39923a8d5e8f8be2d8e16c62c606', 'motorista'),
  ('carla', 'scrypt$d64db83b019f576010f040d9731a5c83$fcea887143153ebc12b82758a5eef7e98f39f58a8407380f3d713c66a255de55', 'motorista');
CREATE TABLE entregas (
  id serial PRIMARY KEY, codigo text NOT NULL, destinatario text NOT NULL, cpf text NOT NULL, endereco text NOT NULL,
  dest_lat double precision NOT NULL, dest_lon double precision NOT NULL,
  motorista_id int REFERENCES usuarios(id), status text NOT NULL DEFAULT 'em_rota',
  conf_lat double precision, conf_lon double precision);
INSERT INTO entregas (codigo, destinatario, cpf, endereco, dest_lat, dest_lon, motorista_id, status) VALUES
  ('E-1001', 'Marina Souza',  '123.456.789-00', 'Av. Paulista, 1000',   -23.561400, -46.655900, 2, 'em_rota'),
  ('E-1002', 'Paulo Lima',    '987.654.321-00', 'Rua Augusta, 300',     -23.553000, -46.652000, 3, 'em_rota'),
  ('E-1003', 'Lucia Ferraz',  '111.222.333-44', 'Rua do Ouvidor, 50',   -23.548000, -46.634000, 2, 'em_rota');
CREATE TABLE notificacoes (id serial PRIMARY KEY, entrega_id int NOT NULL, enviada_em timestamptz NOT NULL DEFAULT now());
-- Trilha de auditoria encadeada: cada linha guarda o hash da anterior (adulterar uma linha quebra a cadeia).
CREATE TABLE auditoria (
  id serial PRIMARY KEY, em timestamptz NOT NULL DEFAULT now(), usuario text NOT NULL, acao text NOT NULL,
  entrega_id int NOT NULL, lat double precision, lon double precision, origem_ip text,
  hash_anterior text NOT NULL, hash text NOT NULL);

-- Privilégio mínimo: cada serviço tem a sua credencial, com só o que precisa.
CREATE ROLE api_seg LOGIN PASSWORD 'api-seg-lab';
GRANT SELECT ON usuarios TO api_seg;
GRANT SELECT ON entregas TO api_seg;
GRANT UPDATE (status, conf_lat, conf_lon) ON entregas TO api_seg;
GRANT SELECT, INSERT ON auditoria TO api_seg;            -- sem UPDATE nem DELETE: a trilha só cresce
GRANT USAGE ON SEQUENCE auditoria_id_seq TO api_seg;

CREATE ROLE notif_seg LOGIN PASSWORD 'notif-seg-lab';
GRANT SELECT (id, codigo, status) ON entregas TO notif_seg;   -- sem CPF, sem endereço, sem UPDATE
GRANT SELECT, INSERT ON notificacoes TO notif_seg;
GRANT USAGE ON SEQUENCE notificacoes_id_seq TO notif_seg;
