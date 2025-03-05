import os
import json

# 主文件夹路径
root_dir = "/Users/kevinfeng/Desktop/outputs"
test_ids_path = "datasets/test/all_ids.json"
validation_ids_path = "datasets/validation/all_ids.json"  # ✅ 新增 validation id 文件路径
output_jsonl_path = "llm_accuracy_results.jsonl"  # 最终 JSONL 文件

# 读取 test set 和 validation set 的所有 id
with open(test_ids_path, "r", encoding="utf-8") as file:
    test_ids = set(json.load(file))  # 使用 set 加速查询

with open(validation_ids_path, "r", encoding="utf-8") as file:
    validation_ids = set(json.load(file))  # ✅ 读取 validation set ids

# 遍历 root_dir 目录下的所有 LLM outputs
llm_results = []

for llm_folder in os.listdir(root_dir):
    llm_path = os.path.join(root_dir, llm_folder)

    if os.path.isdir(llm_path):  # 确保是目录
        print(f"Processing LLM: {llm_folder} ...")

        accuracy_data = {}  # 该 LLM 的 accuracy 统计
        total_test_accuracy = 0.0
        total_test_count = 0  # ✅ 修正为整数
        total_validation_accuracy = 0.0
        total_validation_count = 0  # ✅ 修正为整数

        subset_aggregated = {}  # 统计相同前缀 subset

        # 遍历 LLM 目录下的所有 subset 目录
        for subset in os.listdir(llm_path):
            subset_path = os.path.join(llm_path, subset)

            if os.path.isdir(subset_path):  # 确保是文件夹
                jsonl_file = os.path.join(subset_path, "final_evaluation.jsonl")
                
                # 如果 final_evaluation.jsonl 不存在，则尝试使用 response.jsonl
                if not os.path.exists(jsonl_file):
                    jsonl_file = os.path.join(subset_path, "response.jsonl")
                    if not os.path.exists(jsonl_file):
                        print(f"警告: 未找到 {subset} 的 final_evaluation.jsonl 或 response.jsonl")
                        continue

                test_accuracies = []
                validation_accuracies = []

                with open(jsonl_file, "r", encoding="utf-8") as file:
                    for line in file:
                        try:
                            data = json.loads(line)
                            accuracy = data.get("accuracy")
                            data_id = data.get("id")

                            # ✅ 先检查 id 是否在 test_ids 或 validation_ids 中
                            if data_id in test_ids:
                                if isinstance(accuracy, (int, float)):  # 确保 accuracy 是数字
                                    test_accuracies.append(float(accuracy))
                            elif data_id in validation_ids:
                                if isinstance(accuracy, (int, float)):  # 确保 accuracy 是数字
                                    validation_accuracies.append(float(accuracy))
                            else:
                                continue  # ✅ 如果 id 既不在 test 也不在 validation，则跳过

                        except json.JSONDecodeError as e:
                            print(f"解析错误 {jsonl_file}: {e}")

                # 计算 subset 前缀名称（取第一个 `_` 之前的部分）
                subset_prefix = subset.split("_")[0]

                if subset_prefix not in subset_aggregated:
                    subset_aggregated[subset_prefix] = {
                        "test_accuracies": 0.0,  # ✅ 改为总和
                        "test_counts": 0,  # ✅ 改为整数
                        "validation_accuracies": 0.0,  # ✅ 改为总和
                        "validation_counts": 0  # ✅ 改为整数
                    }

                subset_aggregated[subset_prefix]["test_accuracies"] += sum(test_accuracies)
                subset_aggregated[subset_prefix]["test_counts"] += len(test_accuracies)
                subset_aggregated[subset_prefix]["validation_accuracies"] += sum(validation_accuracies)
                subset_aggregated[subset_prefix]["validation_counts"] += len(validation_accuracies)

        # 计算合并后的 subset 统计数据（加权平均）
        for subset_prefix, values in subset_aggregated.items():
            total_test_accuracy_sum = values["test_accuracies"]
            total_test_count_sum = values["test_counts"]
            total_validation_accuracy_sum = values["validation_accuracies"]
            total_validation_count_sum = values["validation_counts"]

            test_avg = total_test_accuracy_sum / total_test_count_sum if total_test_count_sum > 0 else 0.0
            validation_avg = total_validation_accuracy_sum / total_validation_count_sum if total_validation_count_sum > 0 else 0.0

            accuracy_data[subset_prefix] = {
                "average_test_accuracy": round(test_avg, 3),
                "average_validation_accuracy": round(validation_avg, 3)
            }

            # ✅ **修正 `total_test_count` 和 `total_validation_count` 的累积计算**
            total_test_accuracy += total_test_accuracy_sum
            total_test_count += total_test_count_sum  # ✅ 现在累加的是 `total_test_count_sum`
            total_validation_accuracy += total_validation_accuracy_sum
            total_validation_count += total_validation_count_sum  # ✅ 现在累加的是 `total_validation_count_sum`

        # 计算该 LLM 的整体加权平均 accuracy
        print(f"Total test count: {total_test_count}, Total validation count: {total_validation_count}")
        weighted_test_avg = total_test_accuracy / total_test_count if total_test_count > 0 else 0.0
        weighted_validation_avg = total_validation_accuracy / total_validation_count if total_validation_count > 0 else 0.0

        accuracy_data["overall"] = {
            "average_test_accuracy": round(weighted_test_avg, 3),
            "average_validation_accuracy": round(weighted_validation_avg, 3)
        }

        # 添加该 LLM 的统计数据到最终 JSONL 列表
        llm_results.append({
            "llm_name": llm_folder,  # 记录 LLM 名称
            "accuracy_data": accuracy_data
        })

# 将结果写入 JSONL 文件
with open(output_jsonl_path, "w", encoding="utf-8") as output_file:
    for entry in llm_results:
        output_file.write(json.dumps(entry, ensure_ascii=False) + "\n")

print(f"统计完成，结果已保存到 {output_jsonl_path}")
