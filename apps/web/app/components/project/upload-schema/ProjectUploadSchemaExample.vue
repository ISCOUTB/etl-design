<script setup lang="ts">
    const { data } = useFetch<string>("/examples/schema.example.json", {
        method: "GET",
        key: NuxtKeys.Projects.Schemas.ExampleFormat,
    });
</script>

<template>
    <section>
        <h3 class="mb-1 text-sm font-medium text-foreground">
            {{ $t("projects.id.sections.upload_schema.expected_json.title") }}
        </h3>
        <p class="mb-5 text-sm text-muted-foreground">
            {{ $t("projects.id.sections.upload_schema.expected_json.description") }}
        </p>

        <CodeBlock
            :content="data"
            :file="$t('projects.id.sections.upload_schema.expected_json.example_filename')"
        />
    </section>
</template>
