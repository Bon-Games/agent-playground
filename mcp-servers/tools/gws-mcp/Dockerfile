FROM node:22-alpine

WORKDIR /app

EXPOSE 8100

ENV PORT=8100
ENV HOST=0.0.0.0
ENV GOOGLE_APPLICATION_CREDENTIALS=/app/credentials.json

CMD ["npx", "--yes", "@googleapis/mcp-server-workspace@latest", "--transport", "http", "--port", "8100"]
