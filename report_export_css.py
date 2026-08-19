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
        .chart-group { margin: 15px 0; padding: 12px; border: 1px solid var(--gray-200); border-radius: 8px; background: var(--gray-50); }
        .chart-section { margin: 20px 0; padding: 15px; border: 1px solid var(--gray-200); border-radius: 8px; background: white; }
        .chart-img-container { text-align: center; margin: 8px 0; }
        .chart-img-container img { max-width: 100%; height: auto; box-shadow: 0 2px 12px rgba(0,0,0,0.08); border-radius: 4px; }
        .info-box { background: var(--gray-50); border: 1px solid var(--gray-200); padding: 20px; border-radius: 8px; margin: 20px 0; }
        .recommendations-box { background: #fffbeb; border: 1px solid #fde68a; padding: 24px; border-radius: 8px; margin: 20px 0; }
        .technical-details-box { background: #fef2f2; border: 1px solid #fecaca; padding: 24px; border-radius: 8px; margin: 20px 0; }
        .chart-row { display: flex; flex-wrap: wrap; gap: 20px; }
        .chart-col { flex: 1; min-width: 300px; }
        .chart-container { margin: 10px 0; padding: 12px; background: white; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }
        .footer { text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid var(--gray-200); color: var(--gray-600); font-size: 13px; }
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
            .header { background: var(--primary) !important; print-color-adjust: exact; -webkit-print-color-adjust: exact; }
            h1, h2, h3, h4 { page-break-after: avoid; }
            .section-title { page-break-after: avoid; }
            .chart-row { display: block; }
            .chart-col { flex: none; min-width: auto; width: 100%; page-break-inside: avoid; }
        }
"""
