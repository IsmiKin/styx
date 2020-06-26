from fastapi import FastAPI
from pathlib import Path
from pydantic import BaseModel, Field
from benedict import benedict

import utils
from dead_code_scanner.logic import scan_file_imports_project, scan_translations_project

# example run: uvicorn api:app --reload
app = FastAPI()

# TODO: Move into specific api folder and add descriptions
class FileImportReportRequest(BaseModel):
    project_path: str
    package_json: str
    project_params: str


class FileImportReportResponse(BaseModel):
    data_report: dict
    stats: dict
    errors: list
    isolates: list


class TranslationsReportRequest(BaseModel):
    project_path: str
    project_params: str
    translations_file: str
    similarity_score_acceptance: float = None
    similarity_ratio_type: str = None


class TranslationsReportResponse(BaseModel):
    data_report: dict
    similars: list
    errors: list
    abandons: list


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.post("/scan-project/file-imports", response_model=FileImportReportResponse)
async def new_scan_project(file_import_report_request: FileImportReportRequest):
    project_path = Path(file_import_report_request.project_path)
    package_json = utils.get_json_content(file_import_report_request.package_json)
    project_options = utils.get_json_content(file_import_report_request.project_params)

    data_report, graph_report_data, errors, isolates, stats = scan_file_imports_project(
        project_path, package_json, project_options
    )

    return {
        "data_report": data_report,
        "stats": stats,
        "errors": errors,
        "isolates": isolates,
    }


@app.post("/scan-project/translations", response_model=TranslationsReportResponse)
async def new_scan_project(translations_report_request: TranslationsReportRequest):
    project_path = Path(translations_report_request.project_path)
    project_options = utils.get_json_content(translations_report_request.project_params)
    translations_values = benedict(translations_report_request.translations_file)

    data_report, similars, abandons, errors = scan_translations_project(
        project_path,
        project_options,
        translations_values,
        translations_report_request.similarity_score_acceptance,
        translations_report_request.similarity_ratio_type,
    )

    return {
        "data_report": data_report,
        "similars": similars,
        "errors": errors,
        "abandons": abandons,
    }
