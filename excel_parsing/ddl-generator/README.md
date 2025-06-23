# ddl-generator

Microservicio interno del proyecto [`etl-design`](https://github.com/ISCOUTB/etl-design), responsable de transformar árboles de sintaxis abstracta (ASTs), derivados de fórmulas Excel, en fragmentos SQL válidos (actualmente sólo para PostgreSQL).

## Propósito

Este componente genera fragmentos DDL utilizados para definir columnas calculadas en sentencias SQL como:

```sql
ALTER TABLE ... ADD COLUMN colX NUMERIC GENERATED ALWAYS AS (<expresión>) STORED;
```

Se utiliza dentro del pipeline de transformación de hojas de cálculo hacia estructuras SQL analizables.

## Características principales

- 🎯 Traducción de ASTs (basados en fórmulas Excel) a SQL.
- 🔄 Mapeo entre celdas (A1, B1, etc.) y nombres reales de columnas (col1, edad, ...).
- ➕ Soporte para expresiones matemáticas, lógicas y funciones anidadas.
- 🧠 Soporte para funciones como `SUM`, `IF`, `AND`, con extensibilidad modular.
- 🧱 Generación de fragmentos tipo: `BOOLEAN GENERATED ALWAYS AS (CASE WHEN col1 > 18 THEN TRUE ELSE FALSE END) STORED`
- 💬 Salida estructurada que incluye información enriquecida (sql, columns, error, etc.)

## Instalación

Requiere Python 3.12 o superior. Actualmente no hay dependencias externas

```bash
cd excel_parsing/ddl-generator
uv sync
source .venv/bin/activate
```

## Ejemplo de uso

```python
from main import main
from dtypes import InputData, AST

ast: AST = {
    "type": "binary-expression",
    "operator": "+",
    "left": {"type": "cell", "refType": "relative", "key": "A1"},
    "right": {"type": "cell", "refType": "relative", "key": "B1"}
}

columns = {"A": "col1", "B": "col2"}
data: InputData = {"ast": ast, "columns": columns}

result = main(data)
print(result["sql"])  # (col1) + (col2)
```

## Estructura

| Archivo        | Descripción                                         |
| -------------- | --------------------------------------------------- |
| `main.py`      | Punto de entrada principal del microservicio        |
| `generator.py` | Enrutador por tipo de nodo (`MAPS`)                 |
| `sql.py`       | Mapeo de funciones Excel a SQL (`IF`, `SUM`, etc.)  |
| `utils.py`     | Conversión de celdas, letras de columna, utilidades |
| `dtypes.py`    | Tipos estructurados con TypedDict                   |

### Tipos de nodos soportados

- **binary-expression**: Operadores binarios (+, -, >, <, etc.)
- **function**: Llamadas a funciones (IF, SUM, AND, ...)
- **cell**: Referencias individuales a celdas
- **cell-range**: Rangos de celdas como A1:E1
- **number**: Números constantes (5, 2.1)
- **logical**: Booleanos (TRUE, FALSE)

## Agregar soporte para nuevas funciones

Agrega funciones en `sql.py`, dentro del diccionario `FUNCTION_SQL_MAP`:

```python
FUNCTION_SQL_MAP = {
    "SUM": lambda args: " + ".join(args[0]["columns"]),
    "IF": lambda args: f"CASE WHEN {args[0]['sql']} THEN {args[1]['sql']} ELSE {args[2]['sql']} END",
    "AND": lambda args: " AND ".join(arg["sql"] for arg in args),
    # Agregar más funciones aquí
}
```

## Limitaciones actuales

- Solo soporta salida para dialecto PostgreSQL.
- No construye sentencias `CREATE TABLE`, solo fragmentos por columna.
- El ensamblado final del esquema se realiza en el microservicio `sql-builder`.

## Pruebas

Por ahora, puedes correr `main.py` manualmente para validar transformaciones específicas. En versiones futuras se moverán los ejemplos al directorio `tests/` y se usará `pytest`
