# React Best Practices

**Version 1.0.0**
Vercel Engineering
January 2026

> **Note:**
> This document is mainly for agents and LLMs to follow when maintaining,
> generating, or refactoring React and Next.js codebases. Humans
> may also find it useful, but guidance here is optimized for automation
> and consistency by AI-assisted workflows.

---

## Abstract

Comprehensive performance optimization guide for React and Next.js applications, designed for AI agents and LLMs. Contains 40+ rules across 8 categories, prioritized by impact from critical (eliminating waterfalls, reducing bundle size) to incremental (advanced patterns). Each rule includes detailed explanations, real-world examples comparing incorrect vs. correct implementations, and specific impact metrics to guide automated refactoring and code generation.

---

## Table of Contents

1. [Eliminating Waterfalls](01-eliminating-waterfalls.md#1-eliminating-waterfalls) (**CRITICAL**)
   - 1.1 [Check Cheap Conditions Before Async Flags](01-eliminating-waterfalls.md#11-check-cheap-conditions-before-async-flags)
   - 1.2 [Defer Await Until Needed](01-eliminating-waterfalls.md#12-defer-await-until-needed)
   - 1.3 [Dependency-Based Parallelization](01-eliminating-waterfalls.md#13-dependency-based-parallelization)
   - 1.4 [Prevent Waterfall Chains in API Routes](01-eliminating-waterfalls.md#14-prevent-waterfall-chains-in-api-routes)
   - 1.5 [Promise.all() for Independent Operations](01-eliminating-waterfalls.md#15-promiseall-for-independent-operations)
   - 1.6 [Strategic Suspense Boundaries](01-eliminating-waterfalls.md#16-strategic-suspense-boundaries)
2. [Bundle Size Optimization](02-bundle-size.md#2-bundle-size-optimization) (**CRITICAL**)
   - 2.1 [Avoid Barrel File Imports](02-bundle-size.md#21-avoid-barrel-file-imports)
   - 2.2 [Conditional Module Loading](02-bundle-size.md#22-conditional-module-loading)
   - 2.3 [Defer Non-Critical Third-Party Libraries](02-bundle-size.md#23-defer-non-critical-third-party-libraries)
   - 2.4 [Dynamic Imports for Heavy Components](02-bundle-size.md#24-dynamic-imports-for-heavy-components)
   - 2.5 [Prefer Statically Analyzable Paths](02-bundle-size.md#25-prefer-statically-analyzable-paths)
   - 2.6 [Preload Based on User Intent](02-bundle-size.md#26-preload-based-on-user-intent)
3. [Server-Side Performance](03-server-side.md#3-server-side-performance) (**HIGH**)
   - 3.1 [Authenticate Server Actions Like API Routes](03-server-side.md#31-authenticate-server-actions-like-api-routes)
   - 3.2 [Avoid Duplicate Serialization in RSC Props](03-server-side.md#32-avoid-duplicate-serialization-in-rsc-props)
   - 3.3 [Avoid Shared Module State for Request Data](03-server-side.md#33-avoid-shared-module-state-for-request-data)
   - 3.4 [Cross-Request LRU Caching](03-server-side.md#34-cross-request-lru-caching)
   - 3.5 [Hoist Static I/O to Module Level](03-server-side.md#35-hoist-static-io-to-module-level)
   - 3.6 [Minimize Serialization at RSC Boundaries](03-server-side.md#36-minimize-serialization-at-rsc-boundaries)
   - 3.7 [Parallel Data Fetching with Component Composition](03-server-side.md#37-parallel-data-fetching-with-component-composition)
   - 3.8 [Parallel Nested Data Fetching](03-server-side.md#38-parallel-nested-data-fetching)
   - 3.9 [Per-Request Deduplication with React.cache()](03-server-side.md#39-per-request-deduplication-with-reactcache)
   - 3.10 [Use after() for Non-Blocking Operations](03-server-side.md#310-use-after-for-non-blocking-operations)
4. [Client-Side Data Fetching](04-client-side.md#4-client-side-data-fetching) (**MEDIUM-HIGH**)
   - 4.1 [Deduplicate Global Event Listeners](04-client-side.md#41-deduplicate-global-event-listeners)
   - 4.2 [Use Passive Event Listeners for Scrolling Performance](04-client-side.md#42-use-passive-event-listeners-for-scrolling-performance)
   - 4.3 [Use SWR for Automatic Deduplication](04-client-side.md#43-use-swr-for-automatic-deduplication)
   - 4.4 [Version and Minimize localStorage Data](04-client-side.md#44-version-and-minimize-localstorage-data)
5. [Re-render Optimization](05-rerender.md#5-re-render-optimization) (**MEDIUM**)
   - 5.1 [Calculate Derived State During Rendering](05-rerender.md#51-calculate-derived-state-during-rendering)
   - 5.2 [Defer State Reads to Usage Point](05-rerender.md#52-defer-state-reads-to-usage-point)
   - 5.3 [Do not wrap a simple expression with a primitive result type in useMemo](05-rerender.md#53-do-not-wrap-a-simple-expression-with-a-primitive-result-type-in-usememo)
   - 5.4 [Don't Define Components Inside Components](05-rerender.md#54-dont-define-components-inside-components)
   - 5.5 [Extract Default Non-primitive Parameter Value from Memoized Component to Constant](05-rerender.md#55-extract-default-non-primitive-parameter-value-from-memoized-component-to-constant)
   - 5.6 [Extract to Memoized Components](05-rerender.md#56-extract-to-memoized-components)
   - 5.7 [Narrow Effect Dependencies](05-rerender.md#57-narrow-effect-dependencies)
   - 5.8 [Put Interaction Logic in Event Handlers](05-rerender.md#58-put-interaction-logic-in-event-handlers)
   - 5.9 [Split Combined Hook Computations](05-rerender.md#59-split-combined-hook-computations)
   - 5.10 [Subscribe to Derived State](05-rerender.md#510-subscribe-to-derived-state)
   - 5.11 [Use Functional setState Updates](05-rerender.md#511-use-functional-setstate-updates)
   - 5.12 [Use Lazy State Initialization](05-rerender.md#512-use-lazy-state-initialization)
   - 5.13 [Use Transitions for Non-Urgent Updates](05-rerender.md#513-use-transitions-for-non-urgent-updates)
   - 5.14 [Use useDeferredValue for Expensive Derived Renders](05-rerender.md#514-use-usedeferredvalue-for-expensive-derived-renders)
   - 5.15 [Use useRef for Transient Values](05-rerender.md#515-use-useref-for-transient-values)
6. [Rendering Performance](06-rendering.md#6-rendering-performance) (**MEDIUM**)
   - 6.1 [Animate SVG Wrapper Instead of SVG Element](06-rendering.md#61-animate-svg-wrapper-instead-of-svg-element)
   - 6.2 [CSS content-visibility for Long Lists](06-rendering.md#62-css-content-visibility-for-long-lists)
   - 6.3 [Hoist Static JSX Elements](06-rendering.md#63-hoist-static-jsx-elements)
   - 6.4 [Optimize SVG Precision](06-rendering.md#64-optimize-svg-precision)
   - 6.5 [Prevent Hydration Mismatch Without Flickering](06-rendering.md#65-prevent-hydration-mismatch-without-flickering)
   - 6.6 [Suppress Expected Hydration Mismatches](06-rendering.md#66-suppress-expected-hydration-mismatches)
   - 6.7 [Use Activity Component for Show/Hide](06-rendering.md#67-use-activity-component-for-showhide)
   - 6.8 [Use defer or async on Script Tags](06-rendering.md#68-use-defer-or-async-on-script-tags)
   - 6.9 [Use Explicit Conditional Rendering](06-rendering.md#69-use-explicit-conditional-rendering)
   - 6.10 [Use React DOM Resource Hints](06-rendering.md#610-use-react-dom-resource-hints)
   - 6.11 [Use useTransition Over Manual Loading States](06-rendering.md#611-use-usetransition-over-manual-loading-states)
7. [JavaScript Performance](07-javascript.md#7-javascript-performance) (**LOW-MEDIUM**)
   - 7.1 [Avoid Layout Thrashing](07-javascript.md#71-avoid-layout-thrashing)
   - 7.2 [Build Index Maps for Repeated Lookups](07-javascript.md#72-build-index-maps-for-repeated-lookups)
   - 7.3 [Cache Property Access in Loops](07-javascript.md#73-cache-property-access-in-loops)
   - 7.4 [Cache Repeated Function Calls](07-javascript.md#74-cache-repeated-function-calls)
   - 7.5 [Cache Storage API Calls](07-javascript.md#75-cache-storage-api-calls)
   - 7.6 [Combine Multiple Array Iterations](07-javascript.md#76-combine-multiple-array-iterations)
   - 7.7 [Defer Non-Critical Work with requestIdleCallback](07-javascript.md#77-defer-non-critical-work-with-requestidlecallback)
   - 7.8 [Early Length Check for Array Comparisons](07-javascript.md#78-early-length-check-for-array-comparisons)
   - 7.9 [Early Return from Functions](07-javascript.md#79-early-return-from-functions)
   - 7.10 [Hoist RegExp Creation](07-javascript.md#710-hoist-regexp-creation)
   - 7.11 [Use flatMap to Map and Filter in One Pass](07-javascript.md#711-use-flatmap-to-map-and-filter-in-one-pass)
   - 7.12 [Use Loop for Min/Max Instead of Sort](07-javascript.md#712-use-loop-for-minmax-instead-of-sort)
   - 7.13 [Use Set/Map for O(1) Lookups](07-javascript.md#713-use-setmap-for-o1-lookups)
   - 7.14 [Use toSorted() Instead of sort() for Immutability](07-javascript.md#714-use-tosorted-instead-of-sort-for-immutability)
8. [Advanced Patterns](08-advanced.md#8-advanced-patterns) (**LOW**)
   - 8.1 [Do Not Put Effect Events in Dependency Arrays](08-advanced.md#81-do-not-put-effect-events-in-dependency-arrays)
   - 8.2 [Initialize App Once, Not Per Mount](08-advanced.md#82-initialize-app-once-not-per-mount)
   - 8.3 [Store Event Handlers in Refs](08-advanced.md#83-store-event-handlers-in-refs)
   - 8.4 [useEffectEvent for Stable Callback Refs](08-advanced.md#84-useeffectevent-for-stable-callback-refs)

---


## References

See [references.md](references.md).
