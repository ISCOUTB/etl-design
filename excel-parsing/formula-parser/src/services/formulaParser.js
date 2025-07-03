import { tokenize } from "excel-formula-tokenizer";
import { buildTree } from "excel-formula-ast";

function parseFormula(formula) {
    let tokens = null, ast = null;

    try {
        tokens = tokenize(formula);
    } catch (e) {
        return {
            formula,
            tokens,
            ast,
            error: `Could not tokenise: ${e}`,
        };
    }

    try {
        ast = buildTree(tokens);
    } catch (e) {
        return {
            formula,
            tokens,
            ast,
            error: `Could not build tree: ${e}`,
        };
    }

    return { formula, tokens, ast, error: "" };
}
