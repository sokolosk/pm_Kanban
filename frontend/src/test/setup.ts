import "@testing-library/jest-dom";

class MockResizeObserver {
	observe() {}
	unobserve() {}
	disconnect() {}
}

Object.defineProperty(globalThis, "ResizeObserver", {
	writable: true,
	configurable: true,
	value: MockResizeObserver,
});
