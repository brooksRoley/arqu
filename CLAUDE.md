# CLAUDE.md - AI Assistant Guide for BrooksArqu

This document provides comprehensive guidance for AI assistants working with the BrooksArqu codebase.

## Project Overview

**BrooksArqu** is a Vue 3 single-page application showcasing creative writing content (poetry, fiction, and interactive storytelling). The project uses modern web technologies including TypeScript, Vite, Vue Router, and Tailwind CSS.

**Tech Stack:**
- **Framework:** Vue 3 with Composition API (`<script setup>`)
- **Language:** TypeScript
- **Build Tool:** Vite 5
- **Styling:** Tailwind CSS (JIT mode) + Custom CSS
- **Routing:** Vue Router 4 (with lazy loading)
- **Utilities:** VueUse core composables
- **Package Manager:** npm

## Repository Structure

```
arqu/
├── src/
│   ├── assets/           # Static assets (images, logos, text files)
│   ├── components/       # Reusable Vue components
│   │   ├── icons/       # Icon components
│   │   ├── MultiStepForm.vue
│   │   ├── MoodSelection.vue
│   │   └── ...
│   ├── views/           # Page-level components
│   │   ├── HomeView.vue
│   │   ├── AboutView.vue
│   │   ├── Elora.vue
│   │   ├── Koming.vue
│   │   ├── NatureNurture.vue
│   │   ├── Supplicant.vue
│   │   ├── Descent.vue
│   │   └── CouplesTherapy.vue
│   ├── router/          # Vue Router configuration
│   │   └── index.ts
│   ├── App.vue          # Root component with navigation
│   ├── main.ts          # Application entry point
│   ├── index.css        # Global Tailwind imports
│   └── shims-vue.d.ts   # TypeScript declarations
├── public/              # Public static assets
├── .vscode/            # VS Code settings
├── index.html          # HTML entry point
├── vite.config.ts      # Vite configuration
├── tailwind.config.js  # Tailwind CSS configuration
├── tsconfig.json       # TypeScript configuration
├── .eslintrc.cjs       # ESLint configuration
├── .prettierrc.json    # Prettier configuration
└── package.json        # Dependencies and scripts
```

## Development Workflow

### Initial Setup

```bash
npm install
```

### Development Commands

- **Development Server:** `npm run dev` - Starts Vite dev server with HMR
- **Production Build:** `npm run build` - Type-checks and builds for production
- **Build Only:** `npm run build-only` - Builds without type-checking
- **Type Check:** `npm run type-check` - Runs vue-tsc for type checking
- **Preview:** `npm run preview` - Preview production build locally
- **Lint:** `npm run lint` - Runs ESLint with auto-fix
- **Format:** `npm run format` - Runs Prettier on src/ directory

### Git Workflow

- **Main Branch:** `main` (or `master`)
- **Feature Branches:** Use descriptive branch names (e.g., `feature/add-new-story`, `fix/routing-issue`)
- **Commit Messages:** Use conventional commit format when possible (e.g., `feat:`, `fix:`, `docs:`, `style:`)

## Code Conventions

### Vue Component Structure

Components follow the **Composition API with `<script setup>`** syntax:

```vue
<script setup lang="ts">
import { ref, computed } from 'vue'
// Component logic here
</script>

<template>
  <!-- Template here -->
</template>

<style scoped>
/* Component-specific styles */
</style>
```

### File Organization

- **Components:** Place in `src/components/` - These are reusable UI elements
- **Views:** Place in `src/views/` - These are page-level components mapped to routes
- **Assets:** Place in `src/assets/` - Images, logos, static text files
- **Icons:** Place in `src/components/icons/` - SVG icon components

### Naming Conventions

- **Component Files:** PascalCase (e.g., `MultiStepForm.vue`, `HomeView.vue`)
- **View Components:** Suffix with `View` (e.g., `HomeView.vue`, `AboutView.vue`)
- **Variables/Functions:** camelCase
- **Types/Interfaces:** PascalCase
- **CSS Classes:** kebab-case or Tailwind utility classes

### TypeScript Guidelines

- Use TypeScript for all `.ts` and `.vue` files
- Enable strict type checking (`vue-tsc --build --force`)
- Import types explicitly when needed
- Use `import type` for type-only imports to improve tree-shaking

### Routing Conventions

Routes are defined in `src/router/index.ts`:

- **Home route:** Uses eager loading (`import HomeView from '../views/HomeView.vue'`)
- **Other routes:** Use lazy loading for code splitting (`component: () => import('../views/AboutView.vue')`)
- **Route names:** Use lowercase or PascalCase consistently
- **Route paths:** Use lowercase with hyphens (e.g., `/about`, `/multi`)

### Styling Guidelines

1. **Tailwind CSS First:** Use Tailwind utility classes for styling when possible
2. **Scoped Styles:** Use `<style scoped>` for component-specific CSS
3. **CSS Variables:** Existing code uses CSS variables (e.g., `var(--color-text)`, `var(--color-border)`)
4. **Global Styles:** Import in `src/index.css` and `src/assets/main.css`

### Code Quality Tools

**ESLint Configuration:**
- Extends `plugin:vue/vue3-essential`
- Uses `@vue/eslint-config-typescript`
- Uses `@vue/eslint-config-prettier/skip-formatting`
- Target: `ecmaVersion: 'latest'`

**Prettier Configuration:**
- No semicolons (`"semi": false`)
- Single quotes (`"singleQuote": true`)
- Tab width: 2 spaces
- Print width: 100 characters
- No trailing commas (`"trailingComma": "none"`)

**IMPORTANT:** Always run `npm run lint` before committing. The linter auto-fixes many issues.

## Key Architectural Patterns

### 1. Path Aliasing

Vite is configured with `@` alias pointing to `src/`:

```typescript
import Component from '@/components/Component.vue'
import logo from '@/assets/logo.svg'
```

### 2. Route Lazy Loading

All non-critical routes use lazy loading for better performance:

```typescript
{
  path: '/about',
  name: 'about',
  component: () => import('../views/AboutView.vue')
}
```

### 3. Component Composition

- Keep components small and focused
- Extract reusable logic into composables (VueUse is available)
- Use props for parent-child communication
- Use events for child-parent communication

### 4. Assets Management

- **Images:** Stored in `src/assets/` and referenced via imports or `@/assets/`
- **Large Assets:** Consider using `public/` folder for assets that shouldn't be processed by Vite

## Common Tasks for AI Assistants

### Adding a New Page/View

1. Create a new Vue component in `src/views/` (e.g., `NewView.vue`)
2. Add route in `src/router/index.ts`:
   ```typescript
   {
     path: '/new-page',
     name: 'newPage',
     component: () => import('../views/NewView.vue')
   }
   ```
3. Add navigation link in `src/App.vue`:
   ```vue
   <RouterLink to="/new-page">New Page</RouterLink>
   ```

### Adding a New Component

1. Create component in `src/components/` (e.g., `MyComponent.vue`)
2. Use `<script setup lang="ts">` syntax
3. Export props using `defineProps<{ propName: type }>()`
4. Emit events using `defineEmits<{ eventName: [payload: type] }>()`

### Modifying Styles

1. **Prefer Tailwind utilities** in template
2. For custom styles, use `<style scoped>` within component
3. For global styles, modify `src/assets/base.css` or `src/assets/main.css`
4. Run `npm run format` after making changes

### Working with TypeScript

1. Run `npm run type-check` regularly to catch type errors
2. Don't use `any` types - use proper typing
3. For Vue component props, use `defineProps<{ ... }>()` syntax
4. Check `tsconfig.app.json` for compiler options

### Debugging

1. Use Vue DevTools browser extension
2. Check browser console for errors
3. Run `npm run type-check` for TypeScript errors
4. Run `npm run lint` for linting issues
5. Check Vite dev server output for build errors

## Content Guidelines

This project contains **creative writing content** (poetry, fiction, interactive narratives):

- Respect the artistic nature of the content
- Maintain the tone and style when editing text
- Poetry formatting is intentional - preserve line breaks and spacing
- Interactive components (like MultiStepForm) are part of the storytelling experience

## Performance Considerations

1. **Lazy Loading:** Already implemented for routes - maintain this pattern
2. **Code Splitting:** Vite automatically handles this
3. **Image Optimization:** Consider optimizing large images in `src/assets/`
4. **Bundle Size:** Run `npm run build` and check `dist/` folder size
5. **Tailwind Purging:** Configured to remove unused CSS in production

## VS Code Setup

Recommended extensions (see `.vscode/extensions.json`):
- **Volar** (Vue.volar) - Vue 3 language support
- Disable **Vetur** if installed (conflicts with Volar)

## Testing

**Note:** No testing framework is currently configured. If adding tests:
- Consider Vitest (pairs well with Vite)
- Consider Vue Test Utils for component testing
- Consider Playwright or Cypress for e2e testing

## Deployment

Build artifacts are generated in `dist/` folder:

```bash
npm run build
```

The `dist/` folder can be deployed to:
- Static hosting (Netlify, Vercel, GitHub Pages)
- CDN
- Traditional web server

Make sure to configure the server to handle SPA routing (redirect all routes to `index.html`).

## Environment Variables

If needed, create `.env` files (not currently used):
- `.env` - Loaded in all cases
- `.env.local` - Loaded in all cases, ignored by git
- `.env.production` - Loaded for production builds

Access variables in code: `import.meta.env.VITE_VARIABLE_NAME`

## Troubleshooting

### Common Issues

1. **Type errors:** Run `npm run type-check` to see all errors
2. **Module not found:** Check import paths and `@` alias usage
3. **Styles not applying:** Ensure Tailwind directives are imported in `src/index.css`
4. **Router not working:** Check route definitions in `src/router/index.ts`
5. **Build failures:** Check for TypeScript errors and missing dependencies

### Clean Install

If issues persist:
```bash
rm -rf node_modules package-lock.json
npm install
```

## Important Notes for AI Assistants

1. **Always read files before modifying them** - Don't assume structure
2. **Preserve existing patterns** - Match the coding style used in the project
3. **Run linter** - Use `npm run lint` before suggesting code is complete
4. **Type safety** - Ensure TypeScript types are correct
5. **Test changes** - Suggest running `npm run dev` to verify changes work
6. **Respect content** - This is a creative writing project, handle text carefully
7. **Use Prettier config** - Follow the no-semicolon, single-quote style
8. **Path aliases** - Use `@/` for imports from `src/`
9. **Component structure** - Use `<script setup>` with TypeScript
10. **Lazy loading** - Maintain for non-critical routes

## Additional Resources

- [Vue 3 Documentation](https://vuejs.org/)
- [Vite Documentation](https://vitejs.dev/)
- [Vue Router Documentation](https://router.vuejs.org/)
- [Tailwind CSS Documentation](https://tailwindcss.com/)
- [TypeScript Documentation](https://www.typescriptlang.org/)
- [VueUse Documentation](https://vueuse.org/)

---

**Last Updated:** 2026-01-17

For questions or clarifications about this codebase, refer to the actual source files and configurations.
