from fastapi import FastAPI
from pathlib import Path
from pydantic import BaseModel

import utils
from dead_code_scanner.logic import scan_file_imports_project

# example run: uvicorn api:app --reload
app = FastAPI()

# TODO: Move into specific api folder
class FileImportReportRequest(BaseModel):
    project_path: str
    package_json: str
    project_params: str


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.post("/scan-project/file-imports")
async def new_scan_project(file_import_report_request: FileImportReportRequest):
    project_path = Path(file_import_report_request.project_path)
    package_json = utils.get_json_content(file_import_report_request.package_json)
    project_options = utils.get_json_content(file_import_report_request.project_params)

    data_report, graph_report_data, errors, isolates, stats = scan_file_imports_project(
        project_path, package_json, project_options
    )

    return data_report
