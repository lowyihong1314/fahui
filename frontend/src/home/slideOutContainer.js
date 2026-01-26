export function slideOutContainer(container, direction = "left", onDone) {
  // 1️⃣ 暴力清除所有滚动位置
  const allScrollTargets = [
    window,
    document.scrollingElement,
    document.documentElement,
    document.body,
    document.getElementById("base_container"),
  ].filter(Boolean);

  allScrollTargets.forEach((el) => {
    try {
      if (el === window) {
        window.scrollTo(0, 0);
      } else {
        el.scrollTop = 0;
      }
    } catch (e) {
      console.warn("无法清除滚动位置", el, e);
    }
  });

  // 2️⃣ 等待页面稳定后开始动画
  const waitForTop = () => {
    const stillScrolling = allScrollTargets.some((el) => {
      if (el === window) return window.scrollY > 2;
      return el.scrollTop > 2;
    });

    if (stillScrolling) {
      requestAnimationFrame(waitForTop);
      return;
    }

    // === 动画执行 ===
    const distance = direction === "left" ? "-100%" : "100%";
    const rotate = direction === "left" ? "-12deg" : "12deg";

    container.style.transition = "transform 0.8s ease, opacity 0.8s ease";
    container.style.transformOrigin =
      direction === "left" ? "left center" : "right center";

    container.style.transform = `
      perspective(1200px)
      translateX(${distance})
      rotateY(${rotate})
    `;
    container.style.opacity = "0";

    setTimeout(() => {
      container.innerHTML = "";
      container.style.transition = "";
      container.style.transform = "";
      container.style.opacity = "1";
      container.style.transformOrigin = "";

      if (onDone) onDone();
    }, 800);
  };

  waitForTop();
}
