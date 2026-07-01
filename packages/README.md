# Monorepo Shared Packages

This directory is intended for shared libraries and configurations consumed by multiple applications in the monorepo.

## Expected Packages

- **`packages/config`**: Core ESLint, Prettier, and TypeScript base compiler configurations.
- **`packages/common`**: Shared TypeScript types, enum definitions, or common validation logic.
- **`packages/database`**: If modularized, this would contain the compiled database clients (e.g. Prisma client) and schema helpers.
