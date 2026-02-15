// Theme (light/dark) - stored per site
(() => {
  const KEY = "eduTools:theme";
  const saved = localStorage.getItem(KEY);
  const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
  const theme = (saved === 'light' || saved === 'dark') ? saved : (prefersDark ? 'dark' : 'light');
  document.documentElement.dataset.theme = theme;

  const btn = document.getElementById('themeToggle');
  const setLabel = ()=>{
    const t = document.documentElement.dataset.theme || 'light';
    btn && btn.setAttribute('aria-label', t === 'dark' ? '밝은 모드로 전환' : '어두운 모드로 전환');
  };
  setLabel();
  btn && btn.addEventListener('click', ()=>{
    const cur = document.documentElement.dataset.theme || 'light';
    const next = cur === 'dark' ? 'light' : 'dark';
    document.documentElement.dataset.theme = next;
    localStorage.setItem(KEY, next);
    setLabel();
  });
})();

// Spotlight tracking (future/calm). Respects prefers-reduced-motion.
(() => {
  const mq = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)');
  if (mq && mq.matches) return;

  let raf = null;
  let lastX = window.innerWidth * 0.5;
  let lastY = window.innerHeight * 0.25;

  function apply(x, y){
    const mx = Math.max(0, Math.min(100, (x / Math.max(1, window.innerWidth)) * 100));
    const my = Math.max(0, Math.min(100, (y / Math.max(1, window.innerHeight)) * 100));
    document.documentElement.style.setProperty('--mx', mx.toFixed(2) + '%');
    document.documentElement.style.setProperty('--my', my.toFixed(2) + '%');
  }

  function onMove(e){
    lastX = e.clientX;
    lastY = e.clientY;
    if (raf) return;
    raf = requestAnimationFrame(() => {
      raf = null;
      apply(lastX, lastY);
    });
  }

  window.addEventListener('pointermove', onMove, {passive: true});
  apply(lastX, lastY);
})();

// Contact FAB + form
(() => {
  const $ = (id) => document.getElementById(id);
  const fab = $('contactFab');
  const modal = $('contactModal');
  const form = $('contactForm');
  const sendBtn = $('contactSend');
  const toastEl = $('toast');

  function toast(msg, ms=1800){
    if (!toastEl) return;
    const t = String(msg||'').trim();
    if (!t) return;
    toastEl.textContent = t;
    toastEl.classList.add('show');
    clearTimeout(toast._t);
    toast._t = setTimeout(()=>toastEl.classList.remove('show'), Math.max(700, ms|0));
  }

  function open(){
    if (!modal) return;
    modal.classList.add('is-open');
    modal.setAttribute('aria-hidden','false');
    // focus first visible field
    setTimeout(() => {
      const first = modal.querySelector('input[name="name"], textarea[name="message"]');
      first && first.focus && first.focus();
    }, 0);
  }
  function close(){
    if (!modal) return;
    modal.classList.remove('is-open');
    modal.setAttribute('aria-hidden','true');
  }

  fab && fab.addEventListener('click', open);
  const top = $('topContact');
  top && top.addEventListener('click', (e)=>{ e.preventDefault(); open(); });
  modal && modal.addEventListener('click', (e) => {
    const t = e.target;
    if (t && t.getAttribute && t.getAttribute('data-close') === '1') close();
  });
  window.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') close();
  });

  if (!form) return;

  form.addEventListener('submit', async (e) => {
    e.preventDefault();

    const fd = new FormData(form);
    const payload = {
      name: String(fd.get('name')||'').trim(),
      email: String(fd.get('email')||'').trim(),
      message: String(fd.get('message')||'').trim(),
      company: String(fd.get('company')||'').trim(), // honeypot
    };

    if (!payload.message || payload.message.length < 5){
      toast('문의 내용을 5자 이상 입력해 주세요.', 2200);
      return;
    }

    sendBtn && (sendBtn.disabled = true);
    try{
      const r = await fetch('https://formspree.io/f/mnjbdowv', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
        body: JSON.stringify({
          name: payload.name,
          email: payload.email,
          message: payload.message,
          _subject: 'EDU TOOLS 문의',
          // honeypot: still included (Formspree will ignore unknown fields)
          company: payload.company,
        }),
      });
      const j = await r.json().catch(()=>null);
      if (!r.ok){
        toast(j?.error || '전송에 실패했습니다. 잠시 후 다시 시도해 주세요.', 2400);
        return;
      }
      toast('문의가 접수되었습니다. 감사합니다!', 2200);
      form.reset();
      close();
    }catch{
      toast('전송에 실패했습니다. 네트워크 상태를 확인해 주세요.', 2400);
    }finally{
      sendBtn && (sendBtn.disabled = false);
    }
  });
})();
