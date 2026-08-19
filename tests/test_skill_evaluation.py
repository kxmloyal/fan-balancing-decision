#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from app.services.skill_evaluation import skill_evaluation_service

# 测试数据
test_data = [
    {
        "speed": "1000rpm",
        "p1_samples": [1.1, 1.5, 1.3, 1.4, 1.6, 1.2, 1.3, 1.4, 1.5, 1.3],
        "p2_samples": [2.1, 2.5, 2.3, 2.4, 2.6, 2.2, 2.3, 2.4, 2.5, 2.3],
        "sum_samples": [3.2, 4.0, 3.6, 3.8, 4.2, 3.4, 3.6, 3.8, 4.0, 3.6],
    }
]

# 测试评估功能
print("Testing skill evaluation service...")
try:
    result = skill_evaluation_service.evaluate_skill(test_data)
    print("Evaluation successful!")
    print("Analysis level:", result["comprehensive_evaluation"].get("overall_assessment"))
    print("Skill score:", result["comprehensive_evaluation"].get("skill_score"))
    print("Data quality:", result["comprehensive_evaluation"].get("data_quality"))
    print("Process stability:", result["comprehensive_evaluation"].get("process_stability"))
    print("Anomaly evaluation:", result["comprehensive_evaluation"].get("anomaly_evaluation"))
    print("Test passed!")
except Exception as e:
    print(f"Test failed with error: {e}")
