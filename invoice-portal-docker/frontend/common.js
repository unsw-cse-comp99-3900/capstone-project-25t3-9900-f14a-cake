function saveToken(token){ localStorage.setItem('jwt', token); }
function getToken(){ return localStorage.getItem('jwt') || ''; }
function clearToken(){ localStorage.removeItem('jwt'); }

async function apiFetch(url, opts={}){
  const token = getToken();
  const headers = opts.headers || {};
  if (token) headers['Authorization'] = 'Bearer ' + token;
  headers['Accept'] = 'application/json';
  if (opts.body && !(opts.body instanceof FormData)) {
    headers['Content-Type'] = 'application/json';
    opts.body = JSON.stringify(opts.body);
  }
  const resp = await fetch(url, {...opts, headers});
  if (!resp.ok) {
    const text = await resp.text();
    throw new Error(text || (resp.status + ' ' + resp.statusText));
  }
  const ctype = resp.headers.get('content-type') || '';
  if (ctype.includes('application/json')) return resp.json();
  return resp.text();
}

function ensureAuthed(){
  if (!getToken()) {
    window.location.href = '/login.html';
    return false;
  }
  return true;
}
