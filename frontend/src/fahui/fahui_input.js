const ITEM_OPTIONS = [
  { value: 'A1', label: 'A1 大牌位：超度历代祖先 RM 100' },
  { value: 'A2', label: 'A2 大牌位：超度亡灵 RM 100' },
  { value: 'A3', label: 'A3 大牌位：无缘子女 RM 100' },
  { value: 'B1', label: 'B1 小牌位：超度历代祖先 RM 35' },
  { value: 'B2', label: 'B2 小牌位：超度亡灵 RM 35' },
  { value: 'B3', label: 'B3 小牌位：无缘子女 RM 35' },
  { value: 'C', label: 'C 小牌位：超度冤亲债主 RM 15' },
  { value: 'D', label: 'D 随缘供斋' },
  { value: 'D1', label: 'D1 普度贡品 RM 50' },
];

const RELATION_OPTIONS = [
  '祖先', '曾祖父', '曾祖母', '祖父', '祖母', '显考', '显妣', '伯父', '伯母', '叔父',
  '叔母', '姑父', '姑母', '舅父', '舅母', '姨父', '姨母', '亡夫', '亡妻', '亡兄',
  '亡姐', '嫂嫂', '姐夫', '亡弟', '弟媳', '亡妹', '妹婿', '亡兒', '亡女', '侄兒',
  '外甥', '外甥女', '十方法界', '累劫冤親債主', '地基主', '朋友', '師長', '后裔',
  '外祖父', '外祖母', '家公', '堂兄', '亡亲',
];

function inputRow(labelText, inputEl) {
  const row = document.createElement('div');
  Object.assign(row.style, {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    marginBottom: '12px',
  });

  const label = document.createElement('label');
  label.textContent = labelText;
  Object.assign(label.style, {
    width: '96px',
    color: '#5a492a',
    textAlign: 'right',
    flexShrink: '0',
  });

  Object.assign(inputEl.style, {
    flex: '1',
    minHeight: '36px',
    borderRadius: '8px',
    border: '1px solid #d7ccb2',
    padding: '8px 10px',
    boxSizing: 'border-box',
    background: '#fff',
    color: '#3d301c',
    fontSize: '14px',
  });

  row.appendChild(label);
  row.appendChild(inputEl);
  return row;
}

function createOwnerField() {
  const input = document.createElement('input');
  input.type = 'text';
  input.placeholder = '请输入阳上人';
  return inputRow('阳上人', input);
}

function createDeceasedGroup(index) {
  const wrapper = document.createElement('div');
  Object.assign(wrapper.style, {
    border: '1px solid #e1d7be',
    borderRadius: '10px',
    padding: '12px',
    marginBottom: '10px',
    background: '#fffdf8',
  });

  const relationInput = document.createElement('input');
  relationInput.type = 'text';
  relationInput.placeholder = '关系（例如：祖先）';
  relationInput.setAttribute('list', `relation-options-${index}`);

  const datalist = document.createElement('datalist');
  datalist.id = `relation-options-${index}`;
  RELATION_OPTIONS.forEach((option) => {
    const opt = document.createElement('option');
    opt.value = option;
    datalist.appendChild(opt);
  });

  const nameInput = document.createElement('input');
  nameInput.type = 'text';
  nameInput.placeholder = '亡者姓名';

  wrapper.appendChild(inputRow('关系', relationInput));
  wrapper.appendChild(inputRow('亡者', nameInput));
  wrapper.appendChild(datalist);

  return wrapper;
}

function renderAncestorForm(form) {
  form.appendChild(createOwnerField());

  const deceasedTitle = document.createElement('div');
  deceasedTitle.textContent = '超度对象';
  Object.assign(deceasedTitle.style, {
    textAlign: 'left',
    margin: '16px 0 10px 0',
    color: '#7a5c33',
    fontWeight: '600',
  });
  form.appendChild(deceasedTitle);

  const deceasedContainer = document.createElement('div');
  form.appendChild(deceasedContainer);

  let groupCount = 0;
  const addGroup = () => {
    if (groupCount >= 2) return;
    groupCount += 1;
    deceasedContainer.appendChild(createDeceasedGroup(groupCount));
  };

  const btnWrap = document.createElement('div');
  Object.assign(btnWrap.style, { display: 'flex', gap: '10px', marginTop: '4px' });

  const addBtn = document.createElement('button');
  addBtn.type = 'button';
  addBtn.textContent = '+ 新增超度对象';
  Object.assign(addBtn.style, {
    border: 'none',
    padding: '8px 12px',
    borderRadius: '8px',
    background: '#b3925f',
    color: '#fff',
    cursor: 'pointer',
  });
  addBtn.onclick = addGroup;

  const removeBtn = document.createElement('button');
  removeBtn.type = 'button';
  removeBtn.textContent = '- 删除最后一项';
  Object.assign(removeBtn.style, {
    border: 'none',
    padding: '8px 12px',
    borderRadius: '8px',
    background: '#9f6b4f',
    color: '#fff',
    cursor: 'pointer',
  });
  removeBtn.onclick = () => {
    if (groupCount <= 1) return;
    deceasedContainer.removeChild(deceasedContainer.lastElementChild);
    groupCount -= 1;
  };

  btnWrap.appendChild(addBtn);
  btnWrap.appendChild(removeBtn);
  form.appendChild(btnWrap);

  addGroup();
}

function renderSimpleForm(form, includeAmount = false, defaultAmount = '') {
  form.appendChild(createOwnerField());

  if (includeAmount) {
    const amountInput = document.createElement('input');
    amountInput.type = 'number';
    amountInput.min = '0';
    amountInput.placeholder = '请输入金额';
    if (defaultAmount) amountInput.value = defaultAmount;
    form.appendChild(inputRow('金额', amountInput));
  }

  const noteInput = document.createElement('input');
  noteInput.type = 'text';
  noteInput.placeholder = '备注（可选）';
  form.appendChild(inputRow('备注', noteInput));
}

function renderFormFields(form, itemCode) {
  form.innerHTML = '';

  if (['A1', 'A2', 'A3', 'B1', 'B2', 'B3', 'C'].includes(itemCode)) {
    renderAncestorForm(form);
    return;
  }

  if (itemCode === 'D1') {
    renderSimpleForm(form, true, '50');
    return;
  }

  renderSimpleForm(form, true, '');
}

export function open_fahui_input(container, orderData) {
  if (!container) return;

  container.innerHTML = '';
  Object.assign(container.style, {
    minHeight: '100vh',
    background: 'url("/static/images/bg/buddha_bg4.svg") center / cover no-repeat',
    boxSizing: 'border-box',
    padding: '24px 14px 40px',
  });

  const card = document.createElement('div');
  Object.assign(card.style, {
    maxWidth: '760px',
    margin: '0 auto',
    background: 'rgba(255,255,255,0.95)',
    borderRadius: '16px',
    padding: '22px',
    boxShadow: '0 10px 36px rgba(0,0,0,0.08)',
  });

  const title = document.createElement('h2');
  title.textContent = '新增牌位供奉';
  Object.assign(title.style, {
    margin: '0 0 16px 0',
    color: '#7a5c33',
    textAlign: 'center',
  });

  const hint = document.createElement('div');
  hint.textContent = `订单：${orderData?.id || '-'}  |  姓名：${orderData?.customer_name || '-'}`;
  Object.assign(hint.style, {
    marginBottom: '16px',
    color: '#6c5a3e',
    fontSize: '14px',
  });

  const select = document.createElement('select');
  ITEM_OPTIONS.forEach((item) => {
    const opt = document.createElement('option');
    opt.value = item.value;
    opt.textContent = item.label;
    select.appendChild(opt);
  });

  const selectRow = inputRow('类型', select);
  const form = document.createElement('div');

  const actionWrap = document.createElement('div');
  Object.assign(actionWrap.style, {
    display: 'flex',
    justifyContent: 'flex-end',
    gap: '10px',
    marginTop: '18px',
  });

  const saveBtn = document.createElement('button');
  saveBtn.type = 'button';
  saveBtn.textContent = '保存（待接 API）';
  Object.assign(saveBtn.style, {
    border: 'none',
    background: '#8b6f3d',
    color: '#fff',
    borderRadius: '8px',
    padding: '10px 14px',
    cursor: 'pointer',
  });
  saveBtn.onclick = () => {
    console.log('TODO: save new fahui item', { orderId: orderData?.id, itemCode: select.value });
  };

  actionWrap.appendChild(saveBtn);

  select.onchange = () => renderFormFields(form, select.value);

  card.appendChild(title);
  card.appendChild(hint);
  card.appendChild(selectRow);
  card.appendChild(form);
  card.appendChild(actionWrap);

  container.appendChild(card);

  renderFormFields(form, select.value);
}
