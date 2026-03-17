"use client";

import { useState } from "react";
import {
    ChevronDown,
    ChevronRight,
    Copy,
    EllipsisVertical,
    Hash,
    LayoutList,
    Search,
    Table2,
    ToggleLeft,
    Type,
    Calendar,
    Braces,
    Key,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuSeparator,
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Input } from "@/components/ui/input";

// Types based on the provided schema shape
interface SchemaProperty {
    type: string;
    extra?: Record<string, unknown>;
}

interface ActiveSchema {
    schema: string;
    type: string;
    required: string[];
    properties: Record<string, SchemaProperty>;
}

interface TableSchema {
    id: string;
    import_name: string;
    created_at: string;
    active_schema: ActiveSchema;
    schemas_releases: unknown[];
}

interface Project {
    id: string;
    name: string;
}

// Mock data based on the provided shape
const mockSchemas: TableSchema[] = [
    {
        id: "69b828dbe482a98940378e5d",
        import_name: "000019cc-521b-7a70-aee7-ef426201e70c__acme__users__sample1",
        created_at: "2026-03-16T15:59:23.686452+00:00",
        active_schema: {
            schema: "http://json-schema.org/draft-04/schema#",
            type: "object",
            required: ["name", "age", "is_adult"],
            properties: {
                age: { type: "integer", extra: {} },
                is_adult: { type: "boolean", extra: {} },
                name: { type: "string", extra: {} },
            },
        },
        schemas_releases: [],
    },
    {
        id: "69b846d1e482a98940378e5e",
        import_name: "000019cc-521b-7a70-aee7-ef426201e70c__Sheet1",
        created_at: "2026-03-16T18:07:12.616051+00:00",
        active_schema: {
            schema: "https://json-schema.org/draft-07/schema",
            type: "object",
            required: ["name", "age", "is_adult"],
            properties: {
                age: { type: "string", extra: {} },
                is_adult: { type: "string", extra: {} },
                name: { type: "string", extra: {} },
            },
        },
        schemas_releases: [],
    },
];

// Helper to get a readable table name from import_name
function getTableName(importName: string): string {
    const parts = importName.split("__");
    return parts.length > 1 ? parts.slice(1).join(" / ") : importName;
}

// Helper to get type icon
function getTypeIcon(type: string) {
    switch (type) {
        case "string":
            return Type;
        case "integer":
        case "number":
            return Hash;
        case "boolean":
            return ToggleLeft;
        case "date":
        case "datetime":
            return Calendar;
        case "object":
        case "json":
            return Braces;
        case "uuid":
            return Key;
        default:
            return Type;
    }
}

// Helper to get type color
function getTypeColor(type: string): string {
    switch (type) {
        case "string":
            return "text-emerald-600 bg-emerald-500/10";
        case "integer":
        case "number":
            return "text-blue-600 bg-blue-500/10";
        case "boolean":
            return "text-amber-600 bg-amber-500/10";
        case "date":
        case "datetime":
            return "text-purple-600 bg-purple-500/10";
        case "object":
        case "json":
            return "text-rose-600 bg-rose-500/10";
        case "uuid":
            return "text-cyan-600 bg-cyan-500/10";
        default:
            return "text-muted-foreground bg-muted";
    }
}

function TableCard({ schema }: { schema: TableSchema }) {
    const [isOpen, setIsOpen] = useState(false);
    const tableName = getTableName(schema.import_name);
    const properties = Object.entries(schema.active_schema.properties);
    const requiredFields = schema.active_schema.required;

    const copyId = () => {
        navigator.clipboard.writeText(schema.id);
    };

    return (
        <Card className="overflow-hidden">
            <Collapsible open={isOpen} onOpenChange={setIsOpen}>
                <div className="flex items-center justify-between px-4 py-3">
                    <CollapsibleTrigger asChild>
                        <button className="flex items-center gap-3 text-left hover:opacity-80 transition-opacity">
                            <div className="flex size-8 shrink-0 items-center justify-center rounded-md bg-primary/10">
                                <Table2 className="size-4 text-primary" />
                            </div>
                            <div className="min-w-0">
                                <div className="flex items-center gap-2">
                                    <h3 className="truncate text-sm font-medium text-foreground">
                                        {tableName}
                                    </h3>
                                    <Badge variant="secondary" className="text-[10px] font-normal">
                                        {properties.length} columns
                                    </Badge>
                                </div>
                                <p className="mt-0.5 text-xs text-muted-foreground">
                                    Created{" "}
                                    {new Date(schema.created_at).toLocaleDateString("en-US", {
                                        month: "short",
                                        day: "numeric",
                                        year: "numeric",
                                    })}
                                </p>
                            </div>
                        </button>
                    </CollapsibleTrigger>

                    <div className="flex items-center gap-1">
                        <CollapsibleTrigger asChild>
                            <Button variant="ghost" size="icon" className="size-8">
                                {isOpen ? (
                                    <ChevronDown className="size-4" />
                                ) : (
                                    <ChevronRight className="size-4" />
                                )}
                                <span className="sr-only">Toggle columns</span>
                            </Button>
                        </CollapsibleTrigger>
                        <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                                <Button variant="ghost" size="icon" className="size-8">
                                    <EllipsisVertical className="size-4" />
                                    <span className="sr-only">Table options</span>
                                </Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent align="end">
                                <DropdownMenuItem onClick={copyId}>
                                    <Copy className="size-4" />
                                    Copy ID
                                </DropdownMenuItem>
                                <DropdownMenuItem>
                                    <LayoutList className="size-4" />
                                    View Records
                                </DropdownMenuItem>
                                <DropdownMenuSeparator />
                                <DropdownMenuItem variant="destructive">
                                    Delete Table
                                </DropdownMenuItem>
                            </DropdownMenuContent>
                        </DropdownMenu>
                    </div>
                </div>

                <CollapsibleContent>
                    <div className="border-t bg-muted/30 px-4 py-3">
                        <div className="flex flex-col gap-1">
                            {properties.map(([name, prop]) => {
                                const TypeIcon = getTypeIcon(prop.type);
                                const isRequired = requiredFields.includes(name);
                                const colorClasses = getTypeColor(prop.type);

                                return (
                                    <div
                                        key={name}
                                        className="flex items-center justify-between rounded-md px-2 py-1.5 hover:bg-muted/50 transition-colors"
                                    >
                                        <div className="flex items-center gap-2.5">
                                            <div
                                                className={`flex size-6 items-center justify-center rounded ${colorClasses}`}
                                            >
                                                <TypeIcon className="size-3.5" />
                                            </div>
                                            <span className="font-mono text-sm text-foreground">
                                                {name}
                                            </span>
                                            {isRequired && (
                                                <Badge
                                                    variant="outline"
                                                    className="text-[10px] font-normal text-muted-foreground"
                                                >
                                                    required
                                                </Badge>
                                            )}
                                        </div>
                                        <span className="text-xs text-muted-foreground">
                                            {prop.type}
                                        </span>
                                    </div>
                                );
                            })}
                        </div>
                    </div>
                </CollapsibleContent>
            </Collapsible>
        </Card>
    );
}

export function ProjectTablesTab({ project }: { project: Project }) {
    const [searchQuery, setSearchQuery] = useState("");

    // Replace with real data fetching
    const schemas = mockSchemas;

    const filteredSchemas = schemas.filter((schema) => {
        const tableName = getTableName(schema.import_name).toLowerCase();
        return tableName.includes(searchQuery.toLowerCase());
    });

    return (
        <div className="flex flex-col gap-6">
            {/* Header */}
            <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                <div>
                    <h2 className="text-lg font-medium text-foreground">Tables</h2>
                    <p className="mt-0.5 text-sm text-muted-foreground">
                        {schemas.length} table{schemas.length !== 1 ? "s" : ""} in this project
                    </p>
                </div>
                <div className="relative w-full sm:w-64">
                    <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
                    <Input
                        placeholder="Search tables..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="pl-9"
                    />
                </div>
            </div>

            {/* Tables List */}
            {filteredSchemas.length > 0 ? (
                <div className="flex flex-col gap-3">
                    {filteredSchemas.map((schema) => (
                        <TableCard key={schema.id} schema={schema} />
                    ))}
                </div>
            ) : (
                <Card className="flex flex-col items-center justify-center border-dashed py-12">
                    <div className="flex size-12 items-center justify-center rounded-full bg-muted">
                        <Table2 className="size-6 text-muted-foreground" />
                    </div>
                    <h3 className="mt-4 text-sm font-medium text-foreground">No tables found</h3>
                    <p className="mt-1 text-center text-sm text-muted-foreground">
                        {searchQuery
                            ? "No tables match your search query."
                            : "Import a schema to create your first table."}
                    </p>
                </Card>
            )}
        </div>
    );
}
