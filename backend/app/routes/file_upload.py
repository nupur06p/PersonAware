from fastapi import APIRouter, File, UploadFile, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from starlette.requests import Request
from app.models import spacy_model, nltk_model, hft_model
import pypandoc
import time
import subprocess

router = APIRouter()

templates = Jinja2Templates(directory="app/templates")


def convert_with_calibre(input_file: str, output_file: str) -> None:
    """
    Conversão de ficheiro para plain text através de Calibre's ebook-convert tool.
    """
    command = ["ebook-convert", input_file, output_file]
    subprocess.run(command, check=True)


def convert_with_pandoc(input_file: str, output_file: str) -> None:
    """
    Conversão de ficheiro para plain text através de Pandoc.
    """
    import pypandoc
    pypandoc.convert_file(input_file, 'plain', outputfile=output_file)


@router.post("/uploadfile/")
async def upload_file(request: Request, file: UploadFile = File(...), library: str = Form(...)):
    file_location = f"./{file.filename}"

    with open(file_location, "wb") as f:
        f.write(await file.read())

    output_file_location = file_location.rsplit('.', 1)[0] + '.txt'

    start_conversion_time = time.time()
    pypandoc.convert_file(file_location, 'plain',
                          outputfile=output_file_location)
    end_conversion_time = time.time()
    conversion_time = end_conversion_time - start_conversion_time

    with open(output_file_location, "r", encoding="utf-8") as f:
        text_content = f.read()

    start_processing_time = time.time()
    if library == 'spaCy':
        entities = spacy_model.process_with_spacy(text_content)
    elif library == 'NLTK':
        entities = nltk_model.process_with_nltk(text_content)
    elif library == 'HFT':
        entities = hft_model.process_with_hft(text_content)
    else:
        return {"error": "Invalid library chosen."}
    end_processing_time = time.time()
    processing_time = end_processing_time - start_processing_time

    return templates.TemplateResponse("results.html", {
        "request": request,
        "filename": file.filename,
        "conversion_time": conversion_time,
        "processing_time": processing_time,
        "entities": entities
    })


@router.get("/")
async def main(request: Request):
    return templates.TemplateResponse("form.html", {"request": request})
