# Formula Parser Service

A Node.js gRPC service that parses Excel formulas into token streams and Abstract Syntax Trees (AST). The service is the first computational step in the parsing pipeline and provides structured formula data for the DDL Generator.

## Overview

The Formula Parser service provides:

- **Formula Tokenization**: Breaks Excel formulas into constituent tokens
- **AST Generation**: Builds Abstract Syntax Trees from formula tokens
- **Error Handling**: Comprehensive error reporting for invalid formulas
- **gRPC Interface**: High-performance service communication
- **Multi-format Support**: Handles various Excel formula constructs

## Architecture

```text
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Excel Reader  │───►│  Formula Parser  │───►│  DDL Generator  │
│                 │    │   (Node.js)      │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │ Excel Formula   │
                       │ Libraries:      │
                       │ • Tokenizer     │
                       │ • AST Builder   │
                       └─────────────────┘
```

## Features

- **Excel Formula Tokenization**: Uses `excel-formula-tokenizer` for robust token parsing
- **AST Construction**: Builds hierarchical syntax trees with `excel-formula-ast`
- **Comprehensive Type Support**: Handles all Excel data types (numbers, text, boolean, cell references)
- **Reference Type Detection**: Distinguishes between relative, absolute, and mixed cell references
- **Function Support**: Parses Excel functions with multiple arguments
- **Expression Handling**: Supports binary and unary expressions
- **Protocol Buffer Integration**: Seamless data serialization for gRPC communication

## gRPC Service Definition

The service implements the `FormulaParser` service defined in `formula_parser.proto`:

```proto
service FormulaParser {
    rpc ParseFormula(FormulaParserRequest) returns (FormulaParserResponse) {}
}

message FormulaParserRequest {
    string formula = 1;  // Excel formula to parse
}

message FormulaParserResponse {
    string formula = 1;                  // Original formula
    optional dtypes.Tokens tokens = 2;   // Generated tokens
    optional dtypes.AST ast = 3;         // Abstract Syntax Tree
    string error = 4;                    // Error message if parsing failed
}
```

## Supported Formula Types

### Cell References

- **Relative**: `A1`, `B2`
- **Absolute**: `$A$1`, `$B$2`
- **Mixed**: `$A1`, `A$1`

### Data Types

- **Numbers**: `42`, `3.14`, `-10`
- **Text**: `"Hello World"`, `"Sample Text"`
- **Boolean**: `TRUE`, `FALSE`

### Functions

- **Mathematical**: `SUM(A1:A10)`, `AVERAGE(B1:B5)`
- **Logical**: `IF(A1>0, "Positive", "Negative")`
- **Text**: `CONCATENATE(A1, " ", B1)`

### Expressions

- **Binary**: `A1 + B1`, `A1 * 2`, `A1 > B1`
- **Unary**: `-A1`, `+B1`

### Ranges

- **Cell Ranges**: `A1:B10`, `$A$1:$B$10`

## Installation

### Prerequisites

- Node.js 18+
- pnpm

### Setup

1. Install workspace dependencies from the repository root:

    ```bash
    pnpm install
    ```

2. Configure environment:

    ```bash
    cp ../.env.example .env
    # Edit .env with your configuration
    ```

3. Build the service:

    ```bash
    moon run formula-parser:build
    ```

4. Start the service:

    ```bash
    moon run formula-parser:run
    ```

For iterative development, rebuild after code changes and rerun the service:

```bash
moon run formula-parser:build
moon run formula-parser:run
```

## Configuration

Environment variables (see `.env.example`):

```env
# Formula Parser Configuration
FORMULA_PARSER_HOST="localhost"
FORMULA_PARSER_PORT="50052"
DEBUG_FORMULA_PARSER=true
```

## Development

### Project Structure

```text
formula-parser/
├── src/
│   ├── cli.ts
│   ├── core/
│   ├── handlers/
│   ├── instrumentation.ts
│   ├── server.ts
│   ├── services/
│   └── utils/
├── package.json                     # Project configuration
├── tests/                           # Test files
├── Dockerfile                       # Container configuration
├── moon.yml
├── tsconfig.json
├── tsup.config.ts
├── vitest.config.ts
└── README.md                        # This file
```

### Key Components

#### Core Parser

The main parsing engine that:

1. **Tokenizes** formulas using `excel-formula-tokenizer`
2. **Builds AST** using `excel-formula-ast`
3. **Handles errors** gracefully with descriptive messages

#### Handler Layer

Manages gRPC request/response conversion:

- Converts JavaScript objects to Protocol Buffer messages
- Handles AST type mapping
- Manages error responses

#### Data Type Conversion

The service converts between JavaScript and Protocol Buffer representations:

- **AST Types**: Maps JavaScript AST node types to Protocol Buffer enums
- **Reference Types**: Converts Excel reference types (relative, absolute, mixed)
- **Value Types**: Handles different data types (number, text, boolean)

### Error Handling

The service provides comprehensive error handling:

- **Tokenization Errors**: Invalid formula syntax
- **AST Building Errors**: Malformed expressions
- **Type Conversion Errors**: Unsupported data types
- **Protocol Buffer Errors**: Serialization issues

## Dependencies

### Core Dependencies

- **@grpc/grpc-js**: gRPC implementation for Node.js
- **@grpc/proto-loader**: Protocol Buffer loader
- **excel-formula-tokenizer**: Excel formula tokenization
- **excel-formula-ast**: AST generation from tokens
- **google-protobuf**: Protocol Buffer runtime
- **dotenv**: Environment variable management
- **@sloth/packages-proto-utils-js**: Workspace gRPC client and shared types

### Development Dependencies

- **tsup**: TypeScript build pipeline
- **vitest**: Test runner and coverage
- **typescript**: TypeScript compiler and type checking
- **eslint**: Linting and formatting checks

## API Examples

### Basic Cell Reference

**Input**: `A1`

**Output**:

```json
{
    "formula": "A1",
    "tokens": [{ "value": "A1", "type": "operand", "subtype": "range" }],
    "ast": {
        "type": "cell",
        "name": "A1",
        "refType": "relative"
    },
    "error": ""
}
```

### Mathematical Expression

**Input**: `=A1+B1*2`

**Output**:

```json
{
    "formula": "=A1+B1*2",
    "ast": {
        "type": "binary-expression",
        "operator": "+",
        "left": {
            "type": "cell",
            "name": "A1",
            "refType": "relative"
        },
        "right": {
            "type": "binary-expression",
            "operator": "*",
            "left": { "type": "cell", "name": "B1" },
            "right": { "type": "number", "value": 2 }
        }
    }
}
```

### Function Call

**Input**: `=SUM(A1:A10)`

**Output**:

```json
{
    "formula": "=SUM(A1:A10)",
    "ast": {
        "type": "function",
        "name": "SUM",
        "arguments": [
            {
                "type": "cell-range",
                "start": "A1",
                "end": "A10"
            }
        ]
    }
}
```

## Monitoring and Logging

- **Debug Mode**: Detailed logging when `DEBUG_FORMULA_PARSER=true`
- **Request Logging**: Logs incoming formulas and generated ASTs
- **Error Tracking**: Comprehensive error reporting with stack traces
- **Performance Monitoring**: Built-in timing for parsing operations
