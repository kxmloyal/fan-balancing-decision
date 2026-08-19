import json
import logging
import os
from typing import Any, Dict, List, Optional, Union

import pandas as pd

logger = logging.getLogger(__name__)


# 数据库连接配置
DB_CONNECTED = False
db = None
UploadFile = None
AnalysisResult = None

logger.info("数据处理模块初始化成功")


# ========== 基础工具函数 ==========
def allowed_file(filename: Optional[str], allowed_extensions: Union[List[str], set]) -> bool:
    """
    验证文件是否为支持的格式（CSV/XLSX/XLS/JSON/XML/TXT）

    Args:
        filename: 文件名
        allowed_extensions: 允许的文件扩展名列表或集合

    Returns:
        bool: 文件是否为允许的格式
    """
    # 检查文件名是否包含点号且有扩展名
    if not filename or "." not in filename:
        return False

    # 检查扩展名是否在允许列表中
    try:
        ext = filename.rsplit(".", 1)[1].lower()
        return ext in allowed_extensions
    except (IndexError, AttributeError):
        return False


_MAGIC_BYTES_MAP = {
    "csv": [b",", b";", b"\t"],
    "xlsx": [b"PK\x03\x04"],
    "xls": [b"\xd0\xcf\x11\xe0"],
    "json": [b"[", b"{"],
}


def validate_magic_bytes(file_path: str, ext: str) -> bool:
    ext_lower = ext.lower()
    if ext_lower not in _MAGIC_BYTES_MAP:
        return True
    try:
        with open(file_path, "rb") as f:
            header = f.read(16)
    except OSError:
        return False
    expected = _MAGIC_BYTES_MAP[ext_lower]
    for magic in expected:
        if header.startswith(magic):
            return True
    return False


def read_multiformat_file(file_path: str) -> pd.DataFrame:
    """
    读取多种格式文件，返回DataFrame，支持自动编码检测
    针对大数据量进行了优化：
    - 仅读取需要的行和列
    - 优化编码检测顺序
    - 减少不必要的内存使用

    Args:
        file_path: 文件路径

    Returns:
        pd.DataFrame: 读取的数据

    Raises:
        ValueError: 文件路径为空或不是文件
        FileNotFoundError: 文件不存在
        Exception: 文件读取失败时抛出异常
    """
    if not file_path:
        raise ValueError("文件路径不能为空")

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"文件不存在：{file_path}")

    if not os.path.isfile(file_path):
        raise ValueError(f"路径不是文件：{file_path}")

    try:
        ext = file_path.rsplit(".", 1)[1].lower()
    except IndexError:
        raise ValueError(f"文件没有扩展名：{file_path}")

    # 尝试的编码顺序（优化顺序，优先尝试最常用的编码）
    encodings = ["utf-8-sig", "gbk", "utf-8", "gb2312"]

    # 最大读取行数（考虑到业务需求，最多只需要31行：1行表头 + 30行数据）
    max_rows = 31

    # 文件读取方法映射，针对大数据量优化
    read_methods: Dict[str, Any] = {
        "xlsx": lambda: pd.read_excel(
            file_path,
            header=0,
            engine="openpyxl",
            nrows=max_rows,  # 仅读取需要的行数
            dtype=str,  # 先以字符串读取，减少内存占用
        ),
        "xls": lambda: pd.read_excel(file_path, header=0, engine="xlrd", nrows=max_rows, dtype=str),
        "json": lambda: pd.read_json(file_path, dtype=str).head(max_rows),  # 仅读取需要的行数
        "xml": lambda: pd.read_xml(file_path).head(max_rows),  # 仅读取需要的行数
    }

    # 处理CSV和TXT文件（需要编码检测）
    if ext in ["csv", "txt"]:
        sep = "," if ext == "csv" else "\t"
        for encoding in encodings:
            try:
                # 优化：仅读取需要的行数，减少内存占用
                df = pd.read_csv(
                    file_path,
                    header=0,
                    encoding=encoding,
                    sep=sep,
                    low_memory=False,
                    nrows=max_rows,  # 仅读取需要的行数
                    dtype=str,  # 先以字符串读取，减少内存占用
                )
                return df
            except UnicodeDecodeError:
                continue
            except (ValueError, IOError, TypeError):  # 捕获具体异常类型
                continue
        # 所有编码都失败
        raise Exception(f"文件读取失败：无法识别文件编码，已尝试：{', '.join(encodings)}")

    # 处理其他格式文件
    elif ext in read_methods:
        try:
            return read_methods[ext]()
        except AttributeError:
            if ext == "xml":
                raise ValueError("当前pandas版本不支持XML格式，请升级到1.3.0或更高版本")
            else:
                raise
        except (ValueError, IOError, TypeError) as e:  # 捕获具体异常类型
            raise Exception(f"文件读取失败：{str(e)}")
    else:
        raise ValueError(f"不支持的文件格式：{ext}")


# ========== 数据解析函数 ==========
def parse_single_surface_file(file_path: str) -> Dict[str, List[float]]:
    """
    解析单个面（P1/P2/ST）的文件：第一行转速，第2-31行最多30组数据
    针对大数据量进行了优化：
    - 减少不必要的数据转换和拷贝
    - 及时释放不再使用的内存
    - 优化循环结构，减少重复计算

    Args:
        file_path: 文件路径

    Returns:
        Dict[str, List[float]]: 解析后的数据，键为转速，值为样本数据列表

    Raises:
        ValueError: 解析失败时抛出异常
    """
    if not file_path:
        raise ValueError("文件路径不能为空")

    try:
        df = read_multiformat_file(file_path)
    except (ValueError, IOError, TypeError) as e:  # 捕获具体异常类型
        raise ValueError(f"读取文件失败：{str(e)}")

    # 检查DataFrame是否为空
    if df.empty:
        raise ValueError("文件内容为空")

    # 提取转速（表头），去除空列
    # 优化：使用列表推导式，减少临时变量
    speeds = [str(col).strip() for col in df.columns if str(col).strip() != ""]
    if not speeds:
        raise ValueError("文件无有效转速列（表头为空或格式不正确）")

    # 提取数据行（最多30行）
    # 优化：直接使用iloc，避免链式操作
    data_rows = df.dropna(how="all").iloc[:30]

    # 检查是否有数据行
    if data_rows.empty:
        raise ValueError("文件无有效数据行")

    # 提取每个转速的数据
    parsed_data: Dict[str, List[float]] = {}

    # 优化：预先转换为numpy数组，提高访问效率
    data_array = data_rows.to_numpy()

    # 优化：缓存列索引，避免重复查找
    speed_to_idx = {col: idx for idx, col in enumerate(data_rows.columns)}

    # 优化：使用向量化操作，减少循环次数
    for speed in speeds:
        try:
            # 检查列是否存在
            if speed not in speed_to_idx:
                raise ValueError(f"转速{speed}在数据行中不存在")

            # 获取列索引
            col_idx = speed_to_idx[speed]

            # 提取列数据
            speed_data = data_array[:, col_idx]

            # 过滤掉空值
            non_null_data = [
                x
                for x in speed_data
                if x is not None and str(x).strip() != "" and str(x).strip() != "nan"
            ]

            # 转换为数值类型
            try:
                # 优化：使用列表推导式，比pd.to_numeric更高效
                speed_samples = [float(x) for x in non_null_data][:30]  # 限制为30个
            except ValueError as e:
                raise ValueError(f"转速{speed}包含非数值数据（如文字、空格）：{str(e)}")

            if not speed_samples:
                raise ValueError(f"转速{speed}无有效数值数据")

            parsed_data[speed] = speed_samples
        except KeyError:
            raise ValueError(f"转速{speed}在数据行中不存在")
        except (ValueError, TypeError) as e:
            raise ValueError(f"转速{speed}包含非数值数据（如文字、空格）：{str(e)}")

    # 检查是否解析到有效数据
    if not parsed_data:
        raise ValueError("未解析到有效数据，请检查文件格式")

    # 优化：及时释放内存
    del df, data_rows, data_array, speed_to_idx

    return parsed_data


# ========== 数据库持久化函数 ==========
def save_upload_file(
    filename: str, file_path: str, file_size: int, user_id: Optional[str] = None
) -> bool:
    """
    保存上传文件信息到数据库

    Args:
        filename: 文件名
        file_path: 文件路径
        file_size: 文件大小
        user_id: 用户ID，可选

    Returns:
        bool: 保存是否成功
    """
    if not DB_CONNECTED:
        return False

    try:
        file_ext = os.path.splitext(filename)[1].lower().lstrip(".")
        upload_file = UploadFile(
            filename=filename,
            file_path=file_path,
            file_size=file_size,
            user_id=user_id,
            file_type=file_ext,
            status="uploaded",
        )
        db.session.add(upload_file)
        db.session.commit()
        return True
    except (ValueError, IOError, TypeError) as e:  # 捕获具体异常类型
        logger.error(f"保存上传文件到数据库失败: {str(e)}")
        db.session.rollback()
        return False


def save_analysis_result(
    user_id: Optional[str],
    fan_model: str,
    analysis_type: str,
    input_files: List[Dict[str, Any]],
    output_files: List[Dict[str, Any]],
    best_speed: Optional[str] = None,
) -> bool:
    """
    保存分析结果到数据库

    Args:
        user_id: 用户ID，可选
        fan_model: 扇叶型号
        analysis_type: 分析类型
        input_files: 输入文件列表
        output_files: 输出文件列表
        best_speed: 最优转速，可选

    Returns:
        bool: 保存是否成功
    """
    if not DB_CONNECTED:
        return False

    try:
        analysis_result = AnalysisResult(
            user_id=user_id,
            fan_model=fan_model,
            analysis_type=analysis_type,
            input_files=json.dumps(input_files),
            output_files=json.dumps(output_files),
            best_speed=best_speed,
            status="completed",
        )
        db.session.add(analysis_result)
        db.session.commit()
        # 失效仪表盘缓存（分析结果已变更）
        try:
            from app.utils.cache_utils import query_cache

            query_cache.delete("dashboard_data")
        except Exception:
            pass
        return True
    except (ValueError, IOError, TypeError) as e:  # 捕获具体异常类型
        logger.error(f"保存分析结果到数据库失败: {str(e)}")
        db.session.rollback()
        return False
