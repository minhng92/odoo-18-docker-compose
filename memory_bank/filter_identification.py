from PIL import Image
import openpyxl
import os

def identify_filters(image_path, output_file):
    # Open the image file
    image = Image.open(image_path)

    # Create a new Excel workbook and select the active worksheet
    workbook = openpyxl.Workbook()
    worksheet = workbook.active

    # Write the header row
    worksheet.append(['Model', 'Brand', 'Description'])

# Basic OCR implementation to extract text from the image
from PIL import Image
import pytesseract
import openpyxl
import os

def identify_filters(image_path, output_file):
    # Open the image file
    image = Image.open(image_path)

    # Use pytesseract to extract text from the image
    text = pytesseract.image_to_string(image)

    # Create a new Excel workbook and select the active worksheet
    workbook = openpyxl.Workbook()
    worksheet = workbook.active

    # Write the header row
    worksheet.append(['Model', 'Brand', 'Description'])

    # Process the extracted text to identify filters
    # This is a simplified example - you'll need to adapt it to your specific image
    lines = text.split('\n')
    for line in lines:
        if 'Filter' in line or 'Filtro' in line:
            parts = line.split()
            if len(parts) >= 3:
                model = parts[0]
                brand = parts[1] if len(parts) > 1 else 'Unknown'
                description = ' '.join(parts[2:]) if len(parts) > 2 else 'No description'
                worksheet.append([model, brand, description])

    # Save the workbook
    workbook.save(output_file)

    # Save the workbook
    workbook.save(output_file)

if __name__ == "__main__":
    image_path = "memory_bank/filtros1.jpg"
    output_file = "filters.xlsx"
    identify_filters(image_path, output_file)
    print(f"Filter identification complete. Results saved to {output_file}")
