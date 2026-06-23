| Decision | Options Considered | Choice | Why |
|----------|-------------------|--------|-----|
| Model Hosting Strategy | Enterprise APIs, Cloud Inference, Local Open-Source Models | Local Open-Source Model | Avoid recurring costs and usage limits while retaining full control over inference, experimentation, and deployment. |
| Model Family | Llama 3 8B, Other Models | Llama 3.1 8B Instruct | Strong open-source model with good instruction following |
| Quantization | FP16, Q8, Q6, Q5, Q4, Q3 | Q4_K_M | Best quality-to-resource tradeoff |
| Model Format | GGUF, Safetensors, PyTorch | GGUF | Native format for llama.cpp |
| Inference Engine | llama.cpp, Ollama, Transformers, vLLM | llama.cpp | Efficient local inference and quantized model support |
| Knowledge Source v1 | PDFs, DOCX, Websites | PDFs Only | Simplest scope for first prototype |
| Backend Framework | FastAPI, Flask, Django | FastAPI | Modern, AI-friendly, easy API development |
| Prototype Interface | Terminal, Web UI, Both | Terminal | Fastest path to validation |
| Deployment Strategy | Local Only, Cloud First, Hybrid | Local → Public Demo | Minimize complexity during development |
| Expected Scale | Single User, <10, 10-100, 100+ | <10 Users | Matches project goals and infrastructure |
| Fine-Tuning Strategy | Fine-Tune, No Fine-Tune | No Fine-Tuning | Focus effort on retrieval quality |
| Evaluation Method | Demo Only, Qualitative, Controlled Experiment | Baseline LLM vs LLM+RAG | Produces measurable evidence of RAG effectiveness |