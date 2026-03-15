type AcceptedValue = string | number | Blob;

export class FormBuilder {
    #form: FormData;

    constructor() {
        this.#form = new FormData();
    }

    append(key: string, value: AcceptedValue) {
        if (value instanceof Blob) {
            this.#form.append(key, value);
            return this;
        }

        this.#form.append(key, value.toString());
        return this;
    }

    appendIf(
        key: string,
        value: AcceptedValue | undefined | null,
        condition: (value: AcceptedValue | undefined | null) => value is AcceptedValue,
    ) {
        const shouldAdd = condition(value);
        if (shouldAdd) {
            return this.append(key, value);
        }

        return this;
    }

    build() {
        return this.#form;
    }
}
