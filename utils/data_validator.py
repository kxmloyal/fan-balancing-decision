import math

def validate_and_align_data(p1_samples, p2_samples, st_samples=None):
    """
    验证并对齐P1和P2面的数据，确保生成正确的ST面数据
    
    Args:
        p1_samples (list): P1面数据列表
        p2_samples (list): P2面数据列表
        st_samples (list, optional): ST面数据列表，默认为None
        
    Returns:
        tuple: (p1_aligned, p2_aligned, st_samples, data_info)
               - p1_aligned: 对齐后的P1数据
               - p2_aligned: 对齐后的P2数据
               - st_samples: ST面数据（必须提供，不能通过计算得出）
               - data_info: 数据信息字典
    """
    # 获取数据长度
    p1_len = len(p1_samples)
    p2_len = len(p2_samples)
    st_len = len(st_samples) if st_samples is not None else 0
    
    # 确定共同长度
    common_length = min(p1_len, p2_len, 30)  # 最多30组数据
    if st_samples is not None:
        common_length = min(common_length, st_len)
    
    # 截取共同长度的数据
    p1_aligned = p1_samples[:common_length]
    p2_aligned = p2_samples[:common_length]
    
    # 如果数据不足30组，用NaN填充
    if common_length < 30:
        p1_aligned.extend([float('nan')] * (30 - common_length))
        p2_aligned.extend([float('nan')] * (30 - common_length))
    
    # 处理ST面数据（必须提供，不能通过计算得出）
    if st_samples is not None:
        # 直接使用提供的ST面数据
        st_aligned = st_samples[:common_length]
        if common_length < 30:
            st_aligned.extend([float('nan')] * (30 - common_length))
    else:
        # 如果没有提供ST面数据，则ST面数据全部为NaN
        st_aligned = [float('nan')] * 30
    
    # 数据信息
    data_info = {
        'p1_length': p1_len,
        'p2_length': p2_len,
        'st_length': st_len if st_samples is not None else 0,
        'common_length': common_length,
        'is_complete': common_length == 30,
        'p1_valid': p1_len == 30,
        'p2_valid': p2_len == 30,
        'st_valid': st_len == 30 if st_samples is not None else False,
        'st_provided': st_samples is not None
    }
    
    return p1_aligned, p2_aligned, st_aligned, data_info

def generate_data_warning(data_info, speed):
    """
    根据数据信息生成警告消息
    
    Args:
        data_info (dict): 数据信息字典
        speed (str): 转速标识
        
    Returns:
        str: 警告消息，如果没有问题则返回空字符串
    """
    warnings = []
    
    if not data_info['p1_valid']:
        warnings.append(f"P1面{speed}数据量为{data_info['p1_length']}组，{'少于' if data_info['p1_length'] < 30 else '超过'}标准30组")
    
    if not data_info['p2_valid']:
        warnings.append(f"P2面{speed}数据量为{data_info['p2_length']}组，{'少于' if data_info['p2_length'] < 30 else '超过'}标准30组")
    
    # 注释掉ST面的警告，按照用户要求取消ST面警告
    # if data_info['st_provided'] and not data_info['st_valid']:
    #     warnings.append(f"ST面{speed}数据量为{data_info['st_length']}组，{'少于' if data_info['st_length'] < 30 else '超过'}标准30组")
    # elif not data_info['st_provided']:
    #     warnings.append(f"ST面{speed}未提供数据，将显示为空")
    
    if not data_info['is_complete']:
        warnings.append(f"数据仅使用{data_info['common_length']}组配对")
    
    return "; ".join(warnings) if warnings else ""