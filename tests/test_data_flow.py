import os
import sys

from flask import Flask, session

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.services.project_statistics import (
    calculate_optimal_speed_evaluation,
    generate_stats,
    generate_stats_data,
)
from data_processing import parse_single_surface_file

# 创建测试Flask应用
app = Flask(__name__)
app.secret_key = "test_secret_key"
app.config["OUTPUT_FOLDER"] = "outputs"

# 确保输出目录存在
if not os.path.exists(app.config["OUTPUT_FOLDER"]):
    os.makedirs(app.config["OUTPUT_FOLDER"])


def test_data_flow():
    print("开始测试数据流程...")

    # 1. 测试文件解析
    print("\n1. 测试文件解析...")
    try:
        # 使用示例文件进行测试
        test_files = ["uploads/p1_test.csv", "uploads/p2_test.csv"]

        parsed_data = []
        for file_path in test_files:
            if os.path.exists(file_path):
                data = parse_single_surface_file(file_path)
                print(f"成功解析文件: {file_path}")
                print(f"  转速数量: {len(data)}")
                for speed, samples in data.items():
                    print(f"  {speed}: {len(samples)}个样本")
            else:
                print(f"文件不存在: {file_path}")
                # 创建测试数据
                data = {
                    "2500rpm": [1.1, 2.2, 3.3, 4.4, 5.5],
                    "3000rpm": [2.2, 3.3, 4.4, 5.5, 6.6],
                    "3500rpm": [3.3, 4.4, 5.5, 6.6, 7.7],
                    "4000rpm": [4.4, 5.5, 6.6, 7.7, 8.8],
                    "4500rpm": [5.5, 6.6, 7.7, 8.8, 9.9],
                }
                print("使用测试数据")
                parsed_data.append(data)

        # 2. 测试统计数据生成
        print("\n2. 测试统计数据生成...")
        if parsed_data:
            # 构建测试数据结构
            test_parsed_data = []
            for speed in parsed_data[0].keys():
                test_parsed_data.append(
                    {
                        "speed": speed,
                        "p1_samples": parsed_data[0][speed],
                        "p2_samples": parsed_data[0][speed]
                        if len(parsed_data) > 1
                        else parsed_data[0][speed],
                        "sum_samples": parsed_data[0][speed],
                    }
                )

            # 生成统计数据
            stats_html, stats_csv = generate_stats(
                test_parsed_data, "test", app.config["OUTPUT_FOLDER"]
            )
            print("成功生成统计数据")
            print(f"统计HTML长度: {len(stats_html)}")
            print(f"统计CSV文件: {stats_csv}")

            # 3. 测试最优转速评估
            print("\n3. 测试最优转速评估...")
            stats_data = generate_stats_data(test_parsed_data)
            evaluation_report = calculate_optimal_speed_evaluation(stats_data)
            print(f"最优转速: {evaluation_report['best_speeds']}")
            print(f"最优得分: {evaluation_report['best_score']}")

            # 4. 测试session数据存储
            print("\n4. 测试session数据存储...")
            with app.test_request_context():
                # 模拟session数据
                session["saved_results"] = {
                    "parsed_data": test_parsed_data,
                    "output_prefix": "test",
                    "stats_html": stats_html,
                    "stats_csv": stats_csv,
                    "evaluation_report": evaluation_report,
                    "has_p1": True,
                    "has_p2": True,
                    "has_st": True,
                    "plots": {},
                    "chart_types": ["box"],
                    "chart_layout": "stacked",
                    "fan_model": "Test Model",
                }

                # 验证session数据
                saved_results = session.get("saved_results")
                if saved_results:
                    print("Session数据存储成功")
                    print(f"  统计HTML存在: {bool(saved_results.get('stats_html'))}")
                    print(f"  评估报告存在: {bool(saved_results.get('evaluation_report'))}")
                    print(
                        f"  最优转速存在: {bool(saved_results.get('evaluation_report', {}).get('best_speeds'))}"
                    )
                else:
                    print("Session数据存储失败")
        else:
            print("没有测试数据")

    except Exception as e:
        print(f"测试失败: {str(e)}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    test_data_flow()
