import re
from pathlib import Path

from .utils import in_excluding_list
from utils import get_logger, find_files, get_file_content

log = get_logger()

IMPORT_REGEX = r"\b(?:import)(?:\s*\(?\s*[`'\"]|[^`'\"]*from\s+[`'\"])([^`'\"]+)"


def get_dependencies(package_json):
    log.info("Getting dependencies from package.json")

    requiredDependencies = list(package_json["dependencies"].keys())
    devDependencies = list(package_json["devDependencies"].keys())

    return set(requiredDependencies + devDependencies)


def in_vendor_list(vendor_dependencies, file_import):
    for vendor_dependency in vendor_dependencies:
        if file_import.startswith(vendor_dependency):
            return True

    return False


def apply_aliases(file_import, aliases, parent_file, base_path):
    local_import_path = None
    for alias in aliases:
        # TODO: Improve @ case (or 'resolve' to make it work)
        if alias == "@" and "@" in file_import:
            local_import_path = Path(
                file_import.replace("@", str(base_path.absolute()))
            )
        else:
            local_import_path = parent_file.parent.joinpath(Path(file_import))

    return local_import_path


def filter_local_imports(
    project_file,
    project_path,
    file_imports,
    vendor_dependencies,
    excluding_patterns,
    aliases,
):
    file_imports = [
        file_import
        for file_import in file_imports
        if not in_vendor_list(vendor_dependencies, file_import)
    ]

    file_imports = [
        file_import
        for file_import in file_imports
        if not in_excluding_list(excluding_patterns, file_import)
    ]

    file_imports = [
        apply_aliases(file_import, aliases, project_file, project_path)
        for file_import in file_imports
    ]

    return file_imports


def resolve_local_imports(local_import_path, local_import_extensions):
    local_import_path_resolved = None

    # If local import statement contains extensions, we resolved directy, otherwise check project params
    import_contains_extensions = (
        len(set(local_import_extensions).intersection(set(local_import_path.suffixes)))
        > 1
    )

    if import_contains_extensions and local_import_path.exists():
        local_import_path_resolved = local_import_path
    else:
        for local_import_extension in local_import_extensions:
            local_import_with_suffix = Path(
                "{}{}".format(str(local_import_path.absolute()), local_import_extension)
            )
            if local_import_with_suffix.exists():
                local_import_path_resolved = local_import_with_suffix
                break

    # If JS is on the project params we must contemplate the "index.js" case
    if not local_import_path_resolved and ".js" in local_import_extensions:
        index_js_local_import_path = Path(
            "{}/{}".format(str(local_import_path.absolute()), "index.js")
        )
        if index_js_local_import_path.exists():
            local_import_path_resolved = index_js_local_import_path

    return local_import_path_resolved


# TODO: Improve this, not need for "_" check anymore
def get_isolated_files(data_report):
    isolated_files = []

    for project_file_key, project_file in data_report.items():
        if str(project_file_key).startswith("_"):
            continue

        if len(project_file["importer_by"]) == 0:
            isolated_files.append(project_file["path"])

    return isolated_files


def scan_file_imports_project(project_path, package_json, project_options):
    data_report = {}
    graph_report_data = {
        "nodes": [],
        "links": [],
    }
    errors = []
    isolates = []
    stats = {
        "scanned_files": 0,
        "errors": 0,
        "isolates": 0,
    }

    vendor_dependencies = get_dependencies(package_json)

    log.debug(
        "Dependencies [{}] {}".format(len(vendor_dependencies), vendor_dependencies)
    )

    project_found_files = find_files(project_path, project_options["files_extensions"])

    log.debug(
        "Project files list [{}]: {}".format(
            len(project_found_files), project_found_files
        )
    )

    for project_file in project_found_files:
        log.info("Scanning {}".format(project_file))

        project_file_absolute_path = project_file.absolute()
        project_file_content = get_file_content(project_file_absolute_path)

        # [GRAPH DATA REPORT]  Add node to the graph data
        graph_report_data["nodes"].append(
            {
                "id": str(project_file_absolute_path),
                "group": 1,
                "name": project_file.stem,
            }
        )

        project_file_imports = re.findall(IMPORT_REGEX, project_file_content)

        project_file_imports = filter_local_imports(
            project_file,
            project_path,
            project_file_imports,
            vendor_dependencies,
            project_options["excluding_patterns"],
            project_options["alias"],
        )

        # Resolved local imports
        resolved_local_imports = []

        # Iterating local imports from project file (other project comps/files)
        for local_import_path in project_file_imports:
            log.info("Resolving local import: {}".format(local_import_path))

            local_import_path_resolved = resolve_local_imports(
                local_import_path, project_options["local_import_extensions"]
            )

            if not local_import_path_resolved:
                errors.append(
                    "Couldn't resolve local import for {} on {} file.".format(
                        local_import_path, project_file_absolute_path
                    )
                )
                break

            # [GRAPH DATA REPORT] Add link to graph report data
            graph_report_data["links"].append(
                {
                    "source": str(project_file_absolute_path),
                    "target": str(local_import_path_resolved),
                    "value": 1,
                }
            )

            # If it didn't break (not resolved) we have to add to the local imports
            resolved_local_imports.append(str(local_import_path_resolved))

            # Check if local import was already scanned and increment it's importers
            if str(local_import_path_resolved) in data_report:
                data_report[str(local_import_path_resolved)]["importer_by"].append(
                    str(project_file_absolute_path)
                )
            else:
                data_report[str(local_import_path_resolved)] = {
                    "importer_by": [str(project_file_absolute_path)],
                }

        # Check if file has imported by other file and added to the the data_report
        if str(project_file_absolute_path) in data_report:
            data_report[str(project_file_absolute_path)][
                "imports"
            ] = resolved_local_imports
        else:
            data_report[str(project_file_absolute_path)] = {
                "path": str(project_file),
                "filename": project_file.stem,
                "imports": [str(file_import) for file_import in resolved_local_imports],
                "importer_by": [],
            }

        log.debug("File Imports: {}".format(project_file_imports))
        log.debug("File Local Imports {}".format(list(project_file_imports)))

    isolates = get_isolated_files(data_report)

    stats["scanned_files"] = len(project_found_files)
    stats["errors"] = len(errors)
    stats["isolates"] = len(isolates)

    return data_report, graph_report_data, errors, isolates, stats
