"""
Ejemplo de uso de la nueva funcionalidad de validación de archivos.
Este script demuestra cómo usar el controlador de validación directamente.
"""

import asyncio
import os
from fastapi import UploadFile
from io import BytesIO

# Importar nuestras funciones
from app.controllers.validation import (
    validate_file_against_schema,
    get_validation_summary,
)
from app.services.file_processor import FileProcessor


async def create_mock_upload_file(file_path: str) -> UploadFile:
    """
    Crear un objeto UploadFile mock para testing.
    """
    with open(file_path, "rb") as f:
        content = f.read()

    # Crear un objeto BytesIO que simule un archivo subido
    file_like = BytesIO(content)

    # Crear un UploadFile mock
    upload_file = UploadFile(
        filename=os.path.basename(file_path), file=file_like, size=len(content)
    )

    return upload_file


async def test_file_processor():
    """
    Probar el procesador de archivos directamente.
    """
    print("=== Testing File Processor ===")

    # Probar con el archivo CSV existente
    csv_path = "./static/acme__users__sample1.csv"

    if os.path.exists(csv_path):
        upload_file = await create_mock_upload_file(csv_path)

        # Probar el procesamiento del archivo
        success, data, error = await FileProcessor.process_file(upload_file)

        print("File processing result:")
        print(f"  Success: {success}")
        print(f"  Data length: {len(data) if data else 0}")
        print(f"  Error: {error}")

        if success and data:
            print(f"  First record: {data[0]}")
            print(f"  Total records: {len(data)}")

        # Obtener información del archivo
        file_info = FileProcessor.get_file_info(upload_file)
        print(f"  File info: {file_info}")
    else:
        print(f"CSV file not found: {csv_path}")


async def test_validation_workflow():
    """
    Probar el flujo completo de validación.
    """
    print("\n=== Testing Complete Validation Workflow ===")

    csv_path = "./static/acme__users__sample1.csv"
    import_name = "acme__users__sample1"  # Sin extensión

    if os.path.exists(csv_path):
        # Crear archivo de prueba
        upload_file = await create_mock_upload_file(csv_path)

        # Ejecutar validación completa
        result = await validate_file_against_schema(
            file=upload_file,
            import_name=import_name,
            n_workers=2,  # Usar menos workers para testing
        )

        print("Validation result:")
        print(f"  Success: {result['success']}")
        print(f"  Error: {result.get('error', 'None')}")

        if result["success"] and result["validation_results"]:
            validation_data = result["validation_results"]
            print(f"  Total items: {validation_data['total_items']}")
            print(f"  Valid items: {validation_data['valid_items']}")
            print(f"  Invalid items: {validation_data['invalid_items']}")
            print(f"  Is valid: {validation_data['is_valid']}")

            if validation_data.get("errors"):
                print(f"  First few errors: {validation_data['errors'][:3]}")

            # Obtener resumen
            summary = get_validation_summary(result)
            print(f"  Summary: {summary}")
    else:
        print(f"CSV file not found: {csv_path}")


async def main():
    """
    Función principal para ejecutar las pruebas.
    """
    print("Starting validation system tests...\n")

    try:
        await test_file_processor()
        await test_validation_workflow()

        print("\n=== Tests completed successfully! ===")

    except Exception as e:
        print(f"\nError during testing: {str(e)}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    # Cambiar al directorio del proyecto
    path = os.path.abspath("..")
    os.chdir(path)

    # Ejecutar las pruebas
    asyncio.run(main())
