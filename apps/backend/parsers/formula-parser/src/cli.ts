/**
 * CLI script to parse Excel formulas and generate ASTs
 *
 * Usage: node dist/cli.js "=SUM(A1:A10)"
 * Output: JSON with tokens, AST, and error status
 *
 * This script is designed to be called from external processes (e.g., Python)
 * to generate formula ASTs that can be used for testing and validation.
 */

import process from "node:process";
import { Effect } from "effect";
import { parseFormula } from "@/services/parse";

interface CLIOutput {
    formula: string;
    tokens: any | null;
    ast: any | null;
    error: string;
    success: boolean;
}

async function main() {
    const formula = process.argv[2];

    if (!formula) {
        console.error("ERROR: Formula argument is required");
        console.error("Usage: node dist/cli.js <formula>");
        process.exit(1);
    }

    try {
        const result = await Effect.runPromise(parseFormula(formula));

        const output: CLIOutput = {
            formula: result.formula,
            tokens: result.tokens,
            ast: result.ast,
            error: result.error,
            success: result.error === "",
        };

        console.log(JSON.stringify(output, null, 2));
        process.exit(result.error === "" ? 0 : 1);
    } catch (error) {
        const output: CLIOutput = {
            formula,
            tokens: null,
            ast: null,
            error: `Unexpected error: ${error instanceof Error ? error.message : String(error)}`,
            success: false,
        };

        console.log(JSON.stringify(output, null, 2));
        process.exit(1);
    }
}

main();
