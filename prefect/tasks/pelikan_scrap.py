from selenium import webdriver
from selenium.webdriver.common.by import By

url = 'https://www.pelikan.cz/cs/akcni-letenka/LCC-1309?a_aid=6fef337b'
CZECH_TO_ENGLISH = {
    'leden': 'January',
    'únor': 'February',
    'březen': 'March',
    'duben': 'April',
    'květen': 'May',
    'červen': 'June',
    'červenec': 'July',
    'srpen': 'August',
    'září': 'September',
    'říjen': 'October',
    'listopad': 'November',
    'prosinec': 'December'
}

# Replace 'path_to_chromedriver' with the actual path to your chromedriver executable
driver = webdriver.Chrome(executable_path='/Users/alejandro.perez/Downloads/chromedriver-mac-x64/chromedriver')  # type: ignore
driver.get(url)
try:
    # Check if the cookie acceptance element is present
    cookie_accept_button = driver.find_element(By.XPATH, "//*[@id='ngAppContainer']/div[4]/div/div[3]/button[3]")

    # Click the cookie acceptance button
    cookie_accept_button.click()

except Exception as e:
    print('No cookie acceptance element found:', e)

try:
    # Find the element containing the title
    title_element = driver.find_elements(By.XPATH, "//*[contains(@class,'month-label')]//span")

    # Extract the text from the element
    months_years = [(title_element[i].text, title_element[i+1].text) for i in range(0, len(title_element), 2)]
    number_of_dates = len(months_years)
    parsed_dates = {
        'number_of_dates': number_of_dates,
        'options': [(CZECH_TO_ENGLISH[combination[0].lower()], combination[1]) for combination in months_years]
    }
    print(parsed_dates)

except Exception as e:
    print('Error:', e)

# Close the WebDriver
driver.quit()
