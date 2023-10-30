import os
import pdfplumber
from flask import Flask, request, render_template, send_file
import tempfile

app = Flask(__name__)

def extract_text_from_pdf(pdf_file, separator="<<<<<<------------------------------------------ NEXT PAGE ------------------------------------------>>>>>>"):
    text = ""
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text(x_tolerance=2)
            text += page_text + f"\n{separator}\n"
    return text

@app.route('/', methods=['GET', 'POST'])
def ocr_pdf():
    if request.method == 'POST':
        uploaded_file = request.files['pdf_file']
        if uploaded_file:
            # Create a temporary directory
            with tempfile.TemporaryDirectory() as temp_dir:
                file_path = os.path.join(temp_dir, uploaded_file.filename)
                uploaded_file.save(file_path)

                if 'convert' in request.form:
                    # Convert to grayscale
                    grayscale_pdf = os.path.join(temp_dir, 'grayscale.pdf')
                    os.system(f'gs -sOutputFile="{grayscale_pdf}" -sDEVICE=pdfwrite -sColorConversionStrategy=Gray -dProcessColorModel=/DeviceGray -dCompatibilityLevel=1.4 -dNOPAUSE -dBATCH -dDownsampleMonoImages=true -dMonoImageDownsampleType=/Bicubic -dMonoImageResolution=2400 -dMonoImageDepth=1 "{file_path}"')
                    
                    # Send the grayscale PDF as a response for download
                    original_filename, original_extension = os.path.splitext(uploaded_file.filename)
                    download_name = f"{original_filename} (GRAYSCALE){original_extension}"
                    return send_file(grayscale_pdf, as_attachment=True, download_name=download_name)


                elif 'run' in request.form:
                    # Run OCR
                    grayscale_pdf = os.path.join(temp_dir, 'grayscale.pdf')
                    os.system(f'gs -sOutputFile="{grayscale_pdf}" -sDEVICE=pdfwrite -sColorConversionStrategy=Gray -dProcessColorModel=/DeviceGray -dCompatibilityLevel=1.4 -dNOPAUSE -dBATCH -dDownsampleMonoImages=true -dMonoImageDownsampleType=/Bicubic -dMonoImageResolution=1200 -dMonoImageDepth=-1 "{file_path}"')

                    # Run OCR on the enhanced PDF
                    os.system(f'ocrmypdf "{grayscale_pdf}" "{grayscale_pdf}"')

                    text = extract_text_from_pdf(grayscale_pdf)
                    lines = text.split('\n')

                    # Send the OCR result as a response for download
                    return render_template('result.html', text=text, lines=lines)

    return render_template('upload.html')

if __name__ == '__main__':
    app.run(debug=True)
