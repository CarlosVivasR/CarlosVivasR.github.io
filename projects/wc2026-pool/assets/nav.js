/* Unified site navigation — identical on every page.
   Bottom tab bar (app, mobile) + top bar (desktop) + a floating search magnifier (all sizes).
   Usage: set window.PAGE={active:'teams',crumbs:[...]}; add <div id="site-nav"></div>;
   include nav.js + search.js. active ∈ home|teams|calendar|pool|sedes . */
(function(){
  const P = window.PAGE || {};
  // current language (chosen on Home, stored in localStorage)
  let NL = localStorage.getItem('wc2026-lang') || localStorage.getItem('wc26-lang');
  if(!['en','es','tr'].includes(NL)){ const n=(navigator.language||'es').toLowerCase(); NL=n.startsWith('en')?'en':n.startsWith('tr')?'tr':'es'; }
  const NAV_T = {
    es:{home:'Inicio',teams:'Clasificación',calendar:'Calendario',pool:'Quiniela',sedes:'Sedes',squads:'Plantillas'},
    en:{home:'Home',teams:'Standings',calendar:'Calendar',pool:'Pool',sedes:'Venues',squads:'Squads'},
    tr:{home:'Ana sayfa',teams:'Puan durumu',calendar:'Takvim',pool:'Tahmin',sedes:'Sahalar',squads:'Kadrolar'}
  };
  const NAV_S = {
    es:{home:'Inicio',teams:'Clasif.',calendar:'Calend.',pool:'Quiniela',sedes:'Sedes',squads:'Plantel'},
    en:{home:'Home',teams:'Standings',calendar:'Calendar',pool:'Pool',sedes:'Venues',squads:'Squads'},
    tr:{home:'Ana',teams:'Puan',calendar:'Takvim',pool:'Tahmin',sedes:'Sahalar',squads:'Kadro'}
  };
  const tn = NAV_T[NL] || NAV_T.es, ts = NAV_S[NL] || NAV_S.es;
  const LINKS = [
    {id:'home',     label:tn.home,     short:ts.home,     href:'index.html',      icon:'🌍'},
    {id:'teams',    label:tn.teams,    short:ts.teams,    href:'teams.html',      icon:'📊'},
    {id:'calendar', label:tn.calendar, short:ts.calendar, href:'calendar.html',   icon:'📅'},
    {id:'pool',     label:tn.pool,     short:ts.pool,     href:'pool.html',       icon:'🏆'},
    {id:'sedes',    label:tn.sedes,    short:ts.sedes,    href:'sedes.html',      icon:'📍'},
    {id:'squads',   label:tn.squads,   short:ts.squads,   href:'plantillas.html', icon:'👥'},
  ];
  // translate known breadcrumb section labels by their href
  const CRUMB_BY_HREF = {'index.html':tn.home,'teams.html':tn.teams,'calendar.html':tn.calendar,'pool.html':tn.pool,'sedes.html':tn.sedes,'plantillas.html':tn.squads};
  if(P.crumbs) P.crumbs = P.crumbs.map(c => (c.href && CRUMB_BY_HREF[c.href]) ? {...c, label:CRUMB_BY_HREF[c.href]} : c);
  const css = `
  .sn{position:sticky;top:0;z-index:60;background:rgba(3,4,12,.72);backdrop-filter:saturate(140%) blur(14px);border-bottom:1px solid rgba(255,255,255,.1)}
  .sn-in{max-width:1100px;margin:0 auto;padding:11px 20px;display:flex;align-items:center;gap:18px}
  .sn-brand{display:inline-flex;align-items:center;gap:8px;font-weight:800;letter-spacing:.03em;font-size:.9em;color:#fff;text-decoration:none;flex:none}
  .sn-brand .sn-logo{height:26px;width:auto;display:block;filter:drop-shadow(0 1px 3px rgba(0,0,0,.5))}
  .sn-links{display:flex;align-items:center;gap:4px;margin-left:6px}
  .sn-links a{color:rgba(255,255,255,.65);font-weight:600;font-size:.92em;text-decoration:none;padding:7px 12px;border-radius:99px;transition:all .15s}
  .sn-links a:hover{color:#fff;background:rgba(255,255,255,.06)}
  .sn-links a.active{color:#03040c;background:#e8c247}
  .sn-right{margin-left:auto;display:flex;align-items:center;gap:10px}
  .sn-burger{display:none;background:none;border:1px solid rgba(255,255,255,.18);border-radius:8px;color:#fff;font-size:1.1em;padding:5px 10px;cursor:pointer}
  .sn-crumbs{max-width:1100px;margin:0 auto;padding:10px 20px 0;display:flex;align-items:center;gap:8px;font-size:.82em;color:rgba(255,255,255,.5);flex-wrap:wrap;position:relative;z-index:5}
  .sn-crumbs a{color:rgba(255,255,255,.7);text-decoration:none}.sn-crumbs a:hover{color:#35e0d8}
  .sn-crumbs .sep{opacity:.4}.sn-crumbs .cur{color:#fff;font-weight:600}

  /* floating search magnifier — always visible, top-right */
  .sn-fab{position:fixed;top:62px;right:14px;z-index:80;width:42px;height:42px;border-radius:50%;
    display:grid;place-items:center;font-size:1.1em;cursor:pointer;
    background:rgba(16,20,34,.7);backdrop-filter:blur(14px);border:1px solid rgba(255,255,255,.16);
    box-shadow:0 6px 20px rgba(0,0,0,.4)}
  .sn-fab:hover{border-color:#35e0d8}

  /* language toggle — same spot on every page */
  .sn-lang{position:fixed;top:66px;right:66px;z-index:80;display:inline-flex;border-radius:99px;overflow:hidden;
    border:1px solid rgba(255,255,255,.16);background:rgba(16,20,34,.7);backdrop-filter:blur(14px);box-shadow:0 6px 20px rgba(0,0,0,.4)}
  .sn-lang button{background:transparent;border:none;padding:5px 8px;font:700 .68em 'Inter',sans-serif;color:rgba(255,255,255,.55);cursor:pointer;letter-spacing:.03em}
  .sn-lang button:hover{color:#fff}
  .sn-lang button.on{background:#e8c247;color:#03040c}

  @media(max-width:720px){
    .sn-links{position:absolute;top:54px;left:0;right:0;flex-direction:column;align-items:stretch;gap:2px;
      background:rgba(8,10,20,.98);backdrop-filter:blur(16px);padding:10px 14px;border-bottom:1px solid rgba(255,255,255,.1);display:none}
    .sn-links.open{display:flex}.sn-links a{padding:11px 12px}
    .sn-burger{display:inline-block}
    .sn{display:none}.sn-crumbs{padding-top:16px}
    .topbar{display:none !important}
  }
  /* bottom tab bar — app style, mobile only */
  .sn-tabs{display:none}
  @media(max-width:720px){
    .sn-tabs{display:flex;position:fixed;left:0;right:0;bottom:0;z-index:70;
      background:rgba(6,8,16,.92);backdrop-filter:saturate(140%) blur(16px);border-top:1px solid rgba(255,255,255,.12);
      padding:6px 2px calc(6px + env(safe-area-inset-bottom));}
    .sn-tab{flex:1;display:flex;flex-direction:column;align-items:center;gap:2px;padding:6px 2px;text-decoration:none;
      color:rgba(255,255,255,.55);font-size:.62em;font-weight:700;letter-spacing:.02em}
    .sn-tab .ic{font-size:1.4em;line-height:1;filter:grayscale(.4) opacity(.85)}
    .sn-tab.active{color:#e8c247}.sn-tab.active .ic{filter:none}
    body{padding-bottom:62px}
  }`;
  const st=document.createElement('style'); st.textContent=css; document.head.appendChild(st);

  // top bar links (no search here; search is the floating magnifier)
  const linksHTML = LINKS.map(l=>`<a href="${l.href}" class="${P.active===l.id?'active':''}">${l.label}</a>`).join('');
  const crumbsHTML = (P.crumbs&&P.crumbs.length)
    ? `<div class="sn-crumbs">`+P.crumbs.map((c,i)=>{
        const sep=i?'<span class="sep">›</span>':'';
        return sep+(c.href?`<a href="${c.href}">${c.label}</a>`:`<span class="cur">${c.label}</span>`);
      }).join('')+`</div>` : '';
  const topHTML = `
    <header class="sn"><div class="sn-in">
      <a class="sn-brand" href="index.html"><img class="sn-logo" src="assets/logo-wc2026.svg" alt="" aria-hidden="true">WC&nbsp;26</a>
      <nav class="sn-links" id="snLinks">${linksHTML}</nav>
      <div class="sn-right"><button class="sn-burger" id="snBurger" aria-label="Menú">☰</button></div>
    </div></header>${crumbsHTML}`;

  const mount=document.getElementById('site-nav');
  if(mount) mount.outerHTML=topHTML;

  // bottom tabs (no search tab; search lives in the magnifier)
  const tabs=LINKS.map(l=>`<a class="sn-tab ${P.active===l.id?'active':''}" href="${l.href}"><span class="ic">${l.icon}</span>${l.short||l.label}</a>`).join('');
  document.body.insertAdjacentHTML('beforeend', `<nav class="sn-tabs">${tabs}</nav>`);

  // floating search magnifier (binds via search.js which listens for #searchBtn clicks)
  document.body.insertAdjacentHTML('beforeend', `<button class="sn-fab" id="searchBtn" aria-label="Buscar">🔍</button>`);

  // floating language toggle — ONLY on Home; other pages keep the chosen language.
  if(P.active==='home'){
    const LKEYS=['wc2026-lang','wc26-lang'];
    let lang='es';
    for(const k of LKEYS){ const v=localStorage.getItem(k); if(v){ lang=v; break; } }
    if(!['en','es','tr'].includes(lang)){ const n=(navigator.language||'es').toLowerCase(); lang=n.startsWith('en')?'en':n.startsWith('tr')?'tr':'es'; }
    const langHTML=['EN','ES','TR'].map(L=>`<button data-l="${L.toLowerCase()}" class="${lang===L.toLowerCase()?'on':''}">${L}</button>`).join('');
    document.body.insertAdjacentHTML('beforeend', `<div class="sn-lang" role="group" aria-label="Idioma">${langHTML}</div>`);
    document.querySelector('.sn-lang').addEventListener('click', e=>{ const b=e.target.closest('button'); if(!b) return; LKEYS.forEach(k=>localStorage.setItem(k,b.dataset.l)); location.reload(); });
  }

  const burger=document.getElementById('snBurger'), links=document.getElementById('snLinks');
  burger&&burger.addEventListener('click',()=>links.classList.toggle('open'));
})();
