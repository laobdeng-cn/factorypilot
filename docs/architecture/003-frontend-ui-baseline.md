# ADR 003 — FactoryPilot UI Baseline

## Status

Accepted for Phase 0.4.

## Decision

FactoryPilot adopts Ant Design Pro / Ant Design as the primary enterprise UI system. The application shell and information architecture are optimized for a domestic manufacturing enterprise context rather than a generic SaaS dashboard.

The Phase 0.4 baseline uses:

- a dark industrial side navigation;
- high-density manufacturing information hierarchy;
- dashboard patterns inspired by modern domestic B2B platforms;
- ECharts for operational visualization;
- Ant Design tables, cards, badges and status semantics;
- dedicated future entry points for APS, exception management, AI Decision Center and approval workflows.

## Information architecture

The navigation is organized around business domains: order fulfillment, production operations, material and inventory, procurement and supply, quality, exceptions, AI decisions, approvals, master data and system management.

## Boundary

Phase 0.4 remains a UI and information-architecture milestone. Dashboard data is still deterministic mock data. Real manufacturing domain models and persistent data are introduced in later phases.
