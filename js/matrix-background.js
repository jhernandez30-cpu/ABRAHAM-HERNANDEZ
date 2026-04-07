// === Fondo Matrix Rain ===
(function() {
  const canvas = document.createElement('canvas');
  canvas.id = 'matrix-canvas';
  canvas.style.position = 'fixed';
  canvas.style.top = '0';
  canvas.style.left = '0';
  canvas.style.width = '100%';
  canvas.style.height = '100%';
  canvas.style.zIndex = '0';
  canvas.style.pointerEvents = 'none';
  document.body.prepend(canvas);

  const ctx = canvas.getContext('2d');
  let width, height;
  let columns = [];
  let drops = [];
  const characters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()_+{}[]|;:,.<>?/`~";
  const fontSize = 20;
  let charArray = [];

  function resize() {
    width = window.innerWidth;
    height = window.innerHeight;
    canvas.width = width;
    canvas.height = height;
    ctx.font = `${fontSize}px "Courier New", monospace`;
    
    columns = Math.floor(width / fontSize);
    charArray = [];
    for (let i = 0; i < columns; i++) {
      charArray[i] = [];
      drops[i] = Math.random() * -height;
    }
  }

  function draw() {
    ctx.fillStyle = 'rgba(0, 0, 0, 0.05)'; // efecto estela
    ctx.fillRect(0, 0, width, height);
    ctx.fillStyle = '#00ff9d'; // color neón
    ctx.shadowBlur = 0;
    
    for (let i = 0; i < drops.length; i++) {
      const randomChar = characters.charAt(Math.floor(Math.random() * characters.length));
      const x = i * fontSize;
      const y = drops[i] * fontSize;
      ctx.fillText(randomChar, x, y);
      
      if (y > height && Math.random() > 0.975) {
        drops[i] = 0;
      }
      drops[i]++;
    }
    requestAnimationFrame(draw);
  }

  window.addEventListener('resize', () => {
    resize();
  });
  resize();
  draw();
})();
