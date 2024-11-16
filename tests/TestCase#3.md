### Test case Download Quiz in DOCX Format

Scenario: The system provides an option to download the quiz in DOCX format.

Precondition: The user has successfully generated a quiz.

Steps:

Generate a quiz using the provided text input.

Click the "Download as DOCX" button.

Confirm that the file is downloaded in DOCX format.

Expected Outcome: The quiz should be downloaded as a .docx file, and the content should match the generated questions, formatted correctly for easy readability and editing.

### Test case Download Quiz in PDF Format
Download Quiz in PDF Format

Scenario: The system provides an option to download the quiz in PDF format.

Precondition: The user has successfully generated a quiz.

Steps:

Generate a quiz using the provided text input.

Click the "Download as PDF" button.

Confirm that the file is downloaded in PDF format.

Expected Outcome: The quiz should be downloaded as a .pdf file, and the content should match the generated questions, formatted clearly for easy viewing and printing.

### Test case backend DOCX

Download Quiz as DOCX Endpoint
Scenario: The backend should provide an endpoint to generate a DOCX version of the quiz.
Endpoint: /api/download-quiz-docx (POST)

Request Body:

{
  "questions": [
    "Question 1?",
    "Question 2?",
    "...",
    "Question N?"
  ]
}

Expected Response:
Status Code: 200 OK
Response Body: Binary content representing the DOCX file.

Validation:
Verify that the file content is in the correct DOCX format.
Verify that the downloaded document contains all provided questions in a readable format.

### Test case backend PDF

Download Quiz as PDF Endpoint
Scenario: The backend should provide an endpoint to generate a PDF version of the quiz.
Endpoint: /api/download-quiz-pdf (POST)

Request Body:

{
  "questions": [
    "Question 1?",
    "Question 2?",
    "...",
    "Question N?"
  ]
}

Expected Response:
Status Code: 200 OK

Response Headers:
Content-Disposition: attachment; filename="quiz.pdf"
Response Body: Binary content representing the PDF file.

Validation:
Verify that the file content is in the correct PDF format.
Verify that the downloaded document contains all provided questions, formatted correctly for readability and printing.