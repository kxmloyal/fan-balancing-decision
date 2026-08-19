import re


def sanitize_model_name(model_name):
    if not model_name or model_name == "未知":
        return "未分类"
    safe = re.sub(r'[\\/:*?"<>|]', "_", str(model_name)).strip()
    return safe if safe else "未分类"
