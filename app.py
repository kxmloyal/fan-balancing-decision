import os
import re
import logging
from datetime import timedelta
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, send_from_directory, send_file
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge
import pandas as pd
import base64
from data_processing import parse_single_surface_file
from utils.data_validator import validate_and_align_data, generate_data_warning
from chart_generation import generate_plots, generate_single_surface_plots, create_combined_chart
from statistics import generate_stats, generate_single_surface_stats

# ========== Flask应用配置 ==========
app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # 在生产环境中应使用安全的密钥
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 最大文件大小16MB
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['OUTPUT_FOLDER'] = 'outputs'
app.config['ALLOWED_EXTENSIONS'] = {'csv', 'xlsx', 'xls'}

# 确保必要的目录存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

# 配置日志记录
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ========== 辅助函数 ==========
def allowed_file(filename, allowed_extensions):
    """检查文件扩展名是否允许"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

def cleanup_old_files():
    """清理旧文件（简化版本）"""
    # 实际部署时可能需要更复杂的清理逻辑
    pass

request_count = 0

def before_request():
    global request_count
    request_count += 1
    if request_count >= 100:
        request_count = 0
        cleanup_old_files()

# ========== 路由函数 ==========
@app.route('/', methods=['GET', 'POST'])
def index():
    """主页：文件上传+结果展示"""
    if request.method == 'POST':
        # 检查是否是图表类型更新请求
        p1_file = request.files.get('p1_file')
        p2_file = request.files.get('p2_file')
        st_file = request.files.get('st_file')
        
        # 更准确地检测图表更新请求，确保文件对象存在且文件名不为空
        is_chart_update = ('chart_types' in request.form or 'chart_update' in request.form) and not (
            (p1_file and p1_file.filename != '' and p1_file.filename is not None) or 
            (p2_file and p2_file.filename != '' and p2_file.filename is not None) or 
            (st_file and st_file.filename != '' and st_file.filename is not None)
        )
        
        if is_chart_update:
            # 图表类型更新请求，从session获取数据
            saved_results = session.get('saved_results')
            if not saved_results:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify({'success': False, 'message': '会话已过期，请重新上传数据文件！'})
                flash('会话已过期，请重新上传数据文件！')
                return redirect(request.url)
            
            # 获取图表类型选择
            chart_types_str = request.form.get('chart_types', 'box')
            chart_types = chart_types_str.split(',') if chart_types_str else ['box']
            
            # 获取图表布局选择
            chart_layout = request.form.get('chartLayout', 'stacked')
            
            # 记录日志以便调试
            app.logger.info(f"图表类型: {chart_types}")
            app.logger.info(f"图表布局: {chart_layout}")
            
            # 重新生成图表
            try:
                if saved_results.get('single_surface'):
                    # 单一面情况
                    plots = generate_single_surface_plots(
                        saved_results['parsed_data'], 
                        saved_results['output_prefix'], 
                        saved_results['single_surface'],
                        app.config['OUTPUT_FOLDER'],
                        chart_types
                    )
                else:
                    # 双面或多面情况
                    plots = generate_plots(
                        saved_results['parsed_data'], 
                        saved_results['output_prefix'], 
                        app.config['OUTPUT_FOLDER'], 
                        chart_types
                    )
            except Exception as e:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify({'success': False, 'message': f'图表生成失败：{str(e)}'})
                flash(f'图表生成失败：{str(e)}')
                return redirect(request.url)
            
            # 页面变量
            has_p1 = saved_results['has_p1']
            has_p2 = saved_results['has_p2']
            has_st = saved_results['has_st']
            
            # 更新保存的结果
            saved_results['plots'] = plots
            saved_results['chart_types'] = chart_types  # 保存图表类型选择
            saved_results['chart_layout'] = chart_layout  # 保存图表布局选择
            session['saved_results'] = saved_results
            
            # 检查是否是 AJAX 请求
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                # 直接返回更新后的图表数据，让前端重新渲染
                return jsonify({
                    'success': True,
                    'message': '图表更新成功',
                    'chart_types': chart_types,
                    'chart_layout': chart_layout
                })
            else:
                # 返回完整页面
                return render_template('index.html', 
                                     plots=plots, 
                                     stats_html=saved_results['stats_html'], 
                                     stats_csv=saved_results['stats_csv'],
                                     has_p1=has_p1,
                                     has_p2=has_p2,
                                     has_st=has_st,
                                     saved_results=saved_results)
        
        # 文件上传处理流程
        surface_data = {}
        upload_files = []
        
        # 解析P1面文件（如果上传）
        if p1_file and p1_file.filename != '':
            if allowed_file(p1_file.filename, app.config['ALLOWED_EXTENSIONS']):
                p1_filename = secure_filename(f'p1_{p1_file.filename}')
                p1_path = os.path.join(app.config['UPLOAD_FOLDER'], p1_filename)
                p1_file.save(p1_path)
                upload_files.append(p1_filename)
                try:
                    surface_data['p1'] = parse_single_surface_file(p1_path)
                except Exception as e:
                    flash(f'P1面文件处理失败：{str(e)}')
                    return redirect(request.url)
            else:
                flash(f'P1面文件格式不支持：{p1_file.filename}，仅支持CSV/XLSX/XLS')
                return redirect(request.url)
        
        # 解析P2面文件（如果上传）
        if p2_file and p2_file.filename != '':
            if allowed_file(p2_file.filename, app.config['ALLOWED_EXTENSIONS']):
                p2_filename = secure_filename(f'p2_{p2_file.filename}')
                p2_path = os.path.join(app.config['UPLOAD_FOLDER'], p2_filename)
                p2_file.save(p2_path)
                upload_files.append(p2_filename)
                try:
                    surface_data['p2'] = parse_single_surface_file(p2_path)
                except Exception as e:
                    flash(f'P2面文件处理失败：{str(e)}')
                    return redirect(request.url)
            else:
                flash(f'P2面文件格式不支持：{p2_file.filename}，仅支持CSV/XLSX/XLS')
                return redirect(request.url)
        
        # 解析ST面文件（如果上传）
        if st_file and st_file.filename != '':
            if allowed_file(st_file.filename, app.config['ALLOWED_EXTENSIONS']):
                st_filename = secure_filename(f'st_{st_file.filename}')
                st_path = os.path.join(app.config['UPLOAD_FOLDER'], st_filename)
                st_file.save(st_path)
                upload_files.append(st_filename)
                try:
                    surface_data['st'] = parse_single_surface_file(st_path)
                except Exception as e:
                    flash(f'ST面文件处理失败：{str(e)}')
                    return redirect(request.url)
            else:
                flash(f'ST面文件格式不支持：{st_file.filename}，仅支持CSV/XLSX/XLS')
                return redirect(request.url)
        
        # 必须至少上传一个文件
        if not surface_data:
            flash('请至少上传一个面的数据文件！')
            return redirect(request.url)
        
        # 生成输出前缀
        output_prefix = '_'.join([os.path.splitext(f)[0] for f in upload_files])
        plots = {}
        stats_html = None
        stats_csv = None
        
        # 场景1：同时上传P1和P2面（可能还有ST面）
        if 'p1' in surface_data and 'p2' in surface_data:
            p1_speeds = sorted(surface_data['p1'].keys())
            p2_speeds = sorted(surface_data['p2'].keys())
            st_data = surface_data.get('st', {})
            
            # 存储数据到Session，供匹配页面使用
            session['p1_data'] = surface_data['p1']
            session['p2_data'] = surface_data['p2']
            session['st_data'] = st_data
            session['output_prefix'] = output_prefix
            
            # 转速完全一致：直接生成结果
            if set(p1_speeds) == set(p2_speeds):
                common_speeds = p1_speeds
                parsed_data = []
                # 对应的数据验证对齐
                data_warnings = []
                for speed in common_speeds:
                    # 数据验证对齐
                    st_samples_for_speed = st_data.get(speed) if speed in st_data else None
                    p1_aligned, p2_aligned, st_samples, data_info = validate_and_align_data(
                        surface_data['p1'][speed], surface_data['p2'][speed], st_samples_for_speed)
                    
                    # 数据警告（存在即添加）
                    warning_msg = generate_data_warning(data_info, speed)
                    if warning_msg:
                        data_warnings.append(warning_msg)
                    
                    parsed_data.append({
                        'speed': speed,
                        'p1_samples': p1_aligned,
                        'p2_samples': p2_aligned,
                        'sum_samples': st_samples
                    })
                
                # 数据警告如果有的话，添加到flash消息
                if data_warnings:
                    flash('数据警告：' + '; '.join(data_warnings))
                plots = generate_plots(parsed_data, output_prefix, app.config['OUTPUT_FOLDER'])
                try:
                    stats_html, stats_csv = generate_stats(parsed_data, output_prefix, app.config['OUTPUT_FOLDER'])
                except Exception as e:
                    flash(f'统计报告生成失败：{str(e)}')
                    return redirect(request.url)
                
                # 页面变量
                has_p1 = bool(surface_data.get('p1'))
                has_p2 = bool(surface_data.get('p2'))
                has_st = bool(surface_data.get('st'))
                
                # 保存结果到session，用于图表更新
                saved_results = {
                    'parsed_data': parsed_data,
                    'output_prefix': output_prefix,
                    'stats_html': stats_html,
                    'stats_csv': stats_csv,
                    'has_p1': has_p1,
                    'has_p2': has_p2,
                    'has_st': has_st,
                    'single_surface': None,
                    'plots': plots,
                    'chart_types': ['box'],  # 默认图表类型
                    'chart_layout': 'stacked'  # 默认图表布局
                }
                session['saved_results'] = saved_results
                
                return render_template('index.html',
                                     plots=plots,
                                     stats_html=stats_html,
                                     stats_csv=os.path.basename(stats_csv) if stats_csv else None,
                                     has_p1=has_p1,
                                     has_p2=has_p2,
                                     has_st=has_st,
                                     saved_results=saved_results)
            
            # 转速不一致：跳转到匹配页面
            else:
                return redirect(url_for('match_speeds'))
        
        # 场景2：只上传了单个面（P1/P2/ST）
        else:
            # 确定上传的是哪个面
            surface_type = None
            if 'p1' in surface_data:
                surface_type = 'p1'
                single_surface_data = surface_data['p1']
            elif 'p2' in surface_data:
                surface_type = 'p2'
                single_surface_data = surface_data['p2']
            elif 'st' in surface_data:
                surface_type = 'st'
                single_surface_data = surface_data['st']
            
            # 构造标准格式数据
            parsed_data = []
            for speed, samples in single_surface_data.items():
                item = {
                    'speed': speed,
                    'p1_samples': samples if surface_type == 'p1' else [],
                    'p2_samples': samples if surface_type == 'p2' else [],
                    'sum_samples': samples if surface_type == 'st' else []
                }
                parsed_data.append(item)
            
            # 生成单面图表
            plots = generate_single_surface_plots(parsed_data, output_prefix, surface_type, app.config['OUTPUT_FOLDER'])
            
            # 生成统计报告
            try:
                stats_html, stats_csv = generate_single_surface_stats(parsed_data, output_prefix, surface_type, app.config['OUTPUT_FOLDER'])
            except Exception as e:
                flash(f'统计报告生成失败：{str(e)}')
                return redirect(request.url)
            
            # 页面变量
            has_p1 = (surface_type == 'p1')
            has_p2 = (surface_type == 'p2')
            has_st = (surface_type == 'st')
            
            # 保存结果到session，用于图表更新
            saved_results = {
                'parsed_data': parsed_data,
                'output_prefix': output_prefix,
                'stats_html': stats_html,
                'stats_csv': stats_csv,
                'has_p1': has_p1,
                'has_p2': has_p2,
                'has_st': has_st,
                'single_surface': surface_type,
                'plots': plots,
                'chart_types': ['box'],  # 默认图表类型
                'chart_layout': 'stacked'  # 默认图表布局
            }
            session['saved_results'] = saved_results
                            
            # 结果渲染
            return render_template('index.html',
                                 plots=plots,
                                 stats_html=stats_html,
                                 stats_csv=os.path.basename(stats_csv) if stats_csv else None,
                                 has_p1=has_p1,
                                 has_p2=has_p2,
                                 has_st=has_st,
                                 saved_results=saved_results)

    # GET请求：空页面渲染
    return render_template('index.html',
                         plots=None, stats_html=None, stats_csv=None,
                         has_p1=False, has_p2=False, has_st=False)

@app.route('/match_speeds', methods=['GET', 'POST'])
def match_speeds():
    """转速匹配页面：P1和P2面转速不一致时触发"""
    # 验证Session数据
    if 'p1_data' not in session or 'p2_data' not in session:
        flash('无待匹配的转速数据，请先上传P1和P2面文件！')
        return redirect(url_for('index'))
    
    p1_data = session['p1_data']
    p2_data = session['p2_data']
    st_data = session.get('st_data', {})  # 获取ST面数据（如果有的话）
    p1_speeds = sorted(p1_data.keys())
    p2_speeds = sorted(p2_data.keys())
    output_prefix = session['output_prefix']
    
    # GET请求：展示匹配页面
    if request.method == 'GET':
        # 自动推荐匹配（基于数字相似度）
        def normalize_speed(speed):
            """标准化转速：提取数字部分"""
            return ''.join([c for c in str(speed) if c.isdigit()])
        
        default_matches = []
        for p1_speed in p1_speeds:
            normalized_p1 = normalize_speed(p1_speed)
            matched_p2 = None
            for p2_speed in p2_speeds:
                if normalize_speed(p2_speed) == normalized_p1:
                    matched_p2 = p2_speed
                    break
            default_matches.append({'p1_speed': p1_speed, 'matched_p2': matched_p2})
        
        return render_template('match_speeds.html',
                             default_matches=default_matches,
                             p2_speeds=p2_speeds)
    
    # POST请求：处理匹配结果
    else:
        # 解析用户的匹配关系
        match_relations = {}
        for p1_speed in p1_speeds:
            selected_p2 = request.form.get(f'match_{p1_speed}')
            match_relations[p1_speed] = selected_p2 if selected_p2 != 'none' else None
        
        # 分类：已匹配/未匹配
        matched_pairs = []  # [(p1_speed, p2_speed)]
        unmatched_p1 = []   # 未匹配的P1转速
        unmatched_p2 = set(p2_speeds)  # 未匹配的P2转速
        
        for p1_speed, p2_speed in match_relations.items():
            if p2_speed and p2_speed in p2_data:
                matched_pairs.append((p1_speed, p2_speed))
                if p2_speed in unmatched_p2:
                    unmatched_p2.remove(p2_speed)
            else:
                unmatched_p1.append(p1_speed)
        
        # 准备分析数据
        parsed_data = []  # 匹配数据
        single_parsed_data = {'p1': [], 'p2': []}  # 未匹配数据
        
        # 匹配数据处理
        data_warnings = []
        for p1_speed, p2_speed in matched_pairs:
            # 数据验证和对齐
            st_samples_for_pair = st_data.get(p1_speed) if p1_speed in st_data else None
            p1_aligned, p2_aligned, st_samples, data_info = validate_and_align_data(
                p1_data[p1_speed], p2_data[p2_speed], st_samples_for_pair)
            
            # 生成数据警告（如果有）
            warning_msg = generate_data_warning(data_info, f'{p1_speed}↔{p2_speed}')
            if warning_msg:
                data_warnings.append(warning_msg)
            
            parsed_data.append({
                'speed': f'{p1_speed} ↔ {p2_speed}',
                'p1_samples': p1_aligned,
                'p2_samples': p2_aligned,
                'sum_samples': st_samples
            })
        
        # 如果有数据警告，添加到flash消息
        if data_warnings:
            flash('数据警告：' + '; '.join(data_warnings))
        
        # 处理未匹配P1数据
        for p1_speed in unmatched_p1:
            single_parsed_data['p1'].append({
                'speed': p1_speed,
                'p1_samples': p1_data[p1_speed],
                'p2_samples': [],
                'sum_samples': []
            })
        
        # 处理未匹配P2数据
        for p2_speed in unmatched_p2:
            single_parsed_data['p2'].append({
                'speed': p2_speed,
                'p1_samples': [],
                'p2_samples': p2_data[p2_speed],
                'sum_samples': []
            })
        
        # 图表生成
        plots = {}
        if parsed_data:
            matched_plots = generate_plots(parsed_data, f'{output_prefix}_matched', app.config['OUTPUT_FOLDER'])
            # 转换为文件名（前端访问用）
            for key, val in matched_plots.items():
                plots[key] = {'png': os.path.basename(val['png']), 'html': os.path.basename(val['html'])}
        
        # 未匹配P1图表
        if single_parsed_data['p1']:
            p1_single_plots = generate_single_surface_plots(single_parsed_data['p1'], f'{output_prefix}_p1_unmatched', 'p1', app.config['OUTPUT_FOLDER'])
            plots['p1_unmatched'] = {}
            for key, val in p1_single_plots['single'].items():
                plots['p1_unmatched'][key] = {'png': os.path.basename(val['png']), 'html': os.path.basename(val['html'])}
        
        # 未匹配P2图表
        if single_parsed_data['p2']:
            p2_single_plots = generate_single_surface_plots(single_parsed_data['p2'], f'{output_prefix}_p2_unmatched', 'p2', app.config['OUTPUT_FOLDER'])
            plots['p2_unmatched'] = {}
            for key, val in p2_single_plots['single'].items():
                plots['p2_unmatched'][key] = {'png': os.path.basename(val['png']), 'html': os.path.basename(val['html'])}
        
        # 生成统计报告
        stats_html = ""
        stats_csv_paths = []
        
        # 匹配统计数据（支持IQR高亮）
        if parsed_data:
            try:
                matched_stats_html, matched_stats_csv = generate_stats(parsed_data, f'{output_prefix}_matched', app.config['OUTPUT_FOLDER'])
            except Exception as e:
                flash(f'统计报告生成失败：{str(e)}')
                return redirect(request.url)
            stats_html += f"<h6 class='mt-4 mb-2'>已匹配转速统计（{len(parsed_data)}組）</h6>{matched_stats_html}"
            stats_csv_paths.append(matched_stats_csv)
        
        # 未匹配P1统计（支持IQR高亮）
        if single_parsed_data['p1']:
            try:
                p1_single_stats_html, p1_single_stats_csv = generate_single_surface_stats(single_parsed_data['p1'], f'{output_prefix}_p1_unmatched', 'p1', app.config['OUTPUT_FOLDER'])
            except Exception as e:
                flash(f'统计报告生成失败：{str(e)}')
                return redirect(request.url)
            stats_html += f"<h6 class='mt-4 mb-2'>未匹配P1转速统计（{len(single_parsed_data['p1'])}个）</h6>{p1_single_stats_html}"
            stats_csv_paths.append(p1_single_stats_csv)
        
        # 未匹配P2统计（支持IQR高亮）
        if single_parsed_data['p2']:
            try:
                p2_single_stats_html, p2_single_stats_csv = generate_single_surface_stats(single_parsed_data['p2'], f'{output_prefix}_p2_unmatched', 'p2', app.config['OUTPUT_FOLDER'])
            except Exception as e:
                flash(f'统计报告生成失败：{str(e)}')
                return redirect(request.url)
            stats_html += f"<h6 class='mt-4 mb-2'>未匹配P2转速统计（{len(single_parsed_data['p2'])}个）</h6>{p2_single_stats_html}"
            stats_csv_paths.append(p2_single_stats_csv)
        
        # 合并统计CSV
        if stats_csv_paths:
            combined_csv_path = os.path.join(app.config['OUTPUT_FOLDER'], f'{output_prefix}_combined_stats.csv')
            combined_df = pd.concat([pd.read_csv(path) for path in stats_csv_paths], ignore_index=True)
            combined_df.to_csv(combined_csv_path, index=False, encoding='utf-8-sig')
            stats_csv = combined_csv_path
        else:
            stats_csv = None
        
        # 页面变量
        has_p1 = bool(single_parsed_data['p1']) or bool(parsed_data)
        has_p2 = bool(single_parsed_data['p2']) or bool(parsed_data)
        has_st = bool(st_data)
        
        # 保存结果到session，用于图表更新
        saved_results = {
            'parsed_data': parsed_data,
            'single_parsed_data': single_parsed_data,
            'output_prefix': output_prefix,
            'stats_html': stats_html,
            'stats_csv': stats_csv,
            'has_p1': has_p1,
            'has_p2': has_p2,
            'has_st': has_st,
            'single_surface': None,
            'plots': plots,
            'chart_types': ['box'],  # 默认图表类型
            'chart_layout': 'stacked'  # 默认图表布局
        }
        session['saved_results'] = saved_results
        
        return render_template('match_result.html',
                             plots=plots,
                             stats_html=stats_html,
                             stats_csv=os.path.basename(stats_csv) if stats_csv else None,
                             has_p1=has_p1,
                             has_p2=has_p2,
                             has_st=has_st,
                             saved_results=saved_results)

@app.route('/download/<filename>')
def download_file(filename):
    """文件下载路由"""
    try:
        return send_from_directory(app.config['OUTPUT_FOLDER'], filename, as_attachment=True)
    except FileNotFoundError:
        flash('请求的文件不存在')
        return redirect(request.url)

@app.route('/export_report')
def export_report():
    """导出完整HTML报告"""
    # 从session获取数据
    saved_results = session.get('saved_results')
    if not saved_results:
        flash('会话已过期，请重新上传数据文件！')
        return redirect(url_for('index'))
    
    # 生成报告内容
    report_title = "设备不平衡量分析报告"
    report_time = pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # 准备图表HTML片段
    plots = saved_results.get('plots', {})
    has_p1 = saved_results.get('has_p1', False)
    has_p2 = saved_results.get('has_p2', False)
    has_st = saved_results.get('has_st', False)
    
    # 开始构建图表HTML
    charts_html = ""
    
    # 只有在有图表数据时才生成图表区域
    if plots:
        # 开始堆叠显示区域
        charts_html += '<div class="chart-stacked">'
        
        # P1面图
        if plots.get('p1') and has_p1:
            charts_html += '<div class="chart-group">'
            charts_html += '<h3>P1面数据图表</h3>'
            for chart_type, chart_files in plots['p1'].items():
                chart_title = f"P1面不平衡量{ {'box': '箱线图', 'violin': '小提琴图', 'scatter': '散点图', 'trend': '趋势图', 'heatmap': '热力图', 'histogram': '直方图', 'radar': '雷达图', '3d': '3D散点图'}.get(chart_type, chart_type) }"
                # 使用url_for生成正确的链接
                chart_png_url = url_for('download_file', filename=chart_files['png'])
                chart_html_url = url_for('download_file', filename=chart_files['html'])
                
                # 为导出报告添加base64编码的图像数据
                png_file_path = os.path.join(app.config['OUTPUT_FOLDER'], chart_files['png'])
                img_base64 = ""
                if os.path.exists(png_file_path):
                    with open(png_file_path, "rb") as img_file:
                        img_base64 = base64.b64encode(img_file.read()).decode('utf-8')
                
                charts_html += f'''
                <div class="chart-section">
                    <h4>{chart_title}</h4>
                    <div class="chart-img-container">
                '''
                if img_base64:
                    charts_html += f'''<img src="data:image/png;base64,{img_base64}" alt="{chart_title}" style="max-width: 100%; height: auto;" class="chart-img" data-chart-title="{chart_title}" data-chart-src="{chart_html_url}">'''
                else:
                    charts_html += f'''<img src="{chart_png_url}" alt="{chart_title}" style="max-width: 100%; height: auto;" class="chart-img" data-chart-title="{chart_title}" data-chart-src="{chart_html_url}">'''
                charts_html += '''
                    </div>
                    <div class="chart-links">
                        <a href="''' + chart_png_url + '''" class="btn btn-sm btn-outline-secondary" download>
                            <i class="bi bi-download me-1"></i>下载PNG图表
                        </a> | 
                        <a href="''' + chart_html_url + '''" class="btn btn-sm btn-outline-primary chart-link" download>
                            <i class="bi bi-download me-1"></i>下载交互式HTML图表
                        </a>
                    </div>
                </div>
                '''
            charts_html += '</div>'
        
        # P2面图
        if plots.get('p2') and has_p2:
            charts_html += '<div class="chart-group">'
            charts_html += '<h3>P2面数据图表</h3>'
            for chart_type, chart_files in plots['p2'].items():
                chart_title = f"P2面不平衡量{ {'box': '箱线图', 'violin': '小提琴图', 'scatter': '散点图', 'trend': '趋势图', 'heatmap': '热力图', 'histogram': '直方图', 'radar': '雷达图', '3d': '3D散点图'}.get(chart_type, chart_type) }"
                # 使用url_for生成正确的链接
                chart_png_url = url_for('download_file', filename=chart_files['png'])
                chart_html_url = url_for('download_file', filename=chart_files['html'])
                
                # 为导出报告添加base64编码的图像数据
                png_file_path = os.path.join(app.config['OUTPUT_FOLDER'], chart_files['png'])
                img_base64 = ""
                if os.path.exists(png_file_path):
                    with open(png_file_path, "rb") as img_file:
                        img_base64 = base64.b64encode(img_file.read()).decode('utf-8')
                
                charts_html += f'''
                <div class="chart-section">
                    <h4>{chart_title}</h4>
                    <div class="chart-img-container">
                '''
                if img_base64:
                    charts_html += f'''<img src="data:image/png;base64,{img_base64}" alt="{chart_title}" style="max-width: 100%; height: auto;" class="chart-img" data-chart-title="{chart_title}" data-chart-src="{chart_html_url}">'''
                else:
                    charts_html += f'''<img src="{chart_png_url}" alt="{chart_title}" style="max-width: 100%; height: auto;" class="chart-img" data-chart-title="{chart_title}" data-chart-src="{chart_html_url}">'''
                charts_html += '''
                    </div>
                    <div class="chart-links">
                        <a href="''' + chart_png_url + '''" class="btn btn-sm btn-outline-secondary" download>
                            <i class="bi bi-download me-1"></i>下载PNG图表
                        </a> | 
                        <a href="''' + chart_html_url + '''" class="btn btn-sm btn-outline-primary chart-link" download>
                            <i class="bi bi-download me-1"></i>下载交互式HTML图表
                        </a>
                    </div>
                </div>
                '''
            charts_html += '</div>'
        
        # ST面图
        if plots.get('sum') and has_st:
            charts_html += '<div class="chart-group">'
            charts_html += '<h3>ST面数据图表</h3>'
            for chart_type, chart_files in plots['sum'].items():
                chart_title = f"ST面不平衡量{ {'box': '箱线图', 'violin': '小提琴图', 'scatter': '散点图', 'trend': '趋势图', 'heatmap': '热力图', 'histogram': '直方图', 'radar': '雷达图', '3d': '3D散点图'}.get(chart_type, chart_type) }"
                # 使用url_for生成正确的链接
                chart_png_url = url_for('download_file', filename=chart_files['png'])
                chart_html_url = url_for('download_file', filename=chart_files['html'])
                
                # 为导出报告添加base64编码的图像数据
                png_file_path = os.path.join(app.config['OUTPUT_FOLDER'], chart_files['png'])
                img_base64 = ""
                if os.path.exists(png_file_path):
                    with open(png_file_path, "rb") as img_file:
                        img_base64 = base64.b64encode(img_file.read()).decode('utf-8')
                
                charts_html += f'''
                <div class="chart-section">
                    <h4>{chart_title}</h4>
                    <div class="chart-img-container">
                '''
                if img_base64:
                    charts_html += f'''<img src="data:image/png;base64,{img_base64}" alt="{chart_title}" style="max-width: 100%; height: auto;" class="chart-img" data-chart-title="{chart_title}" data-chart-src="{chart_html_url}">'''
                else:
                    charts_html += f'''<img src="{chart_png_url}" alt="{chart_title}" style="max-width: 100%; height: auto;" class="chart-img" data-chart-title="{chart_title}" data-chart-src="{chart_html_url}">'''
                charts_html += '''
                    </div>
                    <div class="chart-links">
                        <a href="''' + chart_png_url + '''" class="btn btn-sm btn-outline-secondary" download>
                            <i class="bi bi-download me-1"></i>下载PNG图表
                        </a> | 
                        <a href="''' + chart_html_url + '''" class="btn btn-sm btn-outline-primary chart-link" download>
                            <i class="bi bi-download me-1"></i>下载交互式HTML图表
                        </a>
                    </div>
                </div>
                '''
            charts_html += '</div>'
        
        # 单面图（当只有一个面时）
        if plots.get('single'):
            surface_type = saved_results.get('single_surface', '未知')
            surface_name = {'p1': 'P1', 'p2': 'P2', 'st': 'ST'}.get(surface_type, surface_type)
            charts_html += '<div class="chart-group">'
            charts_html += f'<h3>{surface_name}面数据图表</h3>'
            for chart_type, chart_files in plots['single'].items():
                chart_title = f"{surface_name}面不平衡量{ {'box': '箱线图', 'violin': '小提琴图', 'scatter': '散点图', 'trend': '趋势图', 'heatmap': '热力图', 'histogram': '直方图', 'radar': '雷达图', '3d': '3D散点图'}.get(chart_type, chart_type) }"
                # 使用url_for生成正确的链接
                chart_png_url = url_for('download_file', filename=chart_files['png'])
                chart_html_url = url_for('download_file', filename=chart_files['html'])
                
                # 为导出报告添加base64编码的图像数据
                png_file_path = os.path.join(app.config['OUTPUT_FOLDER'], chart_files['png'])
                img_base64 = ""
                if os.path.exists(png_file_path):
                    with open(png_file_path, "rb") as img_file:
                        img_base64 = base64.b64encode(img_file.read()).decode('utf-8')
                
                charts_html += f'''
                <div class="chart-section">
                    <h4>{chart_title}</h4>
                    <div class="chart-img-container">
                '''
                if img_base64:
                    charts_html += f'''<img src="data:image/png;base64,{img_base64}" alt="{chart_title}" style="max-width: 100%; height: auto;" class="chart-img" data-chart-title="{chart_title}" data-chart-src="{chart_html_url}">'''
                else:
                    charts_html += f'''<img src="{chart_png_url}" alt="{chart_title}" style="max-width: 100%; height: auto;" class="chart-img" data-chart-title="{chart_title}" data-chart-src="{chart_html_url}">'''
                charts_html += '''
                    </div>
                    <div class="chart-links">
                        <a href="''' + chart_png_url + '''" class="btn btn-sm btn-outline-secondary" download>
                            <i class="bi bi-download me-1"></i>下载PNG图表
                        </a> | 
                        <a href="''' + chart_html_url + '''" class="btn btn-sm btn-outline-primary chart-link" download>
                            <i class="bi bi-download me-1"></i>下载交互式HTML图表
                        </a>
                    </div>
                </div>
                '''
            charts_html += '</div>'
        
        # 结束堆叠显示区域
        charts_html += '</div>'
    html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>设备不平衡量分析报告</title>
    <style>
        body {{
            font-family: "SimHei", "Microsoft YaHei", "SimSun", "WenQuanYi Zen Hei", sans-serif;
            margin: 0;
            padding: 0;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
        }}
        .header {{
            background-color: #007bff;
            color: white;
            padding: 30px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 28px;
        }}
        .report-info {{
            background-color: #e9ecef;
            padding: 15px 30px;
            display: flex;
            justify-content: space-between;
            flex-wrap: wrap;
        }}
        .report-info-item {{
            margin: 5px 0;
        }}
        .content {{
            padding: 30px;
        }}
        .section {{
            margin-bottom: 30px;
        }}
        .section h2 {{
            color: #007bff;
            border-bottom: 2px solid #007bff;
            padding-bottom: 10px;
        }}
        .chart-group {{
            margin-bottom: 30px;
        }}
        .chart-group h3 {{
            color: #28a745;
            border-left: 4px solid #28a745;
            padding-left: 15px;
        }}
        .chart-section {{
            margin: 20px 0;
            padding: 20px;
            border: 1px solid #dee2e6;
            border-radius: 5px;
        }}
        .chart-section h4 {{
            margin-top: 0;
            color: #6c757d;
        }}
        .chart-img-container {{
            text-align: center;
            margin: 15px 0;
        }}
        .chart-img {{
            max-width: 100%;
            height: auto;
            border: 1px solid #ddd;
            border-radius: 5px;
        }}
        .chart-links {{
            text-align: center;
            margin-top: 15px;
        }}
        .footer {{
            background-color: #343a40;
            color: white;
            text-align: center;
            padding: 20px;
            font-size: 14px;
        }}
        @media print {{
            .chart-links {{
                display: none;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{report_title}</h1>
        </div>
        <div class="report-info">
            <div class="report-info-item">
                <strong>报告生成时间:</strong> {report_time}
            </div>
            <div class="report-info-item">
                <strong>数据来源:</strong> 扇叶平衡补土转速评估工具
            </div>
        </div>
        <div class="content">
            <div class="section">
                <h2><i class="bi bi-bar-chart-line me-2"></i>统计分析结果</h2>
                <div class="table-responsive">
                    {saved_results.get('stats_html', '')}
                </div>
            </div>
            
            <div class="section">
                <h2><i class="bi bi-graph-up me-2"></i>数据图表</h2>
                {charts_html}
            </div>
        </div>
        <div class="footer">
            <p>© 扇叶平衡补土转速评估工具 - 自动生成的分析报告</p>
        </div>
    </div>
</body>
</html>"""

    # 保存报告到文件
    report_filename = f"report_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.html"
    report_path = os.path.join(app.config['OUTPUT_FOLDER'], report_filename)
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    # 提供文件下载
    return send_file(report_path, as_attachment=True, download_name=report_filename)

@app.route('/generate_combined_chart', methods=['POST'])
def generate_combined_chart():
    """生成组合图表"""
    try:
        # 检查是否是 AJAX 请求
        if request.headers.get('X-Requested-With') != 'XMLHttpRequest':
            return jsonify({'success': False, 'message': '无效的请求类型'})
        
        # 从session获取数据
        saved_results = session.get('saved_results')
        if not saved_results:
            return jsonify({'success': False, 'message': '会话已过期，请重新上传数据文件！'})
        
        # 获取请求数据
        request_data = request.get_json()
        if not request_data:
            return jsonify({'success': False, 'message': '请求数据格式错误'})
        
        chart_types = request_data.get('chart_types', ['trend'])
        combine_faces = request_data.get('combine_faces', False)
        
        # 生成组合图表
        if saved_results.get('single_surface'):
            # 单一面情况
            combined_charts = create_combined_chart(
                saved_results['parsed_data'], 
                chart_types, 
                f"{saved_results['output_prefix']}_combined", 
                app.config['OUTPUT_FOLDER'],
                combine_faces
            )
        else:
            # 双面或多面情况
            combined_charts = create_combined_chart(
                saved_results['parsed_data'], 
                chart_types, 
                f"{saved_results['output_prefix']}_combined", 
                app.config['OUTPUT_FOLDER'],
                combine_faces
            )
        
        # 更新保存的结果
        saved_results['combined_charts'] = combined_charts
        session['saved_results'] = saved_results
        
        return jsonify({'success': True, 'message': '组合图表生成成功'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'生成组合图表失败：{str(e)}'})

@app.route('/get_combined_chart')
def get_combined_chart():
    """获取组合图表内容"""
    try:
        # 检查是否是 AJAX 请求
        if request.headers.get('X-Requested-With') != 'XMLHttpRequest':
            return jsonify({'success': False, 'message': '无效的请求类型'})
        
        # 从session获取数据
        saved_results = session.get('saved_results')
        if not saved_results:
            return jsonify({'success': False, 'message': '会话已过期，请重新上传数据文件！'})
        
        # 渲染组合图表部分
        template = render_template('_charts_partial.html', 
                                  plots=saved_results.get('plots', {}),
                                  has_p1=saved_results.get('has_p1', False),
                                  has_p2=saved_results.get('has_p2', False),
                                  has_st=saved_results.get('has_st', False),
                                  saved_results=saved_results)
        
        return template
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取组合图表失败：{str(e)}'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=1322, debug=False)