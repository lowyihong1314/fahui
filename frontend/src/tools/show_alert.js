import { getMaxZIndex } from "./getMaxZIndex.js";

export function show_alert(status, message) {
  // 清除旧弹窗
  const prev = document.getElementById("custom-alert");
  if (prev) prev.remove();

  // ===== 佛教庄严配色 =====
  const COLORS = {
    bg: "#fdf8ef", // 米白
    text: "#5c432d", // 温和棕
    gold: "#b29b49", // 佛金
    red: "#a94442", // 朱赤
    shadow: "rgba(0,0,0,0.18)",
    btnText: "#ffffff",
  };

  const mainColor = status === "success" ? COLORS.gold : COLORS.red;

  // ===== 动画样式 =====
  const style = document.createElement("style");
  style.textContent = `
    @keyframes draw-circle {
      from { stroke-dasharray: 0, 440; }
      to   { stroke-dasharray: 440, 440; }
    }
    @keyframes draw-check {
      from { stroke-dasharray: 0, 100; }
      to   { stroke-dasharray: 100, 100; }
    }
    @keyframes draw-cross {
      from { stroke-dasharray: 0, 100; }
      to   { stroke-dasharray: 100, 100; }
    }
  `;
  document.head.appendChild(style);

  // ===== 弹窗容器 =====
  const box = document.createElement("div");
  box.id = "custom-alert";
  Object.assign(box.style, {
    position: "fixed",
    top: "30%",
    left: "50%",
    transform: "translate(-50%, -50%)",
    background: COLORS.bg,
    padding: "22px 26px",
    borderRadius: "14px",
    boxShadow: `0 18px 40px ${COLORS.shadow}`,
    borderLeft: `6px solid ${mainColor}`,
    textAlign: "center",
    zIndex: getMaxZIndex() + 1,
    minWidth: "280px",
    color: COLORS.text,
    fontFamily: `'Noto Serif SC','Microsoft YaHei',serif`,
  });

  // ===== SVG =====
  const svgNS = "http://www.w3.org/2000/svg";
  const svg = document.createElementNS(svgNS, "svg");
  svg.setAttribute("width", "90");
  svg.setAttribute("height", "90");
  svg.style.display = "block";
  svg.style.margin = "0 auto 6px";

  const circle = document.createElementNS(svgNS, "circle");
  circle.setAttribute("cx", "45");
  circle.setAttribute("cy", "45");
  circle.setAttribute("r", "36");
  circle.setAttribute("fill", "none");
  circle.setAttribute("stroke", mainColor);
  circle.setAttribute("stroke-width", "7");
  circle.setAttribute("stroke-dasharray", "0,440");
  circle.style.animation = "draw-circle 0.6s ease-in-out forwards";
  svg.appendChild(circle);

  if (status === "success") {
    const check = document.createElementNS(svgNS, "polyline");
    check.setAttribute("points", "28,48 40,60 62,32");
    check.setAttribute("fill", "none");
    check.setAttribute("stroke", COLORS.gold);
    check.setAttribute("stroke-width", "7");
    check.setAttribute("stroke-linecap", "round");
    check.setAttribute("stroke-dasharray", "0,100");
    check.style.animation = "draw-check 0.5s ease-in-out 0.6s forwards";
    svg.appendChild(check);
  } else {
    const line1 = document.createElementNS(svgNS, "line");
    line1.setAttribute("x1", "32");
    line1.setAttribute("y1", "32");
    line1.setAttribute("x2", "58");
    line1.setAttribute("y2", "58");
    line1.setAttribute("stroke", COLORS.red);
    line1.setAttribute("stroke-width", "7");
    line1.setAttribute("stroke-linecap", "round");
    line1.setAttribute("stroke-dasharray", "0,100");
    line1.style.animation = "draw-cross 0.4s ease-in-out 0.6s forwards";

    const line2 = document.createElementNS(svgNS, "line");
    line2.setAttribute("x1", "58");
    line2.setAttribute("y1", "32");
    line2.setAttribute("x2", "32");
    line2.setAttribute("y2", "58");
    line2.setAttribute("stroke", COLORS.red);
    line2.setAttribute("stroke-width", "7");
    line2.setAttribute("stroke-linecap", "round");
    line2.setAttribute("stroke-dasharray", "0,100");
    line2.style.animation = "draw-cross 0.4s ease-in-out 0.85s forwards";

    svg.append(line1, line2);
  }

  // ===== 文本 =====
  const msg = document.createElement("div");
  msg.innerText = message;
  msg.style.fontSize = "16px";
  msg.style.margin = "10px 0 14px";
  msg.style.lineHeight = "1.6";

  // ===== 按钮 =====
  const btn = document.createElement("button");
  btn.innerText = "确定";
  Object.assign(btn.style, {
    padding: "6px 18px",
    background: mainColor,
    color: COLORS.btnText,
    border: "none",
    borderRadius: "6px",
    cursor: "pointer",
    fontSize: "14px",
    letterSpacing: "1px",
  });

  btn.onclick = () => {
    box.remove();
    style.remove();
  };

  // ===== DOM 插入 =====
  box.append(svg, msg, btn);
  document.body.appendChild(box);

  // ===== 自动关闭 =====
  setTimeout(() => {
    if (box.parentNode) box.remove();
    style.remove();
  }, 3000);
}
