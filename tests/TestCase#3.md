### Test case Download Quiz in txt Format1

Scenario: The system provides an option to download the quiz in txt format.
Expected Outcome: The quiz should be downloaded as a .txt file, and the content should match the generated questions, formatted correctly for easy readability and editing.

### Test case Download Quiz in PDF Format 2
Download Quiz in PDF Format
Scenario: The system provides an option to download the quiz in PDF format.
Precondition: The user has successfully generated a quiz.

Expected Outcome: The quiz should be downloaded as a .pdf file, and the content should match the generated questions, formatted clearly for easy viewing and printing.


### Test 3
Sequential Question Formatting
Step: Download the generated txt file.
Expected Outcome: The questions are numbered sequentially and grouped appropriately.

### Test 4
Export Time Performance
Step: Generate and download a quiz of 50 questions.
Expected Outcome: The txt file is generated and downloaded within 3 seconds.
### Test 5
Metadata Check
Step: Inspect the metadata of the downloaded txt file.
Expected Outcome: The file should not contain unnecessary metadata or sensitive information.
### Test 6
Step: Attempt to download the quiz without content
Expected Outcome: The button would not be available 
### Test 7
Download Quiz as PDF Button Presence
Step: Navigate to the quiz summary page.
Expected Outcome: The "Download as PDF" button should be visible.
### Test 8
Download as txt
Step: Click on the "Download as txt" button.
Expected Outcome: The system generates and downloads a .txt file with the quiz questions.
### Test 9
PDF Formatting Validation
Step: Download the generated PDF file.
Expected Outcome: The questions in the PDF are clearly formatted, numbered sequentially, and grouped by sections where applicable.
### Test 10
Quiz Question Count Validation
Step: Submit input text to generate a quiz.
Expected Outcome: The number of questions generated should be between 5 and 20, depending on the provided content.
### Test 11
System Availability Check
Step: Attempt to download a quiz during different times of the day.
Expected Outcome: The system should maintain 99.9% availability for download functionality.
### Test 12
Input Validation for Quiz Generation
Step: Submit an empty file as input to the quiz generation endpoint.
Expected Outcome: The system should respond with a 400 Bad Request status code indicating invalid input.
### Test 13
Max file Limit Validation
Step: Submit more than 2 file is not allowed
Expected Outcome: The system should respond with a max limit for this quiz
### Test 14
Invalid File Format Request
Step: Attempt to download the quiz in an unsupported file format (e.g., .xlsx).
Expected Outcome: The system should respond with a 400 Bad Request status code indicating unsupported format.
### Test 15
Concurrent Download Requests
Step: Initiate multiple download requests simultaneously 
Expected Outcome: All requests should be processed successfully without performance degradation.
### Test 16
Download Rate Limiting
Step: Attempt to download the quiz repeatedly within a short time frame.
Expected Outcome: The system should enforce rate limiting to prevent abuse and respond with a 429 Too Many Requests status code if the limit is exceeded.
### Test 17
Quiz Content Integrity Check
Step: Download the quiz in both DOCX and PDF formats.
Expected Outcome: Verify that the content of both files matches and there are no discrepancies between formats.
### Test 18
Verify file ends with .txt
Steps: Download quiz as txt
Expected outcome: File should have .txt at end of file
### Test 19 
Verify file ends with .pdf
Steps: Download quiz as pdf
Expected Outcome: File should have .pdf at end of file
### Test 20
Verify file isnt corrupted
Steps: download quiz as either txt or pdf and open file
Expected Outcome: File should open with having any issues

