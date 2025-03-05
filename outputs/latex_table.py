import json

# 输入 JSONL 文件路径
input_jsonl_path = "llm_accuracy_results.jsonl"
output_tex_path = "llm_accuracy_results.tex"

# 读取 JSONL 文件
llm_data = []
with open(input_jsonl_path, "r", encoding="utf-8") as file:
    for line in file:
        llm_data.append(json.loads(line))

columns = set()
rows = []

for entry in llm_data:
    llm_name = entry["llm_name"].replace("_", "-")  # 替换 "_" 为 "-"
    accuracy_data = entry["accuracy_data"]

    # 获取 overall 统计
    avg_test = accuracy_data.get("overall", {}).get("average_test_accuracy", 0)
    avg_validation = accuracy_data.get("overall", {}).get("average_validation_accuracy", 0)

    # 获取 subset 数据
    row = {
        "Model": llm_name,  # "Model" 作为第一列
        "Avg. Validation": avg_validation,
        "Avg. Test": avg_test
    }

    for subset, values in accuracy_data.items():
        if subset != "overall":
            row[subset] = values.get("average_test_accuracy", 0)
            columns.add(subset)

    rows.append(row)

# **按 Avg. Test 进行降序排序**
rows.sort(key=lambda x: x["Avg. Test"], reverse=True)

# **确保 subset 按字母顺序排列**
columns = sorted(columns)
header_columns = ["Model"] + columns + ["Avg. Validation", "Avg. Test"]

# `Test Set` 只涵盖 subset 部分
num_test_columns = len(columns)

# 生成 LaTeX 表格
with open(output_tex_path, "w", encoding="utf-8") as tex_file:
    tex_file.write("\\begin{table*}[t]\n")
    tex_file.write("\\centering\n")
    tex_file.write("\\footnotesize\n")
    tex_file.write("\\setlength{\\tabcolsep}{6pt}\n")
    tex_file.write("\\begin{tabularx}{\\linewidth}{l " + "r " * (len(header_columns) - 1) + "}\n")
    tex_file.write("\\toprule\n")

    # **添加多列标题**
    tex_file.write("\\textbf{Model} & \\multicolumn{" + str(num_test_columns) + "}{c}{\\textbf{Test Set}} & \\textbf{Avg. Validation} & \\textbf{Avg. Test} \\\\\n")
    tex_file.write("\\cmidrule(lr){2-" + str(num_test_columns + 1) + "}\n")  # 让横线仅覆盖 subset 部分

    # **写表头（不重复 Model）**
    tex_file.write(" & " + " & ".join(columns) + " & Avg. Validation & Avg. Test \\\\\n")
    tex_file.write("\\midrule\n")

    # **写数据行**
    for row in rows:
        values = [row.get(col, "-") for col in header_columns]
        formatted_values = [f"{v*100:.1f}" if isinstance(v, float) else str(v) for v in values]
        tex_file.write(" & ".join(formatted_values) + " \\\\\n")

    tex_file.write("\\bottomrule\n")
    tex_file.write("\\end{tabularx}\n")
    tex_file.write("\\caption{Performance comparison across tasks.}\n")
    tex_file.write("\\label{tab:llm-accuracy}\n")
    tex_file.write("\\end{table*}\n")

print(f"LaTeX 表格已保存至 {output_tex_path}")
