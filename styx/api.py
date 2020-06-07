from fastapi import FastAPI
from pathlib import Path

import utils
from dead_code_scanner.logic import scan_project

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.post("/scan-project")
async def new_scan_project():
    project_path = "/home/ismikin/ubeeqo-dev/webapp/src"
    package_json = "/home/ismikin/ubeeqo-dev/webapp/package.json"
    project_params = "/home/ismikin/projects/styx/project-options.json"
    project_path = Path(project_path)

    package_json = utils.get_json_content(package_json)
    project_options = utils.get_json_content(project_params)

    data_report, graph_report_data, errors, isolates, stats = scan_project(
        project_path, package_json, project_options
    )

    return data_report
