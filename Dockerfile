FROM python:3.13-slim

ENV PORT=7860
ENV PYTHONUNBUFFERED=1
ENV TRANSFORMERS_CACHE=/tmp/hf_cache

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY backend/pyproject.toml ./
# Versionen wie in backend/uv.lock; neuere Pakete rechnen anders (statsmodels 0.15 bricht die Holt-Prognose ab)
RUN pip install --no-cache-dir torch==2.10.0 --index-url https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir fastapi==0.124.0 uvicorn==0.38.0 python-dotenv==1.2.1 python-multipart==0.0.21 \
    gensim==4.4.0 numpy==2.4.0 scipy==1.16.3 pandas==2.3.3 openpyxl==3.1.5 supabase==2.27.0 statsmodels==0.14.6 \
    transformers==5.1.0 tokenizers==0.22.2 huggingface-hub==1.4.1 sentencepiece==0.2.2 \
    ruptures==1.1.10 yfinance==1.7.0

COPY backend/ .

RUN mkdir -p models/saved_models

RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app /tmp
USER appuser

EXPOSE 7860

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]
