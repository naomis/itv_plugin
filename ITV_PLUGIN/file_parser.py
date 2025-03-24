import os

class FileParser:
    def __init__(self):
        pass

    def parse(self, file_path):
        content = self.get_file_content(file_path)
        lines = content.split("\n")
        metadata = self.parse_metadata(lines[:6])
        final_data = [{"n_passage": 1, "tables": {}}]

        index = 1
        current_table_name = None
        for line in lines[6:]:
            if line.startswith("#Z"):
                current_table_name = None
                final_data.append({"n_passage": index + 1, "tables": {}})
                index += 1
            elif line.startswith("#B") or line.startswith("#C"):
                table_name, column_string = line.split("=")
                columns = column_string.split(metadata["delimiter"])
                current_table_name = table_name
                if table_name not in final_data[index - 1]["tables"]:
                    final_data[index - 1]["tables"][table_name] = {
                        "columns": columns,
                        "rows": [],
                    }
            elif current_table_name and line:
                row = self.parse_line(line, metadata["delimiter"], metadata["quoteChar"])
                final_data[index - 1]["tables"][current_table_name]["rows"].append(row)

        return {
            "metadata": metadata,
            "passages": final_data,
        }

    def parse_line(self, line, delimiter, quote_char):
        line = line.strip()
        result = []
        current = ""
        in_quotes = False
        for char in line:
            if char == quote_char:
                in_quotes = not in_quotes
            elif char == delimiter and not in_quotes:
                result.append(current.strip())
                current = ""
            else:
                current += char
        result.append(current.strip())
        return result

    def get_file_content(self, file_path):
        with open(file_path, "r", encoding="ISO-8859-1") as file:
            return file.read()

    def parse_metadata(self, metadata_lines):
        metadata = {}
        for line in metadata_lines:
            key, value = line.split("=")
            if key == "#A1":
                metadata["charset"] = value.strip()
            elif key == "#A2":
                metadata["language"] = value.strip()
            elif key == "#A3":
                metadata["delimiter"] = value.strip()
            elif key == "#A4":
                metadata["decimalSeparator"] = value.strip()
            elif key == "#A5":
                metadata["quoteChar"] = value.strip()
            elif key == "#A6":
                metadata["version"] = value.strip()
        return metadata
