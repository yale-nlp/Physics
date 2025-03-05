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

### Proprietary Model Performance

| Model               | Atomic | E&M  | CM   | Optics | QM   | Stats | Overall |
| ------------------- | ------ | ---- | ---- | ------ | ---- | ----- | ------- |
| o3-mini            | 52.4   | 64.9 | 59.8 | 51.5   | 66.0 | 60.0  | 59.9    |
| GPT-4o             | 35.3   | 44.1 | 33.4 | 23.4   | 33.8 | 45.0  | 36.7    |
| Claude-3.5-Sonnet  | 37.2   | 34.8 | 27.6 | 35.5   | 35.1 | 38.4  | 34.7    |

### Open-Source Model Performance

| Model                  | Atomic | E&M  | CM   | Optics | QM   | Stats | Overall |
| ---------------------- | ------ | ---- | ---- | ------ | ---- | ----- | ------- |
| DeepSeek-R1           | 37.0   | 48.6 | 38.3 | 43.1   | 44.5 | 51.5  | 44.3    |
| Qwen2.5-Math-72B      | 27.0   | 34.8 | 27.3 | 27.4   | 36.2 | 37.0  | 32.2    |
| Llama-3.3-70B         | 28.2   | 35.8 | 27.9 | 17.2   | 31.4 | 41.3  | 31.5    |

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

