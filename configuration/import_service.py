import pandas as pd
from django.core.files.storage import default_storage
from django.core.exceptions import ValidationError
from django.db.models import Q
from configuration.models import Level, Node
from configuration.utils import check_bool_value

class ImportService:
    @staticmethod
    def validate_import_file(file_obj):
        """
        Reads the uploaded file and returns a pandas DataFrame.
        """
        file_name = file_obj.name.lower()
        try:
            if file_name.endswith(".csv"):
                df = pd.read_csv(file_obj, encoding="utf-8")
            elif file_name.endswith((".xlsx", ".xls")):
                df = pd.read_excel(file_obj)
            else:
                raise ValueError("Invalid file format. Please upload .csv, .xls, or .xlsx.")
                
            df = df.astype(object).where(pd.notnull(df), None)
            df.columns = df.columns.str.strip()
            return df
        except Exception as e:
            raise ValueError(f"Error parsing file: {str(e)}")

    @staticmethod
    def resolve_parent_node(target_level, row_data, mapping_dict, row_index):
        """
        Traverses up the hierarchy using the provided mapping to find the parent Node.
        """
        parent_level = target_level.parent
        if not parent_level:
            return None

        col_parent_name = mapping_dict.get(parent_level.name)
        parent_name_val = row_data.get(col_parent_name)
        
        if not parent_name_val:
            raise ValueError(f"Missing parent '{parent_level.name}' (column '{col_parent_name}').")
        
        lookup_kwargs = {
            'dimension': target_level.dimension
        }
        
        current_ancestor_level = parent_level
        prefix = ""
        missing_ancestor_data = False
        attempted_path = []
        
        while current_ancestor_level:
            level_name = current_ancestor_level.name
            
            if level_name in mapping_dict:
                col_name = mapping_dict[level_name]
                ancestor_val = row_data.get(col_name)
                
                if not ancestor_val:
                    missing_ancestor_data = True
                    break
                
                lookup_kwargs[f"{prefix}name"] = ancestor_val
                lookup_kwargs[f"{prefix}level"] = current_ancestor_level
                attempted_path.insert(0, str(ancestor_val))
            
            current_ancestor_level = current_ancestor_level.parent
            prefix += "parent__"

        if missing_ancestor_data:
            raise ValueError(f"Missing required hierarchy data for resolving parent.")

        parent_node = Node.objects.filter(**lookup_kwargs).first()

        if not parent_node:
            path_str = " -> ".join(attempted_path)
            raise ValueError(f"Hierarchy '{path_str}' not found in database.")
            
        return parent_node

    @staticmethod
    def validate_row(row_data, row_index, target_level, mapping_dict):
        """
        Validates a single row and returns (parsed_data, error_message).
        """
        try:
            target_level_name_key = target_level.name
            col_target_name = mapping_dict.get(target_level_name_key)
            name_val = row_data.get(col_target_name)
            
            if not name_val:
                return None, f"Missing target name for column '{col_target_name}'."

            # Step 1: Resolve Parent Node
            try:
                parent_node = ImportService.resolve_parent_node(target_level, row_data, mapping_dict, row_index)
            except ValueError as e:
                return None, str(e)

            # Step 2: Determine Create vs Update via ID
            # Also allow custom mapped ID column if present, fallback to "ID"
            id_col_name = mapping_dict.get('id', "ID")
            id_val = row_data.get(id_col_name)
            
            node = None
            if id_val not in ["", None]:
                if isinstance(id_val, str) and id_val.isdigit():
                    id_val = int(id_val)
                elif isinstance(id_val, float):
                    id_val = int(id_val)
                elif not isinstance(id_val, int):
                    return None, f"Provided ID '{id_val}' is not a valid integer."
                    
            if id_val is not None:
                node = Node.objects.filter(id=id_val, level=target_level).first()
                if not node:
                    return None, f"Provided ID '{id_val}' does not exist in the database for level '{target_level.name}'."

            def get_mapped_val(key, default=None):
                if key in mapping_dict and mapping_dict[key] in row_data:
                    return row_data[mapping_dict[key]]
                return default

            # Step 3: Validate Code
            code_val = get_mapped_val('code')
            if code_val in ["", None]:
                return None, "Missing Code."
            
            if type(code_val) not in [str, int, float]:
                return None, f"Code '{code_val}' is invalid."
                
            if isinstance(code_val, (float, str)):
                try:
                    code_val = int(code_val)
                except ValueError:
                    return None, f"Code '{code_val}' must be an integer."

            if len(str(code_val)) > target_level.code_digits:
                return None, f"Code '{code_val}' too long for level '{target_level.name}'."
            
            if code_val <= 0:
                return None, f"Code '{code_val}' is not positive."
            
            collision_qs = Node.objects.filter(
                level=target_level,
                code=code_val,
                parent=parent_node
            )

            if node:
                collision_qs = collision_qs.exclude(id=node.id)
            
            if collision_qs.exists():
                return None, f"Code '{code_val}' already used by '{collision_qs.first().name}'."

            # Step 4: Hidden / Hold Status
            is_hidden_raw = get_mapped_val('is_hidden', None)
            is_hidden = False
            if is_hidden_raw is not None:
                is_hidden = check_bool_value(is_hidden_raw)
                if is_hidden is None:
                    return None, f"Invalid value for is_hidden: {is_hidden_raw}"
                
            on_hold_raw = get_mapped_val('on_hold', None)
            on_hold = False
            if on_hold_raw is not None:
                on_hold = check_bool_value(on_hold_raw)
                if on_hold is None:
                    return None, f"Invalid value for on_hold: {on_hold_raw}"

            hold_date_raw = get_mapped_val('hold_date')
            hold_date_val = None
            if hold_date_raw:
                try:
                    dt = pd.to_datetime(hold_date_raw, dayfirst=True)
                    hold_date_val = dt.date()
                except:
                    return None, "Invalid date format for Hold Date."

            # Step 5: Attributes
            node_attributes = {}
            valid_attr_keys = {col['name']: col['type'] for col in (target_level.extra_fields_schema or [])}
            
            if 'attributes' in mapping_dict and isinstance(mapping_dict['attributes'], dict):
                for sys_attr, excel_header in mapping_dict['attributes'].items():
                    if sys_attr in valid_attr_keys:
                        val = row_data.get(excel_header)
                        if val is not None:
                            node_attributes[sys_attr] = val

            # Step 6: Create Dummy Node for Model Validation
            temp_node = Node(
                id=node.id if node else None,
                name=name_val,
                code=code_val,
                is_hidden=is_hidden,
                on_hold=on_hold,
                hold_date=hold_date_val,
                level=target_level,
                parent=parent_node,
                dimension=target_level.dimension,
                attributes=node_attributes
            )
            
            try:
                temp_node.validate_attributes()
            except ValidationError as e:
                clean_error_text = " ".join(e.messages) if hasattr(e, 'messages') else str(e)
                return None, clean_error_text

            parsed_data = {
                "id": node.id if node else None,
                "name": name_val,
                "code": code_val,
                "is_hidden": is_hidden,
                "on_hold": on_hold,
                "hold_date": str(hold_date_val) if hold_date_val else None,
                "parent_id": parent_node.id if parent_node else None,
                "dimension_id": target_level.dimension.id,
                "level_id": target_level.id,
                "attributes": node_attributes,
                "is_update": node is not None
            }
            
            # Additional UI fields for preview
            parsed_data["parent_name"] = parent_node.name if parent_node else None
            
            return parsed_data, None

        except Exception as e:
            return None, str(e)

    @staticmethod
    def build_preview(df, target_level, mapping_dict, progress_callback=None):
        """
        Validates all rows and returns the summary, valid_rows, and invalid_rows.
        """
        valid_rows = []
        invalid_rows = []
        seen_codes = set()
        
        total_rows = len(df)
        
        for index, row in df.iterrows():
            current_row_number = index + 1
            if progress_callback and (current_row_number % 5 == 0 or current_row_number == total_rows):
                progress_callback(current_row_number, total_rows)
                
            row_index = index + 2
            row_data = row.to_dict()
            
            target_level_name_key = target_level.name
            col_target_name = mapping_dict.get(target_level_name_key)
            name_val = row_data.get(col_target_name)
            
            if not name_val:
                continue
                
            parsed_data, error = ImportService.validate_row(row_data, row_index, target_level, mapping_dict)
            
            if error:
                invalid_rows.append({
                    "row": row_index,
                    "error": error,
                    "raw_data": row_data
                })
            else:
                # Catch in-file duplicate codes before they hit the database commit
                code_val = parsed_data["code"]
                parent_id = parsed_data["parent_id"]
                
                unique_key = (parent_id, code_val)
                if unique_key in seen_codes:
                    invalid_rows.append({
                        "row": row_index,
                        "error": f"Code '{code_val}' is duplicated within the uploaded file for this parent.",
                        "raw_data": row_data
                    })
                else:
                    seen_codes.add(unique_key)
                    parsed_data["row"] = row_index
                    valid_rows.append(parsed_data)
                
        summary = {
            "total": len(valid_rows) + len(invalid_rows),
            "valid": len(valid_rows),
            "invalid": len(invalid_rows)
        }
        
        return valid_rows, invalid_rows, summary
