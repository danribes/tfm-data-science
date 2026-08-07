import "@testing-library/jest-dom/vitest";
import { cleanup } from "@testing-library/react";
import { afterAll, afterEach, beforeAll } from "vitest";
import { server } from "./msw/server";

beforeAll(() => server.listen({ onUnhandledRequest: "error" }));
afterEach(() => server.resetHandlers());
// RTL's auto-cleanup relies on a *global* afterEach; this project runs with
// `test.globals: false`, so it never registers. Unmount explicitly instead —
// otherwise DOM from one `it()`'s render() leaks into the next.
afterEach(() => cleanup());
afterAll(() => server.close());
