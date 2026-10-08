# FactoryPilot Web

FactoryPilot 前端基于 Ant Design Pro v6 / Ant Design 6 体系构建，当前已进入 **Phase 1.7 — Frontend Authentication + Permission-aware Navigation**。

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
- 正式制造业导航与 Dashboard 基线
- 登录页与 JWT access / refresh token 客户端
- `/api/v1/auth/me` 当前用户态
- Access Token 临近过期自动刷新与 401 单次重试
- Umi Access 路由守卫与 permission-aware 系统菜单
- 服务端会话注销
- Biome / TypeScript / Vitest

受保护业务 API 的前端服务应统一通过 `src/services/auth.ts` 中的 `apiFetch` 发起请求，避免重复实现 Bearer Token 与 Refresh Rotation 逻辑。
