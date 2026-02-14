import json

# 测试修复后的JSON数据处理
print("测试修复后的JSON数据处理...")

# 测试1: 测试JSON字符串解析
test_json_str = '{"name": "2500rpm", "data": [1.1, 2.2, 3.3, 4.4, 5.5]}'
print(f"测试JSON字符串: {test_json_str}")

try:
    parsed_data = json.loads(test_json_str)
    print(f"解析成功: {parsed_data}")
    print("测试1通过！")
except Exception as e:
    print(f"解析失败: {str(e)}")
    print("测试1失败！")

# 测试2: 测试HTML编码的JSON字符串解析
test_html_encoded_str = '{&quot;name&quot;: &quot;2500rpm&quot;, &quot;data&quot;: [1.1, 2.2, 3.3, 4.4, 5.5]}'
print(f"\n测试HTML编码的JSON字符串: {test_html_encoded_str}")

try:
    # 解码HTML实体
    decoded_str = test_html_encoded_str.replace('&quot;', '"').replace('&amp;', '&')
    print(f"解码后的字符串: {decoded_str}")
    parsed_data = json.loads(decoded_str)
    print(f"解析成功: {parsed_data}")
    print("测试2通过！")
except Exception as e:
    print(f"解析失败: {str(e)}")
    print("测试2失败！")

print("\n测试完成！")
