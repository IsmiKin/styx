from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from pathlib import Path
from pydantic import BaseModel, Field
from humps import camelize
from benedict import benedict

import utils
from dead_code_scanner.logic import scan_file_imports_project, scan_translations_project

# example run: uvicorn api:app --reload
app = FastAPI()


def to_camel(string):
    return camelize(string)


class CamelModel(BaseModel):
    class Config:
        alias_generator = to_camel
        allow_population_by_field_name = True


# TODO: Move into specific api folder and add descriptions
class FileImportReportRequest(CamelModel):
    project_path: str
    package_json: str
    project_options: str


class FileImportReportResponse(CamelModel):
    data_report: dict
    graph_report_data: dict
    stats: dict
    errors: list
    isolates: list


class TranslationsReportRequest(CamelModel):
    project_path: str
    project_params: str
    translations_file: str
    similarity_score_acceptance: float = None
    similarity_ratio_type: str = None


class TranslationsReportResponse(CamelModel):
    data_report: dict
    similars: list
    errors: list
    abandons: list
    interpolations: list


origins = [
    "http://localhost",
    "http://localhost:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.post("/scan-project/file-imports", response_model=FileImportReportResponse)
async def new_scan_project(file_import_report_request: FileImportReportRequest):
    project_path = Path(file_import_report_request.project_path)
    package_json = utils.get_json_content(file_import_report_request.package_json)
    project_options = utils.get_json_content(file_import_report_request.project_options)

    data_report, graph_report_data, errors, isolates, stats = scan_file_imports_project(
        project_path, package_json, project_options
    )

    return {
        "data_report": data_report,
        "graph_report_data": graph_report_data,
        "stats": stats,
        "errors": errors,
        "isolates": isolates,
    }


@app.post("/scan-project/translations", response_model=TranslationsReportResponse)
async def new_scan_project(translations_report_request: TranslationsReportRequest):
    project_path = Path(translations_report_request.project_path)
    project_options = utils.get_json_content(translations_report_request.project_params)
    translations_values = benedict(translations_report_request.translations_file)

    data_report, similars, abandons, interpolations, errors = scan_translations_project(
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
        "interpolations": interpolations,
        "abandons": abandons,
    }
