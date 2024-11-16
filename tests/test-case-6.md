# Test Case for User Story 6 - Inputting Text

## Description
As a client, I want the quiz generator to allow me to input text, so it can automatically generate a quiz with relevant questions based on the provided information. This will save me time and effort by creating questions that are directly aligned with the content I provide.

----

## Acceptance Criteria 1: Text Input Area and Content Length
The quiz generator must provide a clear text input area where clients can paste or type the information they want to use for quiz generation. The system should support a content length of up to 10,000 characters for generating quiz questions.
1. **Test Case 1.1: Text Input Functionality**
   - **Description:** Verify that the text input area is present and accepts text input.
   - **Steps:**
     1. Open the quiz generator interface.
     2. Locate the text input area.
     3. Type or paste sample text.
   - **Expected Result:** Text input area is visible and accepts input.

2. **Test Case 1.2: Maximum Content Length**
   - **Description:** Verify that the system accepts and processes up to 10,000 characters.
   - **Steps:**
     1. Paste text with 10,000 characters into the input area.
     2. Submit for quiz generation.
   - **Expected Result:** The system accepts input and generates a quiz without errors.

3. **Test Case 1.3: Exceeding Maximum Length**
   - **Description:** Verify that the system handles input exceeding 10,000 characters.
   - **Steps:**
     1. Paste text with 10,001 characters into the input area.
     2. Submit for quiz generation.
   - **Expected Result:** The system rejects the input and displays an error message.

---

## Acceptance Criteria 2: Quiz Question Generation
The quiz generator must be able to create at least 5 and up to 20 relevant questions based on the provided text.
1. **Test Case 2.1: Minimum Questions**
   - **Description:** Verify that at least 5 questions are generated for valid input.
   - **Steps:**
     1. Enter a valid text input (e.g., 500 characters).
     2. Submit for quiz generation.
   - **Expected Result:** At least 5 relevant questions are generated.

2. **Test Case 2.2: Maximum Questions**
   - **Description:** Verify that no more than 20 questions are generated, even for large input.
   - **Steps:**
     1. Enter a large text input (e.g., 10,000 characters).
     2. Submit for quiz generation.
   - **Expected Result:** A maximum of 20 relevant questions are generated.

3. **Test Case 2.3: Relevance of Questions**
   - **Description:** Verify that the generated questions are relevant to the input text.
   - **Steps:**
     1. Enter a specific text with clear context.
     2. Submit for quiz generation.
   - **Expected Result:** The generated questions are closely related to the input content.

---

## Acceptance Criteria 3: Performance, Usability, and Reliability
Performance Efficiency: The quiz should be generated within 5 seconds for an average input size of 5,000 characters.
Usability: The text input area must be prominently displayed, easy to use, and include placeholder text or instructions to guide users on the type of content they should input.
Reliability: The system should be capable of handling submissions without crashing or slowing down significantly, ensuring a 99.9% uptime.
1. **Test Case 3.1: Performance for Average Input**
   - **Description:** Verify that quiz generation takes less than 5 seconds for 5,000 characters.
   - **Steps:**
     1. Enter a 5,000-character text input.
     2. Measure the time taken for quiz generation.
   - **Expected Result:** The quiz is generated within 5 seconds.

2. **Test Case 3.2: Usability of Text Input Area**
   - **Description:** Verify that the input area includes placeholder text or instructions.
   - **Steps:**
     1. Locate the input area.
     2. Check for placeholder text or instructions.
   - **Expected Result:** Placeholder text or instructions guide the user on input expectations.

3. **Test Case 3.3: Reliability Under Load**
   - **Description:** Verify that the system remains stable when multiple simultaneous submissions are made.
   - **Steps:**
     1. Perform 10 concurrent submissions of 10,000-character input.
   - **Expected Result:** The system handles all submissions without crashing or significant delays.

---

## Acceptance Criteria 4: Formatting of Generated Questions
The generated questions should be formatted clearly, including numbering and proper spacing for readability.
1. **Test Case 4.1: Proper Numbering**
   - **Description:** Verify that the generated questions are numbered sequentially.
   - **Steps:**
     1. Submit valid input text.
     2. Check the numbering of the generated questions.
   - **Expected Result:** Questions are numbered sequentially (e.g., 1, 2, 3...).

2. **Test Case 4.2: Proper Spacing**
   - **Description:** Verify that the generated questions are clearly spaced for readability.
   - **Steps:**
     1. Submit valid input text.
     2. Observe the formatting of the questions.
   - **Expected Result:** Questions are spaced appropriately, ensuring readability.

---

## Metrics Testing
Metric: Maximum size of text that can be processed without slowing the system.
Target: Up to 10,000 characters without performance issues.
1. **Test Case M1: Performance for Maximum Input**
   - **Description:** Verify that the system processes 10,000 characters without significant performance issues.
   - **Steps:**
     1. Paste a 10,000-character input.
     2. Measure the response time and system stability.
   - **Expected Result:** The system processes the input within acceptable limits (e.g., <5 seconds) without slowing down.

2. **Test Case M2: Stability Under Heavy Load**
   - **Description:** Verify system stability with high-volume usage.
   - **Steps:**
     1. Simulate 100 users submitting quizzes simultaneously.
   - **Expected Result:** The system maintains performance and uptime without degradation.

---

## Notes
- These test cases focus on functional, performance, usability, and reliability aspects of the quiz generator.
- Additional edge cases and exploratory testing may be needed based on system behavior during real-world use.