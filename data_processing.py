import pandas as pd
import os

# ========== 基础工具函数 ==========
def allowed_file(filename, allowed_extensions):
    """验证文件是否为支持的格式（CSV/XLSX/XLS/JSON/XML/TXT）"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

def read_multiformat_file(file_path):
    """读取多种格式文件，返回DataFrame"""
    ext = file_path.rsplit('.', 1)[1].lower()
    try:
        if ext == 'csv':
            return pd.read_csv(file_path, header=0, encoding='utf-8-sig')
        elif ext == 'xlsx':
            return pd.read_excel(file_path, header=0, engine='openpyxl')
        elif ext == 'xls':
            return pd.read_excel(file_path, header=0, engine='xlrd')
        elif ext == 'json':
            # 支持JSON格式
            return pd.read_json(file_path)
        elif ext == 'xml':
            # 支持XML格式
            try:
                return pd.read_xml(file_path)
            except AttributeError:
                # pandas版本较低不支持read_xml
                raise ValueError("当前pandas版本不支持XML格式，请升级到1.3.0或更高版本")
        elif ext == 'txt':
            # 支持TXT格式，默认使用制表符分隔
            return pd.read_csv(file_path, header=0, encoding='utf-8-sig', sep='\t')
        else:
            raise ValueError(f"不支持的文件格式：{ext}")
    except Exception as e:
        raise Exception(f"文件读取失败：{str(e)}")

# ========== 数据解析函数 ==========
def parse_single_surface_file(file_path):
    """解析单个面（P1/P2/ST）的文件：第一行转速，第2-31行最多30组数据"""
    try:
        # 读取文件
        df = read_multiformat_file(file_path)
        # 提取转速（表头），去除空列
        speeds = [str(col).strip() for col in df.columns if str(col).strip() != '']
        if len(speeds) == 0:
            raise ValueError("文件无有效转速列（表头为空）")
        # 提取数据行（第2-31行，最多30行）
        data_rows = df.dropna(how='all').iloc[0:30]  # 仅取前30行有效数据
        # 提取每个转速的数据
        parsed_data = {}  # 格式：{speed: [最多30个样本值]}
        for speed in speeds:
            speed_data = data_rows[speed].dropna().tolist()
            # 验证数据类型（必须为数值）
            try:
                speed_samples = [float(val) for val in speed_data]
            except ValueError:
                raise ValueError(f"转速{speed}包含非数值数据（如文字、空格）")
            # 限制最多30个数据点
            if len(speed_samples) > 30:
                speed_samples = speed_samples[:30]
            parsed_data[speed] = speed_samples
        return parsed_data
    except Exception as e:
        raise Exception(f"文件解析失败：{str(e)}")

def parse_triple_surface_files(p1_file_path, p2_file_path, st_file_path=None):
    """
    解析三个面（P1/P2/ST）的文件
    
    Args:
        p1_file_path (str): P1面文件路径
        p2_file_path (str): P2面文件路径
        st_file_path (str, optional): ST面文件路径，默认为None
        
    Returns:
        dict: 包含三个面数据的字典
    """
    # 解析P1面
    p1_data = parse_single_surface_file(p1_file_path)
    
    # 解析P2面
    p2_data = parse_single_surface_file(p2_file_path)
    
    # 如果提供了ST面文件，也解析它
    st_data = None
    if st_file_path:
        st_data = parse_single_surface_file(st_file_path)
    
    return {
        'p1': p1_data,
        'p2': p2_data,
        'st': st_data
    }