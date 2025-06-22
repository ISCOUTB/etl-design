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

    return { formula, tokens, ast, error: null };
}

const formula = "=SUM(A1:A10) + IF(B1 > 10, C1, D1) - E1 / F1";
const result = parseFormula(formula);
console.log("Formula:", JSON.stringify(result, null, 4));
