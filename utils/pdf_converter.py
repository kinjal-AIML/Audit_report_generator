import subprocess


def convert_to_pdf(docx_path):

    subprocess.run([
        'libreoffice',
        '--headless',
        '--convert-to',
        'pdf',
        docx_path
    ])