FROM node:20-slim
RUN apt-get update && apt-get install -y git python3 make g++ \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /opt
RUN git clone --depth 1 https://github.com/gemini-cli-extensions/workspace.git
WORKDIR /opt/workspace
RUN npm install && npm run build \
    && npm run build:auth-utils -w workspace-server
ENV GEMINI_CLI_WORKSPACE_FORCE_FILE_STORAGE=true
CMD ["node", "workspace-server/dist/index.js"]