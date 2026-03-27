function SchemaDetailView({
    schema,
    projectId,
    onBack,
    onRevert,
    onDeleteRelease,
}: {
    schema: TableSchema;
    projectId: string;
    onBack: () => void;
    onRevert: (releaseIndex: number) => void;
    onDeleteRelease: (releaseIndex: number) => void;
}) {
    const [showRawJson, setShowRawJson] = useState(false);
    const tableName = getTableName(schema.import_name);
    const properties = Object.entries(schema.active_schema.properties);
    const requiredFields = schema.active_schema.required;
    const schemaVersion = schema.active_schema.$schema || schema.active_schema.schema;

    const copyToClipboard = (text: string) => {
        navigator.clipboard.writeText(text);
    };

    return (
        <div className="flex flex-col gap-6">
            {/* Header */}
            <div className="flex items-center gap-4">
                <Button variant="ghost" size="icon" onClick={onBack} className="shrink-0">
                    <ArrowLeft className="size-4" />
                    <span className="sr-only">Back to tables</span>
                </Button>
                <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-3">
                        <div className="flex size-10 shrink-0 items-center justify-center rounded-lg bg-primary/10">
                            <Table2 className="size-5 text-primary" />
                        </div>
                        <div>
                            <h2 className="text-lg font-medium text-foreground">{tableName}</h2>
                            <p className="text-xs text-muted-foreground font-mono">{schema.id}</p>
                        </div>
                    </div>
                </div>
                <Button variant="outline" asChild>
                    <Link href={`/projects/${projectId}/tables/${schema.id}`}>
                        <Pencil className="size-4" />
                        Edit Schema
                    </Link>
                </Button>
            </div>

            {/* Active Schema Card */}
            <Card className="overflow-hidden">
                <div className="flex items-center justify-between border-b px-5 py-4">
                    <div className="flex items-center gap-3">
                        <Badge variant="default" className="bg-emerald-600 hover:bg-emerald-600">
                            Active
                        </Badge>
                        <span className="text-sm text-muted-foreground">
                            {properties.length} columns
                        </span>
                    </div>
                    <div className="flex items-center gap-2 text-xs text-muted-foreground">
                        <Clock className="size-3.5" />
                        {new Date(schema.created_at).toLocaleDateString("en-US", {
                            month: "short",
                            day: "numeric",
                            year: "numeric",
                            hour: "2-digit",
                            minute: "2-digit",
                            timeZone: "UTC",
                        })}
                    </div>
                </div>

                {/* Schema Info */}
                <div className="px-5 py-4">
                    <div className="mb-4 flex items-center gap-2 text-xs text-muted-foreground">
                        <span className="font-medium">Schema:</span>
                        <code className="rounded bg-muted px-1.5 py-0.5 font-mono">
                            {schemaVersion}
                        </code>
                    </div>

                    {/* Columns Table */}
                    <div className="rounded-lg border">
                        {/* Table Header */}
                        <div className="grid grid-cols-12 gap-3 border-b bg-muted/50 px-4 py-2.5 text-xs font-medium text-muted-foreground">
                            <div className="col-span-4">Column</div>
                            <div className="col-span-3">Type</div>
                            <div className="col-span-5">Constraints</div>
                        </div>

                        {/* Table Body */}
                        <div className="divide-y">
                            {properties.map(([name, prop]) => {
                                const TypeIcon = getTypeIcon(prop.type);
                                const isRequired = requiredFields.includes(name);
                                const colorClasses = getTypeColor(prop.type);

                                return (
                                    <div
                                        key={name}
                                        className="grid grid-cols-12 items-center gap-3 px-4 py-3"
                                    >
                                        {/* Column Name */}
                                        <div className="col-span-4 flex items-center gap-2">
                                            <span className="font-mono text-sm text-foreground">
                                                {name}
                                            </span>
                                        </div>

                                        {/* Type */}
                                        <div className="col-span-3 flex items-center gap-2">
                                            <div
                                                className={`flex size-6 items-center justify-center rounded ${colorClasses}`}
                                            >
                                                <TypeIcon className="size-3.5" />
                                            </div>
                                            <span className="text-sm text-muted-foreground">
                                                {prop.type}
                                            </span>
                                        </div>

                                        {/* Constraints */}
                                        <div className="col-span-5 flex flex-wrap items-center gap-1.5">
                                            {prop.primary_key && (
                                                <Badge
                                                    variant="outline"
                                                    className="gap-1 border-amber-500/50 bg-amber-500/10 text-amber-700 text-[10px]"
                                                >
                                                    <Key className="size-2.5" />
                                                    Primary
                                                </Badge>
                                            )}
                                            {prop.unique && !prop.primary_key && (
                                                <Badge
                                                    variant="outline"
                                                    className="gap-1 border-cyan-500/50 bg-cyan-500/10 text-cyan-700 text-[10px]"
                                                >
                                                    <Fingerprint className="size-2.5" />
                                                    Unique
                                                </Badge>
                                            )}
                                            {isRequired && !prop.primary_key && (
                                                <Badge
                                                    variant="outline"
                                                    className="gap-1 border-rose-500/50 bg-rose-500/10 text-rose-700 text-[10px]"
                                                >
                                                    <Asterisk className="size-2.5" />
                                                    Required
                                                </Badge>
                                            )}
                                            {prop.optional && (
                                                <Badge
                                                    variant="outline"
                                                    className="text-[10px] text-muted-foreground"
                                                >
                                                    Optional
                                                </Badge>
                                            )}
                                            {!prop.primary_key &&
                                                !prop.unique &&
                                                !isRequired &&
                                                !prop.optional && (
                                                    <span className="text-xs text-muted-foreground">
                                                        —
                                                    </span>
                                                )}
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    </div>
                </div>

                {/* Raw JSON Collapsible */}
                <Collapsible open={showRawJson} onOpenChange={setShowRawJson}>
                    <div className="border-t">
                        <CollapsibleTrigger asChild>
                            <button className="flex w-full items-center justify-between px-5 py-3 text-sm text-muted-foreground hover:bg-muted/50 transition-colors">
                                <span className="flex items-center gap-2">
                                    <Braces className="size-4" />
                                    Raw JSON Schema
                                </span>
                                {showRawJson ? (
                                    <ChevronDown className="size-4" />
                                ) : (
                                    <ChevronRight className="size-4" />
                                )}
                            </button>
                        </CollapsibleTrigger>
                        <CollapsibleContent>
                            <div className="relative border-t bg-muted/30 p-4">
                                <pre className="max-h-[300px] overflow-auto rounded-lg bg-muted p-4 text-xs">
                                    <code className="text-foreground">
                                        {JSON.stringify(schema.active_schema, null, 2)}
                                    </code>
                                </pre>
                                <Button
                                    variant="outline"
                                    size="sm"
                                    className="absolute top-6 right-6"
                                    onClick={() =>
                                        copyToClipboard(
                                            JSON.stringify(schema.active_schema, null, 2),
                                        )
                                    }
                                >
                                    <Copy className="size-3" />
                                    Copy
                                </Button>
                            </div>
                        </CollapsibleContent>
                    </div>
                </Collapsible>
            </Card>

            {/* Schema Releases History */}
            <Card>
                <div className="flex items-center justify-between border-b px-5 py-4">
                    <div className="flex items-center gap-2">
                        <History className="size-4 text-muted-foreground" />
                        <h3 className="text-sm font-medium text-foreground">Version History</h3>
                    </div>
                    <Badge variant="secondary" className="text-xs font-normal">
                        {schema.schemas_releases.length} release
                        {schema.schemas_releases.length !== 1 ? "s" : ""}
                    </Badge>
                </div>

                {schema.schemas_releases.length > 0 ? (
                    <div className="divide-y">
                        {schema.schemas_releases.map((release, index) => {
                            const releaseProperties = Object.entries(release.schema.properties);
                            return (
                                <div
                                    key={index}
                                    className="flex items-center justify-between px-5 py-4"
                                >
                                    <div className="flex items-center gap-4">
                                        <div className="flex size-8 shrink-0 items-center justify-center rounded-full bg-muted text-xs font-medium text-muted-foreground">
                                            v{schema.schemas_releases.length - index}
                                        </div>
                                        <div>
                                            <p className="text-sm text-foreground">
                                                {releaseProperties.length} columns
                                            </p>
                                            <p className="text-xs text-muted-foreground">
                                                {new Date(release.created_at).toLocaleDateString(
                                                    "en-US",
                                                    {
                                                        month: "short",
                                                        day: "numeric",
                                                        year: "numeric",
                                                        hour: "2-digit",
                                                        minute: "2-digit",
                                                        timeZone: "UTC",
                                                    },
                                                )}
                                            </p>
                                        </div>
                                    </div>
                                    <div className="flex items-center gap-2">
                                        <Button
                                            variant="outline"
                                            size="sm"
                                            onClick={() => onRevert(index)}
                                        >
                                            <RotateCcw className="size-3.5" />
                                            Revert
                                        </Button>
                                        <DropdownMenu>
                                            <DropdownMenuTrigger asChild>
                                                <Button
                                                    variant="ghost"
                                                    size="icon"
                                                    className="size-8"
                                                >
                                                    <EllipsisVertical className="size-4" />
                                                </Button>
                                            </DropdownMenuTrigger>
                                            <DropdownMenuContent align="end">
                                                <DropdownMenuItem
                                                    onClick={() =>
                                                        copyToClipboard(
                                                            JSON.stringify(release.schema, null, 2),
                                                        )
                                                    }
                                                >
                                                    <Copy className="size-4" />
                                                    Copy JSON
                                                </DropdownMenuItem>
                                                <DropdownMenuSeparator />
                                                <DropdownMenuItem
                                                    variant="destructive"
                                                    onClick={() => onDeleteRelease(index)}
                                                >
                                                    <Trash2 className="size-4" />
                                                    Delete Release
                                                </DropdownMenuItem>
                                            </DropdownMenuContent>
                                        </DropdownMenu>
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                ) : (
                    <div className="flex flex-col items-center justify-center py-8 text-center">
                        <div className="flex size-10 items-center justify-center rounded-full bg-muted">
                            <History className="size-5 text-muted-foreground" />
                        </div>
                        <p className="mt-3 text-sm text-muted-foreground">No previous versions</p>
                        <p className="text-xs text-muted-foreground">
                            Version history will appear here after updates.
                        </p>
                    </div>
                )}
            </Card>
        </div>
    );
}
