import fire
from pathlib import Path
from benedict import benedict

import utils
import cli_logic

from graph.graph_generator import generate_graph
from dead_code_scanner.logic import scan_file_imports_project, scan_translations_project

log = utils.get_logger()

# example
# python styx/main.py scan_file_imports /home/ismikin/ubeeqo-dev/webapp/src --package_json /home/ismikin/ubeeqo-dev/webapp/package.json --project_params ./project-options.json --data_report_output --graph_report_output --graph_image
# TODO : improve cli flow (arguments)
def scan_file_imports(
    project_dir="src",
    package_json=".",
    project_params=".",
    data_report_output=None,
    graph_report_output=None,
    graph_image=None,
    overrides=True,
):

    project_path = Path(project_dir)

    package_json = utils.get_json_content(package_json)
    project_options = utils.get_json_content(project_params)

    data_report, graph_report_data, errors, isolates, stats = scan_file_imports_project(
        project_path, package_json, project_options
    )

    log.info(
        "Total files / Isolated files [{} / {}]! on {}".format(
            len(data_report), stats["isolates"], project_path,
        )
    )

    random_file_prefix = utils.get_random_prefix(project_path.stem)

    if data_report_output:
        cli_logic.save_report_file(
            data_report,
            data_report_output,
            cli_logic.FILE_IMPORTS_REPORT_NAME,
            random_file_prefix,
            overrides,
        )

    if graph_report_output:
        cli_logic.save_report_file(
            graph_report_data,
            graph_report_output,
            cli_logic.GRAPH_DATA_REPORT_NAME,
            random_file_prefix,
            overrides,
        )

    if graph_image:
        output_graph_file = cli_logic.get_output_filename(
            graph_image, cli_logic.GRAPH_IMAGE, random_file_prefix
        )

        generate_graph(graph_report_data, output_graph_file)


def scan_translations(
    project_dir="src",
    project_params=".",
    translations_dictionary=".",
    data_report_output=None,
    similarity_score_acceptance=None,
    similarity_ratio_type=None,
    overrides=True,
):

    project_path = Path(project_dir)
    project_options = utils.get_json_content(project_params)

    translations_values = benedict(translations_dictionary)

    data_report, similars, abandons, errors = scan_translations_project(
        project_path,
        project_options,
        translations_values,
        similarity_score_acceptance,
        similarity_ratio_type,
    )

    random_file_prefix = utils.get_random_prefix(project_path.stem)

    if data_report_output:
        cli_logic.save_report_file(
            data_report,
            data_report_output,
            cli_logic.TRANSLATIONS_REPORT_NAME,
            random_file_prefix,
            overrides,
        )

        if similarity_score_acceptance:
            cli_logic.save_report_file(
                similars,
                data_report_output,
                cli_logic.TRANSLATIONS_SIMILARS_REPORT_NAME,
                random_file_prefix,
                overrides,
            )

    return data_report, similars, abandons, errors


# example full run:
# python styx/main.py run /home/ismikin/ubeeqo-dev/webapp/src --package_json /home/ismikin/ubeeqo-dev/webapp/package.json --project_params ./project-options.json --data_report_output --graph_report_output --graph_image
if __name__ == "__main__":
    fire.Fire()
