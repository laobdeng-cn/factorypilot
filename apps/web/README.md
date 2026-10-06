# FactoryPilot Web

FactoryPilot 前端基于 Ant Design Pro v6 / Ant Design 6 体系构建，当前阶段为 **Phase 0.3 — Frontend Foundation**。

## 环境

- Node.js 22+
- pnpm 10+
- FastAPI 默认运行在 `http://127.0.0.1:8000`
- Web 默认运行在 `http://127.0.0.1:8001`

## 本地开发

```bash
pnpm install
pnpm --dir apps/web dev
```

或者在 `apps/web` 目录：

```bash
pnpm dev
```

Umi 开发代理会将 `/api/*` 转发至本地 FastAPI。

## 质量检查

```bash
pnpm lint
pnpm typecheck
pnpm test
pnpm build
```

## 当前包含

- Ant Design Pro / Umi Max 工程基础
- Ant Design 6 + ProComponents
- React Query 数据请求状态
- Zustand 应用状态
- FastAPI `/api/v1/health/*` 联调
- Mock Factory Dashboard
- 初始制造业菜单骨架
- Biome / TypeScript / Vitest

Phase 0.4 将完成 FactoryPilot Design Tokens、完整导航和正式 Dashboard 视觉。
