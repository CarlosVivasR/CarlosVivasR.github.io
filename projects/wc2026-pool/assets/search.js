/* Global search overlay — include on any page:
   <script src="assets/search.js" defer></script>
   Trigger: press "/" or click an element with id="searchBtn".
   Searches players + teams from data/search_index.json (accent-insensitive). */
(function(){
  let INDEX=null, loaded=false;
  const norm=s=>(s||'').normalize('NFKD').replace(/[̀-ͯ]/g,'').toLowerCase();

  const css=`
  #gs-ov{position:fixed;inset:0;z-index:1000;display:none;background:rgba(2,3,10,.72);backdrop-filter:blur(6px)}
  #gs-ov.open{display:block}
  #gs-box{max-width:560px;margin:9vh auto 0;background:rgba(16,20,34,.85);backdrop-filter:blur(24px);
    border:1px solid rgba(255,255,255,.14);border-radius:18px;overflow:hidden;
    box-shadow:0 30px 80px rgba(0,0,0,.6),inset 0 1px 0 rgba(255,255,255,.14)}
  #gs-in{width:100%;border:none;background:transparent;color:#fff;font:600 1.1em 'Inter',sans-serif;padding:18px 20px;outline:none}
  #gs-in::placeholder{color:rgba(255,255,255,.4)}
  #gs-res{max-height:56vh;overflow:auto;border-top:1px solid rgba(255,255,255,.08)}
  .gs-item{display:flex;align-items:center;gap:12px;padding:11px 18px;cursor:pointer;color:#fff;text-decoration:none}
  .gs-item:hover,.gs-item.sel{background:rgba(53,224,216,.12)}
  .gs-item img{width:28px;height:20px;object-fit:cover;border-radius:3px;box-shadow:0 0 0 1px rgba(255,255,255,.18);flex:none}
  .gs-item .nm{font-weight:600;font-size:.95em}
  .gs-item .sub{margin-left:auto;font-size:.74em;color:rgba(255,255,255,.45)}
  .gs-item .tag{font-size:.62em;font-weight:800;letter-spacing:.08em;text-transform:uppercase;color:#35e0d8;background:rgba(53,224,216,.12);border-radius:4px;padding:2px 6px;flex:none}
  #gs-hint{padding:10px 18px;font-size:.74em;color:rgba(255,255,255,.4);border-top:1px solid rgba(255,255,255,.08)}
  #gs-hint b{color:rgba(255,255,255,.7);font-weight:700}`;
  const style=document.createElement('style'); style.textContent=css; document.head.appendChild(style);

  const ov=document.createElement('div'); ov.id='gs-ov';
  ov.innerHTML=`<div id="gs-box">
    <input id="gs-in" placeholder="Buscar jugador o selección…" autocomplete="off">
    <div id="gs-res"></div>
    <div id="gs-hint"><b>↑↓</b> moverse · <b>Enter</b> abrir · <b>Esc</b> cerrar</div>
  </div>`;
  document.body.appendChild(ov);
  const inp=ov.querySelector('#gs-in'), res=ov.querySelector('#gs-res');
  let sel=0, items=[];

  async function ensure(){
    if(loaded) return;
    try{ INDEX=await (await fetch('data/search_index.json')).json(); }catch(e){ INDEX={teams:[],players:[]}; }
    loaded=true;
  }
  function open(){ ensure().then(()=>{ ov.classList.add('open'); inp.value=''; inp.focus(); render(''); }); }
  function close(){ ov.classList.remove('open'); }

  function render(q){
    const nq=norm(q); let out=[];
    if(!nq){
      out = INDEX.teams.slice(0,8).map(t=>({type:'team',...t}));
    } else {
      const tt=INDEX.teams.filter(t=>norm(t.name).includes(nq)).map(t=>({type:'team',...t}));
      const pp=INDEX.players.filter(p=>norm(p.name).includes(nq)).slice(0,40).map(p=>({type:'player',...p}));
      out=[...tt,...pp].slice(0,50);
    }
    items=out; sel=0;
    res.innerHTML = out.length ? out.map((o,i)=>row(o,i)).join('') : '<div style="padding:18px;color:rgba(255,255,255,.4);font-size:.9em">Sin resultados</div>';
    [...res.children].forEach((el,i)=>{ if(el.dataset)el.onclick=()=>go(items[i]); });
  }
  function row(o,i){
    const flag=`<img src="https://flagcdn.com/w40/${o.flag}.png" alt="">`;
    if(o.type==='team') return `<a class="gs-item ${i===0?'sel':''}" data-i="${i}">${flag}<span class="nm">${o.name}</span><span class="tag">Selección</span><span class="sub">Grupo ${o.group}</span></a>`;
    return `<a class="gs-item" data-i="${i}">${flag}<span class="nm">${o.name}</span><span class="sub">${o.teamName}</span></a>`;
  }
  function go(o){ if(!o) return; location.href = o.type==='team' ? `team.html?code=${o.code}` : `player.html?id=${o.pid}`; }
  function move(d){
    const els=[...res.querySelectorAll('.gs-item')]; if(!els.length) return;
    els[sel]&&els[sel].classList.remove('sel');
    sel=(sel+d+els.length)%els.length; els[sel].classList.add('sel'); els[sel].scrollIntoView({block:'nearest'});
  }

  inp&&inp.addEventListener('input',e=>render(e.target.value));
  document.addEventListener('keydown',e=>{
    if(e.key==='/' && !/input|textarea/i.test((e.target.tagName||'')) && !ov.classList.contains('open')){ e.preventDefault(); open(); return; }
    if(!ov.classList.contains('open')) return;
    if(e.key==='Escape') close();
    else if(e.key==='ArrowDown'){ e.preventDefault(); move(1); }
    else if(e.key==='ArrowUp'){ e.preventDefault(); move(-1); }
    else if(e.key==='Enter'){ e.preventDefault(); go(items[sel]); }
  });
  ov.addEventListener('click',e=>{ if(e.target===ov) close(); });
  document.addEventListener('click',e=>{ if(e.target.closest && e.target.closest('#searchBtn')){ e.preventDefault(); open(); } });
  window.openSearch=open;
})();
