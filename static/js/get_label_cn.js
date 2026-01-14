let feild_label = {
  father: '父',
  mother: '母',
  owner: '阳上',
  relation:'关系',
  suffix:'字段',
  surname:'姓氏',
  deceased:'亡者',
  quantity:'数量',
  price:'金额'
};

function get_label_cn(value) {
  for (let key in feild_label) {
    if (value.startsWith(key)) {
      return feild_label[key];
    }
  }
  return value; // 如果没有匹配项，返回空字符串
}

let fahui_type = {
  A1: '大牌位_超度历代祖先',
  A2: '大牌位_超度亡灵',
  A3: '大牌位_无缘子女',
  B1: '小牌位_超度历代祖先',
  B2: '小牌位_超度亡灵',
  B3: '小牌位_无缘子女',
  D1:'普度贡品',
  C:'超度冤亲债主',
  D:'随缘供斋'
};

function get_fahui_type(value) {
  return fahui_type[value] || value;
}
