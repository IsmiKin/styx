from fastapi import FastAPI
from pathlib import Path

from dead_code_scanner.logic import scan_project

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.post("/scan-project")
async def new_scan_project():
    project_path = "/home/ismikin/ubeeqo-dev/webapp/src"
    package_json = "/home/ismikin/ubeeqo-dev/webapp/package.json"
    project_params = "./project-options.json"
    project_path = Path(project_path)

    data_report, graph_report_data = scan_project(
        project_path, package_json, project_params
    )

    return data_report
