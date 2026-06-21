import subprocess

subprocess.run([
    r"C:\llama.cpp\llama-cli.exe",
    "-m",
    r"C:\RAG-ChatBot\models\Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf",
    "-c",
    "4096"
])