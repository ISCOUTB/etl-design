<script setup lang="ts">
    import { AlignLeft, Cloud, Database, Info } from "lucide-vue-next";
    import { z } from "zod";

    definePageMeta({
        title: "Create Project",
        layout: "sidebar",
        i18n: {
            paths: {
                en: "/projects/create",
            },
        },
    });

    const CreateProjectSchema = computed(() =>
        z.object({
            name: z.string().min(1),
            description: z.string().optional(),
            provider: z.string().optional(),
            dbHost: z.string().optional(),
            dbPort: z.string().optional(),
            dbUser: z.string().optional(),
            dbPassword: z.string().optional(),
            dbName: z.string().optional(),
            dbParams: z.string().optional(),
        }),
    );

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

    const onSubmit = handleSubmit((values) => {
        console.warn(values);
    });
</script>

<template>
    <TooltipProvider>
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
                                placeholder="..."
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
                    <VeeField v-slot="{ field, errors }" name="dbHost">
                        <Field :data-invalid="!!errors.length">
                            <FieldLabel for="dbHost">
                                {{ $t("projects.create.fields.db_host.label") }}
                            </FieldLabel>

                            <InputGroup>
                                <InputGroupInput
                                    id="dbHost"
                                    v-bind="field"
                                    autocomplete="off"
                                    :aria-invalid="!!errors.length"
                                />

                                <InputGroupAddon align="inline-start">
                                    <Cloud class="size-4" stroke-width="2" />
                                </InputGroupAddon>
                            </InputGroup>
                            <FieldDescription>
                                {{ $t("projects.create.fields.db_host.description") }}
                            </FieldDescription>
                            <FieldError v-if="errors.length" :errors="errors" />
                        </Field>
                    </VeeField>
                </div>
            </section>
        </form>
    </TooltipProvider>
</template>
