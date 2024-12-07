### Test 1 
Download Quiz in txt Format
- PreCondition: Quiz is generated already
- Step: User clicks button to download that is presented
- Expected Outcome: The quiz should be downloaded as a .txt file, and the content should match the generated questions, formatted correctly for easy readability and editing.
- Wrong outcome: Quiz is not downloadable

### Test 2 
Download Quiz in PDF Format
- PreCondition: Quiz is generated already
- Steps: User clicks on button to download
- Expected Outcome: The quiz should be downloaded as a .pdf file
- Wrong outcome: Quiz is not downloadable


### Test 3
Sequential Question Formatting
- Step: Download the generated txt or pdf file.
- Expected Outcome: The questions are numbered sequentially and grouped appropriately.
- Negative Outcome: Question are formatted incorrectly Ex:Q2,Q5,Q1

### Test 4
Export Time Performance
- Step: Generate and download a quiz of 40 questions.
- Expected Outcome: The txt or pdf file is generated and downloaded within 3 seconds.
- Negative Outcome: Takes longer that 3 seconds or crashes

### Test 5
Metadata Check
- Step: Inspect the metadata of the downloaded txt or pdf file.
- Expected Outcome: The file should not contain unnecessary metadata or sensitive information.
- Negative Outcome: The file contains extra Data not relavent to prompt. 

### Test 6
No genertaed quiz
- Step: Attempt to download the quiz without content
- Expected Outcome: The button would not be available 
- Negative Outcome: button is available and provides an empty file

### Test 7
Download Quiz as PDF Button Presence
- Step: Navigate to the dowload button
- Expected Outcome: The "Download as PDF" button should be visible.
- Negative OutcomeL Button is not visible and user cannot download as pdf

### Test 8
Download as txt
- Step: Navigate to download button
- Expected Outcome: User clicks on button and .txt file is downloaded
- Negative Outcome: Button is not avaiable and user cannot download as .txt

### Test 9
Formatting Validation
- Step: Download the generated PDF or txt file.
- Expected Outcome: The questions in the PDF or txt are clearly formatted, numbered sequentially, and grouped by sections where applicable.
- Negative Outcome: The questions are not correctly formatted in .pdf EX incomplete sentences or incorrect formating of questions

### Test 10
Quiz Question Count Validation
- Step: Submit input text to generate a quiz.
- Expected Outcome: The number of questions generated should be between 5 and 40, depending on the range user provided.
- Negative Outcome: the number of question are less or beyond what the user asked for

### Test 11
System Availability Check
- Step: Attempt to download a quiz during different times of the day.
- Expected Outcome: The system should maintain 99.9% availability for download functionality.
- Negative Outcome: System download fuction is down and user can not longer download

### Test 12
File Name 
- Step: User download file
- Expected Outcome: File name should be quiz
- Negative Outcome: file name is empty or is not quiz

### Test 13
Max file Limit Validation
- Step: Download more than 2 file is not allowed
- Expected Outcome: The system should respond with a max limit for this quiz
- Negative Outcome: User can download more than 2 file 

### Test 14
Invalid File Format Request
- Step: Attempt to download the quiz in an unsupported file format (e.g., .xlsx).
- Expected Outcome: The option should is not going to be available
- Negative outcome: Request is sent and internal server error occurs

### Test 15
Concurrent Download Requests
- Step: Initiate multiple download requests simultaneously 
- Expected Outcome: All requests should be processed successfully without performance degradation.
- Negative Ourcome: User are not allowed to download both a txt and odf at the same time

### Test 16
Download Rate Limiting
- Step: Attempt to download the quiz repeatedly within a short time frame.
- Expected Outcome: The system should enforce rate limiting to prevent abuse and respond with a 429 Too Many Requests status code if the limit is exceeded.
- Negative Outcome: User can spam the button to download with can lead to overload in the server

### Test 17
Quiz Content Integrity Check
- Step: Download the quiz in both TXT and PDF formats.
- Expected Outcome: Verify that the content of both files matches and there are no discrepancies between formats.
- Negative Outcome: Both file have very different context and different questions

### Test 18
Verify file ends with .txt
- Steps: Download quiz as txt
- Expected outcome: File should have .txt at end of file
- Negative Outcome: File does not end with .txt and user may not be able to open

### Test 19 
Verify file ends with .pdf
- Steps: Download quiz as pdf
- Expected Outcome: File should have .pdf at end of file
- Negative Outcome: File does not end with .pdf and user may not be able to open

### Test 20
Verify file isnt corrupted
- Steps: download quiz as either txt or pdf and open file
- Expected Outcome: File should open with having any issues
- Negative Outcome: File cannot be open and quiz data is lost

