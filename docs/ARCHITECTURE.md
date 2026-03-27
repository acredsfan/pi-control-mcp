# Architecture

## Layers

1. **Transport layer**: stdio and streamable HTTP
2. **Security layer**: auth, policy and tier gating
3. **Tool layer**: desktop, file, and system tools
4. **Backend layer**: Wayland/X11 desktop capability abstraction

## Policy resolution

Effective tools are resolved by:

1. Explicit include list (`tools.enable`) if present
2. Otherwise default tier set (Tier 1 + Tier 2, optional Tier 3)
3. Exclude list (`tools.exclude`)
4. Intersect with known registered tools
