// Subtle spotlight tracking (future/calm). Respects prefers-reduced-motion.
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
