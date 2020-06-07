
import fire
from pathlib import Path

import utils
import cli_logic

from graph.graph_generator import generate_graph
from dead_code_scanner.logic import scan_project

log = utils.get_logger()


# TODO : improve cli flow (arguments)
def run(
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

    data_report, graph_report_data = scan_project(
        project_path, package_json, project_options
    )

    log.info(
        "Finish of scanning project [{} files]: {}!".format(
            len(data_report), project_path
        )
    )

    log.info(
        "Total files / Isolated files [{} / {}]!".format(
            len(data_report), len(data_report["_isolates"])
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


# example full run:
# python styx/main.py run /home/ismikin/ubeeqo-dev/webapp/src --package_json /home/ismikin/ubeeqo-dev/webapp/package.json --project_params ./project-options.json --data_report_output --graph_report_output --graph_image
if __name__ == "__main__":
    fire.Fire()
