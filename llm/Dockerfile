# Our own private AI model server for Cloud Run (Ollama + open-weight models).
# Models are baked into the image so cold starts don't download anything.

FROM ollama/ollama:0.9.0

ENV OLLAMA_HOST=0.0.0.0:8080 \
    OLLAMA_MODELS=/models \
    OLLAMA_KEEP_ALIVE=-1 \
    OLLAMA_NUM_PARALLEL=4

# Change these together with CHAT_MODEL / EMBED_MODEL in the app service.
ARG CHAT_MODEL=gemma3:4b
ARG EMBED_MODEL=nomic-embed-text

RUN ollama serve & sleep 5 \
    && ollama pull ${CHAT_MODEL} \
    && ollama pull ${EMBED_MODEL}

ENTRYPOINT ["ollama", "serve"]
