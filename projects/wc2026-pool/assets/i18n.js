/* Shared i18n helper for the JS-rendered pages (standings, squads, venues, match, player, team).
   Language is chosen on the Home page and stored in localStorage; these pages just read it.
   Usage:
     <script src="assets/i18n.js"></script>   (before the page script, NOT deferred)
     const T = { es:{...}, en:{...}, tr:{...} };
     wcT(T, 'key')   → translated string for the current language (falls back to es, then key)
*/
(function(){
  let v = localStorage.getItem('wc2026-lang') || localStorage.getItem('wc26-lang');
  if(!['en','es','tr'].includes(v)){
    const n = (navigator.language || 'es').toLowerCase();
    v = n.startsWith('en') ? 'en' : n.startsWith('tr') ? 'tr' : 'es';
  }
  window.WC_LANG = v;
  document.documentElement.lang = v;
  window.wcT = function(dict, key){
    return (dict[v] && dict[v][key]) || (dict.es && dict.es[key]) || key;
  };
})();
