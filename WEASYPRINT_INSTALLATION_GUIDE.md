# WeasyPrint 安装指南

## 一、概述

WeasyPrint 是一个用于将 HTML 和 CSS 转换为 PDF 的 Python 库，本项目使用它来实现 PDF 导出功能。由于 WeasyPrint 依赖于 GTK+ 运行时，安装过程相对复杂，本指南将详细说明在不同操作系统上的安装步骤。

## 二、Windows 系统安装步骤

### 1. 安装 GTK+ 运行时

WeasyPrint 在 Windows 上依赖于 GTK+ 3.0 运行时。请按照以下步骤安装：

1. 下载 GTK+ 3.0 运行时安装包：
   - 推荐下载地址：[GTK for Windows Runtime Environment Installer](https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer/releases)
   - 选择最新版本的安装包，例如 `gtk3-runtime-3.24.xx-202x-xx-xx.exe`

2. 运行安装程序：
   - 按照默认设置进行安装
   - 确保选择将 GTK+ 添加到系统 PATH 环境变量

3. 验证 GTK+ 安装：
   - 打开命令提示符（cmd）
   - 运行 `pkg-config --modversion gtk+-3.0`
   - 如果安装成功，将显示 GTK+ 版本号

### 2. 安装 WeasyPrint

1. 使用 pip 安装 WeasyPrint：
   ```bash
   pip install weasyprint
   ```

2. 验证安装：
   ```bash
   python -c "import weasyprint; print(weasyprint.__version__)"
   ```
   - 如果安装成功，将显示 WeasyPrint 版本号

## 三、Linux 系统安装步骤

### 1. 安装系统依赖

在 Ubuntu/Debian 系统上：
```bash
sudo apt-get update
sudo apt-get install -y python3-pip python3-dev libcairo2-dev libgdk-pixbuf2.0-dev libpango1.0-dev libffi-dev shared-mime-info
```

在 CentOS/RHEL 系统上：
```bash
sudo yum install -y python3-pip python3-devel cairo-devel gdk-pixbuf2-devel pango-devel libffi-devel
```

在 Fedora 系统上：
```bash
sudo dnf install -y python3-pip python3-devel cairo-devel gdk-pixbuf2-devel pango-devel libffi-devel
```

### 2. 安装 WeasyPrint

```bash
pip3 install weasyprint
```

### 3. 验证安装

```bash
python3 -c "import weasyprint; print(weasyprint.__version__)"
```

## 四、macOS 系统安装步骤

### 1. 安装系统依赖

使用 Homebrew 安装依赖：
```bash
brew install cairo pango gdk-pixbuf libffi
```

### 2. 安装 WeasyPrint

```bash
pip3 install weasyprint
```

### 3. 验证安装

```bash
python3 -c "import weasyprint; print(weasyprint.__version__)"
```

## 五、Docker 环境安装步骤

如果您在 Docker 容器中运行项目，可以使用以下 Dockerfile 作为参考：

```dockerfile
FROM python:3.9

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    build-essential \
    libcairo2-dev \
    libgdk-pixbuf2.0-dev \
    libpango1.0-dev \
    libffi-dev \
    shared-mime-info \
    && rm -rf /var/lib/apt/lists/*

# 安装 WeasyPrint
RUN pip install weasyprint

# 设置工作目录
WORKDIR /app

# 复制项目文件
COPY . /app

# 安装项目依赖
RUN pip install -r requirements.txt

# 运行项目
CMD ["python", "app.py"]
```

## 六、常见问题及解决方案

### 1. 无法找到 libgobject-2.0-0.dll

**问题**：在 Windows 上运行时出现错误：`OSError: cannot load library 'libgobject-2.0-0': error 0x7e`

**解决方案**：
- 确保 GTK+ 运行时已正确安装
- 确保 GTK+ 安装目录已添加到系统 PATH 环境变量
- 重启计算机以确保环境变量生效

### 2. 缺少 cairo 或 pango 库

**问题**：安装时出现错误：`Failed building wheel for WeasyPrint`

**解决方案**：
- 确保已安装所有必要的系统依赖
- 按照本指南中对应操作系统的步骤安装依赖

### 3. 版本兼容性问题

**问题**：WeasyPrint 版本与 Python 版本不兼容

**解决方案**：
- 对于 Python 3.10+，推荐使用 WeasyPrint 54.0+
- 对于 Python 3.9，推荐使用 WeasyPrint 52.5+
- 可以指定版本安装：`pip install weasyprint==54.0`

## 七、测试 PDF 导出功能

安装完成后，可以使用以下代码测试 PDF 导出功能：

```python
from report_export import report_exporter

# 测试数据
mock_session_data = {
    'fan_model': '测试型号',
    'stats_html': '<table><tr><th>转速</th><th>中位数</th></tr><tr><td>2500rpm</td><td>2.2</td></tr></table>',
    'evaluation_report': {
        'best_speeds': ['2500rpm']
    },
    'plots': {}
}

# 测试 PDF 导出
try:
    pdf_path = report_exporter.export_report_from_session(mock_session_data, "test_report")
    print(f"PDF 导出成功！保存到: {pdf_path}")
except Exception as e:
    print(f"PDF 导出失败: {e}")
```

## 八、故障排除

如果遇到安装问题，可以尝试以下步骤：

1. **检查系统环境**：确保操作系统版本与 WeasyPrint 兼容
2. **更新 pip**：`pip install --upgrade pip`
3. **安装特定版本**：尝试安装特定版本的 WeasyPrint
4. **查看详细错误信息**：运行安装命令时添加 `-v` 参数查看详细错误
5. **参考官方文档**：[WeasyPrint 官方安装指南](https://doc.courtbouillon.org/weasyprint/stable/first_steps.html#installation)

## 九、结论

通过本指南的步骤，您应该能够成功安装 WeasyPrint 及其依赖，从而启用项目的 PDF 导出功能。如果遇到任何问题，请参考故障排除部分或查阅官方文档。

---

**注意**：WeasyPrint 的安装过程可能因操作系统版本和环境差异而有所不同。如果遇到特殊情况，请根据实际环境进行调整。