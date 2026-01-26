import { onRegisterClick } from "./onRegisterClick.js";
import { onRegisteredClick } from "./onRegisteredClick.js";

export function onHomeClick(container, targetSection = "hero") {
  console.log("[nav] home clicked", container);

  // 清空内容区
  container.innerHTML = "";

  /* =========================
     Hero Section
  ========================= */
  const hero = document.createElement("section");
  hero.id = "onHomeClick";

  Object.assign(hero.style, {
    width: "100%",
    height: "100vh",
    backgroundImage:
      "url('https://utbabuddha.com/media_file/NAS/UTBA/event_photo/EVT_20250908_006/1000160820.jpg')",
    backgroundSize: "cover",
    backgroundPosition: "center center",
    backgroundRepeat: "no-repeat",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    position: "relative",
    opacity: "0",
    transform: "translateY(20px)",
    transition: "opacity 1.2s ease, transform 1.2s ease",
  });

  // 触发 hero 动画
  requestAnimationFrame(() => {
    hero.style.opacity = "1";
    hero.style.transform = "translateY(0)";
  });

  // 遮罩
  const overlay = document.createElement("div");
  Object.assign(overlay.style, {
    position: "absolute",
    top: "0",
    left: "0",
    width: "100%",
    height: "100%",
    backgroundColor: "rgba(0, 0, 0, 0.35)",
  });

  /* =========================
     中央主题框
  ========================= */
  const contentBox = document.createElement("div");

  Object.assign(contentBox.style, {
    position: "relative",
    padding: "36px 44px",
    backgroundColor: "rgba(247, 243, 235, 0.72)",
    borderRadius: "18px",
    textAlign: "center",
    color: "#4a3b22",
    boxShadow: "0 16px 48px rgba(0,0,0,0.35)",
    lineHeight: "1.8",
    opacity: "0",
    transform: "translateY(16px)",
    transition: "opacity 1s ease 0.4s, transform 1s ease 0.4s",
  });

  requestAnimationFrame(() => {
    contentBox.style.opacity = "1";
    contentBox.style.transform = "translateY(0)";
  });

  const title = document.createElement("div");
  title.textContent = "2026 盂兰盆法会";
  Object.assign(title.style, {
    fontSize: "30px",
    fontWeight: "600",
    letterSpacing: "2px",
    marginBottom: "14px",
  });

  const org = document.createElement("div");
  org.textContent = "地南佛学会";
  Object.assign(org.style, {
    fontSize: "18px",
    marginBottom: "12px",
  });

  const desc = document.createElement("div");
  desc.textContent = "超度亡灵 · 怨亲债主";
  Object.assign(desc.style, {
    fontSize: "16px",
    opacity: "0.85",
  });

  contentBox.appendChild(title);
  contentBox.appendChild(org);
  contentBox.appendChild(desc);

  hero.appendChild(overlay);
  hero.appendChild(contentBox);

  /* =========================
     下方 Section
  ========================= */
  const section = document.createElement("section");
  section.id = "register";

  Object.assign(section.style, {
    height: "100vh",
    width: "100%",
    /* ✅ 新增背景图 */
    backgroundImage: "url('/static/images/bg/buddha_bg.svg')",
    backgroundSize: "cover",
    backgroundPosition: "center center",
    backgroundRepeat: "no-repeat",
    display: "flex",
    alignItems: "center",
    justifyContent: "column",
    position: "relative",
    transform: "translateY(20px)",
  });

  /* =========================
   Logo 外层包裹
========================= */
  const contentWrapper = document.createElement("div");
  Object.assign(contentWrapper.style, {
    width: "100%",
    maxWidth: "480px",
    margin: "0 auto",
    padding: "20px",
    textAlign: "center",
    position: "relative",
    zIndex: "2",
  });

  /* ✅ LOGO */
  const logoWrapper = document.createElement("div");
  Object.assign(logoWrapper.style, {
    marginBottom: "20px",
  });

  const logo = document.createElement("img");
  logo.src = "/static/images/logo/logo.png";
  logo.alt = "UTBA Buddha Logo";
  Object.assign(logo.style, {
    width: "180px",
    maxWidth: "80%",
    opacity: "0",
    transform: "translateY(-20px) scale(0.95)",
    transition: "all 1.2s ease",
  });
  logoWrapper.appendChild(logo);

  /* ✅ 标题 */
  const sectionTitle = document.createElement("h2");
  sectionTitle.textContent = "法会缘起";
  Object.assign(sectionTitle.style, {
    fontSize: "24px",
    marginBottom: "16px",
    opacity: "0",
    transform: "translateY(10px)",
    transition: "all 1s ease 0.2s",
  });

  /* ✅ 简介文字 */
  const sectionText = document.createElement("p");
  sectionText.textContent =
    "盂兰盆法会乃佛门孝道之行，以慈悲之心，普度幽冥，化解冤结，增长福慧。";
  Object.assign(sectionText.style, {
    fontSize: "15px",
    lineHeight: "1.7",
    marginBottom: "24px",
    color: "#5a4a30",
    opacity: "0",
    transform: "translateY(10px)",
    transition: "all 1s ease 0.4s",
  });

  /* ✅ 按钮组 */
  const btnGroup = document.createElement("div");
  Object.assign(btnGroup.style, {
    display: "flex",
    justifyContent: "center",
    gap: "20px",
    flexWrap: "wrap",
  });

  function createBigButton(text, onClick) {
    const btn = document.createElement("div");
    btn.textContent = text;

    Object.assign(btn.style, {
      padding: "16px 32px",
      fontSize: "16px",
      borderRadius: "36px",
      backgroundColor: "#8b6f3d",
      color: "#fff",
      cursor: "pointer",
      letterSpacing: "1px",
      transition: "all 0.3s ease",
      boxShadow: "0 10px 24px rgba(0,0,0,0.25)",
    });

    btn.onclick = () => onClick(container);

    btn.onmouseenter = () => {
      Object.assign(btn.style, {
        transform: "translateY(-4px)",
        boxShadow: "0 16px 32px rgba(0,0,0,0.3)",
        backgroundColor: "#7a6136",
      });
    };

    btn.onmouseleave = () => {
      Object.assign(btn.style, {
        transform: "translateY(0)",
        boxShadow: "0 10px 24px rgba(0,0,0,0.25)",
        backgroundColor: "#8b6f3d",
      });
    };

    return btn;
  }

  btnGroup.appendChild(createBigButton("我曾经注册", onRegisteredClick));
  btnGroup.appendChild(createBigButton("我想注册", onRegisterClick));

  /* ✅ 挂载进内容容器 */
  contentWrapper.appendChild(logoWrapper);
  contentWrapper.appendChild(logo);
  contentWrapper.appendChild(sectionTitle);
  contentWrapper.appendChild(sectionText);
  contentWrapper.appendChild(btnGroup);

  /* ✅ 最终挂载进 section */
  section.appendChild(contentWrapper);

  /* ✅ 动画触发 */
  requestAnimationFrame(() => {
    logo.style.opacity = "1";
    logo.style.transform = "translateY(0) scale(1)";

    sectionTitle.style.opacity = "1";
    sectionTitle.style.transform = "translateY(0)";

    sectionText.style.opacity = "1";
    sectionText.style.transform = "translateY(0)";
  });

  /* =========================
     挂载
  ========================= */
  container.appendChild(hero);
  container.appendChild(section);
  /* =========================
   根据 section 滚动定位
========================= */
  requestAnimationFrame(() => {
    const targetId = targetSection === "register" ? "register" : "hero";
    const target = container.querySelector(`#${targetId}`);

    if (target) {
      target.scrollIntoView({
        behavior: "smooth",
        block: "start",
      });
    }
  });
}
