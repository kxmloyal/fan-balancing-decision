"""报告导出器 CSS 样式表 — 从 report_export.py 外部化，便于单独维护和审查。"""

EXPORTER_CSS = """        :root {
            --primary: #2563eb; --primary-dark: #1d4ed8;
            --success: #10b981; --warning: #f59e0b; --danger: #ef4444;
            --gray-50: #f8fafc; --gray-100: #f1f5f9; --gray-200: #e2e8f0; --gray-600: #475569; --gray-800: #1e293b;
        }
        body {
            font-family: "Segoe UI", "Microsoft YaHei", "SimHei", "Helvetica Neue", Helvetica, Arial, sans-serif;
            margin: 0; padding: 0; background-color: var(--gray-100); color: var(--gray-800);
        }
        .container { max-width: 1200px; margin: 0 auto; background: white; box-shadow: 0 4px 16px rgba(0,0,0,0.08); }
        .header { background: linear-gradient(135deg, var(--primary-dark), var(--primary)); color: white; padding: 40px 30px; text-align: center; }
        .header h1 { margin: 0; font-size: 28px; letter-spacing: 1px; }
        .header h2 { margin: 12px 0 0 0; font-size: 20px; font-weight: 400; opacity: 0.9; }
        .report-info { background: var(--gray-50); padding: 15px 30px; display: flex; justify-content: space-between; flex-wrap: wrap; border-bottom: 2px solid var(--gray-200); }
        .report-info-item { margin: 5px 0; }
        .highlight-speed { color: var(--primary); font-weight: 700; font-size: 1.05em; }
        .content { padding: 30px; }
        h2.section-title { color: var(--primary); border-left: 4px solid var(--primary); padding-left: 15px; margin: 36px 0 20px 0; }
        .summary-box { background: linear-gradient(135deg, #ecfdf5, #d1fae5); border: 1px solid #a7f3d0; padding: 24px; border-radius: 8px; margin: 20px 0; }
        .summary-box h3 { margin-top: 0; color: #065f46; }
        .methodology-box { background: #f0f9ff; border: 1px solid #bae6fd; padding: 24px; border-radius: 8px; margin: 20px 0; }
        .formula-box { background: #fff; border: 2px solid var(--primary); padding: 16px 20px; border-radius: 6px; margin: 12px 0; font-family: "Courier New", monospace; }
        .formula-box p { margin: 4px 0; font-size: 14px; }
        table { width: 100%; border-collapse: collapse; margin: 15px 0; border-radius: 8px; overflow: hidden; }
        table, th, td { border: 1px solid var(--gray-200); }
        th, td { padding: 12px 10px; text-align: center; }
        th { background-color: var(--primary); color: white; font-weight: 600; }
        tr:nth-child(even) { background-color: var(--gray-50); }
        tr:hover { background-color: #e0f2fe; }
        .method-table { box-shadow: 0 2px 8px rgba(0,0,0,0.06); }
        .method-table th { background-color: var(--gray-800); }
        .table-responsive { overflow-x: auto; margin: 15px 0; }
        /* 统计方法章节末尾：样本量小字附注 */
        .sample-note-footer { margin-top: 14px; padding-top: 10px; border-top: 1px dashed var(--gray-200); font-size: 12px; color: var(--gray-500); }
        .sample-note-footer strong { color: var(--gray-700); }
        /* Bootstrap 兼容样式（stats_html 内嵌依赖，与前端 div 样式对齐） */
        .table { width: 100%; }
        .table-striped tbody tr:nth-of-type(odd) { background-color: var(--gray-50); }
        .table-hover tbody tr:hover { background-color: #e0f2fe; }
        .table-sm th, .table-sm td { padding: 6px 8px; }
        .table-light th { background-color: var(--gray-100); color: var(--gray-800); }
        .bg-primary { background-color: var(--primary) !important; }
        .table-success, .table-success > td { background-color: #d1e7dd; }
        .table-warning, .table-warning > td { background-color: #fff3cd; }
        .text-center { text-align: center; }
        .align-middle { vertical-align: middle; }
        .text-muted { color: var(--gray-600); }
        .text-success { color: var(--success); }
        .mb-2 { margin-bottom: 0.5rem; }
        .ms-2 { margin-left: 0.5rem; }
        .me-1 { margin-right: 0.25rem; }
        .table-statistics th { background-color: var(--gray-50); color: var(--gray-800); font-weight: 600; vertical-align: middle; }
        .table-statistics .header-main { background-color: var(--gray-200); color: var(--gray-800); font-weight: 700; }
        .table-statistics .header-sub { background-color: var(--gray-50); color: var(--gray-800); font-weight: 600; }
        .table-statistics .face-p1 { background-color: #cce5ff; color: #004085; font-weight: 600; }
        .table-statistics .face-p2 { background-color: #ffeacc; color: #856404; font-weight: 600; }
        .table-statistics .face-st { background-color: #d4edda; color: #155724; font-weight: 600; }
        .table-statistics .evaluation-col { background-color: #f0f0f0; color: #333; font-weight: 600; }
        .chart-group-title { margin: 4px 0 10px; font-size: 15px; color: var(--gray-800); }
        .chart-group { margin: 15px 0; padding: 12px; border: 1px solid var(--gray-200); border-radius: 8px; background: var(--gray-50); }
        .chart-section { margin: 20px 0; padding: 15px; border: 1px solid var(--gray-200); border-radius: 8px; background: white; }
        .chart-img-container { text-align: center; margin: 8px 0; }
        .chart-img-container img { max-width: 100%; height: auto; box-shadow: 0 2px 12px rgba(0,0,0,0.08); border-radius: 4px; }
        .chart-plotly-container { width: 100%; height: 420px; }
        .info-box { background: var(--gray-50); border: 1px solid var(--gray-200); padding: 20px; border-radius: 8px; margin: 20px 0; }
        .recommendations-box { background: #fffbeb; border: 1px solid #fde68a; padding: 24px; border-radius: 8px; margin: 20px 0; }
        .technical-details-box { background: #fef2f2; border: 1px solid #fecaca; padding: 24px; border-radius: 8px; margin: 20px 0; }
        .chart-row { display: flex; flex-wrap: wrap; gap: 20px; }
        .chart-col { flex: 1; min-width: 300px; }
        .chart-container { margin: 10px 0; padding: 12px; background: white; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }
        .footer { text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid var(--gray-200); color: var(--gray-600); font-size: 13px; }
        .cover { display: flex; flex-direction: column; justify-content: center; align-items: center; min-height: 90vh; text-align: center; background: linear-gradient(160deg, var(--primary-dark), var(--primary) 55%, #3b82f6); color: white; padding: 40px 30px; }
        .cover h1 { font-size: 36px; letter-spacing: 2px; margin: 0 0 8px; }
        .cover h2 { font-size: 22px; font-weight: 400; opacity: 0.92; margin: 0 0 36px; }
        .cover .cover-meta { display: inline-block; text-align: left; background: rgba(255,255,255,0.12); border: 1px solid rgba(255,255,255,0.35); border-radius: 10px; padding: 18px 30px; font-size: 14px; line-height: 2; }
        .cover .cover-meta strong { display: inline-block; min-width: 110px; }
        .cover .cover-badge { margin-top: 30px; background: #f59e0b; color: #1e293b; font-weight: 700; padding: 8px 22px; border-radius: 999px; font-size: 15px; }
        .toc { background: var(--gray-50); border: 1px solid var(--gray-200); border-radius: 8px; padding: 20px 28px; margin: 20px 0; }
        .toc h3 { margin: 0 0 12px; color: var(--primary); }
        .toc ol { margin: 0; padding-left: 20px; line-height: 2; }
        .toc a { color: var(--gray-800); text-decoration: none; }
        .toc a:hover { color: var(--primary); text-decoration: underline; }
        .page-header { display: flex; justify-content: space-between; align-items: center; padding: 8px 30px; background: var(--primary); color: white; font-size: 12px; }
        .page-footer { display: flex; justify-content: space-between; align-items: center; padding: 8px 30px; color: var(--gray-600); font-size: 12px; border-top: 1px solid var(--gray-200); }
        .score-table td.best, .score-table tr.best { background: #fef3c7; font-weight: 700; color: #92400e; }
        .score-table th.face { background-color: var(--gray-800); }
        .sample-info { color: var(--gray-600); font-size: 13px; margin: 8px 0; }
        .best-badge { display: inline-block; background: var(--success); color: white; font-size: 12px; padding: 2px 10px; border-radius: 999px; margin-left: 8px; }
        @media (min-width: 1400px) { .container { max-width: 1320px; } .chart-col { min-width: 350px; } }
        @media print {
            @page {
                size: A4 landscape;
                margin: 12mm 10mm;
            }
            body { background: white; font-size: 10pt; print-color-adjust: exact; -webkit-print-color-adjust: exact; }
            .container { box-shadow: none; max-width: none; width: 100%; padding: 0; }
            table { page-break-inside: avoid; font-size: 9pt; }
            table thead { display: table-header-group; }
            tr { page-break-inside: avoid; }
            .chart-img-container img { max-width: 100% !important; max-height: 380px; page-break-inside: avoid; }
            .chart-plotly-container { display: none !important; }
            .chart-img-container { display: block !important; }
            .header { background: var(--primary) !important; print-color-adjust: exact; -webkit-print-color-adjust: exact; }
            h1, h2, h3, h4 { page-break-after: avoid; }
            .section-title { page-break-after: avoid; }
            .chart-row { display: block; }
            .chart-col { flex: none; min-width: auto; width: 100%; page-break-inside: avoid; }
            .cover { min-height: 0; page-break-after: always; }
            .toc { page-break-after: always; }
            .page-header, .page-footer { display: none; }
            .chart-group { page-break-inside: avoid; }
        }
        /* 导出样式：body.report-compact / body.report-detailed（由 export_format 选项控制） */
        body.report-compact .content { font-size: 12px; padding: 18px; }
        body.report-compact h2.section-title { font-size: 18px; padding: 10px 0 6px; margin: 24px 0 12px; }
        body.report-compact h3, body.report-compact h4 { margin: 8px 0 4px; }
        body.report-compact .chart-container, body.report-compact .summary-box,
        body.report-compact .methodology-box, body.report-compact .recommendations-box,
        body.report-compact .technical-details-box { padding: 10px 14px; margin: 10px 0; }
        body.report-compact table { font-size: 12px; }
        body.report-detailed .content { font-size: 15px; padding: 36px; }
        body.report-detailed .chart-container, body.report-detailed .summary-box,
        body.report-detailed .methodology-box, body.report-detailed .recommendations-box,
        body.report-detailed .technical-details-box { padding: 20px 28px; margin: 18px 0; }
        body.report-detailed h2.section-title { font-size: 24px; }
        body.report-detailed .sample-note-footer { font-size: 14px; }
"""
