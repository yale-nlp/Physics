import evaluate_claude_3_5_sonnet
import evaluate_gemini_1_5_pro
import evaluate_gpt4o
import evaluate_Llama_3_2_11B_Vision_Instruct
import evaluate_Llama_3_3_70B_Instruct
import evaluate_Qwen2_5_72B_Instruct_Turbo
import evaluate_Qwen2_VL_7B_Instruct
from concurrent.futures import ThreadPoolExecutor, as_completed

def execute_task(task, category, max_lines):
    """包装任务执行函数，捕获异常并返回结果"""
    try:
        task(category, max_lines)
        return f"{task.__module__} completed successfully."
    except Exception as e:
        return f"Error in {task.__module__}: {e}"

def main():
    category = "mechanics"
    max_lines = 20

    # 定义所有任务
    tasks = [
        evaluate_claude_3_5_sonnet.main,
        evaluate_gemini_1_5_pro.main,
        evaluate_gpt4o.main,
        evaluate_Llama_3_2_11B_Vision_Instruct.main,
        evaluate_Llama_3_3_70B_Instruct.main,
        evaluate_Qwen2_5_72B_Instruct_Turbo.main,
        #evaluate_Qwen2_VL_7B_Instruct.main,
    ]

    # 使用线程池并发执行任务
    with ThreadPoolExecutor() as executor:
        # 提交任务
        future_to_task = {
            executor.submit(execute_task, task, category, max_lines): task
            for task in tasks
        }

        # 处理任务结果
        for future in as_completed(future_to_task):
            result = future.result()
            print(result)

if __name__ == "__main__":
    main()
