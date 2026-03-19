const Oe="fahui_guest_customers",Te="fahui_guest_verified_tokens";function Ae(s,e){try{const t=window.localStorage.getItem(s);return t?JSON.parse(t):e}catch{return e}}function Be(s,e){window.localStorage.setItem(s,JSON.stringify(e))}function le(){const s=Ae(Oe,[]);return Array.isArray(s)?s:[]}function We(s){Be(Oe,s)}function Ce(){const s=Ae(Te,{});return s&&typeof s=="object"?s:{}}function ze(s){Be(Te,s)}function te(){return le()}function Xe(s){return le().some(e=>e.phone===s)}function Ge(s){const e=le();return e.some(t=>t.phone===s.phone)?!1:(e.push(s),We(e),!0)}function _e(s){const e=`verified_${s}_${Date.now()}_${Math.random().toString(36).slice(2,10)}`,t=Ce();return t[s]=e,ze(t),e}function Re(s){return Ce()[s]||""}function Qe(s){return!!Re(s)}const Ze="/api/fahui_router/new_customer";function et(s){let e={loading:!1,error:"",success:""};function t(){const r=te();s.innerHTML=`
      <section class="guest-home">
        <header class="guest-home-head">
          <h2 class="section-title">游客登记</h2>
          <p class="section-subtitle">先登记功德主资料，再用手机号继续后续验证流程。</p>
        </header>

        <div class="guest-home-grid">
          <form class="guest-form" data-role="guest-form">
            <label class="field">
              <span>功德主姓名</span>
              <input name="customer_name" type="text" placeholder="请输入姓名" />
            </label>

            <label class="field">
              <span>联络手机号码</span>
              <input name="phone" type="tel" placeholder="必填" required />
            </label>

            <label class="field">
              <span>登记名称</span>
              <input name="name" type="text" placeholder="可与功德主姓名相同" />
            </label>

            ${e.error?`<div class="form-error">${e.error}</div>`:""}
            ${e.success?`<div class="form-success">${e.success}</div>`:""}

            <button class="submit-btn" type="submit" ${e.loading?"disabled":""}>
              ${e.loading?"提交中...":"创建登记"}
            </button>
          </form>

          <section class="guest-local-panel">
            <h3>本机已登记手机号</h3>
            <div class="local-list">
              ${r.length?r.map(i=>`
                          <article class="local-card">
                            <div class="local-name">${i.customer_name||i.name||"未命名"}</div>
                            <div class="local-meta">${i.phone}</div>
                            <div class="local-meta">订单 #${i.order_id}</div>
                          </article>
                        `).join(""):'<div class="state-banner">本机还没有保存的游客登记</div>'}
            </div>
          </section>
        </div>
      </section>
    `,n()}function n(){const r=s.querySelector('[data-role="guest-form"]');r&&r.addEventListener("submit",async i=>{i.preventDefault(),e.error="",e.success="";const a=new FormData(r),l=String(a.get("customer_name")||"").trim(),o=String(a.get("name")||l).trim(),_=String(a.get("phone")||"").trim();if(!_){e.error="手机号码必填",t();return}if(Xe(_)){e.error="这个浏览器已经保存过这个手机号码，不能重复登记",t();return}e.loading=!0,t();try{const v=await fetch(Ze,{method:"POST",headers:{"Content-Type":"application/json"},credentials:"include",body:JSON.stringify({name:o,customer_name:l||o,phone:_})}),y=await v.json().catch(()=>({}));if(!v.ok||(y==null?void 0:y.success)!==!0)throw new Error((y==null?void 0:y.message)||(y==null?void 0:y.error)||"创建失败");const O=y.order||{};Ge({customer_name:O.customer_name||l||o,name:O.name||o,phone:_,order_id:O.id}),e.loading=!1,e.success=y!=null&&y.duplicated?"后台已有同名登记，已把订单和手机号保存到本机":"登记成功，后台已推送实时更新，手机号已保存到本机",t()}catch(v){e.loading=!1,e.error=v.message||"提交失败",t()}})}return t(),()=>{s.innerHTML=""}}const tt="/api/twilio/send_otp",st="/api/twilio/verify",nt="/api/fahui_router/get_orders_by_phone",G=10;function rt(s){let e={selectedPhone:"",manualPhone:"",otpCode:"",loading:!1,message:"",error:"",listLoading:!1,phoneOrders:[],pagedOrdersByYear:{},pagesByYear:{}};function t(){return te().find(g=>g.phone===e.selectedPhone)||null}function n(){return(e.selectedPhone||e.manualPhone||"").trim()}function r(g){const p=String(g||"").match(/^(\d{4})/);return p?p[1]:"未分类"}function i(g){const p={};for(const m of g){const u=r(m.version);p[u]||(p[u]=[]),p[u].push(m)}return Object.keys(p).sort((m,u)=>Number(u)-Number(m)).map(m=>({year:m,items:p[m]}))}function a(g,p){const u=((e.pagesByYear[g]||1)-1)*G;return p.slice(u,u+G)}function l(g){window.dispatchEvent(new CustomEvent("fahui:navigate",{detail:{page:"fahui_detail",params:{orderId:g,returnPage:"search"}}}))}function o(){const g=te();t();const p=n(),m=p?Re(p):"",u=p?Qe(p):!1;s.innerHTML=`
      <section class="guest-home">
        <header class="guest-home-head">
          <h2 class="section-title">查找订单</h2>
          <p class="section-subtitle">查看订单前，需要先通过手机验证码认证。</p>
        </header>

        <div class="search-layout">
          <section class="guest-local-panel">
            <h3>本机手机号</h3>
            <div class="local-list">
              ${g.length?g.map(f=>`
                          <button
                            class="saved-phone-card ${e.selectedPhone===f.phone?"active":""}"
                            type="button"
                            data-action="select-phone"
                            data-phone="${f.phone}"
                          >
                            <div class="local-name">${f.customer_name||f.name||"未命名"}</div>
                            <div class="local-meta">${f.phone}</div>
                            <div class="local-meta">订单 #${f.order_id}</div>
                          </button>
                        `).join(""):'<div class="state-banner">请先到首页完成登记</div>'}
            </div>

            <form class="search-form" data-action="manual-phone-form">
              <input
                class="search-input"
                name="phone"
                placeholder="或直接输入手机号码"
                value="${e.manualPhone}"
              />
              <button class="mode-switch secondary" type="submit">使用手机号</button>
            </form>
          </section>

          <section class="guest-local-panel">
            <h3>手机号认证</h3>
            ${p?`
                  <div class="verify-summary">
                    <div class="local-meta">当前手机号：${p}</div>
                    <div class="local-meta">本地 token：${m||"未认证"}</div>
                  </div>

                  <div class="verify-actions">
                    <button class="mode-switch secondary" type="button" data-action="send-otp">
                      发送验证码
                    </button>
                  </div>

                  ${u?`
                        <div class="verify-actions">
                          <button
                            class="mode-switch secondary"
                            type="button"
                            data-action="load-detail"
                          >
                            查看订单
                          </button>
                        </div>
                      `:`
                        <form class="search-form" data-action="verify-form">
                          <input
                            class="search-input"
                            name="otp"
                            placeholder="输入短信验证码"
                            value="${e.otpCode}"
                          />
                          <button class="mode-switch secondary" type="submit">验证</button>
                          <button
                            class="mode-switch secondary"
                            type="button"
                            data-action="load-detail"
                            disabled
                          >
                            查看订单
                          </button>
                        </form>
                      `}
                `:'<div class="state-banner">请选择或输入一个手机号</div>'}

            ${e.message?`<div class="form-success">${e.message}</div>`:""}
            ${e.error?`<div class="form-error">${e.error}</div>`:""}
          </section>
        </div>

        ${e.listLoading?'<div class="state-banner">手机号订单加载中...</div>':e.phoneOrders.length?`
                <section class="detail-panel">
                  <div class="detail-row"><strong>手机号</strong><span>${p||"-"}</span></div>
                  <div class="detail-row"><strong>关联订单</strong><span>${e.phoneOrders.length} 笔</span></div>
                </section>

                ${i(e.phoneOrders).map(f=>{const w=Math.max(1,Math.ceil(f.items.length/G)),I=a(f.year,f.items);return`
                      <section class="detail-panel">
                        <div class="detail-head">
                          <h3 class="section-title">${f.year} 年</h3>
                          <span class="local-meta">${f.items.length} 笔</span>
                        </div>

                        <div class="local-list">
                          ${I.map(x=>`
                                <button
                                  class="saved-phone-card"
                                  type="button"
                                  data-action="open-order-detail"
                                  data-order-id="${x.id}"
                                >
                                  <div class="local-name">${x.customer_name||x.name||"未命名"}</div>
                                  <div class="local-meta">订单 #${x.id}</div>
                                  <div class="local-meta">${x.created_at||"-"}</div>
                                  <div class="local-meta">${x.status||"-"}</div>
                                </button>
                              `).join("")}
                        </div>

                        ${w>1?`
                              <div class="pagination-bar">
                                <button
                                  class="mode-switch secondary"
                                  type="button"
                                  data-action="change-year-page"
                                  data-year="${f.year}"
                                  data-page="${Math.max(1,(e.pagesByYear[f.year]||1)-1)}"
                                  ${(e.pagesByYear[f.year]||1)<=1?"disabled":""}
                                >
                                  上一页
                                </button>
                                <span class="local-meta">第 ${e.pagesByYear[f.year]||1} / ${w} 页</span>
                                <button
                                  class="mode-switch secondary"
                                  type="button"
                                  data-action="change-year-page"
                                  data-year="${f.year}"
                                  data-page="${Math.min(w,(e.pagesByYear[f.year]||1)+1)}"
                                  ${(e.pagesByYear[f.year]||1)>=w?"disabled":""}
                                >
                                  下一页
                                </button>
                              </div>
                            `:""}
                      </section>
                    `}).join("")}
              `:""}
      </section>
    `,O()}async function _(){const g=t(),p=n();if(!p){e.error="请先选择或输入手机号",o();return}e.loading=!0,e.error="",e.message="",o();try{const m=await fetch(tt,{method:"POST",credentials:"include",headers:{"Content-Type":"application/json"},body:JSON.stringify(g?{order_id:g.order_id}:{phone:p})}),u=await m.json().catch(()=>({}));if(!m.ok||!["success","cookie_true","login_bypass"].includes(u==null?void 0:u.status))throw new Error((u==null?void 0:u.message)||"验证码发送失败");if((u==null?void 0:u.status)==="login_bypass"){_e(p),e.loading=!1,e.otpCode="",e.message="当前已登录，已直接生成本地认证 token",o();return}e.loading=!1,e.message=u.message||"验证码已发送",o()}catch(m){e.loading=!1,e.error=m.message||"验证码发送失败",o()}}async function v(g){const p=n();if(!p){e.error="请先选择或输入手机号",o();return}if(!g){e.error="请输入验证码",o();return}e.loading=!0,e.error="",e.message="",o();try{const m=await fetch(st,{method:"POST",credentials:"include",headers:{"Content-Type":"application/json"},body:JSON.stringify({otp:g,phone:p})}),u=await m.json().catch(()=>({}));if(!m.ok||(u==null?void 0:u.status)!=="success")throw new Error((u==null?void 0:u.message)||"验证码验证失败");_e(p),e.loading=!1,e.message="验证成功，本地认证 token 已保存",e.otpCode="",o()}catch(m){e.loading=!1,e.error=m.message||"验证码验证失败",o()}}async function y(){var p;const g=n();if(!g){e.error="请先选择或输入手机号",o();return}e.listLoading=!0,e.phoneOrders=[],e.pagedOrdersByYear={},e.pagesByYear={},e.error="",e.message="",o();try{const m=await fetch(`${nt}?phone=${encodeURIComponent(g)}`,{credentials:"include"}),u=await m.json().catch(()=>({}));if(!m.ok||(u==null?void 0:u.status)!=="success")throw new Error((u==null?void 0:u.message)||"查看订单失败，请重新验证手机号");const f=((p=u==null?void 0:u.data)==null?void 0:p.items)||[];e.listLoading=!1,e.phoneOrders=f,e.pagesByYear=i(f).reduce((w,I)=>(w[I.year]=1,w),{}),e.message=f.length?"手机号关联订单已同步":"这个手机号下还没有订单",o()}catch(m){e.listLoading=!1,e.phoneOrders=[],e.pagesByYear={},e.error=m.message||"查看订单失败",o()}}function O(){s.querySelectorAll('[data-action="select-phone"]').forEach(f=>{f.addEventListener("click",()=>{e.selectedPhone=f.dataset.phone||"",e.manualPhone="",e.phoneOrders=[],e.pagesByYear={},e.message="",e.error="",o()})});const g=s.querySelector('[data-action="manual-phone-form"]');g&&g.addEventListener("submit",f=>{f.preventDefault();const w=new FormData(g);e.manualPhone=String(w.get("phone")||"").trim(),e.selectedPhone="",e.phoneOrders=[],e.pagesByYear={},e.message="",e.error=e.manualPhone?"":"请输入手机号码",o()});const p=s.querySelector('[data-action="send-otp"]');p&&p.addEventListener("click",_);const m=s.querySelector('[data-action="verify-form"]');m&&m.addEventListener("submit",f=>{f.preventDefault();const w=new FormData(m);e.otpCode=String(w.get("otp")||"").trim(),v(e.otpCode)});const u=s.querySelector('[data-action="load-detail"]');u&&u.addEventListener("click",y),s.querySelectorAll('[data-action="open-order-detail"]').forEach(f=>{f.addEventListener("click",()=>{const w=Number(f.dataset.orderId);l(w)})}),s.querySelectorAll('[data-action="change-year-page"]').forEach(f=>{f.addEventListener("click",()=>{const w=String(f.dataset.year||""),I=Number(f.dataset.page||1);e.pagesByYear={...e.pagesByYear,[w]:I},o()})})}return o(),()=>{s.innerHTML=""}}const C=Object.create(null);C.open="0";C.close="1";C.ping="2";C.pong="3";C.message="4";C.upgrade="5";C.noop="6";const V=Object.create(null);Object.keys(C).forEach(s=>{V[C[s]]=s});const se={type:"error",data:"parser error"},Le=typeof Blob=="function"||typeof Blob<"u"&&Object.prototype.toString.call(Blob)==="[object BlobConstructor]",Ne=typeof ArrayBuffer=="function",$e=s=>typeof ArrayBuffer.isView=="function"?ArrayBuffer.isView(s):s&&s.buffer instanceof ArrayBuffer,he=({type:s,data:e},t,n)=>Le&&e instanceof Blob?t?n(e):ve(e,n):Ne&&(e instanceof ArrayBuffer||$e(e))?t?n(e):ve(new Blob([e]),n):n(C[s]+(e||"")),ve=(s,e)=>{const t=new FileReader;return t.onload=function(){const n=t.result.split(",")[1];e("b"+(n||""))},t.readAsDataURL(s)};function be(s){return s instanceof Uint8Array?s:s instanceof ArrayBuffer?new Uint8Array(s):new Uint8Array(s.buffer,s.byteOffset,s.byteLength)}let Q;function it(s,e){if(Le&&s.data instanceof Blob)return s.data.arrayBuffer().then(be).then(e);if(Ne&&(s.data instanceof ArrayBuffer||$e(s.data)))return e(be(s.data));he(s,!1,t=>{Q||(Q=new TextEncoder),e(Q.encode(t))})}const we="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/",Y=typeof Uint8Array>"u"?[]:new Uint8Array(256);for(let s=0;s<we.length;s++)Y[we.charCodeAt(s)]=s;const ot=s=>{let e=s.length*.75,t=s.length,n,r=0,i,a,l,o;s[s.length-1]==="="&&(e--,s[s.length-2]==="="&&e--);const _=new ArrayBuffer(e),v=new Uint8Array(_);for(n=0;n<t;n+=4)i=Y[s.charCodeAt(n)],a=Y[s.charCodeAt(n+1)],l=Y[s.charCodeAt(n+2)],o=Y[s.charCodeAt(n+3)],v[r++]=i<<2|a>>4,v[r++]=(a&15)<<4|l>>2,v[r++]=(l&3)<<6|o&63;return _},at=typeof ArrayBuffer=="function",ue=(s,e)=>{if(typeof s!="string")return{type:"message",data:Pe(s,e)};const t=s.charAt(0);return t==="b"?{type:"message",data:ct(s.substring(1),e)}:V[t]?s.length>1?{type:V[t],data:s.substring(1)}:{type:V[t]}:se},ct=(s,e)=>{if(at){const t=ot(s);return Pe(t,e)}else return{base64:!0,data:s}},Pe=(s,e)=>{switch(e){case"blob":return s instanceof Blob?s:new Blob([s]);case"arraybuffer":default:return s instanceof ArrayBuffer?s:s.buffer}},xe="",lt=(s,e)=>{const t=s.length,n=new Array(t);let r=0;s.forEach((i,a)=>{he(i,!1,l=>{n[a]=l,++r===t&&e(n.join(xe))})})},ht=(s,e)=>{const t=s.split(xe),n=[];for(let r=0;r<t.length;r++){const i=ue(t[r],e);if(n.push(i),i.type==="error")break}return n};function ut(){return new TransformStream({transform(s,e){it(s,t=>{const n=t.length;let r;if(n<126)r=new Uint8Array(1),new DataView(r.buffer).setUint8(0,n);else if(n<65536){r=new Uint8Array(3);const i=new DataView(r.buffer);i.setUint8(0,126),i.setUint16(1,n)}else{r=new Uint8Array(9);const i=new DataView(r.buffer);i.setUint8(0,127),i.setBigUint64(1,BigInt(n))}s.data&&typeof s.data!="string"&&(r[0]|=128),e.enqueue(r),e.enqueue(t)})}})}let Z;function M(s){return s.reduce((e,t)=>e+t.length,0)}function F(s,e){if(s[0].length===e)return s.shift();const t=new Uint8Array(e);let n=0;for(let r=0;r<e;r++)t[r]=s[0][n++],n===s[0].length&&(s.shift(),n=0);return s.length&&n<s[0].length&&(s[0]=s[0].slice(n)),t}function dt(s,e){Z||(Z=new TextDecoder);const t=[];let n=0,r=-1,i=!1;return new TransformStream({transform(a,l){for(t.push(a);;){if(n===0){if(M(t)<1)break;const o=F(t,1);i=(o[0]&128)===128,r=o[0]&127,r<126?n=3:r===126?n=1:n=2}else if(n===1){if(M(t)<2)break;const o=F(t,2);r=new DataView(o.buffer,o.byteOffset,o.length).getUint16(0),n=3}else if(n===2){if(M(t)<8)break;const o=F(t,8),_=new DataView(o.buffer,o.byteOffset,o.length),v=_.getUint32(0);if(v>Math.pow(2,21)-1){l.enqueue(se);break}r=v*Math.pow(2,32)+_.getUint32(4),n=3}else{if(M(t)<r)break;const o=F(t,r);l.enqueue(ue(i?o:Z.decode(o),e)),n=0}if(r===0||r>s){l.enqueue(se);break}}}})}const qe=4;function b(s){if(s)return ft(s)}function ft(s){for(var e in b.prototype)s[e]=b.prototype[e];return s}b.prototype.on=b.prototype.addEventListener=function(s,e){return this._callbacks=this._callbacks||{},(this._callbacks["$"+s]=this._callbacks["$"+s]||[]).push(e),this};b.prototype.once=function(s,e){function t(){this.off(s,t),e.apply(this,arguments)}return t.fn=e,this.on(s,t),this};b.prototype.off=b.prototype.removeListener=b.prototype.removeAllListeners=b.prototype.removeEventListener=function(s,e){if(this._callbacks=this._callbacks||{},arguments.length==0)return this._callbacks={},this;var t=this._callbacks["$"+s];if(!t)return this;if(arguments.length==1)return delete this._callbacks["$"+s],this;for(var n,r=0;r<t.length;r++)if(n=t[r],n===e||n.fn===e){t.splice(r,1);break}return t.length===0&&delete this._callbacks["$"+s],this};b.prototype.emit=function(s){this._callbacks=this._callbacks||{};for(var e=new Array(arguments.length-1),t=this._callbacks["$"+s],n=1;n<arguments.length;n++)e[n-1]=arguments[n];if(t){t=t.slice(0);for(var n=0,r=t.length;n<r;++n)t[n].apply(this,e)}return this};b.prototype.emitReserved=b.prototype.emit;b.prototype.listeners=function(s){return this._callbacks=this._callbacks||{},this._callbacks["$"+s]||[]};b.prototype.hasListeners=function(s){return!!this.listeners(s).length};const W=typeof Promise=="function"&&typeof Promise.resolve=="function"?e=>Promise.resolve().then(e):(e,t)=>t(e,0),S=typeof self<"u"?self:typeof window<"u"?window:Function("return this")(),pt="arraybuffer";function Ie(s,...e){return e.reduce((t,n)=>(s.hasOwnProperty(n)&&(t[n]=s[n]),t),{})}const mt=S.setTimeout,gt=S.clearTimeout;function z(s,e){e.useNativeTimers?(s.setTimeoutFn=mt.bind(S),s.clearTimeoutFn=gt.bind(S)):(s.setTimeoutFn=S.setTimeout.bind(S),s.clearTimeoutFn=S.clearTimeout.bind(S))}const yt=1.33;function _t(s){return typeof s=="string"?vt(s):Math.ceil((s.byteLength||s.size)*yt)}function vt(s){let e=0,t=0;for(let n=0,r=s.length;n<r;n++)e=s.charCodeAt(n),e<128?t+=1:e<2048?t+=2:e<55296||e>=57344?t+=3:(n++,t+=4);return t}function De(){return Date.now().toString(36).substring(3)+Math.random().toString(36).substring(2,5)}function bt(s){let e="";for(let t in s)s.hasOwnProperty(t)&&(e.length&&(e+="&"),e+=encodeURIComponent(t)+"="+encodeURIComponent(s[t]));return e}function wt(s){let e={},t=s.split("&");for(let n=0,r=t.length;n<r;n++){let i=t[n].split("=");e[decodeURIComponent(i[0])]=decodeURIComponent(i[1])}return e}class Et extends Error{constructor(e,t,n){super(e),this.description=t,this.context=n,this.type="TransportError"}}class de extends b{constructor(e){super(),this.writable=!1,z(this,e),this.opts=e,this.query=e.query,this.socket=e.socket,this.supportsBinary=!e.forceBase64}onError(e,t,n){return super.emitReserved("error",new Et(e,t,n)),this}open(){return this.readyState="opening",this.doOpen(),this}close(){return(this.readyState==="opening"||this.readyState==="open")&&(this.doClose(),this.onClose()),this}send(e){this.readyState==="open"&&this.write(e)}onOpen(){this.readyState="open",this.writable=!0,super.emitReserved("open")}onData(e){const t=ue(e,this.socket.binaryType);this.onPacket(t)}onPacket(e){super.emitReserved("packet",e)}onClose(e){this.readyState="closed",super.emitReserved("close",e)}pause(e){}createUri(e,t={}){return e+"://"+this._hostname()+this._port()+this.opts.path+this._query(t)}_hostname(){const e=this.opts.hostname;return e.indexOf(":")===-1?e:"["+e+"]"}_port(){return this.opts.port&&(this.opts.secure&&Number(this.opts.port)!==443||!this.opts.secure&&Number(this.opts.port)!==80)?":"+this.opts.port:""}_query(e){const t=bt(e);return t.length?"?"+t:""}}class kt extends de{constructor(){super(...arguments),this._polling=!1}get name(){return"polling"}doOpen(){this._poll()}pause(e){this.readyState="pausing";const t=()=>{this.readyState="paused",e()};if(this._polling||!this.writable){let n=0;this._polling&&(n++,this.once("pollComplete",function(){--n||t()})),this.writable||(n++,this.once("drain",function(){--n||t()}))}else t()}_poll(){this._polling=!0,this.doPoll(),this.emitReserved("poll")}onData(e){const t=n=>{if(this.readyState==="opening"&&n.type==="open"&&this.onOpen(),n.type==="close")return this.onClose({description:"transport closed by the server"}),!1;this.onPacket(n)};ht(e,this.socket.binaryType).forEach(t),this.readyState!=="closed"&&(this._polling=!1,this.emitReserved("pollComplete"),this.readyState==="open"&&this._poll())}doClose(){const e=()=>{this.write([{type:"close"}])};this.readyState==="open"?e():this.once("open",e)}write(e){this.writable=!1,lt(e,t=>{this.doWrite(t,()=>{this.writable=!0,this.emitReserved("drain")})})}uri(){const e=this.opts.secure?"https":"http",t=this.query||{};return this.opts.timestampRequests!==!1&&(t[this.opts.timestampParam]=De()),!this.supportsBinary&&!t.sid&&(t.b64=1),this.createUri(e,t)}}let Ye=!1;try{Ye=typeof XMLHttpRequest<"u"&&"withCredentials"in new XMLHttpRequest}catch{}const St=Ye;function Ot(){}class Tt extends kt{constructor(e){if(super(e),typeof location<"u"){const t=location.protocol==="https:";let n=location.port;n||(n=t?"443":"80"),this.xd=typeof location<"u"&&e.hostname!==location.hostname||n!==e.port}}doWrite(e,t){const n=this.request({method:"POST",data:e});n.on("success",t),n.on("error",(r,i)=>{this.onError("xhr post error",r,i)})}doPoll(){const e=this.request();e.on("data",this.onData.bind(this)),e.on("error",(t,n)=>{this.onError("xhr poll error",t,n)}),this.pollXhr=e}}class B extends b{constructor(e,t,n){super(),this.createRequest=e,z(this,n),this._opts=n,this._method=n.method||"GET",this._uri=t,this._data=n.data!==void 0?n.data:null,this._create()}_create(){var e;const t=Ie(this._opts,"agent","pfx","key","passphrase","cert","ca","ciphers","rejectUnauthorized","autoUnref");t.xdomain=!!this._opts.xd;const n=this._xhr=this.createRequest(t);try{n.open(this._method,this._uri,!0);try{if(this._opts.extraHeaders){n.setDisableHeaderCheck&&n.setDisableHeaderCheck(!0);for(let r in this._opts.extraHeaders)this._opts.extraHeaders.hasOwnProperty(r)&&n.setRequestHeader(r,this._opts.extraHeaders[r])}}catch{}if(this._method==="POST")try{n.setRequestHeader("Content-type","text/plain;charset=UTF-8")}catch{}try{n.setRequestHeader("Accept","*/*")}catch{}(e=this._opts.cookieJar)===null||e===void 0||e.addCookies(n),"withCredentials"in n&&(n.withCredentials=this._opts.withCredentials),this._opts.requestTimeout&&(n.timeout=this._opts.requestTimeout),n.onreadystatechange=()=>{var r;n.readyState===3&&((r=this._opts.cookieJar)===null||r===void 0||r.parseCookies(n.getResponseHeader("set-cookie"))),n.readyState===4&&(n.status===200||n.status===1223?this._onLoad():this.setTimeoutFn(()=>{this._onError(typeof n.status=="number"?n.status:0)},0))},n.send(this._data)}catch(r){this.setTimeoutFn(()=>{this._onError(r)},0);return}typeof document<"u"&&(this._index=B.requestsCount++,B.requests[this._index]=this)}_onError(e){this.emitReserved("error",e,this._xhr),this._cleanup(!0)}_cleanup(e){if(!(typeof this._xhr>"u"||this._xhr===null)){if(this._xhr.onreadystatechange=Ot,e)try{this._xhr.abort()}catch{}typeof document<"u"&&delete B.requests[this._index],this._xhr=null}}_onLoad(){const e=this._xhr.responseText;e!==null&&(this.emitReserved("data",e),this.emitReserved("success"),this._cleanup())}abort(){this._cleanup()}}B.requestsCount=0;B.requests={};if(typeof document<"u"){if(typeof attachEvent=="function")attachEvent("onunload",Ee);else if(typeof addEventListener=="function"){const s="onpagehide"in S?"pagehide":"unload";addEventListener(s,Ee,!1)}}function Ee(){for(let s in B.requests)B.requests.hasOwnProperty(s)&&B.requests[s].abort()}const At=(function(){const s=Me({xdomain:!1});return s&&s.responseType!==null})();class Bt extends Tt{constructor(e){super(e);const t=e&&e.forceBase64;this.supportsBinary=At&&!t}request(e={}){return Object.assign(e,{xd:this.xd},this.opts),new B(Me,this.uri(),e)}}function Me(s){const e=s.xdomain;try{if(typeof XMLHttpRequest<"u"&&(!e||St))return new XMLHttpRequest}catch{}if(!e)try{return new S[["Active"].concat("Object").join("X")]("Microsoft.XMLHTTP")}catch{}}const Fe=typeof navigator<"u"&&typeof navigator.product=="string"&&navigator.product.toLowerCase()==="reactnative";class Ct extends de{get name(){return"websocket"}doOpen(){const e=this.uri(),t=this.opts.protocols,n=Fe?{}:Ie(this.opts,"agent","perMessageDeflate","pfx","key","passphrase","cert","ca","ciphers","rejectUnauthorized","localAddress","protocolVersion","origin","maxPayload","family","checkServerIdentity");this.opts.extraHeaders&&(n.headers=this.opts.extraHeaders);try{this.ws=this.createSocket(e,t,n)}catch(r){return this.emitReserved("error",r)}this.ws.binaryType=this.socket.binaryType,this.addEventListeners()}addEventListeners(){this.ws.onopen=()=>{this.opts.autoUnref&&this.ws._socket.unref(),this.onOpen()},this.ws.onclose=e=>this.onClose({description:"websocket connection closed",context:e}),this.ws.onmessage=e=>this.onData(e.data),this.ws.onerror=e=>this.onError("websocket error",e)}write(e){this.writable=!1;for(let t=0;t<e.length;t++){const n=e[t],r=t===e.length-1;he(n,this.supportsBinary,i=>{try{this.doWrite(n,i)}catch{}r&&W(()=>{this.writable=!0,this.emitReserved("drain")},this.setTimeoutFn)})}}doClose(){typeof this.ws<"u"&&(this.ws.onerror=()=>{},this.ws.close(),this.ws=null)}uri(){const e=this.opts.secure?"wss":"ws",t=this.query||{};return this.opts.timestampRequests&&(t[this.opts.timestampParam]=De()),this.supportsBinary||(t.b64=1),this.createUri(e,t)}}const ee=S.WebSocket||S.MozWebSocket;class Rt extends Ct{createSocket(e,t,n){return Fe?new ee(e,t,n):t?new ee(e,t):new ee(e)}doWrite(e,t){this.ws.send(t)}}class Lt extends de{get name(){return"webtransport"}doOpen(){try{this._transport=new WebTransport(this.createUri("https"),this.opts.transportOptions[this.name])}catch(e){return this.emitReserved("error",e)}this._transport.closed.then(()=>{this.onClose()}).catch(e=>{this.onError("webtransport error",e)}),this._transport.ready.then(()=>{this._transport.createBidirectionalStream().then(e=>{const t=dt(Number.MAX_SAFE_INTEGER,this.socket.binaryType),n=e.readable.pipeThrough(t).getReader(),r=ut();r.readable.pipeTo(e.writable),this._writer=r.writable.getWriter();const i=()=>{n.read().then(({done:l,value:o})=>{l||(this.onPacket(o),i())}).catch(l=>{})};i();const a={type:"open"};this.query.sid&&(a.data=`{"sid":"${this.query.sid}"}`),this._writer.write(a).then(()=>this.onOpen())})})}write(e){this.writable=!1;for(let t=0;t<e.length;t++){const n=e[t],r=t===e.length-1;this._writer.write(n).then(()=>{r&&W(()=>{this.writable=!0,this.emitReserved("drain")},this.setTimeoutFn)})}}doClose(){var e;(e=this._transport)===null||e===void 0||e.close()}}const Nt={websocket:Rt,webtransport:Lt,polling:Bt},$t=/^(?:(?![^:@\/?#]+:[^:@\/]*@)(http|https|ws|wss):\/\/)?((?:(([^:@\/?#]*)(?::([^:@\/?#]*))?)?@)?((?:[a-f0-9]{0,4}:){2,7}[a-f0-9]{0,4}|[^:\/?#]*)(?::(\d*))?)(((\/(?:[^?#](?![^?#\/]*\.[^?#\/.]+(?:[?#]|$)))*\/?)?([^?#\/]*))(?:\?([^#]*))?(?:#(.*))?)/,Pt=["source","protocol","authority","userInfo","user","password","host","port","relative","path","directory","file","query","anchor"];function ne(s){if(s.length>8e3)throw"URI too long";const e=s,t=s.indexOf("["),n=s.indexOf("]");t!=-1&&n!=-1&&(s=s.substring(0,t)+s.substring(t,n).replace(/:/g,";")+s.substring(n,s.length));let r=$t.exec(s||""),i={},a=14;for(;a--;)i[Pt[a]]=r[a]||"";return t!=-1&&n!=-1&&(i.source=e,i.host=i.host.substring(1,i.host.length-1).replace(/;/g,":"),i.authority=i.authority.replace("[","").replace("]","").replace(/;/g,":"),i.ipv6uri=!0),i.pathNames=xt(i,i.path),i.queryKey=qt(i,i.query),i}function xt(s,e){const t=/\/{2,9}/g,n=e.replace(t,"/").split("/");return(e.slice(0,1)=="/"||e.length===0)&&n.splice(0,1),e.slice(-1)=="/"&&n.splice(n.length-1,1),n}function qt(s,e){const t={};return e.replace(/(?:^|&)([^&=]*)=?([^&]*)/g,function(n,r,i){r&&(t[r]=i)}),t}const re=typeof addEventListener=="function"&&typeof removeEventListener=="function",H=[];re&&addEventListener("offline",()=>{H.forEach(s=>s())},!1);class $ extends b{constructor(e,t){if(super(),this.binaryType=pt,this.writeBuffer=[],this._prevBufferLen=0,this._pingInterval=-1,this._pingTimeout=-1,this._maxPayload=-1,this._pingTimeoutTime=1/0,e&&typeof e=="object"&&(t=e,e=null),e){const n=ne(e);t.hostname=n.host,t.secure=n.protocol==="https"||n.protocol==="wss",t.port=n.port,n.query&&(t.query=n.query)}else t.host&&(t.hostname=ne(t.host).host);z(this,t),this.secure=t.secure!=null?t.secure:typeof location<"u"&&location.protocol==="https:",t.hostname&&!t.port&&(t.port=this.secure?"443":"80"),this.hostname=t.hostname||(typeof location<"u"?location.hostname:"localhost"),this.port=t.port||(typeof location<"u"&&location.port?location.port:this.secure?"443":"80"),this.transports=[],this._transportsByName={},t.transports.forEach(n=>{const r=n.prototype.name;this.transports.push(r),this._transportsByName[r]=n}),this.opts=Object.assign({path:"/engine.io",agent:!1,withCredentials:!1,upgrade:!0,timestampParam:"t",rememberUpgrade:!1,addTrailingSlash:!0,rejectUnauthorized:!0,perMessageDeflate:{threshold:1024},transportOptions:{},closeOnBeforeunload:!1},t),this.opts.path=this.opts.path.replace(/\/$/,"")+(this.opts.addTrailingSlash?"/":""),typeof this.opts.query=="string"&&(this.opts.query=wt(this.opts.query)),re&&(this.opts.closeOnBeforeunload&&(this._beforeunloadEventListener=()=>{this.transport&&(this.transport.removeAllListeners(),this.transport.close())},addEventListener("beforeunload",this._beforeunloadEventListener,!1)),this.hostname!=="localhost"&&(this._offlineEventListener=()=>{this._onClose("transport close",{description:"network connection lost"})},H.push(this._offlineEventListener))),this.opts.withCredentials&&(this._cookieJar=void 0),this._open()}createTransport(e){const t=Object.assign({},this.opts.query);t.EIO=qe,t.transport=e,this.id&&(t.sid=this.id);const n=Object.assign({},this.opts,{query:t,socket:this,hostname:this.hostname,secure:this.secure,port:this.port},this.opts.transportOptions[e]);return new this._transportsByName[e](n)}_open(){if(this.transports.length===0){this.setTimeoutFn(()=>{this.emitReserved("error","No transports available")},0);return}const e=this.opts.rememberUpgrade&&$.priorWebsocketSuccess&&this.transports.indexOf("websocket")!==-1?"websocket":this.transports[0];this.readyState="opening";const t=this.createTransport(e);t.open(),this.setTransport(t)}setTransport(e){this.transport&&this.transport.removeAllListeners(),this.transport=e,e.on("drain",this._onDrain.bind(this)).on("packet",this._onPacket.bind(this)).on("error",this._onError.bind(this)).on("close",t=>this._onClose("transport close",t))}onOpen(){this.readyState="open",$.priorWebsocketSuccess=this.transport.name==="websocket",this.emitReserved("open"),this.flush()}_onPacket(e){if(this.readyState==="opening"||this.readyState==="open"||this.readyState==="closing")switch(this.emitReserved("packet",e),this.emitReserved("heartbeat"),e.type){case"open":this.onHandshake(JSON.parse(e.data));break;case"ping":this._sendPacket("pong"),this.emitReserved("ping"),this.emitReserved("pong"),this._resetPingTimeout();break;case"error":const t=new Error("server error");t.code=e.data,this._onError(t);break;case"message":this.emitReserved("data",e.data),this.emitReserved("message",e.data);break}}onHandshake(e){this.emitReserved("handshake",e),this.id=e.sid,this.transport.query.sid=e.sid,this._pingInterval=e.pingInterval,this._pingTimeout=e.pingTimeout,this._maxPayload=e.maxPayload,this.onOpen(),this.readyState!=="closed"&&this._resetPingTimeout()}_resetPingTimeout(){this.clearTimeoutFn(this._pingTimeoutTimer);const e=this._pingInterval+this._pingTimeout;this._pingTimeoutTime=Date.now()+e,this._pingTimeoutTimer=this.setTimeoutFn(()=>{this._onClose("ping timeout")},e),this.opts.autoUnref&&this._pingTimeoutTimer.unref()}_onDrain(){this.writeBuffer.splice(0,this._prevBufferLen),this._prevBufferLen=0,this.writeBuffer.length===0?this.emitReserved("drain"):this.flush()}flush(){if(this.readyState!=="closed"&&this.transport.writable&&!this.upgrading&&this.writeBuffer.length){const e=this._getWritablePackets();this.transport.send(e),this._prevBufferLen=e.length,this.emitReserved("flush")}}_getWritablePackets(){if(!(this._maxPayload&&this.transport.name==="polling"&&this.writeBuffer.length>1))return this.writeBuffer;let t=1;for(let n=0;n<this.writeBuffer.length;n++){const r=this.writeBuffer[n].data;if(r&&(t+=_t(r)),n>0&&t>this._maxPayload)return this.writeBuffer.slice(0,n);t+=2}return this.writeBuffer}_hasPingExpired(){if(!this._pingTimeoutTime)return!0;const e=Date.now()>this._pingTimeoutTime;return e&&(this._pingTimeoutTime=0,W(()=>{this._onClose("ping timeout")},this.setTimeoutFn)),e}write(e,t,n){return this._sendPacket("message",e,t,n),this}send(e,t,n){return this._sendPacket("message",e,t,n),this}_sendPacket(e,t,n,r){if(typeof t=="function"&&(r=t,t=void 0),typeof n=="function"&&(r=n,n=null),this.readyState==="closing"||this.readyState==="closed")return;n=n||{},n.compress=n.compress!==!1;const i={type:e,data:t,options:n};this.emitReserved("packetCreate",i),this.writeBuffer.push(i),r&&this.once("flush",r),this.flush()}close(){const e=()=>{this._onClose("forced close"),this.transport.close()},t=()=>{this.off("upgrade",t),this.off("upgradeError",t),e()},n=()=>{this.once("upgrade",t),this.once("upgradeError",t)};return(this.readyState==="opening"||this.readyState==="open")&&(this.readyState="closing",this.writeBuffer.length?this.once("drain",()=>{this.upgrading?n():e()}):this.upgrading?n():e()),this}_onError(e){if($.priorWebsocketSuccess=!1,this.opts.tryAllTransports&&this.transports.length>1&&this.readyState==="opening")return this.transports.shift(),this._open();this.emitReserved("error",e),this._onClose("transport error",e)}_onClose(e,t){if(this.readyState==="opening"||this.readyState==="open"||this.readyState==="closing"){if(this.clearTimeoutFn(this._pingTimeoutTimer),this.transport.removeAllListeners("close"),this.transport.close(),this.transport.removeAllListeners(),re&&(this._beforeunloadEventListener&&removeEventListener("beforeunload",this._beforeunloadEventListener,!1),this._offlineEventListener)){const n=H.indexOf(this._offlineEventListener);n!==-1&&H.splice(n,1)}this.readyState="closed",this.id=null,this.emitReserved("close",e,t),this.writeBuffer=[],this._prevBufferLen=0}}}$.protocol=qe;class It extends ${constructor(){super(...arguments),this._upgrades=[]}onOpen(){if(super.onOpen(),this.readyState==="open"&&this.opts.upgrade)for(let e=0;e<this._upgrades.length;e++)this._probe(this._upgrades[e])}_probe(e){let t=this.createTransport(e),n=!1;$.priorWebsocketSuccess=!1;const r=()=>{n||(t.send([{type:"ping",data:"probe"}]),t.once("packet",y=>{if(!n)if(y.type==="pong"&&y.data==="probe"){if(this.upgrading=!0,this.emitReserved("upgrading",t),!t)return;$.priorWebsocketSuccess=t.name==="websocket",this.transport.pause(()=>{n||this.readyState!=="closed"&&(v(),this.setTransport(t),t.send([{type:"upgrade"}]),this.emitReserved("upgrade",t),t=null,this.upgrading=!1,this.flush())})}else{const O=new Error("probe error");O.transport=t.name,this.emitReserved("upgradeError",O)}}))};function i(){n||(n=!0,v(),t.close(),t=null)}const a=y=>{const O=new Error("probe error: "+y);O.transport=t.name,i(),this.emitReserved("upgradeError",O)};function l(){a("transport closed")}function o(){a("socket closed")}function _(y){t&&y.name!==t.name&&i()}const v=()=>{t.removeListener("open",r),t.removeListener("error",a),t.removeListener("close",l),this.off("close",o),this.off("upgrading",_)};t.once("open",r),t.once("error",a),t.once("close",l),this.once("close",o),this.once("upgrading",_),this._upgrades.indexOf("webtransport")!==-1&&e!=="webtransport"?this.setTimeoutFn(()=>{n||t.open()},200):t.open()}onHandshake(e){this._upgrades=this._filterUpgrades(e.upgrades),super.onHandshake(e)}_filterUpgrades(e){const t=[];for(let n=0;n<e.length;n++)~this.transports.indexOf(e[n])&&t.push(e[n]);return t}}let Dt=class extends It{constructor(e,t={}){const n=typeof e=="object"?e:t;(!n.transports||n.transports&&typeof n.transports[0]=="string")&&(n.transports=(n.transports||["polling","websocket","webtransport"]).map(r=>Nt[r]).filter(r=>!!r)),super(e,n)}};function Yt(s,e="",t){let n=s;t=t||typeof location<"u"&&location,s==null&&(s=t.protocol+"//"+t.host),typeof s=="string"&&(s.charAt(0)==="/"&&(s.charAt(1)==="/"?s=t.protocol+s:s=t.host+s),/^(https?|wss?):\/\//.test(s)||(typeof t<"u"?s=t.protocol+"//"+s:s="https://"+s),n=ne(s)),n.port||(/^(http|ws)$/.test(n.protocol)?n.port="80":/^(http|ws)s$/.test(n.protocol)&&(n.port="443")),n.path=n.path||"/";const i=n.host.indexOf(":")!==-1?"["+n.host+"]":n.host;return n.id=n.protocol+"://"+i+":"+n.port+e,n.href=n.protocol+"://"+i+(t&&t.port===n.port?"":":"+n.port),n}const Mt=typeof ArrayBuffer=="function",Ft=s=>typeof ArrayBuffer.isView=="function"?ArrayBuffer.isView(s):s.buffer instanceof ArrayBuffer,Ue=Object.prototype.toString,Ut=typeof Blob=="function"||typeof Blob<"u"&&Ue.call(Blob)==="[object BlobConstructor]",Vt=typeof File=="function"||typeof File<"u"&&Ue.call(File)==="[object FileConstructor]";function fe(s){return Mt&&(s instanceof ArrayBuffer||Ft(s))||Ut&&s instanceof Blob||Vt&&s instanceof File}function K(s,e){if(!s||typeof s!="object")return!1;if(Array.isArray(s)){for(let t=0,n=s.length;t<n;t++)if(K(s[t]))return!0;return!1}if(fe(s))return!0;if(s.toJSON&&typeof s.toJSON=="function"&&arguments.length===1)return K(s.toJSON(),!0);for(const t in s)if(Object.prototype.hasOwnProperty.call(s,t)&&K(s[t]))return!0;return!1}function Ht(s){const e=[],t=s.data,n=s;return n.data=ie(t,e),n.attachments=e.length,{packet:n,buffers:e}}function ie(s,e){if(!s)return s;if(fe(s)){const t={_placeholder:!0,num:e.length};return e.push(s),t}else if(Array.isArray(s)){const t=new Array(s.length);for(let n=0;n<s.length;n++)t[n]=ie(s[n],e);return t}else if(typeof s=="object"&&!(s instanceof Date)){const t={};for(const n in s)Object.prototype.hasOwnProperty.call(s,n)&&(t[n]=ie(s[n],e));return t}return s}function Kt(s,e){return s.data=oe(s.data,e),delete s.attachments,s}function oe(s,e){if(!s)return s;if(s&&s._placeholder===!0){if(typeof s.num=="number"&&s.num>=0&&s.num<e.length)return e[s.num];throw new Error("illegal attachments")}else if(Array.isArray(s))for(let t=0;t<s.length;t++)s[t]=oe(s[t],e);else if(typeof s=="object")for(const t in s)Object.prototype.hasOwnProperty.call(s,t)&&(s[t]=oe(s[t],e));return s}const Ve=["connect","connect_error","disconnect","disconnecting","newListener","removeListener"],jt=5;var d;(function(s){s[s.CONNECT=0]="CONNECT",s[s.DISCONNECT=1]="DISCONNECT",s[s.EVENT=2]="EVENT",s[s.ACK=3]="ACK",s[s.CONNECT_ERROR=4]="CONNECT_ERROR",s[s.BINARY_EVENT=5]="BINARY_EVENT",s[s.BINARY_ACK=6]="BINARY_ACK"})(d||(d={}));class Jt{constructor(e){this.replacer=e}encode(e){return(e.type===d.EVENT||e.type===d.ACK)&&K(e)?this.encodeAsBinary({type:e.type===d.EVENT?d.BINARY_EVENT:d.BINARY_ACK,nsp:e.nsp,data:e.data,id:e.id}):[this.encodeAsString(e)]}encodeAsString(e){let t=""+e.type;return(e.type===d.BINARY_EVENT||e.type===d.BINARY_ACK)&&(t+=e.attachments+"-"),e.nsp&&e.nsp!=="/"&&(t+=e.nsp+","),e.id!=null&&(t+=e.id),e.data!=null&&(t+=JSON.stringify(e.data,this.replacer)),t}encodeAsBinary(e){const t=Ht(e),n=this.encodeAsString(t.packet),r=t.buffers;return r.unshift(n),r}}class pe extends b{constructor(e){super(),this.reviver=e}add(e){let t;if(typeof e=="string"){if(this.reconstructor)throw new Error("got plaintext data when reconstructing a packet");t=this.decodeString(e);const n=t.type===d.BINARY_EVENT;n||t.type===d.BINARY_ACK?(t.type=n?d.EVENT:d.ACK,this.reconstructor=new Wt(t),t.attachments===0&&super.emitReserved("decoded",t)):super.emitReserved("decoded",t)}else if(fe(e)||e.base64)if(this.reconstructor)t=this.reconstructor.takeBinaryData(e),t&&(this.reconstructor=null,super.emitReserved("decoded",t));else throw new Error("got binary data when not reconstructing a packet");else throw new Error("Unknown type: "+e)}decodeString(e){let t=0;const n={type:Number(e.charAt(0))};if(d[n.type]===void 0)throw new Error("unknown packet type "+n.type);if(n.type===d.BINARY_EVENT||n.type===d.BINARY_ACK){const i=t+1;for(;e.charAt(++t)!=="-"&&t!=e.length;);const a=e.substring(i,t);if(a!=Number(a)||e.charAt(t)!=="-")throw new Error("Illegal attachments");n.attachments=Number(a)}if(e.charAt(t+1)==="/"){const i=t+1;for(;++t&&!(e.charAt(t)===","||t===e.length););n.nsp=e.substring(i,t)}else n.nsp="/";const r=e.charAt(t+1);if(r!==""&&Number(r)==r){const i=t+1;for(;++t;){const a=e.charAt(t);if(a==null||Number(a)!=a){--t;break}if(t===e.length)break}n.id=Number(e.substring(i,t+1))}if(e.charAt(++t)){const i=this.tryParse(e.substr(t));if(pe.isPayloadValid(n.type,i))n.data=i;else throw new Error("invalid payload")}return n}tryParse(e){try{return JSON.parse(e,this.reviver)}catch{return!1}}static isPayloadValid(e,t){switch(e){case d.CONNECT:return J(t);case d.DISCONNECT:return t===void 0;case d.CONNECT_ERROR:return typeof t=="string"||J(t);case d.EVENT:case d.BINARY_EVENT:return Array.isArray(t)&&(typeof t[0]=="number"||typeof t[0]=="string"&&Ve.indexOf(t[0])===-1);case d.ACK:case d.BINARY_ACK:return Array.isArray(t)}}destroy(){this.reconstructor&&(this.reconstructor.finishedReconstruction(),this.reconstructor=null)}}class Wt{constructor(e){this.packet=e,this.buffers=[],this.reconPack=e}takeBinaryData(e){if(this.buffers.push(e),this.buffers.length===this.reconPack.attachments){const t=Kt(this.reconPack,this.buffers);return this.finishedReconstruction(),t}return null}finishedReconstruction(){this.reconPack=null,this.buffers=[]}}function zt(s){return typeof s=="string"}const Xt=Number.isInteger||function(s){return typeof s=="number"&&isFinite(s)&&Math.floor(s)===s};function Gt(s){return s===void 0||Xt(s)}function J(s){return Object.prototype.toString.call(s)==="[object Object]"}function Qt(s,e){switch(s){case d.CONNECT:return e===void 0||J(e);case d.DISCONNECT:return e===void 0;case d.EVENT:return Array.isArray(e)&&(typeof e[0]=="number"||typeof e[0]=="string"&&Ve.indexOf(e[0])===-1);case d.ACK:return Array.isArray(e);case d.CONNECT_ERROR:return typeof e=="string"||J(e);default:return!1}}function Zt(s){return zt(s.nsp)&&Gt(s.id)&&Qt(s.type,s.data)}const es=Object.freeze(Object.defineProperty({__proto__:null,Decoder:pe,Encoder:Jt,get PacketType(){return d},isPacketValid:Zt,protocol:jt},Symbol.toStringTag,{value:"Module"}));function T(s,e,t){return s.on(e,t),function(){s.off(e,t)}}const ts=Object.freeze({connect:1,connect_error:1,disconnect:1,disconnecting:1,newListener:1,removeListener:1});class He extends b{constructor(e,t,n){super(),this.connected=!1,this.recovered=!1,this.receiveBuffer=[],this.sendBuffer=[],this._queue=[],this._queueSeq=0,this.ids=0,this.acks={},this.flags={},this.io=e,this.nsp=t,n&&n.auth&&(this.auth=n.auth),this._opts=Object.assign({},n),this.io._autoConnect&&this.open()}get disconnected(){return!this.connected}subEvents(){if(this.subs)return;const e=this.io;this.subs=[T(e,"open",this.onopen.bind(this)),T(e,"packet",this.onpacket.bind(this)),T(e,"error",this.onerror.bind(this)),T(e,"close",this.onclose.bind(this))]}get active(){return!!this.subs}connect(){return this.connected?this:(this.subEvents(),this.io._reconnecting||this.io.open(),this.io._readyState==="open"&&this.onopen(),this)}open(){return this.connect()}send(...e){return e.unshift("message"),this.emit.apply(this,e),this}emit(e,...t){var n,r,i;if(ts.hasOwnProperty(e))throw new Error('"'+e.toString()+'" is a reserved event name');if(t.unshift(e),this._opts.retries&&!this.flags.fromQueue&&!this.flags.volatile)return this._addToQueue(t),this;const a={type:d.EVENT,data:t};if(a.options={},a.options.compress=this.flags.compress!==!1,typeof t[t.length-1]=="function"){const v=this.ids++,y=t.pop();this._registerAckCallback(v,y),a.id=v}const l=(r=(n=this.io.engine)===null||n===void 0?void 0:n.transport)===null||r===void 0?void 0:r.writable,o=this.connected&&!(!((i=this.io.engine)===null||i===void 0)&&i._hasPingExpired());return this.flags.volatile&&!l||(o?(this.notifyOutgoingListeners(a),this.packet(a)):this.sendBuffer.push(a)),this.flags={},this}_registerAckCallback(e,t){var n;const r=(n=this.flags.timeout)!==null&&n!==void 0?n:this._opts.ackTimeout;if(r===void 0){this.acks[e]=t;return}const i=this.io.setTimeoutFn(()=>{delete this.acks[e];for(let l=0;l<this.sendBuffer.length;l++)this.sendBuffer[l].id===e&&this.sendBuffer.splice(l,1);t.call(this,new Error("operation has timed out"))},r),a=(...l)=>{this.io.clearTimeoutFn(i),t.apply(this,l)};a.withError=!0,this.acks[e]=a}emitWithAck(e,...t){return new Promise((n,r)=>{const i=(a,l)=>a?r(a):n(l);i.withError=!0,t.push(i),this.emit(e,...t)})}_addToQueue(e){let t;typeof e[e.length-1]=="function"&&(t=e.pop());const n={id:this._queueSeq++,tryCount:0,pending:!1,args:e,flags:Object.assign({fromQueue:!0},this.flags)};e.push((r,...i)=>(this._queue[0],r!==null?n.tryCount>this._opts.retries&&(this._queue.shift(),t&&t(r)):(this._queue.shift(),t&&t(null,...i)),n.pending=!1,this._drainQueue())),this._queue.push(n),this._drainQueue()}_drainQueue(e=!1){if(!this.connected||this._queue.length===0)return;const t=this._queue[0];t.pending&&!e||(t.pending=!0,t.tryCount++,this.flags=t.flags,this.emit.apply(this,t.args))}packet(e){e.nsp=this.nsp,this.io._packet(e)}onopen(){typeof this.auth=="function"?this.auth(e=>{this._sendConnectPacket(e)}):this._sendConnectPacket(this.auth)}_sendConnectPacket(e){this.packet({type:d.CONNECT,data:this._pid?Object.assign({pid:this._pid,offset:this._lastOffset},e):e})}onerror(e){this.connected||this.emitReserved("connect_error",e)}onclose(e,t){this.connected=!1,delete this.id,this.emitReserved("disconnect",e,t),this._clearAcks()}_clearAcks(){Object.keys(this.acks).forEach(e=>{if(!this.sendBuffer.some(n=>String(n.id)===e)){const n=this.acks[e];delete this.acks[e],n.withError&&n.call(this,new Error("socket has been disconnected"))}})}onpacket(e){if(e.nsp===this.nsp)switch(e.type){case d.CONNECT:e.data&&e.data.sid?this.onconnect(e.data.sid,e.data.pid):this.emitReserved("connect_error",new Error("It seems you are trying to reach a Socket.IO server in v2.x with a v3.x client, but they are not compatible (more information here: https://socket.io/docs/v3/migrating-from-2-x-to-3-0/)"));break;case d.EVENT:case d.BINARY_EVENT:this.onevent(e);break;case d.ACK:case d.BINARY_ACK:this.onack(e);break;case d.DISCONNECT:this.ondisconnect();break;case d.CONNECT_ERROR:this.destroy();const n=new Error(e.data.message);n.data=e.data.data,this.emitReserved("connect_error",n);break}}onevent(e){const t=e.data||[];e.id!=null&&t.push(this.ack(e.id)),this.connected?this.emitEvent(t):this.receiveBuffer.push(Object.freeze(t))}emitEvent(e){if(this._anyListeners&&this._anyListeners.length){const t=this._anyListeners.slice();for(const n of t)n.apply(this,e)}super.emit.apply(this,e),this._pid&&e.length&&typeof e[e.length-1]=="string"&&(this._lastOffset=e[e.length-1])}ack(e){const t=this;let n=!1;return function(...r){n||(n=!0,t.packet({type:d.ACK,id:e,data:r}))}}onack(e){const t=this.acks[e.id];typeof t=="function"&&(delete this.acks[e.id],t.withError&&e.data.unshift(null),t.apply(this,e.data))}onconnect(e,t){this.id=e,this.recovered=t&&this._pid===t,this._pid=t,this.connected=!0,this.emitBuffered(),this._drainQueue(!0),this.emitReserved("connect")}emitBuffered(){this.receiveBuffer.forEach(e=>this.emitEvent(e)),this.receiveBuffer=[],this.sendBuffer.forEach(e=>{this.notifyOutgoingListeners(e),this.packet(e)}),this.sendBuffer=[]}ondisconnect(){this.destroy(),this.onclose("io server disconnect")}destroy(){this.subs&&(this.subs.forEach(e=>e()),this.subs=void 0),this.io._destroy(this)}disconnect(){return this.connected&&this.packet({type:d.DISCONNECT}),this.destroy(),this.connected&&this.onclose("io client disconnect"),this}close(){return this.disconnect()}compress(e){return this.flags.compress=e,this}get volatile(){return this.flags.volatile=!0,this}timeout(e){return this.flags.timeout=e,this}onAny(e){return this._anyListeners=this._anyListeners||[],this._anyListeners.push(e),this}prependAny(e){return this._anyListeners=this._anyListeners||[],this._anyListeners.unshift(e),this}offAny(e){if(!this._anyListeners)return this;if(e){const t=this._anyListeners;for(let n=0;n<t.length;n++)if(e===t[n])return t.splice(n,1),this}else this._anyListeners=[];return this}listenersAny(){return this._anyListeners||[]}onAnyOutgoing(e){return this._anyOutgoingListeners=this._anyOutgoingListeners||[],this._anyOutgoingListeners.push(e),this}prependAnyOutgoing(e){return this._anyOutgoingListeners=this._anyOutgoingListeners||[],this._anyOutgoingListeners.unshift(e),this}offAnyOutgoing(e){if(!this._anyOutgoingListeners)return this;if(e){const t=this._anyOutgoingListeners;for(let n=0;n<t.length;n++)if(e===t[n])return t.splice(n,1),this}else this._anyOutgoingListeners=[];return this}listenersAnyOutgoing(){return this._anyOutgoingListeners||[]}notifyOutgoingListeners(e){if(this._anyOutgoingListeners&&this._anyOutgoingListeners.length){const t=this._anyOutgoingListeners.slice();for(const n of t)n.apply(this,e.data)}}}function q(s){s=s||{},this.ms=s.min||100,this.max=s.max||1e4,this.factor=s.factor||2,this.jitter=s.jitter>0&&s.jitter<=1?s.jitter:0,this.attempts=0}q.prototype.duration=function(){var s=this.ms*Math.pow(this.factor,this.attempts++);if(this.jitter){var e=Math.random(),t=Math.floor(e*this.jitter*s);s=(Math.floor(e*10)&1)==0?s-t:s+t}return Math.min(s,this.max)|0};q.prototype.reset=function(){this.attempts=0};q.prototype.setMin=function(s){this.ms=s};q.prototype.setMax=function(s){this.max=s};q.prototype.setJitter=function(s){this.jitter=s};class ae extends b{constructor(e,t){var n;super(),this.nsps={},this.subs=[],e&&typeof e=="object"&&(t=e,e=void 0),t=t||{},t.path=t.path||"/socket.io",this.opts=t,z(this,t),this.reconnection(t.reconnection!==!1),this.reconnectionAttempts(t.reconnectionAttempts||1/0),this.reconnectionDelay(t.reconnectionDelay||1e3),this.reconnectionDelayMax(t.reconnectionDelayMax||5e3),this.randomizationFactor((n=t.randomizationFactor)!==null&&n!==void 0?n:.5),this.backoff=new q({min:this.reconnectionDelay(),max:this.reconnectionDelayMax(),jitter:this.randomizationFactor()}),this.timeout(t.timeout==null?2e4:t.timeout),this._readyState="closed",this.uri=e;const r=t.parser||es;this.encoder=new r.Encoder,this.decoder=new r.Decoder,this._autoConnect=t.autoConnect!==!1,this._autoConnect&&this.open()}reconnection(e){return arguments.length?(this._reconnection=!!e,e||(this.skipReconnect=!0),this):this._reconnection}reconnectionAttempts(e){return e===void 0?this._reconnectionAttempts:(this._reconnectionAttempts=e,this)}reconnectionDelay(e){var t;return e===void 0?this._reconnectionDelay:(this._reconnectionDelay=e,(t=this.backoff)===null||t===void 0||t.setMin(e),this)}randomizationFactor(e){var t;return e===void 0?this._randomizationFactor:(this._randomizationFactor=e,(t=this.backoff)===null||t===void 0||t.setJitter(e),this)}reconnectionDelayMax(e){var t;return e===void 0?this._reconnectionDelayMax:(this._reconnectionDelayMax=e,(t=this.backoff)===null||t===void 0||t.setMax(e),this)}timeout(e){return arguments.length?(this._timeout=e,this):this._timeout}maybeReconnectOnOpen(){!this._reconnecting&&this._reconnection&&this.backoff.attempts===0&&this.reconnect()}open(e){if(~this._readyState.indexOf("open"))return this;this.engine=new Dt(this.uri,this.opts);const t=this.engine,n=this;this._readyState="opening",this.skipReconnect=!1;const r=T(t,"open",function(){n.onopen(),e&&e()}),i=l=>{this.cleanup(),this._readyState="closed",this.emitReserved("error",l),e?e(l):this.maybeReconnectOnOpen()},a=T(t,"error",i);if(this._timeout!==!1){const l=this._timeout,o=this.setTimeoutFn(()=>{r(),i(new Error("timeout")),t.close()},l);this.opts.autoUnref&&o.unref(),this.subs.push(()=>{this.clearTimeoutFn(o)})}return this.subs.push(r),this.subs.push(a),this}connect(e){return this.open(e)}onopen(){this.cleanup(),this._readyState="open",this.emitReserved("open");const e=this.engine;this.subs.push(T(e,"ping",this.onping.bind(this)),T(e,"data",this.ondata.bind(this)),T(e,"error",this.onerror.bind(this)),T(e,"close",this.onclose.bind(this)),T(this.decoder,"decoded",this.ondecoded.bind(this)))}onping(){this.emitReserved("ping")}ondata(e){try{this.decoder.add(e)}catch(t){this.onclose("parse error",t)}}ondecoded(e){W(()=>{this.emitReserved("packet",e)},this.setTimeoutFn)}onerror(e){this.emitReserved("error",e)}socket(e,t){let n=this.nsps[e];return n?this._autoConnect&&!n.active&&n.connect():(n=new He(this,e,t),this.nsps[e]=n),n}_destroy(e){const t=Object.keys(this.nsps);for(const n of t)if(this.nsps[n].active)return;this._close()}_packet(e){const t=this.encoder.encode(e);for(let n=0;n<t.length;n++)this.engine.write(t[n],e.options)}cleanup(){this.subs.forEach(e=>e()),this.subs.length=0,this.decoder.destroy()}_close(){this.skipReconnect=!0,this._reconnecting=!1,this.onclose("forced close")}disconnect(){return this._close()}onclose(e,t){var n;this.cleanup(),(n=this.engine)===null||n===void 0||n.close(),this.backoff.reset(),this._readyState="closed",this.emitReserved("close",e,t),this._reconnection&&!this.skipReconnect&&this.reconnect()}reconnect(){if(this._reconnecting||this.skipReconnect)return this;const e=this;if(this.backoff.attempts>=this._reconnectionAttempts)this.backoff.reset(),this.emitReserved("reconnect_failed"),this._reconnecting=!1;else{const t=this.backoff.duration();this._reconnecting=!0;const n=this.setTimeoutFn(()=>{e.skipReconnect||(this.emitReserved("reconnect_attempt",e.backoff.attempts),!e.skipReconnect&&e.open(r=>{r?(e._reconnecting=!1,e.reconnect(),this.emitReserved("reconnect_error",r)):e.onreconnect()}))},t);this.opts.autoUnref&&n.unref(),this.subs.push(()=>{this.clearTimeoutFn(n)})}}onreconnect(){const e=this.backoff.attempts;this._reconnecting=!1,this.backoff.reset(),this.emitReserved("reconnect",e)}}const D={};function j(s,e){typeof s=="object"&&(e=s,s=void 0),e=e||{};const t=Yt(s,e.path||"/socket.io"),n=t.source,r=t.id,i=t.path,a=D[r]&&i in D[r].nsps,l=e.forceNew||e["force new connection"]||e.multiplex===!1||a;let o;return l?o=new ae(n,e):(D[r]||(D[r]=new ae(n,e)),o=D[r]),t.query&&!e.query&&(e.query=t.queryKey),o.socket(t.path,e)}Object.assign(j,{Manager:ae,Socket:He,io:j,connect:j});const ss="/api/fahui_router/search",ke=[2025,2024,2023];let L=null;const h={years:[...ke],selectedYear:ke[0],query:"",loading:!1,error:"",ordersByYear:{},paginationByYear:{},realtimeConnected:!1,realtimeStatus:"未连接",lastEvent:null},ce=new Set;function A(){const s=ge();ce.forEach(e=>e(s))}function me(s){h.years.includes(s)||(h.years=[s,...h.years].sort((e,t)=>t-e))}function ns(s){if(typeof s=="number"&&Number.isFinite(s))return s;const e=String(s||"").match(/^(\d{4})/);return e?Number(e[1]):NaN}function rs(s){return(s||[]).map(e=>({id:e.id,customer_name:e.customer_name||e.name||"未命名订单",phone:e.phone||"-",status:e.status||"Not-ready",created_at:e.created_at||"-",version:e.version}))}function ge(){return{years:[...h.years],selectedYear:h.selectedYear,query:h.query,loading:h.loading,error:h.error,ordersByYear:{...h.ordersByYear},paginationByYear:{...h.paginationByYear},realtimeConnected:h.realtimeConnected,realtimeStatus:h.realtimeStatus,lastEvent:h.lastEvent?{...h.lastEvent}:null}}function is(s){return ce.add(s),s(ge()),()=>ce.delete(s)}function os(s){me(s),h.selectedYear=s,A()}function as(s){h.query=s,A()}async function U(s=h.selectedYear,e={}){const t=e.query??h.query,n=e.page??1;me(s),h.selectedYear=s,h.query=t,h.loading=!0,h.error="",A();try{const r=new URLSearchParams({version:String(s),value:t,page:String(n),per_page:"20"}),i=await fetch(`${ss}?${r.toString()}`,{credentials:"include"}),a=await i.json().catch(()=>({}));if(!i.ok||(a==null?void 0:a.status)!=="success")throw new Error((a==null?void 0:a.message)||"加载法会数据失败");const l=a.data||{};h.ordersByYear={...h.ordersByYear,[s]:rs(l.items)},h.paginationByYear={...h.paginationByYear,[s]:l.pagination||{}},h.loading=!1,h.error="",A()}catch(r){h.loading=!1,h.error=r.message||"加载失败",A()}}function cs(s,e={}){var o;const t=ns(s==null?void 0:s.version);if(!t)return;me(t);const n=h.ordersByYear[t]||[],r={id:s.id,customer_name:s.customer_name||s.name||"未命名订单",phone:s.phone||"-",status:s.status||"Not-ready",created_at:s.created_at||"-",version:s.version},i=n.findIndex(_=>_.id===r.id),a=[...n];let l=(o=h.paginationByYear[t])==null?void 0:o.total;i>=0?a[i]=r:(a.unshift(r),typeof l=="number"&&(l+=1)),h.ordersByYear={...h.ordersByYear,[t]:a},h.paginationByYear={...h.paginationByYear,[t]:{...h.paginationByYear[t]||{},total:l??a.length}},h.lastEvent={type:i>=0?"updated":"created",orderId:r.id,source:e.source||"socket",year:t,createdAt:new Date().toISOString()},A()}function ls(){return L||(h.realtimeStatus="连接中",A(),L=j("/",{withCredentials:!0,transports:["websocket","polling"]}),L.on("connect",()=>{h.realtimeConnected=!0,h.realtimeStatus="实时已连接",A()}),L.on("disconnect",()=>{h.realtimeConnected=!1,h.realtimeStatus="连接已断开",A()}),L.on("connect_error",()=>{h.realtimeConnected=!1,h.realtimeStatus="实时连接失败",A()}),L.on("fahui:order_created",s=>{s!=null&&s.order&&cs(s.order,{source:s.source||"new_customer"})}),L)}function hs(s){function e(i){window.dispatchEvent(new CustomEvent("fahui:navigate",{detail:{page:"fahui_detail",params:{orderId:i,returnPage:"fahui_data"}}}))}let t=null;function n(i){const a=i.ordersByYear[i.selectedYear]||[],l=i.paginationByYear[i.selectedYear]||{};s.innerHTML=`
      <section class="fahui-shell">
        <header class="fahui-header">
          <div>
            <h2 class="section-title">法会数据</h2>
            <p class="section-subtitle">统一从 state 读取，后面方便接 socket 增量更新。</p>
          </div>
          <div class="realtime-chip ${i.realtimeConnected?"connected":""}">
            <span>${i.realtimeStatus}</span>
            ${i.lastEvent?`<strong>最新 #${i.lastEvent.orderId}</strong>`:""}
          </div>
        </header>

        <div class="fahui-toolbar">
          <div class="year-tabs">
            ${i.years.map(o=>`
                  <button
                    class="year-tab ${o===i.selectedYear?"active":""}"
                    type="button"
                    data-year="${o}"
                  >
                    ${o}
                  </button>
                `).join("")}
          </div>

          <form class="search-form" data-role="search-form">
            <input
              class="search-input"
              name="query"
              placeholder="搜索功德主 / 电话 / 表单内容"
              value="${i.query}"
            />
            <button class="mode-switch secondary" type="submit">搜索</button>
            <button class="mode-switch secondary" type="button" data-action="refresh-year">刷新</button>
          </form>
        </div>

        ${i.error?`<div class="state-banner error">${i.error}</div>`:""}

        <section class="order-list">
          ${i.loading?'<div class="state-banner">加载中...</div>':a.length?a.map(o=>`
                        <button class="order-card order-card-button" type="button" data-order-id="${o.id}">
                          <div class="order-main">
                            <div class="order-name">${o.customer_name}</div>
                            <div class="order-meta">#${o.id} · ${o.created_at}</div>
                          </div>
                          <div class="order-side">
                            <span class="status-tag">${o.status}</span>
                            <span class="order-phone">${o.phone}</span>
                          </div>
                        </button>
                      `).join(""):'<div class="state-banner">这个年份还没有数据</div>'}
        </section>

        <footer class="fahui-footer">
          <span>当前年份：${i.selectedYear}</span>
          <span>总数：${l.total??a.length}</span>
        </footer>
      </section>
    `,r(i)}function r(i){s.querySelectorAll("[data-year]").forEach(o=>{o.addEventListener("click",async()=>{const _=Number(o.dataset.year);os(_),await U(_)})});const a=s.querySelector('[data-role="search-form"]');a&&a.addEventListener("submit",async o=>{o.preventDefault();const _=new FormData(a),v=String(_.get("query")||"").trim();as(v),await U(i.selectedYear,{query:v})});const l=s.querySelector('[data-action="refresh-year"]');l&&l.addEventListener("click",async()=>{await U(i.selectedYear)}),s.querySelectorAll("[data-order-id]").forEach(o=>{o.addEventListener("click",()=>{e(Number(o.dataset.orderId))})})}return t=is(n),U(ge().selectedYear),()=>{t&&t(),s.innerHTML=""}}const us="/api/fahui_router/get_order_by_id";function ds(s,e={}){const t=Number(e.orderId),n=typeof e.onBack=="function"?e.onBack:()=>{};let r={loading:!0,error:"",detail:null};function i(){s.innerHTML=`
      <section class="detail-shell">
        <div class="detail-head">
          <button class="mode-switch secondary" type="button" data-action="detail-back">返回</button>
          <h2 class="section-title">法会订单详情</h2>
        </div>

        ${r.loading?'<div class="state-banner">订单详情加载中...</div>':r.error?`<div class="state-banner error">${r.error}</div>`:r.detail?`
                  <section class="detail-panel">
                    <div class="detail-row"><strong>订单号</strong><span>${r.detail.id}</span></div>
                    <div class="detail-row"><strong>功德主</strong><span>${r.detail.customer_name||"-"}</span></div>
                    <div class="detail-row"><strong>登记名称</strong><span>${r.detail.name||"-"}</span></div>
                    <div class="detail-row"><strong>手机号</strong><span>${r.detail.phone||"-"}</span></div>
                    <div class="detail-row"><strong>状态</strong><span>${r.detail.status||"-"}</span></div>
                    <div class="detail-row"><strong>版本</strong><span>${r.detail.version||"-"}</span></div>
                    <div class="detail-row"><strong>创建时间</strong><span>${r.detail.created_at||"-"}</span></div>
                  </section>

                  <section class="detail-panel">
                    <h3 class="section-title">项目明细</h3>
                    <div class="local-list">
                      ${(r.detail.order_items||[]).length?r.detail.order_items.map(o=>`
                                  <article class="local-card">
                                    <div class="local-name">${o.item_name||o.code||"未命名项目"}</div>
                                    <div class="local-meta">项目 #${o.id}</div>
                                    <div class="local-meta">价格：${o.price??0}</div>
                                  </article>
                                `).join(""):'<div class="state-banner">这笔订单还没有项目明细</div>'}
                    </div>
                  </section>
                `:""}
      </section>
    `;const l=s.querySelector('[data-action="detail-back"]');l&&l.addEventListener("click",n)}async function a(){i();try{const l=await fetch(`${us}?id=${t}`,{credentials:"include"}),o=await l.json().catch(()=>({}));if(!l.ok||(o==null?void 0:o.status)!=="success")throw new Error((o==null?void 0:o.message)||"加载订单详情失败");r.loading=!1,r.detail=o.data||null,r.error="",i()}catch(l){r.loading=!1,r.detail=null,r.error=l.message||"加载订单详情失败",i()}}return a(),()=>{s.innerHTML=""}}const Ke="fahui_frontend_mode",R="guest",k="admin",fs="/static/images/logo/logo.png",ps="/api/user_control/get_user_data",ms="/api/user_control/login",gs="/api/user_control/logout",N=document.getElementById("app"),Se={[R]:{label:"游客模式",subtitle:"浏览公开入口",navItems:[{key:"home",icon:"fa-solid fa-house",title:"首页"},{key:"search",icon:"fa-solid fa-magnifying-glass",title:"查找订单"},{key:"payment",icon:"fa-solid fa-file-invoice",title:"付款与凭证"},{key:"scan",icon:"fa-solid fa-qrcode",title:"扫码入口"}]},[k]:{label:"管理员模式",subtitle:"运营与管理",navItems:[{key:"fahui_data",icon:"fa-solid fa-file-lines",title:"法会数据"},{key:"accounting",icon:"fa-solid fa-book",title:"做账 / 支付"},{key:"scan",icon:"fa-solid fa-qrcode",title:"扫码工具"},{key:"user_control",icon:"fa-solid fa-users-gear",title:"用户管理"}]}},c={mode:R,page:"home",user:null,loginOpen:!1,loginError:"",loginLoading:!1,pageParams:{}};let P=null;function ys(){return window.localStorage.getItem(Ke)===k?k:R}function X(s){window.localStorage.setItem(Ke,s)}function je(s){return s===k?R:k}async function ye(){try{const s=await fetch(ps,{credentials:"include"});if(!s.ok)return null;const e=await s.json();return(e==null?void 0:e.status)==="success"?e.user??null:null}catch{return null}}async function _s(){const s=await ye();return c.user=s,!!s}function vs(s){return`
    <button
      class="nav-pill ${c.page===s.key?"active":""}"
      type="button"
      data-action="set-page"
      data-page="${s.key}"
    >
      <i class="${s.icon}"></i>
      <span>${s.title}</span>
    </button>
  `}function bs(){return c.user?`
      <div class="user-chip">
        <i class="fa-solid fa-user-check"></i>
        <span>${c.user.display_name||c.user.username||"已登录"}</span>
      </div>
      <button class="mode-switch secondary" type="button" data-action="logout">
        登出
      </button>
    `:`
    <button class="mode-switch secondary" type="button" data-action="open-login">
      登录
    </button>
  `}function ws(){return c.user?`
      <button class="mode-switch secondary" type="button" data-action="logout">
        登出
      </button>
    `:`
    <button class="mode-switch secondary" type="button" data-action="open-login">
      登录
    </button>
  `}function Es(){return c.loginOpen?`
    <div class="modal-backdrop" data-action="close-login">
      <div class="login-modal" role="dialog" aria-modal="true" aria-label="登录">
        <div class="login-modal-head">
          <h2>管理员登录</h2>
          <button class="icon-btn" type="button" data-action="close-login" aria-label="关闭">
            <i class="fa-solid fa-xmark"></i>
          </button>
        </div>
        <form class="login-form" data-action="submit-login">
          <label class="field">
            <span>用户名</span>
            <input name="username" type="text" autocomplete="username" required />
          </label>
          <label class="field">
            <span>密码</span>
            <input name="password" type="password" autocomplete="current-password" required />
          </label>
          ${c.loginError?`<div class="form-error">${c.loginError}</div>`:""}
          <button class="submit-btn" type="submit" ${c.loginLoading?"disabled":""}>
            ${c.loginLoading?"登录中...":"登录"}
          </button>
        </form>
      </div>
    </div>
  `:""}function E(){const s=Se[c.mode],e=je(c.mode),t=Se[e].label;N.innerHTML=`
    <div class="app-shell">
      <header class="topbar">
        <div class="topbar-inner">
          <div class="brand">
            <img class="brand-logo" src="${fs}" alt="地南佛学会 logo" />
            <div class="brand-copy">
              <h1 class="brand-title">地南佛学会</h1>
              <p class="brand-subtitle">法会系统</p>
            </div>
          </div>
          <div class="nav-actions">
            <div class="mode-chip">
              <i class="fa-solid fa-circle-dot"></i>
              <span>${s.label}</span>
            </div>
            ${bs()}
            <button class="mode-switch" type="button" data-action="toggle-mode">
              切换到${t}
            </button>
          </div>
        </div>
      </header>

      <main class="page">
      <section class="nav-grid">
          ${c.page==="fahui_detail"?"":s.navItems.map(vs).join("")}
        </section>
        <section class="content-slot" data-role="content-slot"></section>
      </main>

      <div class="mobile-nav">
        <div class="mobile-mode">
          <strong>${s.label}</strong>
          <span>${s.subtitle}</span>
        </div>
        <div class="mobile-actions">
          ${ws()}
          <button class="mode-switch" type="button" data-action="toggle-mode">
            切换
          </button>
        </div>
      </div>

      ${Es()}
    </div>
  `,As(),Bs()}function Je(){c.loginOpen=!0,c.loginError="",E()}function ks(){c.loginOpen=!1,c.loginError="",c.loginLoading=!1,E()}async function Ss(){const s=je(c.mode);if(s===k&&!await _s()){Je();return}c.mode=s,c.page=s===k?"fahui_data":"home",X(s),E()}async function Os(s){const e=new FormData(s),t=String(e.get("username")||"").trim(),n=String(e.get("password")||"");if(!t||!n){c.loginError="请输入用户名和密码",E();return}c.loginLoading=!0,c.loginError="",E();try{const r=await fetch(ms,{method:"POST",credentials:"include",headers:{"Content-Type":"application/json"},body:JSON.stringify({username:t,password:n})}),i=await r.json().catch(()=>({}));if(!r.ok||(i==null?void 0:i.status)!=="success"){c.loginLoading=!1,c.loginError=(i==null?void 0:i.message)||"登录失败",E();return}c.user=i.user??await ye(),c.mode=k,c.page="fahui_data",c.loginOpen=!1,c.loginLoading=!1,c.loginError="",X(k),E()}catch{c.loginLoading=!1,c.loginError="网络错误，请稍后重试",E()}}async function Ts(){try{await fetch(gs,{method:"GET",credentials:"include"})}catch{}c.user=null,c.mode=R,c.page="home",c.loginOpen=!1,c.loginError="",c.loginLoading=!1,X(R),E()}function As(){N.querySelectorAll('[data-action="toggle-mode"]').forEach(e=>{e.addEventListener("click",Ss)}),N.querySelectorAll('[data-action="set-page"]').forEach(e=>{e.addEventListener("click",()=>{c.page=e.dataset.page||"home",c.pageParams={},E()})}),N.querySelectorAll('[data-action="open-login"]').forEach(e=>{e.addEventListener("click",Je)}),N.querySelectorAll('[data-action="logout"]').forEach(e=>{e.addEventListener("click",Ts)}),N.querySelectorAll('[data-action="close-login"]').forEach(e=>{e.addEventListener("click",t=>{t.target===e&&ks()})});const s=N.querySelector('[data-action="submit-login"]');s&&s.addEventListener("submit",e=>{e.preventDefault(),Os(s)})}function Bs(){const s=N.querySelector('[data-role="content-slot"]');if(s){if(typeof P=="function"&&(P(),P=null),c.mode===k&&c.page==="fahui_data"){P=hs(s);return}if(c.page==="fahui_detail"){P=ds(s,{orderId:c.pageParams.orderId,onBack:()=>{c.page=c.pageParams.returnPage||(c.mode===k?"fahui_data":"search"),c.pageParams={},E()}});return}if(c.mode===R&&c.page==="home"){P=et(s);return}if(c.mode===R&&c.page==="search"){P=rt(s);return}s.innerHTML=""}}async function Cs(){c.user=await ye(),ls(),c.mode=ys(),c.page=c.mode===k?"fahui_data":"home",c.mode===k&&!c.user&&(c.mode=R,c.page="home",X(R)),E()}window.addEventListener("fahui:navigate",s=>{const e=s.detail||{};c.page=e.page||c.page,c.pageParams=e.params||{},E()});Cs();
