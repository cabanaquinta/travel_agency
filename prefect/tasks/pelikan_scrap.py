from selenium import webdriver
from selenium.webdriver.common.by import By

url = "https://www.pelikan.cz/cs/akcni-letenka/LCC-1309?a_aid=6fef337b"

# Replace 'path_to_chromedriver' with the actual path to your chromedriver executable
driver = webdriver.Chrome(executable_path='/Users/alejandro.perez/Downloads/chromedriver-mac-x64/chromedriver')
driver.get(url)
try:
    # Check if the cookie acceptance element is present
    cookie_accept_button = driver.find_element(By.XPATH, "//*[@id='ngAppContainer']/div[4]/div/div[3]/button[3]")

    # Click the cookie acceptance button
    cookie_accept_button.click()

except Exception as e:
    print("No cookie acceptance element found:", e)

try:
    # Find the element containing the title
    title_element = driver.find_elements(By.XPATH, "//*[contains(@class,'month-label')]//span")

    # Extract the text from the element
    title_text = [(e.text for e in title_element[i:i+2]) for i in range(0,len(title_element),2)]

    # [(e.text, title_element[i + 1].text) for i, e in enumerate(title_element, start=0) if i < len(title_element) - 1]
    # [e.text for e in title_element]
    print("Title:", title_text)
    print([(e.text) for e in title_element ])

except Exception as e:
    print("Error:", e)

# Close the WebDriver
driver.quit()