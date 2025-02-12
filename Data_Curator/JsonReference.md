Root Object ({ ... }): The entire JSON data is enclosed in curly braces, indicating a JSON object.

"document" Object:

Contains metadata about the PDF document itself.

"document_id": A string representing the document's ID (often the filename).

"filename": A string, the name of the PDF file.

"total_pages": An integer, the total number of pages in the PDF.

"metadata": Another nested JSON object containing specific metadata properties:

"Title", "Author", "Creator", "Producer": Strings representing document metadata.

"CreationDate", "ModDate": Strings representing creation and modification dates in a specific PDF date format.

"pages" Array ([ ... ]):

Contains an array of JSON objects, where each object represents a page from the PDF.

Each object in the "pages" array has the following properties:

"page_id": A string, the ID of the page (e.g., "page_1").

"pdf_title": A string, the title of the PDF document (repeated for each page).

"text": A string, the textual content extracted from the page.

"tables": An array of JSON objects, each representing a table found on the page.

Each table object has:

"table_id": A string, the ID of the table (e.g., "table_38_1").

"data": A 2D array of strings, representing the table's rows and cells.