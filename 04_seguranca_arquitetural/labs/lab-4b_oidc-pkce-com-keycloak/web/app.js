// Cliente OpenID Connect escrito à mão, de propósito, para o fluxo ficar visível.
// Em um aplicativo real use uma biblioteca madura (por exemplo, oidc-client-ts).
const KC = 'http://localhost:8180/realms/lunalog';
const CLIENT_ID = window.CONFIG.clientId;
const REDIRECT = location.origin + '/';
const $ = (id) => document.getElementById(id);

document.title = `${window.CONFIG.nome} - OIDC com PKCE`;
$('titulo').textContent = `${window.CONFIG.nome}: login com OpenID Connect`;

const b64url = (buf) => btoa(String.fromCharCode(...new Uint8Array(buf))).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
const aleatorio = (n) => { const a = new Uint8Array(n); crypto.getRandomValues(a); return b64url(a); };
const sha256 = async (txt) => b64url(await crypto.subtle.digest('SHA-256', new TextEncoder().encode(txt)));

function decodificar(jwt) {
  const [h, p] = jwt.split('.').slice(0, 2).map((s) => {
    const pad = s.replace(/-/g, '+').replace(/_/g, '/');
    return JSON.parse(decodeURIComponent(escape(atob(pad))));
  });
  return { cabecalho: h, payload: p };
}
const mostrarJwt = (jwt) => {
  const { cabecalho, payload } = decodificar(jwt);
  return `${jwt.slice(0, 40)}...\n\ncabeçalho: ${JSON.stringify(cabecalho)}\npayload:   ${JSON.stringify(payload, null, 2)}`;
};

// ------------------------------------------------------------------ passo 1 e 2: preparar e redirecionar
async function preparar() {
  const verifier = aleatorio(48);            // segredo que fica só neste navegador
  const challenge = await sha256(verifier);  // hash dele, que vai na URL
  const state = aleatorio(16);               // protege contra CSRF
  sessionStorage.setItem('pkce', JSON.stringify({ verifier, state }));

  const params = new URLSearchParams({
    client_id: CLIENT_ID, response_type: 'code', scope: 'openid profile email',
    redirect_uri: REDIRECT, state, code_challenge: challenge, code_challenge_method: 'S256',
  });
  const url = `${KC}/protocol/openid-connect/auth?${params}`;
  $('preparo-detalhe').textContent =
    `code_verifier  (fica só aqui, nunca vai na URL):\n  ${verifier}\n\n` +
    `code_challenge = BASE64URL(SHA-256(code_verifier)), vai na URL:\n  ${challenge}\n\n` +
    `state (anti-CSRF):\n  ${state}\n\n` +
    `URL de autorização:\n  ${url}`;
  $('preparo').hidden = false;
  $('btn-ir').onclick = () => { location.href = url; };
}
$('btn-preparar').onclick = preparar;

// ------------------------------------------------------------------ passo 3: trocar o code por tokens
async function trocar(comVerifier) {
  const pkce = JSON.parse(sessionStorage.getItem('pkce') || '{}');
  const code = new URLSearchParams(location.search).get('code');
  const corpo = new URLSearchParams({ grant_type: 'authorization_code', client_id: CLIENT_ID, code, redirect_uri: REDIRECT });
  if (comVerifier) corpo.set('code_verifier', pkce.verifier);

  const resp = await fetch(`${KC}/protocol/openid-connect/token`, { method: 'POST', body: corpo });
  const dados = await resp.json();
  const el = $('troca-resultado');
  el.hidden = false;
  if (!resp.ok) {
    el.innerHTML = `<span class="erro">HTTP ${resp.status}: ${dados.error} - ${dados.error_description}</span>\n\n` +
      (comVerifier
        ? 'O code é de uso único e já foi consumido ou expirou. Recomece o login.'
        : 'Sem o code_verifier, o Keycloak recusou: quem roubou só o code não consegue tokens.\n' +
          'Repare também que a tentativa INVALIDOU o code (uso único). O login legítimo precisa recomeçar.') +
      '\n\n<button id="btn-recomecar">Recomeçar o login</button>';
    $('btn-recomecar').onclick = () => { history.replaceState({}, '', REDIRECT); location.href = REDIRECT; };
    return;
  }
  sessionStorage.setItem('tokens', JSON.stringify(dados));
  history.replaceState({}, '', REDIRECT);
  exibirTokens(dados);
}
$('btn-trocar').onclick = () => trocar(true);
$('btn-atacar').onclick = () => trocar(false);

// ------------------------------------------------------------------ exibição
function exibirTokens(t) {
  $('inicio').hidden = true;
  $('callback').hidden = true;
  $('tokens').hidden = false;
  const idp = decodificar(t.id_token).payload;
  $('usuario').textContent = `${idp.name || idp.preferred_username} (${idp.email || ''})`;
  $('app-tag').textContent = `client: ${CLIENT_ID}`;
  $('expira').textContent = t.expires_in;
  $('id-token').textContent = mostrarJwt(t.id_token);
  $('access-token').textContent = mostrarJwt(t.access_token);
  $('refresh-token').textContent = `${t.refresh_token.slice(0, 40)}...  (opaco para o aplicativo; expira em ${t.refresh_expires_in} s)`;
}

$('btn-sair').onclick = () => {
  const t = JSON.parse(sessionStorage.getItem('tokens') || '{}');
  sessionStorage.clear();
  const p = new URLSearchParams({ client_id: CLIENT_ID, post_logout_redirect_uri: REDIRECT });
  if (t.id_token) p.set('id_token_hint', t.id_token);
  location.href = `${KC}/protocol/openid-connect/logout?${p}`;
};

// ------------------------------------------------------------------ ao carregar a página
(function iniciar() {
  const q = new URLSearchParams(location.search);
  const salvos = sessionStorage.getItem('tokens');
  if (salvos) return exibirTokens(JSON.parse(salvos));

  if (q.get('error')) {
    $('inicio').hidden = false;
    $('preparo').hidden = false;
    $('preparo-detalhe').textContent = `Erro vindo do Keycloak: ${q.get('error')} - ${q.get('error_description') || ''}`;
    return;
  }
  if (q.get('code')) {
    const pkce = JSON.parse(sessionStorage.getItem('pkce') || '{}');
    const estadoOk = q.get('state') === pkce.state;
    $('inicio').hidden = true;
    $('callback').hidden = false;
    $('callback-detalhe').textContent =
      `code:  ${q.get('code')}\nstate: ${q.get('state')}  ${estadoOk ? '(confere com o enviado)' : '(NÃO confere: possível CSRF, abortar)'}`;
    $('btn-trocar').disabled = !estadoOk;
  }
})();
