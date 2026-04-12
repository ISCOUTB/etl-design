type AnyFunction = (...args: any[]) => unknown;

export function Singleton() {
    return function <T extends AnyFunction>(
        value: T,
        _context: ClassMethodDecoratorContext<unknown, T>,
    ) {
        let instance: ReturnType<T> | null = null;

        return function (this: unknown, ...args: Parameters<T>): ReturnType<T> {
            if (instance === null) {
                instance = value.apply(this, args) as ReturnType<T>;
            }

            return instance;
        } as T;
    };
}
