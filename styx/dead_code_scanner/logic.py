import re
from pathlib import Path

from .utils import in_excluding_list
from utils import get_logger, find_files, get_file_content
from .constants import (
    IMPORT_REGEX,
    TRANSLATIONS_REGEX,
    FUZZY_WUZZY_RATIO_TYPE,
    DEFAULT_FUZZY_WUZZY_RATIO_TYPE,
)

log = get_logger()


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


def get_fuzzy_ratio_type(ratio_type):
    return (
        FUZZY_WUZZY_RATIO_TYPE[ratio_type]
        if ratio_type in FUZZY_WUZZY_RATIO_TYPE
        else FUZZY_WUZZY_RATIO_TYPE[DEFAULT_FUZZY_WUZZY_RATIO_TYPE]
    )


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


def search_for_similars(
    translations_found,
    new_translation_key,
    new_translation_text_value,
    similarity_score_acceptance,
    similarity_ratio_type,
):
    similars = []
    for translation_key, translation_data in translations_found.items():
        fuzzy_wuzzy_ratio_type = get_fuzzy_ratio_type(similarity_ratio_type)
        similarity_score = fuzzy_wuzzy_ratio_type(
            new_translation_text_value, translation_data["text"]
        )
        if similarity_score > similarity_score_acceptance:
            similars.append(
                {
                    "first": {
                        "translation_key": translation_key,
                        "translation_value": translation_data["text"],
                    },
                    "second": {
                        "translation_key": new_translation_key,
                        "translation_value": new_translation_text_value,
                    },
                    "similarity_score": similarity_score,
                },
            )

    return similars


def has_interpolation(translation_key):
    return "${" in translation_key


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
                "name": project_file.name,
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
                resolve_file_import_error = {
                    "error_id": "{}-{}".format(
                        project_file_absolute_path.name, local_import_path.name,
                    ),
                    "importer": {
                        "path": project_file_absolute_path,
                        "filename": project_file_absolute_path.name,
                        "format": project_file_absolute_path.suffixes[0]
                        if len(project_file_absolute_path.suffixes) == 1
                        else project_file_absolute_path.suffixes,
                    },
                    "imported": {
                        "path": local_import_path,
                        "filename": local_import_path.name,
                        "format": local_import_path.suffixes[0]
                        if len(local_import_path.suffixes) == 1
                        else local_import_path.suffixes,
                    },
                    "message": "Couldn't resolve local import for {} on {} file.".format(
                        local_import_path, project_file_absolute_path
                    ),
                }
                errors.append(resolve_file_import_error)
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
                    "path": str(local_import_path_resolved),
                    "filename": local_import_path_resolved.name,
                    "importer_by": [str(project_file_absolute_path)],
                    "format": local_import_path_resolved.suffixes[0]
                    if len(local_import_path_resolved.suffixes) == 1
                    else local_import_path_resolved.suffixes,
                }

        # Check if file has imported by other file and added to the the data_report
        if str(project_file_absolute_path) in data_report:
            data_report[str(project_file_absolute_path)][
                "imports"
            ] = resolved_local_imports
        else:
            data_report[str(project_file_absolute_path)] = {
                "path": str(project_file),
                "filename": project_file.name,
                "imports": [str(file_import) for file_import in resolved_local_imports],
                "importer_by": [],
                "format": project_file.suffixes[0]
                if len(project_file.suffixes) == 1
                else project_file.suffixes,
            }

        log.debug("File Imports: {}".format(project_file_imports))
        log.debug("File Local Imports {}".format(list(project_file_imports)))

    isolates = get_isolated_files(data_report)

    stats["scanned_files"] = len(project_found_files)
    stats["errors"] = len(errors)
    stats["isolates"] = len(isolates)

    return data_report, graph_report_data, errors, isolates, stats


def scan_translations_project(
    project_path,
    project_options,
    translations_values,
    similarity_score_acceptance,
    similarity_ratio_type,
):
    data_report = {}

    errors = []
    similars = []
    abandons = []
    interpolations = set()
    stats = {
        "scanned_files": 0,
        "errors": 0,
        "isolates": 0,
    }

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

        project_file_translations_used = re.findall(
            TRANSLATIONS_REGEX, project_file_content
        )
        for translations_key_match in project_file_translations_used:
            # TODO: Improve regex to avoid this
            translations_key = translations_key_match[1]

            # If phraseapp string key has interpolation, we skip it
            if has_interpolation(translations_key):
                interpolations.add(translations_key)
            else:
                if translations_key in data_report:
                    data_report[translations_key]["ocurrences"] = (
                        data_report[translations_key]["ocurrences"] + 1
                    )
                else:
                    try:
                        translated_value = translations_values[translations_key]

                        if similarity_score_acceptance:
                            new_similars = search_for_similars(
                                data_report,
                                translations_key,
                                translated_value,
                                similarity_score_acceptance,
                                similarity_ratio_type,
                            )
                            similars = similars + new_similars

                        data_report[translations_key] = {
                            "ocurrences": 1,
                            "text": translations_values[translations_key],
                        }
                    except KeyError:
                        log.debug(
                            "translation key not found: {}".format(translations_key)
                        )
                        abandons.append(translations_key)

            # log.info('translations found: {}'.format(translations_key))

    return data_report, similars, abandons, interpolations, errors
