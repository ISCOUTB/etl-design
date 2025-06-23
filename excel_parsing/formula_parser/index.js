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

const formula = "=SUM(A1:$E$1) + IF(AND(A1 > 5, B1 < 20), TRUE, FALSE) - E1 / 2.1";
const result = parseFormula(formula);
console.log("Formula:", JSON.stringify(result, null, 4));

/*
Output:
Formula: {
    "formula": "=SUM(A1:$E$1) + IF(AND(A1 > 5, B1 < 20), TRUE, FALSE) - E1 / 2.1",
    "tokens": [
        {
            "value": "SUM",
            "type": "function",
            "subtype": "start"
        },
        {
            "value": "A1:$E$1",
            "type": "operand",
            "subtype": "range"
        },
        {
            "value": "",
            "type": "function",
            "subtype": "stop"
        },
        {
            "value": "+",
            "type": "operator-infix",
            "subtype": "math"
        },
        {
            "value": "IF",
            "type": "function",
            "subtype": "start"
        },
        {
            "value": "AND",
            "type": "function",
            "subtype": "start"
        },
        {
            "value": "A1",
            "type": "operand",
            "subtype": "range"
        },
        {
            "value": ">",
            "type": "operator-infix",
            "subtype": "logical"
        },
        {
            "value": "5",
            "type": "operand",
            "subtype": "number"
        },
        {
            "value": ",",
            "type": "argument",
            "subtype": ""
        },
        {
            "value": "B1",
            "type": "operand",
            "subtype": "range"
        },
        {
            "value": "<",
            "type": "operator-infix",
            "subtype": "logical"
        },
        {
            "value": "20",
            "type": "operand",
            "subtype": "number"
        },
        {
            "value": "",
            "type": "function",
            "subtype": "stop"
        },
        {
            "value": ",",
            "type": "argument",
            "subtype": ""
        },
        {
            "value": "TRUE",
            "type": "operand",
            "subtype": "logical"
        },
        {
            "value": ",",
            "type": "argument",
            "subtype": ""
        },
        {
            "value": "FALSE",
            "type": "operand",
            "subtype": "logical"
        },
        {
            "value": "",
            "type": "function",
            "subtype": "stop"
        },
        {
            "value": "-",
            "type": "operator-infix",
            "subtype": "math"
        },
        {
            "value": "E1",
            "type": "operand",
            "subtype": "range"
        },
        {
            "value": "/",
            "type": "operator-infix",
            "subtype": "math"
        },
        {
            "value": "2.1",
            "type": "operand",
            "subtype": "number"
        }
    ],
    "ast": {
        "type": "binary-expression",
        "operator": "-",
        "left": {
            "type": "binary-expression",
            "operator": "+",
            "left": {
                "type": "function",
                "name": "SUM",
                "arguments": [
                    {
                        "type": "cell-range",
                        "left": {
                            "type": "cell",
                            "refType": "relative",
                            "key": "A1"
                        },
                        "right": {
                            "type": "cell",
                            "refType": "absolute",
                            "key": "$E$1"
                        }
                    }
                ]
            },
            "right": {
                "type": "function",
                "name": "IF",
                "arguments": [
                    {
                        "type": "function",
                        "name": "AND",
                        "arguments": [
                            {
                                "type": "binary-expression",
                                "operator": ">",
                                "left": {
                                    "type": "cell",
                                    "refType": "relative",
                                    "key": "A1"
                                },
                                "right": {
                                    "type": "number",
                                    "value": 5
                                }
                            },
                            {
                                "type": "binary-expression",
                                "operator": "<",
                                "left": {
                                    "type": "cell",
                                    "refType": "relative",
                                    "key": "B1"
                                },
                                "right": {
                                    "type": "number",
                                    "value": 20
                                }
                            }
                        ]
                    },
                    {
                        "type": "logical",
                        "value": true
                    },
                    {
                        "type": "logical",
                        "value": false
                    }
                ]
            }
        },
        "right": {
            "type": "binary-expression",
            "operator": "/",
            "left": {
                "type": "cell",
                "refType": "relative",
                "key": "E1"
            },
            "right": {
                "type": "number",
                "value": 2.1
            }
        }
    },
    "error": null
}
*/
