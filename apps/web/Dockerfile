FROM node:22-alpine

RUN corepack enable && corepack prepare pnpm@10.17.1 --activate

WORKDIR /workspace

COPY package.json pnpm-workspace.yaml ./
COPY apps/web/package.json ./apps/web/package.json
RUN pnpm install --filter @factorypilot/web...

COPY apps/web ./apps/web

WORKDIR /workspace/apps/web

ENV PORT=8001 \
    HOST=0.0.0.0

EXPOSE 8001

CMD ["pnpm", "dev"]
