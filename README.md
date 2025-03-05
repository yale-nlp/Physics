# PHYSICS: Benchmarking Foundation Models for PhD-Qualifying Exam Physics Problem Solving

## Overview
PHYSICS is a comprehensive benchmark designed to evaluate foundation models' ability to solve physics problems at the PhD-qualifying exam level. The dataset consists of 1,297 expert-annotated problems spanning six core physics domains, requiring advanced mathematical reasoning and theoretical knowledge.

## Features
- **Expert-Annotated Problems**: Covers six major physics disciplines:
  - Classical Mechanics
  - Quantum Mechanics
  - Thermodynamics and Statistical Mechanics
  - Electromagnetism
  - Atomic Physics
  - Optics
- **Advanced Multi-Step Reasoning**: The problems demand deep logical reasoning, theoretical understanding, and mathematical modeling.
- **Automated Evaluation System**:
  - Uses SymPy for symbolic computation-based correctness checking.
  - Leverages GPT-4o for natural language answer assessment.
- **Model Performance Benchmarking**: Evaluates 33 frontier foundation models, including proprietary (e.g., GPT-4o, Gemini-1.5-Pro) and open-source models (e.g., DeepSeek-R1, Llama-3.3-70B).
- **Comparative Performance Analysis**:
  - Best-performing model (o3-mini) achieves only **59.9% accuracy**.
  - Most open-source models struggle significantly, highlighting current limitations in AI-driven physics problem solving.

## Dataset
- **Total Problems**: 1,297
- **Validation Set**: 297 problems
- **Test Set**: 1,000 problems
- **Problems with Figures**: 298
- **Average Solution Length**: 234.75 words
- **Average Reasoning Steps**: 5.38

## Evaluation Methodology
1. **Model Response Processing**: Extracts final boxed answers, standardizes notations, and ensures consistency.
2. **Mathematical Verification**: Uses SymPy to check symbolic equivalence of mathematical expressions.
3. **Natural Language Evaluation**: Applies GPT-4o to verify logical correctness and conceptual clarity.
4. **Error Categorization**: Identifies common failure patterns, including:
   - Inability to integrate professional knowledge
   - Reliance on incorrect assumptions
   - Misinterpretation of problem constraints
   - Calculation errors in complex equations

## Experiment Findings
- **Proprietary Models**: o3-mini outperforms others but still struggles with multi-step reasoning and complex mathematical formulations.
- **Open-Source Models**: Most models perform below 30%, revealing substantial gaps in physics problem-solving ability.
- **Prompting Methods**: Self-reflection prompts improve model performance but do not fully bridge the gap.
- **Retrieval-Augmented Generation (RAG)**: Incorporating external knowledge sources enhances model accuracy, suggesting potential future improvements.

## Future Work
- Improve model reasoning frameworks for scientific domains.
- Enhance integration of external knowledge sources for domain-specific problem solving.
- Expand dataset to include interdisciplinary physics problems.

## Citation
If you use PHYSICS in your research, please cite:
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

