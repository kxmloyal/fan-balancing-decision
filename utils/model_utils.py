import re


def sanitize_model_name(model_name):
    if not model_name or model_name == "未知":
        return "未分类"
    safe = re.sub(r'[\\/:*?"<>|]', "_", str(model_name)).strip()
    # 拦截 "." / ".." 及点开头名称：os.path.join(output_folder, "..") 会把文件写到输出目录之外
    if safe in (".", "..") or safe.startswith("."):
        return "未分类"
    return safe if safe else "未分类"
