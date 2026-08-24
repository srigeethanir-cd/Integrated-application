import os
import re
from pathlib import Path
from typing import Dict, Any, List

class DatabaseVisualizer:
    """Extracts tables, columns, and relations from SQL or SQLAlchemy models."""

    def generate_er_diagram(self, root_path: Path) -> Dict[str, Any]:
        """Scan SQL files or SQLAlchemy model directories and build an ER map."""
        tables = []
        sql_files = list(root_path.glob("**/*.sql"))

        for f in sql_files:
            try:
                with open(f, "r", encoding="utf-8", errors="ignore") as file_obj:
                    content = file_obj.read()
                
                # Simple SQL parser for tables
                table_blocks = re.findall(r'CREATE\s+TABLE\s+(\w+)\s*\((.*?)\);', content, re.DOTALL | re.IGNORECASE)
                for tbl_name, col_block in table_blocks:
                    cols = []
                    fks = []
                    for line in col_block.split(","):
                        line = line.strip()
                        if not line:
                            continue
                        if "FOREIGN KEY" in line.upper():
                            # extract foreign keys
                            fk_match = re.search(r'FOREIGN\s+KEY\s*\((\w+)\)\s*REFERENCES\s*(\w+)\s*\((\w+)\)', line, re.IGNORECASE)
                            if fk_match:
                                fks.append({
                                    "column": fk_match.group(1),
                                    "references_table": fk_match.group(2),
                                    "references_column": fk_match.group(3)
                                })
                        else:
                            parts = line.split()
                            if parts:
                                col_name = parts[0].replace('"', '').replace('`', '')
                                col_type = parts[1] if len(parts) > 1 else "VARCHAR"
                                cols.append({
                                    "name": col_name,
                                    "type": col_type,
                                    "primary_key": "PRIMARY" in line.upper()
                                })
                    tables.append({
                        "table_name": tbl_name,
                        "columns": cols,
                        "foreign_keys": fks
                    })
            except Exception:
                pass

        # If empty, let's scan Python files for SQLAlchemy models as a fallback
        if not tables:
            py_files = list(root_path.glob("**/*.py"))
            for f in py_files:
                try:
                    with open(f, "r", encoding="utf-8", errors="ignore") as file_obj:
                        content = file_obj.read()
                    
                    class_blocks = re.findall(r'class\s+(\w+)\(Base\):.*TableName\s*=\s*["\'](\w+)["\'](.*?)(\n\s*\n|\Z)', content, re.DOTALL | re.IGNORECASE)
                    for cls_name, tbl_name, body in class_blocks:
                        cols = []
                        fks = []
                        col_defs = re.findall(r'(\w+)\s*:\s*Mapped\[.*?\]\s*=\s*mapped_column\((.*?)\)', body)
                        for col_name, args in col_defs:
                            primary = "primary_key=True" in args
                            fk = re.search(r'ForeignKey\(["\'](.*?)\.(.*?)["\']\)', args)
                            col_type = "UUID" if "GUID" in args else "VARCHAR"
                            if fk:
                                fks.append({
                                    "column": col_name,
                                    "references_table": fk.group(1),
                                    "references_column": fk.group(2)
                                })
                            cols.append({
                                "name": col_name,
                                "type": col_type,
                                "primary_key": primary
                            })
                        tables.append({
                            "table_name": tbl_name,
                            "columns": cols,
                            "foreign_keys": fks
                        })
                except Exception:
                    pass

        return {
            "tables": tables,
            "relationships": [
                {
                    "from_table": tbl["table_name"],
                    "to_table": fk["references_table"],
                    "from_col": fk["column"],
                    "to_col": fk["references_column"]
                }
                for tbl in tables for fk in tbl.get("foreign_keys", [])
            ]
        }
