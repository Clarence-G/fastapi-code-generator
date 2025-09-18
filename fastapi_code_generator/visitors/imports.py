from pathlib import Path
from typing import Dict, Optional

from datamodel_code_generator.imports import Import, Imports
from datamodel_code_generator.reference import Reference
from datamodel_code_generator.types import DataType

from fastapi_code_generator.parser import OpenAPIParser
from fastapi_code_generator.visitor import Visitor


def _get_most_of_reference(data_type: DataType) -> Optional[Reference]:
    if data_type.reference:
        return data_type.reference
    for data_type in data_type.data_types:
        reference = _get_most_of_reference(data_type)
        if reference:
            return reference
    return None


def get_imports(parser: OpenAPIParser, model_path: Path) -> Dict[str, object]:
    imports = Imports()

    imports.update(parser.imports)
    
    # 收集被替换schema的外部导入
    replaced_schema_imports = set()
    if hasattr(parser, 'schema_replacements') and parser.schema_replacements:
        for schema_name, import_path in parser.schema_replacements.items():
            replaced_schema_imports.add(schema_name)
            # 添加外部导入
            imports.append(Import.from_full_path(import_path))
    
    for data_type in parser.data_types:
        reference = _get_most_of_reference(data_type)
        if reference:
            # 检查是否是被替换schema的Model版本，如果是则跳过
            should_skip = False
            if hasattr(parser, 'schema_replacements') and parser.schema_replacements:
                for schema_name in parser.schema_replacements:
                    # 只过滤精确匹配被替换schema的Model版本
                    # 不过滤包含被替换schema名称但不是Model版本的正常模型
                    if (reference.name == schema_name or 
                        reference.name == f"{schema_name}Model"):
                        should_skip = True
                        break
            
            if not should_skip:
                imports.append(data_type.all_imports)
                imports.append(
                    Import.from_full_path(f'.{model_path.stem}.{reference.name}')
                )
    for from_, imports_ in parser.imports_for_fastapi.items():
        imports[from_].update(imports_)
    for operation in parser.operations.values():
        if operation.imports:
            imports.alias.update(operation.imports.alias)
    return {'imports': imports}


visit: Visitor = get_imports
