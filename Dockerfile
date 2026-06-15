FROM python:3.10-slim

WORKDIR /app

# Copia todo o código fonte para dentro do container
COPY . /app/

# Executa o script python no modo interativo padrão
CMD ["python", "main.py"]
