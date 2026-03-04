<script setup lang="ts">
    import type { z } from "zod";
    import {
        AlignLeft,
        CirclePlus,
        Cloud,
        Database,
        Info,
        Lock,
        Plug,
        RotateCcw,
        Server,
        User,
    } from "lucide-vue-next";
    import { FetchError } from "ofetch";
    import { toast } from "vue-sonner";

    interface Props {
        project: MaybeRefOrGetter<z.infer<typeof ResponseProjectSchema> | undefined>;
    }

    defineOptions({ inheritAttrs: false });

    const props = defineProps<Props>();
    const project = computed(() => toValue(props.project));

    const errorToast = useErrorToast();

    const { CreateProjectSchema } = useCreateProjectSchema();
    const { handleSubmit, resetField } = useForm({
        validationSchema: toTypedSchema(CreateProjectSchema.value),
        initialValues: {
            name: project.value?.name || "",
            description: project.value?.description || "",
            provider: project.value?.provider || "",
            dbHost: project.value?.db_host || "",
            dbPort: project.value?.db_port?.toString() || "",
            dbUser: project.value?.db_user || "",
            dbPassword: project.value?.db_password || "",
            dbName: project.value?.db_name || "",
            dbParams: project.value?.db_params || "",
        },
    });

    const { $localeRoute } = useNuxtApp();
    const router = useRouter();
    const api = useApi();
    const [loading] = useToggle(false);
    const onSubmit = handleSubmit((values) => {
        if (!project.value) {
            return;
        }

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
        api(`/projects/${project.value.id}`, {
            method: "PATCH",
            body,
        })
            .then(async (response) => {
                const parsedResponse = ResponseProjectSchema.safeParse(response);
                if (!parsedResponse.success) {
                    throw new Error(ResponseCodesRecord.Server.UnknownError);
                }

                toast.success($t("projects.edit.events.project_updated.title"));

                await refreshNuxtData(NuxtKeys.Projects.Id);

                router.push(
                    $localeRoute({ name: "projects-id", params: { id: parsedResponse.data.id } }),
                );
            })
            .catch((error) => {
                if (error instanceof FetchError) {
                    const parsedError = ApiErrorSchema.safeParse(error);
                    if (!parsedError.success) {
                        errorToast.handle(ResponseCodesRecord.Server.UnknownError);

                        return;
                    }

                    errorToast.handle(parsedError.data.error);
                }
            })
            .finally(() => (loading.value = false));
    });
</script>

<template>
    <Suspense>
        <form v-bind="$attrs" @submit="onSubmit">
            <div class="mb-8 space-y-1.5">
                <h1 class="text-2xl font-semibold tracking-tight text-foreground">
                    {{ $t("projects.edit.header.title") }}
                </h1>
                <p class="text-sm text-muted-foreground">
                    {{ $t("projects.edit.header.description") }}
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
                    <VeeField v-slot="{ field, errors, meta }" name="name">
                        <Field :data-invalid="!!errors.length">
                            <FieldLabel for="name">
                                {{ $t("projects.create.fields.name.label") }}
                                <span class="text-destructive">*</span>
                            </FieldLabel>

                            <InputGroup>
                                <InputGroupInput
                                    id="name"
                                    v-bind="field"
                                    :default-value="project?.name"
                                    :placeholder="$t('projects.create.fields.name.placeholder')"
                                    autocomplete="off"
                                    :aria-invalid="!!errors.length"
                                />

                                <InputGroupAddon align="inline-start">
                                    <AlignLeft class="size-4" stroke-width="2" />
                                </InputGroupAddon>

                                <InputGroupAddon v-if="meta.dirty" align="inline-end">
                                    <InputGroupButton
                                        variant="ghost"
                                        size="icon-xs"
                                        type="button"
                                        @click="resetField('name')"
                                    >
                                        <RotateCcw class="size-4" />
                                    </InputGroupButton>
                                </InputGroupAddon>
                            </InputGroup>
                            <FieldError v-if="errors.length" :errors="errors" />
                        </Field>
                    </VeeField>

                    <VeeField v-slot="{ field, errors, meta }" name="description">
                        <Field :data-invalid="!!errors.length">
                            <FieldLabel for="description">
                                {{ $t("projects.create.fields.description.label") }}
                            </FieldLabel>

                            <InputGroup>
                                <InputGroupTextarea
                                    id="description"
                                    v-bind="field"
                                    autocomplete="off"
                                    :default-value="project?.description?.toString()"
                                    :placeholder="
                                        $t('projects.create.fields.description.placeholder')
                                    "
                                    :aria-invalid="!!errors.length"
                                />

                                <InputGroupAddon v-if="meta.dirty" align="block-end">
                                    <InputGroupButton
                                        class="ml-auto"
                                        variant="ghost"
                                        size="icon-xs"
                                        type="button"
                                        @click="resetField('description')"
                                    >
                                        <RotateCcw class="size-4" />
                                    </InputGroupButton>
                                </InputGroupAddon>
                            </InputGroup>

                            <FieldError v-if="errors.length" :errors="errors" />
                        </Field>
                    </VeeField>
                </div>
            </section>

            <Separator class="my-4" />

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
                    <VeeField v-slot="{ field, errors, meta }" name="provider">
                        <Field :data-invalid="!!errors.length">
                            <FieldLabel for="provider">
                                {{ $t("projects.create.fields.provider.label") }}
                            </FieldLabel>

                            <InputGroup>
                                <InputGroupInput
                                    id="provider"
                                    v-bind="field"
                                    autocomplete="off"
                                    :default-value="project?.provider?.toString()"
                                    :placeholder="$t('projects.create.fields.provider.placeholder')"
                                    :aria-invalid="!!errors.length"
                                />

                                <InputGroupAddon align="inline-start">
                                    <Cloud class="size-4" stroke-width="2" />
                                </InputGroupAddon>

                                <InputGroupAddon v-if="meta.dirty" align="inline-end">
                                    <InputGroupButton
                                        variant="ghost"
                                        size="icon-xs"
                                        type="button"
                                        @click="resetField('provider')"
                                    >
                                        <RotateCcw class="size-4" />
                                    </InputGroupButton>
                                </InputGroupAddon>
                            </InputGroup>
                            <FieldError v-if="errors.length" :errors="errors" />
                        </Field>
                    </VeeField>

                    <div class="grid grid-cols-12 space-x-4">
                        <div class="col-span-6">
                            <VeeField v-slot="{ field, errors, meta }" name="dbHost">
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
                                            :default-value="project?.db_host?.toString()"
                                            :aria-invalid="!!errors.length"
                                        />

                                        <InputGroupAddon align="inline-start">
                                            <Server class="size-4" stroke-width="2" />
                                        </InputGroupAddon>

                                        <InputGroupAddon v-if="meta.dirty" align="inline-end">
                                            <InputGroupButton
                                                variant="ghost"
                                                size="icon-xs"
                                                type="button"
                                                @click="resetField('dbHost')"
                                            >
                                                <RotateCcw class="size-4" />
                                            </InputGroupButton>
                                        </InputGroupAddon>
                                    </InputGroup>
                                    <FieldError v-if="errors.length" :errors="errors" />
                                </Field>
                            </VeeField>
                        </div>
                        <div class="col-span-6">
                            <VeeField v-slot="{ field, errors, meta }" name="dbPort">
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
                                            :default-value="project?.db_port?.toString()"
                                            :aria-invalid="!!errors.length"
                                        />

                                        <InputGroupAddon align="inline-start">
                                            <Plug class="size-4" stroke-width="2" />
                                        </InputGroupAddon>

                                        <InputGroupAddon v-if="meta.dirty" align="inline-end">
                                            <InputGroupButton
                                                variant="ghost"
                                                size="icon-xs"
                                                type="button"
                                                @click="resetField('dbPort')"
                                            >
                                                <RotateCcw class="size-4" />
                                            </InputGroupButton>
                                        </InputGroupAddon>
                                    </InputGroup>
                                    <FieldError v-if="errors.length" :errors="errors" />
                                </Field>
                            </VeeField>
                        </div>
                    </div>

                    <div class="grid grid-cols-12 space-x-4">
                        <div class="col-span-6">
                            <VeeField v-slot="{ field, errors, meta }" name="dbUser">
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
                                            :default-value="project?.db_user?.toString()"
                                            :aria-invalid="!!errors.length"
                                        />

                                        <InputGroupAddon align="inline-start">
                                            <User class="size-4" stroke-width="2" />
                                        </InputGroupAddon>

                                        <InputGroupAddon v-if="meta.dirty" align="inline-end">
                                            <InputGroupButton
                                                variant="ghost"
                                                size="icon-xs"
                                                type="button"
                                                @click="resetField('dbUser')"
                                            >
                                                <RotateCcw class="size-4" />
                                            </InputGroupButton>
                                        </InputGroupAddon>
                                    </InputGroup>
                                    <FieldError v-if="errors.length" :errors="errors" />
                                </Field>
                            </VeeField>
                        </div>
                        <div class="col-span-6">
                            <VeeField v-slot="{ field, errors, meta }" name="dbPassword">
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
                                            :default-value="project?.db_password?.toString()"
                                            :aria-invalid="!!errors.length"
                                        />

                                        <InputGroupAddon align="inline-start">
                                            <Lock class="size-4" stroke-width="2" />
                                        </InputGroupAddon>

                                        <InputGroupAddon v-if="meta.dirty" align="inline-end">
                                            <InputGroupButton
                                                variant="ghost"
                                                size="icon-xs"
                                                type="button"
                                                @click="resetField('dbPassword')"
                                            >
                                                <RotateCcw class="size-4" />
                                            </InputGroupButton>
                                        </InputGroupAddon>
                                    </InputGroup>
                                    <FieldError v-if="errors.length" :errors="errors" />
                                </Field>
                            </VeeField>
                        </div>
                    </div>

                    <VeeField v-slot="{ field, errors, meta }" name="dbName">
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
                                    :default-value="project?.db_name?.toString()"
                                    :aria-invalid="!!errors.length"
                                />

                                <InputGroupAddon align="inline-start">
                                    <AlignLeft class="size-4" stroke-width="2" />
                                </InputGroupAddon>

                                <InputGroupAddon v-if="meta.dirty" align="inline-end">
                                    <InputGroupButton
                                        variant="ghost"
                                        size="icon-xs"
                                        type="button"
                                        @click="resetField('dbName')"
                                    >
                                        <RotateCcw class="size-4" />
                                    </InputGroupButton>
                                </InputGroupAddon>
                            </InputGroup>
                            <FieldError v-if="errors.length" :errors="errors" />
                        </Field>
                    </VeeField>

                    <VeeField v-slot="{ field, errors, meta }" name="dbParams">
                        <Field :data-invalid="!!errors.length">
                            <FieldLabel for="dbParams">
                                {{ $t("projects.create.fields.db_params.label") }}
                            </FieldLabel>
                            <InputGroup>
                                <InputGroupInput
                                    id="dbParams"
                                    v-bind="field"
                                    autocomplete="off"
                                    :default-value="project?.db_params?.toString()"
                                    :placeholder="
                                        $t('projects.create.fields.db_params.placeholder')
                                    "
                                    :aria-invalid="!!errors.length"
                                />

                                <InputGroupAddon>
                                    <CirclePlus class="size-4" stroke-width="2" />
                                </InputGroupAddon>

                                <InputGroupAddon v-if="meta.dirty" align="inline-end">
                                    <InputGroupButton
                                        variant="ghost"
                                        size="icon-xs"
                                        type="button"
                                        @click="resetField('dbParams')"
                                    >
                                        <RotateCcw class="size-4" />
                                    </InputGroupButton>
                                </InputGroupAddon>
                            </InputGroup>
                            <FieldError v-if="errors.length" :errors="errors" />
                        </Field>
                    </VeeField>
                </div>
            </section>

            <Separator class="my-6" />

            <div class="space-y-4">
                <div class="flex justify-end space-x-4">
                    <Button type="submit" :disabled="loading">
                        <Spinner v-if="loading" />
                        <span>
                            {{ $t("common.actions.save_changes") }}
                        </span>
                    </Button>

                    <Button type="button" variant="destructive" @click="$router.back()">
                        {{ $t("common.actions.cancel") }}
                    </Button>
                </div>
            </div>
        </form>
    </Suspense>
</template>
