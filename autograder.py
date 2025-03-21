import getpass
import csv
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.support import expected_conditions as EC
import time
import traceback

grades = {}

###################################################################

# Please add your comments / grades here!
# An example would be:
#        number you type in     grade      comment
# grades[        1         ] = [  8  , "great job $!"]
# Please place a dollar sign ($) where you want the student's
# name to be.
# When you type in the number in the comment box, the grade andb
# comment box will be filled in with the value you specified.

grades[1] = [52, "Great job $!"]

###################################################################

def handle_popup(driver):
    """
    Handles the popup that appears after grading the first student.
    Clicks the 'Do not show again for this assignment' checkbox and 'Proceed' button.
    """
    try:
        # Wait for the popup to appear (if it exists)
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.ID, "unposted_comment_proceed"))
        )
        print("Popup detected.")

        # Click the 'Do not show again for this assignment' checkbox
        do_not_show_checkbox = driver.find_element(By.CSS_SELECTOR, "label.do-not-show-again input[type='checkbox']")
        if not do_not_show_checkbox.is_selected():
            do_not_show_checkbox.click()
            print("Checked 'Do not show again for this assignment'.")

        # Click the 'Proceed' button
        proceed_button = driver.find_element(By.ID, "unposted_comment_proceed")
        proceed_button.click()
        print("Clicked 'Proceed' button.")

    except TimeoutException:
        # If no popup appears, continue without handling it
        print("No popup detected. Proceeding to next student.")
    except Exception as e:
        print(f"An error occurred while handling the popup: {e}")
        traceback.print_exc()

def switch_to_new_tab(driver):
    """
    Switches to the newly opened tab and waits for it to load.
    """
    try:
        # Store the original window handle
        original_window = driver.current_window_handle

        # Wait for a new tab to open
        WebDriverWait(driver, 10).until(EC.number_of_windows_to_be(2))

        # Get all window handles and switch to the new one
        for handle in driver.window_handles:
            if handle != original_window:
                driver.switch_to.window(handle)
                break

        # Wait for an element on the new page (e.g., logo or header) to ensure it's loaded
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "gradebook_header"))
        )
    except Exception as e:
        print(f"Error while switching to new tab: {e}")
        traceback.print_exc()

def click_next_student_and_wait(driver):
    """
    Clicks the 'Next Student' button and waits for the next student's page to load.
    """
    try:
        # Locate and click the "Next Student" button
        next_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "next-student-button"))
        )
        next_button.click()

        # Wait for a unique element on the new page (e.g., grade box or student name)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "ui-selectmenu-item-header"))  # Wait for student name
        )
    except TimeoutException:
        print("Timed out waiting for the next student's page to load.")
        return False  # Indicate failure to load next student
    except Exception as e:
        print(f"An error occurred: {e}")
        traceback.print_exc()
        return False  # Indicate failure

    return True  # Indicate success

def get_student_first_name(driver):
    """
    Extracts the student's first name from the UI element.
    Handles cases where the student name element is not found.
    """
    try:
        # Wait for the student name element to be present
        student_name_element = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CLASS_NAME, "ui-selectmenu-item-header"))
        )
        full_name = student_name_element.text.strip()
        first_name = full_name.split()[0]  # Get the first part of the name before a space
        return first_name
    except TimeoutException:
        print("Error: Student name element not found.")
        return None
    except Exception as e:
        print(f"Error in get_student_first_name(): {e}")
        traceback.print_exc()
        return None

def enter_comment_in_iframe(driver, comment_text):
    """
    Enters the comment into the comment box inside the iframe.
    """
    try:
        # Wait for the iframe to be available and switch to it
        WebDriverWait(driver, 10).until(
            EC.frame_to_be_available_and_switch_to_it((By.ID, "comment_rce_textarea_ifr"))
        )

        # Locate the editable body inside the iframe
        editable_body = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        # Clear any existing content and send the comment
        editable_body.clear()
        editable_body.send_keys(comment_text)

        # Switch back to main content
        driver.switch_to.default_content()

    except TimeoutException:
        print("Error: Timed out waiting for iframe or comment body.")
    except Exception as e:
        print(f"Error in enter_comment_in_iframe(): {e}")
        traceback.print_exc()

if __name__ == "__main__":
    # Credentials
    netid_input = input("Enter your email: ")
    password_input = getpass.getpass("Enter your password: ")

    # Retrieve page & parse
    options = uc.ChromeOptions()
    options.headless = False

    driver = uc.Chrome(
        use_subprocess=False,
        options=options,
    )

    driver.get('https://canvas.uw.edu/')

    # Login to Canvas
    try:
        netid = driver.find_element(By.ID, "weblogin_netid")
        password = driver.find_element(By.ID, "weblogin_password")
        submit_button = driver.find_element(By.ID, "submit_button")

        netid.send_keys(netid_input)
        password.send_keys(password_input)
        submit_button.click()

        # Wait for Canvas dashboard to load (logo element)
        WebDriverWait(driver, 60).until(EC.presence_of_element_located((By.CLASS_NAME, "ic-app-header__logomark")))
    except Exception as e:
        print(f"Login failed: {e}")
        driver.quit()
        exit()

    print("Navigate to the autograder.")
    input("Press Enter when you are ready to continue... (wait until page completely loads)")

    # Check if a new tab is opened and switch focus
    if len(driver.window_handles) > 1:
        switch_to_new_tab(driver)

    while True:
        try:
            # Check if the current student has a submission
            has_submission = True
            try:
                no_submission_element = driver.find_element(By.ID, "this_student_does_not_have_a_submission")
                if no_submission_element.is_displayed():
                    has_submission = False
                    print("This student does not have a submission.")
            except NoSuchElementException:
                pass

            if not has_submission:
                print("Moving to the next student...")
                if not click_next_student_and_wait(driver):
                    print("Failed to load next student. Exiting loop.")
                    break
                continue

            # Wait for user input in terminal for grading
            user_input = input("Enter a number corresponding to a grade (or type 'exit' to quit): ").strip()

            if user_input.lower() == "exit":
                print("Exiting...")
                break

            # Convert input to integer and fetch grade/comment from dictionary
            grade_key = int(user_input)
            if grade_key not in grades:
                print(f"No grade/comment found for key: {grade_key}")
                continue

            grade, comment_template = grades[grade_key]

            # Extract student's first name from the UI element
            first_name = get_student_first_name(driver)
            if not first_name:
                print("Skipping student due to missing name.")
                if not click_next_student_and_wait(driver):
                    print("Failed to load next student. Exiting loop.")
                    break
                continue

            # Replace $ in comment template with the student's first name
            comment_text = comment_template.replace("$", first_name)

            # Fill in the grade box
            grade_box = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "grading-box-extended"))
            )
            grade_box.clear()  # Clear any existing value
            grade_box.send_keys(str(grade))

            # Enter comment in the comment box inside iframe
            enter_comment_in_iframe(driver, comment_text)

            # Click the submit button
            submit_button = WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable((By.ID, "comment_submit_button"))
            )
            submit_button.click()

            # Handle popup if it appears
            handle_popup(driver)

            # Proceed to next student
            if not click_next_student_and_wait(driver):
                print("Failed to load next student. Exiting loop.")
                break

        except Exception as e:
            print(f"An error occurred: {e}")
            traceback.print_exc()

    # Close browser after exiting loop
    driver.quit()
