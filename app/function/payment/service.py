ALLOWED_EXTENSIONS = {"pdf", "png", "jpg", "jpeg"}

FIELD_LABEL = {
    "father": "父",
    "mother": "母",
    "owner": "阳上",
    "relation": "关系",
    "suffix": "字段",
    "surname": "姓氏",
    "deceased": "亡者姓名",
    "price": "金额",
    "quantity": "数量",
}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def get_label_cn_filter(value):
    for key in FIELD_LABEL:
        if value.startswith(key):
            return FIELD_LABEL[key]
    return value
