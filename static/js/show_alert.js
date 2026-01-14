function show_alert(status, message) {
  // 清除旧弹窗
  const prev = document.getElementById('custom-alert');
  if (prev) prev.remove();

  // 添加动画样式
  const style = document.createElement('style');
  style.textContent = `
    @keyframes draw-circle {
      from { stroke-dasharray: 0, 440; }
      to { stroke-dasharray: 440, 440; }
    }
    @keyframes draw-check {
      from { stroke-dasharray: 0, 100; }
      to { stroke-dasharray: 100, 100; }
    }
    @keyframes draw-cross {
      from { stroke-dasharray: 0, 100; }
      to { stroke-dasharray: 100, 100; }
    }
  `;
  document.head.appendChild(style);

  // 弹窗容器
  const box = document.createElement('div');
  box.id = 'custom-alert';
  Object.assign(box.style, {
    position: 'fixed', top: '30%', left: '50%',
    transform: 'translate(-50%, -50%)',
    background: 'var(--notify-bg-color)',
    padding: '20px', boxShadow: '0 0 15px rgba(0,0,0,0.2)',
    borderRadius: '10px', textAlign: 'center', zIndex: 9999,
    fontFamily: 'sans-serif', minWidth: '280px',
    borderLeft: `6px solid var(${status === 'success' ? '--save-button-bg' : '--delete-button-bg'})`,
    color: 'var(--notify-text-color)'
  });

  // SVG 容器
  const svgNS = 'http://www.w3.org/2000/svg';
  const svg = document.createElementNS(svgNS, 'svg');
  svg.setAttribute('width', '100');
  svg.setAttribute('height', '100');
  svg.style.display = 'block';
  svg.style.margin = '0 auto 10px';

  // 圆圈
  const circle = document.createElementNS(svgNS, 'circle');
  circle.setAttribute('cx', '50');
  circle.setAttribute('cy', '50');
  circle.setAttribute('r', '40');
  circle.setAttribute('fill', 'none');
  circle.setAttribute('stroke', `var(${status === 'success' ? '--save-button-bg' : '--delete-button-bg'})`);
  circle.setAttribute('stroke-width', '8');
  circle.setAttribute('stroke-dasharray', '0,440');
  circle.style.animation = 'draw-circle 0.6s ease-out forwards';
  svg.appendChild(circle);

  // 钩或叉
  if (status === 'success') {
    const check = document.createElementNS(svgNS, 'polyline');
    check.setAttribute('points', '30,55 45,70 75,35');
    check.setAttribute('fill', 'none');
    check.setAttribute('stroke', 'var(--save-button-bg)');
    check.setAttribute('stroke-width', '8');
    check.setAttribute('stroke-linecap', 'round');
    check.setAttribute('stroke-dasharray', '0,100');
    check.style.animation = 'draw-check 0.5s ease-out 0.6s forwards';
    svg.appendChild(check);
  } else {
    const line1 = document.createElementNS(svgNS, 'line');
    line1.setAttribute('x1', '35'); line1.setAttribute('y1', '35');
    line1.setAttribute('x2', '65'); line1.setAttribute('y2', '65');
    line1.setAttribute('stroke', 'var(--delete-button-bg)');
    line1.setAttribute('stroke-width', '8');
    line1.setAttribute('stroke-linecap', 'round');
    line1.setAttribute('stroke-dasharray', '0,100');
    line1.style.animation = 'draw-cross 0.5s ease-out 0.6s forwards';

    const line2 = document.createElementNS(svgNS, 'line');
    line2.setAttribute('x1', '65'); line2.setAttribute('y1', '35');
    line2.setAttribute('x2', '35'); line2.setAttribute('y2', '65');
    line2.setAttribute('stroke', 'var(--delete-button-bg)');
    line2.setAttribute('stroke-width', '8');
    line2.setAttribute('stroke-linecap', 'round');
    line2.setAttribute('stroke-dasharray', '0,100');
    line2.style.animation = 'draw-cross 0.5s ease-out 0.9s forwards';

    svg.appendChild(line1);
    svg.appendChild(line2);
  }

  // 消息文本
  const msg = document.createElement('div');
  msg.innerText = message;
  msg.style.margin = '10px 0';
  msg.style.fontSize = '16px';

  // OK 按钮
  const btn = document.createElement('button');
  btn.innerText = 'OK';
  Object.assign(btn.style, {
    padding: '6px 16px',
    background: `var(${status === 'success' ? '--save-button-bg' : '--delete-button-bg'})`,
    color: 'var(--button-text-color)',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '14px',
    marginTop: '5px'
  });
  btn.onclick = () => {
    box.remove();
    style.remove();
  };

  // 插入 DOM
  box.append(svg, msg, btn);
  document.body.appendChild(box);

  // 自动关闭
  setTimeout(() => {
    if (box.parentNode) box.remove();
    style.remove();
  }, 3000);
}
