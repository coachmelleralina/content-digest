// API boundary error type (feature 007, issue #4).
// Every rejection crossing lib/api.ts is an ApiError. `message` is always
// user-displayable (the UI may render it verbatim); `status` carries the
// HTTP status code when one applies.

// Note: declared as an explicit field (not a constructor parameter property)
// because the app tsconfig enables `erasableSyntaxOnly`, which forbids the
// `public status?: number` parameter-property syntax. Same public shape.
export class ApiError extends Error {
  status?: number;

  constructor(message: string, status?: number) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}
