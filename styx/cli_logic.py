from pathlib import Path
import ujson

import utils

DATA_REPORT_FILE_EXTENSION = "json"
FILE_IMPORTS_REPORT_NAME = "file_imports_report"
GRAPH_DATA_REPORT_NAME = "graph_data_report"
GRAPH_IMAGE = "graph-image"

log = utils.get_logger()


def get_output_filename(
    cli_argument, output_type, random_file_prefix, file_extension=""
):
    return (
        Path("{}--{}.{}".format(output_type, random_file_prefix, file_extension))
        if isinstance(cli_argument, bool)
        else Path(cli_argument)
    )


def save_report_file(
    data_report,
    output_filename_cli_argument,
    data_report_name,
    random_file_prefix,
    overrides,
):
    output_report_file = get_output_filename(
        output_filename_cli_argument,
        data_report_name,
        random_file_prefix,
        DATA_REPORT_FILE_EXTENSION,
    )

    if overrides and output_report_file.exists():
        output_report_file.unlink()

    with open(output_report_file, "w") as output_file:
        ujson.dump(data_report, output_file, escape_forward_slashes=False, indent=2)

    log.info("Saved {} data report on {}".format(data_report_name, output_report_file))
