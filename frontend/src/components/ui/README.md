# SiteDesk UI components

Small, accessible primitives for the counter workflow. Components use the existing Tailwind 3 setup and shared CSS variables; no extra runtime package is required.

```tsx
import { Badge, Button, Card, CardContent, CardHeader, CardTitle, Input } from "@/components/ui";
```

- `Button`: primary, secondary, outline, ghost and danger variants; default, small, large and icon sizes.
- `Card`: semantic section with optional header, title, description and content regions.
- `Input` / `Textarea`: shared field sizing, focus treatment and disabled states.
- `Badge`: neutral, success, warning, danger and info status styles.

Keep workflow-specific hotkeys in `components/pos/Terminal.tsx`; use these primitives for standard controls and content surfaces.
