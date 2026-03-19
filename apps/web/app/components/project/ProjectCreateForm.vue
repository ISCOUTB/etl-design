<script setup lang="ts">
    import {
        AlignLeft,
        CirclePlus,
        Cloud,
        Database,
        Info,
        Lock,
        Plug,
        Server,
        User,
    } from "lucide-vue-next";
    import { toast } from "vue-sonner";

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

    const { $localeRoute } = useNuxtApp();
    const errorToast = useErrorToast();
    const api = useApi();
    const [loading] = useToggle(false);
    const router = useRouter();
    const onSubmit = handleSubmit((values) => {
        const body = {
            name: values.name,
            description: values.description || null,
            provider: values.provider || null,
            db_host: values.dbHost || null,
            db_port: values.dbPort || null,
            db_user: values.dbUser || null,
            db_password: values.dbPassword || null,
            db_name: values.dbName || null,
            db_params: values.dbParams || null,
        };

        loading.value = true;
        api("/projects/", {
            method: "POST",
            body,
        })
            .then((response) => {
                const parsedResponse = ResponseProjectSchema.safeParse(response);
                if (!parsedResponse.success) {
                    throw new Error(ResponseCodesRecord.Server.UnknownError);
                }

                toast.success($t("projects.create.events.project_created.title"), {
                    description: $t("projects.create.events.project_created.description", {
                        projectName: parsedResponse.data.name,
                    }),
                });

                router.push(
                    $localeRoute({ name: "projects-id", params: { id: parsedResponse.data.id } }),
                );
            })
            .catch((error) => errorToast.handleServer(error))
            .finally(() => (loading.value = false));
    });
</script>

<template>
    <form @submit="onSubmit">
        <div class="mb-8">
            <h1 class="text-2xl font-semibold tracking-tight text-foreground">
                {{ $t("projects.create.header.title") }}
            </h1>
            <p class="mt-1.5 text-sm text-muted-foreground">
                {{ $t("projects.create.header.description") }}
            </p>
        </div>

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
                                <InputGroup>
                                    <InputGroupInput
                                        id="dbHost"
                                        v-bind="field"
                                        placeholder="localhost"
                                        autocomplete="off"
                                        :aria-invalid="!!errors.length"
                                    />
                                    <InputGroupAddon align="inline-start">
                                        <Server class="size-4" stroke-width="2" />
                                    </InputGroupAddon>
                                </InputGroup>
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
                                <InputGroup>
                                    <InputGroupInput
                                        id="dbPort"
                                        v-bind="field"
                                        placeholder="5432"
                                        autocomplete="off"
                                        :aria-invalid="!!errors.length"
                                    />
                                    <InputGroupAddon align="inline-start">
                                        <Plug class="size-4" stroke-width="2" />
                                    </InputGroupAddon>
                                </InputGroup>
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
                        <InputGroup>
                            <InputGroupInput
                                id="dbName"
                                v-bind="field"
                                :placeholder="$t('projects.create.fields.db_name.placeholder')"
                                autocomplete="off"
                                :aria-invalid="!!errors.length"
                            />
                            <InputGroupAddon align="inline-start">
                                <AlignLeft class="size-4" stroke-width="2" />
                            </InputGroupAddon>
                        </InputGroup>
                        <FieldError v-if="errors.length" :errors="errors" />
                    </Field>
                </VeeField>

                <VeeField v-slot="{ field, errors }" name="dbParams">
                    <Field :data-invalid="!!errors.length">
                        <FieldLabel for="dbParams">
                            {{ $t("projects.create.fields.db_params.label") }}
                        </FieldLabel>
                        <InputGroup>
                            <InputGroupInput
                                id="dbParams"
                                v-bind="field"
                                autocomplete="off"
                                :placeholder="$t('projects.create.fields.db_params.placeholder')"
                                :aria-invalid="!!errors.length"
                            />
                            <InputGroupAddon>
                                <CirclePlus class="size-4" stroke-width="2" />
                            </InputGroupAddon>
                        </InputGroup>
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
            <div class="text-muted-foreground text-sm space-y-2">
                <p>{{ $t("projects.create.sections.missing_args.text") }}</p>
                <p>{{ $t("projects.create.sections.encryption_notice.text") }}</p>
            </div>

            <div class="flex justify-end space-x-4">
                <Button type="submit" :disabled="loading">
                    <Spinner v-if="loading" />
                    <span>
                        {{ $t("projects.create.header.title") }}
                    </span>
                </Button>

                <Button type="button" variant="destructive" @click="$router.back()">
                    {{ $t("common.actions.cancel") }}
                </Button>
            </div>
        </div>
    </form>
</template>
