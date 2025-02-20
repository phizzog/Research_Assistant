import sys
import PyPDF2

def remove_pages(input_pdf_path, output_pdf_path):
    # Open the input PDF in read-binary mode.
    with open(input_pdf_path, 'rb') as infile:
        reader = PyPDF2.PdfReader(infile)
        writer = PyPDF2.PdfWriter()
        
        total_pages = len(reader.pages)
        print(f"Total pages in input PDF: {total_pages}")
        
        # Loop through all pages.
        for i in range(total_pages):
            # Remove pages 1-23 (indices 0-22) and 281-382 (indices 280-381)
            if i < 23 or (280 <= i <= 381):
                continue
            writer.add_page(reader.pages[i])
        
        # Write out the new PDF.
        with open(output_pdf_path, 'wb') as outfile:
            writer.write(outfile)
            
    print(f"New PDF with selected pages written to '{output_pdf_path}'.")

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: python script.py input.pdf output.pdf")
        sys.exit(1)
    
    input_pdf = sys.argv[1]
    output_pdf = sys.argv[2]
    
    remove_pages(input_pdf, output_pdf)
