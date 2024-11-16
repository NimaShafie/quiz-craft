### Test case Download Quiz in DOCX Format1

Scenario: The system provides an option to download the quiz in DOCX format.
Expected Outcome: The quiz should be downloaded as a .docx file, and the content should match the generated questions, formatted correctly for easy readability and editing.

### Test case Download Quiz in PDF Format 2
Download Quiz in PDF Format
Scenario: The system provides an option to download the quiz in PDF format.
Precondition: The user has successfully generated a quiz.

Expected Outcome: The quiz should be downloaded as a .pdf file, and the content should match the generated questions, formatted clearly for easy viewing and printing.

### Test case backend DOCX 3

Download Quiz as DOCX Endpoint
Scenario: The backend should provide an endpoint to generate a DOCX version of the quiz.
Endpoint: /api/download-quiz-docx (POST)

Validation:
Verify that the file content is in the correct DOCX format.
Verify that the downloaded document contains all provided questions in a readable format.

### Test case backend PDF 4

Download Quiz as PDF Endpoint
Scenario: The backend should provide an endpoint to generate a PDF version of the quiz.
Endpoint: /api/download-quiz-pdf (POST)

Expected outcome:
Verify that the file content is in the correct PDF format.
Verify that the downloaded document contains all provided questions, formatted correctly for readability and printing.

### Test 5
Sequential Question Formatting
Step: Download the generated DOCX file.
Expected Outcome: The questions are numbered sequentially and grouped appropriately.

### Test 6
Export Time Performance
Step: Generate and download a quiz of 50 questions.
Expected Outcome: The DOCX file is generated and downloaded within 3 seconds.
### Test 7
Metadata Check
Step: Inspect the metadata of the downloaded DOCX file.
Expected Outcome: The file should not contain unnecessary metadata or sensitive information.
### Test 8
Unauthorized Download Attempt
Step: Attempt to download the quiz without authentication.
Expected Outcome: The system should reject the request with a 401 Unauthorized status code.
### Test 9
Download Quiz as PDF Button Presence
Step: Navigate to the quiz summary page.
Expected Outcome: The "Download as PDF" button should be visible.
### Test 10
Download as PDF
Step: Click on the "Download as PDF" button.
Expected Outcome: The system generates and downloads a .pdf file with the quiz questions.
### Test 11
PDF Formatting Validation
Step: Download the generated PDF file.
Expected Outcome: The questions in the PDF are clearly formatted, numbered sequentially, and grouped by sections where applicable.
### Test 12
Quiz Question Count Validation
Step: Submit input text to generate a quiz.
Expected Outcome: The number of questions generated should be between 5 and 20, depending on the provided content.
### Test 13
System Availability Check
Step: Attempt to download a quiz during different times of the day.
Expected Outcome: The system should maintain 99.9% availability for download functionality.
### Test 14
Input Validation for Quiz Generation
Step: Submit an empty string as input to the quiz generation endpoint.
Expected Outcome: The system should respond with a 400 Bad Request status code indicating invalid input.
### Test 15
Max Character Limit Validation
Step: Submit input text exceeding the maximum character limit allowed (e.g., 10,000 characters).
Expected Outcome: The system should respond with a 400 Bad Request status code and an appropriate error message.
### Test 16
Invalid File Format Request
Step: Attempt to download the quiz in an unsupported file format (e.g., .xlsx).
Expected Outcome: The system should respond with a 400 Bad Request status code indicating unsupported format.
### Test 17
Concurrent Download Requests
Step: Initiate multiple download requests simultaneously as an authenticated user.
Expected Outcome: All requests should be processed successfully without performance degradation.
### Test 18
Download Rate Limiting
Step: Attempt to download the quiz repeatedly within a short time frame.
Expected Outcome: The system should enforce rate limiting to prevent abuse and respond with a 429 Too Many Requests status code if the limit is exceeded.
### Test 19
Quiz Content Integrity Check
Step: Download the quiz in both DOCX and PDF formats.
Expected Outcome: Verify that the content of both files matches and there are no discrepancies between formats.
### Test 20
Special Characters Handling
Step: Submit input text with special characters and emojis to generate a quiz.
Expected Outcome: The generated quiz should correctly display special characters without errors in both DOCX and PDF formats.