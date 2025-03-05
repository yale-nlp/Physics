# PHYSICS: A Comprehensive Benchmark for Advanced Physics Reasoning

## Overview
PHYSICS is a high-level physics problem-solving benchmark designed to assess the reasoning and analytical capabilities of foundation models. The dataset contains 1,297 PhD-qualifying exam problems spanning six fundamental physics disciplines.

## Key Features

- **Dataset Size**: 1,297 problems
- **Problem Domains**:
  - Classical Mechanics
  - Quantum Mechanics
  - Thermodynamics & Statistical Mechanics
  - Electromagnetism
  - Atomic Physics
  - Optics
- **Problem Complexity**: Requires deep mathematical modeling and multi-step logical reasoning.
- **Automated Evaluation System**:
  - Uses SymPy for symbolic verification
  - GPT-4o-based natural language answer validation
- **Benchmarking Across 33 Models**:
  - Proprietary models (e.g., GPT-4o, Gemini-1.5-Pro)
  - Open-source models (e.g., DeepSeek-R1, Llama-3.3-70B)
- **Performance Gap Analysis**:
  - Best-performing model achieves only **59.9% accuracy**
  - Open-source models struggle significantly, revealing gaps in physics problem-solving abilities.

## Data Collection
- **Sources**: Publicly available PhD-qualifying exam questions
- **Annotation Process**:
  - Structured review by expert annotators
  - Strict data quality control
- **Evaluation Metrics**:
  - Problem complexity classification
  - Multi-step reasoning depth assessment

## Benchmark Comparison

| Benchmark      | Multi-modal | Size  | Level | Question Type | Evaluation | Reasoning Steps |
| ------------- | ----------- | ----- | ----- | ------------- | ---------- | --------------- |
| JEEBench      | ❌           | 515   | CEE   | OE, MC        | Rule-Based | -               |
| MATH          | ❌           | 12,500 | K12-Comp | OE      | Rule-Based | -               |
| HARDMATH      | ❌           | 1,466 | Graduate | OE      | Rule + Model | -               |
| GSM8K         | ❌           | 8,500 | K8    | OE            | Rule-Based | 5               |
| SciQ          | ❌           | 13,679 | K4-K8 | MC, OE        | Rule-Based | -               |
| OlympiadBench | ✅           | 2,334 | Comp  | OE            | Rule-Based | 3.7             |
| PHYSICS       | ✅           | 1,297 | PhD-Qualifying | OE | Rule + Model | 5.7             |

## Evaluation Framework

### Answer-Level Evaluation
- SymPy-based symbolic equivalence checking
- LLM-based accuracy verification
- Weighted scoring based on correctness and complexity

### Step-Level Evaluation
- Step-by-step reasoning assessment
- Identification of first error step
- Error categorization for detailed failure analysis

## Experimental Results

| Model                          | AMO  | E&M  | CM   | Opt. | QM   | Stats. | Val  | Test  |
|--------------------------------|------|------|------|------|------|--------|------|-------|
| **Proprietary Models**         |      |      |      |      |      |        |      |       |
| o3-mini                        | 52.4 | 64.9 | 59.8 | 51.5 | 66.0 | 60.0   | 55.0 | 59.9  |
| o1-mini                        | 45.4 | 41.8 | 41.9 | 40.6 | 44.3 | 48.0   | 44.1 | 43.6  |
| Gemini-1.5-pro†                | 35.5 | 40.2 | 31.5 | 32.2 | 44.5 | 43.7   | 35.3 | 38.4  |
| GPT-4o†                        | 35.3 | 44.1 | 33.4 | 23.4 | 33.8 | 45.0   | 34.7 | 36.7  |
| Claude-3.5-Sonnet†             | 37.2 | 34.8 | 27.6 | 35.5 | 35.1 | 38.4   | 31.7 | 34.7  |

| **Open-Source Models**         |      |      |      |      |      |        |      |       |
| DeepSeek-R1                    | 37.0 | 48.6 | 38.3 | 43.1 | 44.5 | 51.5   | 44.2 | 44.3  |
| Qwen2.5-Math-72B               | 27.0 | 34.8 | 27.3 | 27.4 | 36.2 | 37.0   | 38.5 | 32.2  |
| Llama-3.3-70B                  | 28.2 | 35.8 | 27.9 | 17.2 | 31.4 | 41.3   | 34.3 | 31.5  |
| phi-4                          | 32.8 | 33.0 | 19.8 | 27.2 | 23.4 | 35.2   | 28.7 | 29.1  |
| Qwen2.5-72B                    | 28.8 | 30.9 | 23.0 | 25.4 | 27.4 | 33.2   | 31.5 | 28.7  |
| Qwen2.5-32B                    | 25.5 | 27.5 | 19.4 | 20.8 | 24.7 | 41.1   | 23.3 | 27.6  |
| Mistral-Small-24B              | 19.1 | 29.5 | 19.6 | 17.6 | 15.2 | 28.4   | 25.1 | 21.8  |
| Qwen2.5-7B                     | 21.8 | 28.1 | 11.2 | 18.7 | 17.4 | 22.1   | 20.9 | 20.4  |
| Qwen2.5-14B                    | 23.8 | 19.7 | 14.1 | 12.3 | 13.5 | 28.2   | 25.3 | 19.6  |
| Gemma-2-27b                    | 14.3 | 19.0 | 16.2 | 13.4 | 18.4 | 25.9   | 21.7 | 18.3  |
| Yi-1.5-34B                     | 11.0 | 15.4 | 18.0 | 13.2 | 19.6 | 25.2   | 25.3 | 17.4  |
| Qwen2.5-Math-1.5B              | 13.3 | 14.8 | 16.5 | 16.2 | 17.2 | 19.5   | 15.1 | 16.4  |
| InternVL2-5-38B†               | 15.3 | 12.5 | 12.5 | 7.7  | 18.0 | 23.1   | 16.7 | 15.3  |
| Aria†                          | 13.0 | 14.0 | 14.2 | 11.7 | 9.7  | 14.4   | 12.7 | 12.9  |
| QwQ-32B-Preview                | 16.7 | 7.5  | 10.1 | 11.2 | 10.6 | 14.8   | 12.4 | 12.1  |
| Gemma-2-9b                     | 9.4  | 8.2  | 9.1  | 16.5 | 12.1 | 16.9   | 15.2 | 11.9  |
| Mistral-7B                     | 10.1 | 10.4 | 5.1  | 13.7 | 11.6 | 17.6   | 12.6 | 11.7  |
| Llama-3.1-8B                   | 8.4  | 17.4 | 6.8  | 14.7 | 7.4  | 16.1   | 9.1  | 11.7  |
| Mathstral-7B                   | 7.3  | 10.0 | 12.0 | 9.6  | 8.2  | 17.6   | 12.0 | 10.8  |
| c4ai-command-r-v01             | 2.0  | 7.8  | 7.5  | 3.8  | 7.5  | 11.4   | 6.8  | 7.0   |
| DeepSeek-R1-Distill-Qwen-32B   | 9.1  | 5.4  | 4.8  | 9.8  | 2.3  | 10.2   | 7.1  | 6.8   |
| Gemma-2-2b                     | 6.6  | 6.2  | 3.9  | 10.3 | 3.9  | 7.3    | 6.1  | 6.1   |
| Qwen2-VL-72B†                  | 11.8 | 3.5  | 4.6  | 4.0  | 2.9  | 4.2    | 4.5  | 5.0   |
| Internlm3-8b                   | 1.8  | 4.6  | 4.7  | 3.2  | 4.0  | 9.2    | 4.1  | 4.8   |
| DeepSeek-vl2-small†            | 3.1  | 1.8  | 1.8  | 4.5  | 0.0  | 0.3    | 4.8  | 1.7   |
| THUDM-chatglm3-6b              | 0.9  | 2.3  | 0.0  | 0.7  | 0.9  | 2.0    | 0.9  | 1.2   |
| Qwen2.5-Math-7B                | 1.4  | 1.7  | 0.0  | 2.1  | 0.0  | 1.5    | 1.9  | 1.0   |
| DeepSeek-math-7b-rl            | 0.7  | 0.0  | 0.0  | 1.5  | 0.0  | 0.6    | 0.9  | 0.4   |

† These models are equipped with multi-model abilities. Problems with images are also tested on these models.

**Abbreviations:** AMO (Atomic Physics) | E\&M (Electromagnetism) | CM (Classical Mechanics) | Opt. (Optics) | QM (Quantum Mechanics) | Stats. (Theromodynamics and Statistical Physics).

## Key Findings
- **Current foundation models struggle with complex physics reasoning**
- **Best models achieve less than 60% accuracy, revealing substantial limitations**
- **Self-reflection prompts improve reasoning consistency**
- **Retrieval-Augmented Generation (RAG) enhances accuracy**

## How to Use
1. Clone the repository:
   ```sh
   git clone https://github.com/yale-nlp/Physics.git
   ```
2. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```
3. Run the evaluation system:
   ```sh
   python evaluate.py --model <model_name>
   ```

## Future Work
- **Improve reasoning capabilities for physics problem-solving**
- **Integrate external physics knowledge for enhanced AI comprehension**
- **Expand dataset coverage to include interdisciplinary problems**

## Citation
```
@article{feng2025physics,
  title={PHYSICS: Benchmarking Foundation Models for PhD-Qualifying Exam Physics Problem Solving},
  author={Kaiyue Feng and Yilun Zhao and Yixin Liu and Tianyu Yang and Chen Zhao and John Sous and Arman Cohan},
  journal={arXiv preprint arXiv:2501.12948},
  year={2025}
}
```

## License
This project is licensed under the MIT License.

## Acknowledgments
This work is supported by the NVIDIA Academic Grant Program and Google TRC. Special thanks to Together AI for providing API credits.

