type AcceptedValue = string | number | Blob;

export class FormBuilder {
    #form: FormData;

    constructor() {
        this.#form = new FormData();
    }

    append(key: string, value: string): this;
    append(key: string, value: number): this;
    append(key: string, value: Blob, filename?: string): this;
    append(key: string, value: AcceptedValue, filename?: string): this;
    append(key: string, value: AcceptedValue, filename?: string): this {
        if (value instanceof Blob) {
            this.#form.append(key, value, filename);
            return this;
        }

        this.#form.append(key, value.toString());
        return this;
    }

    appendIf(
        key: string,
        value: AcceptedValue | undefined | null,
        condition: (value: AcceptedValue | undefined | null) => value is AcceptedValue,
    ): this {
        const shouldAdd = condition(value);
        if (shouldAdd) {
            return this.append(key, value);
        }

        return this;
    }

    build(): FormData {
        return this.#form;
    }
}
