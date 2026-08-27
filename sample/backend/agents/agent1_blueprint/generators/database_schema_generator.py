from typing import Any, Dict, List

class DatabaseSchemaGenerator:
    """Generate database schema blueprint (JSON) based on user stories."""

    def generate(self, project_config: Dict[str, Any], stories: List[Dict[str, Any]]) -> Dict[str, Any]:
        project_name = project_config.get("project_name", "generated_project")
        database_type = project_config.get("tech_stack", {}).get("database", "postgresql")

        tables = []
        
        # Always generate users table
        tables.append({
            "name": "users",
            "columns": [
                {"name": "id", "type": "SERIAL", "primary_key": True, "nullable": False},
                {"name": "email", "type": "VARCHAR(255)", "unique": True, "nullable": False},
                {"name": "password_hash", "type": "VARCHAR(255)", "nullable": False},
                {"name": "created_at", "type": "TIMESTAMP", "default": "CURRENT_TIMESTAMP"}
            ]
        })

        # Generate custom tables based on stories feature_group
        feature_groups = set()
        for story in stories:
            fg = story.get("feature_group")
            if fg and fg != "authentication":
                feature_groups.add(fg)

        for fg in sorted(feature_groups):
            table_name = fg.lower().replace(" ", "_")
            tables.append({
                "name": table_name,
                "columns": [
                    {"name": "id", "type": "SERIAL", "primary_key": True, "nullable": False},
                    {"name": "user_id", "type": "INTEGER", "foreign_key": "users.id", "nullable": False},
                    {"name": "title", "type": "VARCHAR(255)", "nullable": False},
                    {"name": "description", "type": "TEXT", "nullable": True},
                    {"name": "status", "type": "VARCHAR(50)", "default": "'draft'"},
                    {"name": "created_at", "type": "TIMESTAMP", "default": "CURRENT_TIMESTAMP"}
                ]
            })

        # Generate a DDL SQL string representation
        sql_lines = []
        for t in tables:
            sql_lines.append(f"CREATE TABLE {t['name']} (")
            col_definitions = []
            for col in t["columns"]:
                def_str = f"    {col['name']} {col['type']}"
                if col.get("primary_key"):
                    def_str += " PRIMARY KEY"
                if col.get("unique"):
                    def_str += " UNIQUE"
                if col.get("nullable") is False:
                    def_str += " NOT NULL"
                if col.get("default"):
                    def_str += f" DEFAULT {col['default']}"
                if col.get("foreign_key"):
                    def_str += f" REFERENCES {col['foreign_key']}"
                col_definitions.append(def_str)
            sql_lines.append(",\n".join(col_definitions))
            sql_lines.append(");\n")

        schema_sql = "\n".join(sql_lines)

        return {
            "project_name": project_name,
            "database_type": database_type,
            "tables": tables,
            "schema_sql": schema_sql
        }
