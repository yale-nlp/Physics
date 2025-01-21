import json

# 定义输入和输出文件路径
input_jsonl_path = "datasets/statistics_dataset.jsonl"  # 替换为你的实际输入文件路径
output_jsonl_path = "datasets/statistics_dataset_textonly.jsonl"  # 替换为你希望输出的文件路径

# 打开输入 JSONL 文件，筛选出 graph 为 None 的元素
filtered_entries = []
with open(input_jsonl_path, "r", encoding="utf-8") as infile:
    for line in infile:
        entry = json.loads(line)
        # 检查 graph 是否为 None
        if entry.get("graphs") is None:
            filtered_entries.append(entry)

# 将筛选后的结果写入新的 JSONL 文件
with open(output_jsonl_path, "w", encoding="utf-8") as outfile:
    for entry in filtered_entries:
        outfile.write(json.dumps(entry, ensure_ascii=False) + "\n")

print(f"过滤完成，已生成包含 {len(filtered_entries)} 条记录的新 JSONL 文件：{output_jsonl_path}")
