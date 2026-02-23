<script setup lang="ts">
    import { AlignLeft, Cloud, Database, Info, Lock, User } from "lucide-vue-next";

    definePageMeta({
        title: "Create Project",
        layout: "sidebar",
        i18n: {
            paths: {
                en: "/projects/create",
            },
        },
    });

    const { CreateProjectSchema } = useCreateProjectSchema();
    const { handleSubmit } = useForm({
        validationSchema: toTypedSchema(CreateProjectSchema.value),
        initialValues: {
            name: "",
            description: "",
            provider: "",
            dbHost: "",
            dbPort: "",
            dbUser: "",
            dbPassword: "",
            dbName: "",
            dbParams: "",
        },
    });

    const api = useApi();
    const [loading] = useToggle(false);
    const onSubmit = handleSubmit((values) => {
        const formData = new FormData();

        formData.set("name", values.name);

        /**
         * TODO: Some issues here with the typing
         * Basically, .set(key, value)
         * value cannot be of type undefined, that's why
         * it yells at me
         */
        // formData.set("description", values.description);
        // formData.set("provider", values.provider);
        // formData.set("db_host", values.dbHost);
        // formData.set("db_port", values.dbPort);
        // formData.set("db_user", values.dbUser);
        // formData.set("db_password", values.dbPassword);
        // formData.set("db_name", values.dbName);
        // formData.set("db_params", values.dbParams);

        api("/projects/", {
            method: "POST",
            body: formData,
            onRequest({ options }) {
                console.warn(Array.from(options.headers.entries()).length);
                options.headers.forEach((value, key) =>
                    console.warn(`Header. key=${key} value=${value}`),
                );
            },
        })
            .then((response) => {
                console.warn(response);
            })
            .finally(() => (loading.value = false));
    });
</script>

<template>
    <form class="mx-auto w-full max-w-2xl" @submit="onSubmit">
        <!-- HEADER -->
        <div class="mb-8">
            <h1 class="text-2xl font-semibold tracking-tight text-foreground">
                {{ $t("projects.create.header.title") }}
            </h1>
            <p class="mt-1.5 text-sm text-muted-foreground">
                {{ $t("projects.create.header.description") }}
            </p>
        </div>

        <!-- BASIC INFORMATION -->
        <section>
            <div class="mb-4 flex items-center gap-2">
                <div
                    class="flex size-7 items-center justify-center rounded-md bg-primary/10 text-primary"
                >
                    <Info class="size-3.5" />
                </div>
                <h2 class="text-sm font-medium text-foreground">
                    {{ $t("projects.create.sections.general.title") }}
                </h2>
            </div>

            <div class="flex flex-col space-y-4">
                <VeeField v-slot="{ field, errors }" name="name">
                    <Field :data-invalid="!!errors.length">
                        <FieldLabel for="title">
                            {{ $t("projects.create.fields.name.label") }}
                            <span class="text-destructive">*</span>
                        </FieldLabel>

                        <InputGroup>
                            <InputGroupInput
                                id="name"
                                v-bind="field"
                                :placeholder="$t('projects.create.fields.name.placeholder')"
                                autocomplete="off"
                                :aria-invalid="!!errors.length"
                            />

                            <InputGroupAddon align="inline-start">
                                <AlignLeft class="size-4" stroke-width="2" />
                            </InputGroupAddon>
                        </InputGroup>
                        <FieldDescription>
                            {{ $t("projects.create.fields.name.description") }}
                        </FieldDescription>
                        <FieldError v-if="errors.length" :errors="errors" />
                    </Field>
                </VeeField>

                <VeeField v-slot="{ field, errors }" name="description">
                    <Field :data-invalid="!!errors.length">
                        <FieldLabel for="description">
                            {{ $t("projects.create.fields.description.label") }}
                        </FieldLabel>

                        <Textarea
                            id="description"
                            v-bind="field"
                            autocomplete="off"
                            :placeholder="$t('projects.create.fields.description.placeholder')"
                            :aria-invalid="!!errors.length"
                        />
                        <FieldDescription>
                            {{ $t("projects.create.fields.description.description") }}
                        </FieldDescription>
                        <FieldError v-if="errors.length" :errors="errors" />
                    </Field>
                </VeeField>
            </div>
        </section>

        <Separator class="my-8" />

        <!-- DATABASE INFORMATION -->
        <section>
            <div class="mb-4 flex items-center gap-2">
                <div
                    class="flex size-7 items-center justify-center rounded-md bg-primary/10 text-primary"
                >
                    <Database class="size-3.5" />
                </div>
                <h2 class="text-sm font-medium text-foreground">
                    {{ $t("projects.create.sections.database.title") }}
                </h2>
            </div>

            <div class="flex flex-col space-y-4">
                <VeeField v-slot="{ field, errors }" name="provider">
                    <Field :data-invalid="!!errors.length">
                        <FieldLabel for="provider">
                            {{ $t("projects.create.fields.provider.label") }}
                        </FieldLabel>

                        <InputGroup>
                            <InputGroupInput
                                id="provider"
                                v-bind="field"
                                autocomplete="off"
                                :placeholder="$t('projects.create.fields.provider.placeholder')"
                                :aria-invalid="!!errors.length"
                            />

                            <InputGroupAddon align="inline-start">
                                <Cloud class="size-4" stroke-width="2" />
                            </InputGroupAddon>
                        </InputGroup>
                        <FieldDescription>
                            {{ $t("projects.create.fields.provider.description") }}
                        </FieldDescription>
                        <FieldError v-if="errors.length" :errors="errors" />
                    </Field>
                </VeeField>

                <div class="grid grid-cols-12 space-x-4">
                    <div class="col-span-6">
                        <VeeField v-slot="{ field, errors }" name="dbHost">
                            <Field :data-invalid="!!errors.length">
                                <FieldLabel for="dbHost">
                                    {{ $t("projects.create.fields.db_host.label") }}
                                </FieldLabel>
                                <Input
                                    id="dbHost"
                                    v-bind="field"
                                    placeholder="localhost"
                                    autocomplete="off"
                                    :aria-invalid="!!errors.length"
                                />
                                <FieldError v-if="errors.length" :errors="errors" />
                            </Field>
                        </VeeField>
                    </div>
                    <div class="col-span-6">
                        <VeeField v-slot="{ field, errors }" name="dbPort">
                            <Field :data-invalid="!!errors.length">
                                <FieldLabel for="dbPort">
                                    {{ $t("projects.create.fields.db_port.label") }}
                                </FieldLabel>
                                <Input
                                    id="dbPort"
                                    v-bind="field"
                                    placeholder="5432"
                                    autocomplete="off"
                                    :aria-invalid="!!errors.length"
                                />
                                <FieldError v-if="errors.length" :errors="errors" />
                            </Field>
                        </VeeField>
                    </div>
                </div>

                <div class="grid grid-cols-12 space-x-4">
                    <div class="col-span-6">
                        <VeeField v-slot="{ field, errors }" name="dbUser">
                            <Field :data-invalid="!!errors.length">
                                <FieldLabel for="dbUser">
                                    {{ $t("projects.create.fields.db_user.label") }}
                                </FieldLabel>
                                <InputGroup>
                                    <InputGroupInput
                                        id="dbUser"
                                        v-bind="field"
                                        placeholder="postgres"
                                        autocomplete="off"
                                        :aria-invalid="!!errors.length"
                                    />
                                    <InputGroupAddon align="inline-start">
                                        <User class="size-4" stroke-width="2" />
                                    </InputGroupAddon>
                                </InputGroup>
                                <FieldError v-if="errors.length" :errors="errors" />
                            </Field>
                        </VeeField>
                    </div>
                    <div class="col-span-6">
                        <VeeField v-slot="{ field, errors }" name="dbPassword">
                            <Field :data-invalid="!!errors.length">
                                <FieldLabel for="dbPassword">
                                    {{ $t("projects.create.fields.db_password.label") }}
                                </FieldLabel>
                                <InputGroup>
                                    <InputGroupInput
                                        id="dbPassword"
                                        v-bind="field"
                                        type="password"
                                        placeholder="******"
                                        autocomplete="off"
                                        :aria-invalid="!!errors.length"
                                    />
                                    <InputGroupAddon align="inline-start">
                                        <Lock class="size-4" stroke-width="2" />
                                    </InputGroupAddon>
                                </InputGroup>
                                <FieldError v-if="errors.length" :errors="errors" />
                            </Field>
                        </VeeField>
                    </div>
                </div>

                <VeeField v-slot="{ field, errors }" name="dbName">
                    <Field :data-invalid="!!errors.length">
                        <FieldLabel for="dbName">
                            {{ $t("projects.create.fields.db_name.label") }}
                        </FieldLabel>
                        <Input
                            id="dbName"
                            v-bind="field"
                            :placeholder="$t('projects.create.fields.db_name.placeholder')"
                            autocomplete="off"
                            :aria-invalid="!!errors.length"
                        />
                        <FieldError v-if="errors.length" :errors="errors" />
                    </Field>
                </VeeField>

                <VeeField v-slot="{ field, errors }" name="dbParams">
                    <Field :data-invalid="!!errors.length">
                        <FieldLabel for="dbParams">
                            {{ $t("projects.create.fields.db_params.label") }}
                        </FieldLabel>
                        <Input
                            id="dbParams"
                            v-bind="field"
                            autocomplete="off"
                            :aria-invalid="!!errors.length"
                        />
                        <FieldDescription>
                            {{ $t("projects.create.fields.db_params.description") }}
                        </FieldDescription>
                        <FieldError v-if="errors.length" :errors="errors" />
                    </Field>
                </VeeField>
            </div>
        </section>

        <Separator class="my-6" />

        <div class="space-y-4">
            <div class="text-muted-foreground text-sm">
                {{ $t("projects.create.sections.missing_args.text") }}
            </div>

            <div class="flex justify-end space-x-4">
                <Button type="submit">
                    {{ $t("projects.create.header.title") }}
                </Button>

                <Button
                    :disabled="loading"
                    type="button"
                    variant="destructive"
                    @click="$router.back()"
                >
                    <Spinner v-if="loading" />
                    {{ $t("common.actions.cancel") }}
                </Button>
            </div>
        </div>
    </form>
</template>
