#login.py
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from tempfile import mkdtemp

def login(user_dgr, password_dgr):
    try:
        chrome_options = ChromeOptions()
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-dev-tools")
        chrome_options.add_argument("--no-zygote")
        chrome_options.add_argument("--single-process")
        chrome_options.add_argument(f"--user-data-dir={mkdtemp()}")
        chrome_options.add_argument(f"--data-path={mkdtemp()}")
        chrome_options.add_argument(f"--disk-cache-dir={mkdtemp()}")
        chrome_options.add_argument("--remote-debugging-pipe")
        chrome_options.add_argument("--verbose")
        chrome_options.add_argument("--log-path=/tmp")
        chrome_options.binary_location = "/opt/chrome/chrome-linux64/chrome"

        # Add download preferences to automatically save files to /tmp
        prefs = {
            "download.default_directory": "/tmp",  # Use the Lambda tmp directory
            "download.prompt_for_download": False,  # Don't prompt for download
            "download.directory_upgrade": True,  # Automatically download to the specified directory
            "safebrowsing.enabled": True  # Enable safe browsing (could be needed for headless mode)
        }
        chrome_options.add_experimental_option("prefs", prefs)

        service = Service(
        executable_path="/opt/chrome-driver/chromedriver-linux64/chromedriver",
        service_log_path="/tmp/chromedriver.log"
        )

        driver = webdriver.Chrome(
            service=service,
            options=chrome_options)
       
        ########## LOGIN ###################
        driver.get("https://www.dgr.gub.uy/sr/principal.jsf")
        
        # Encuentra y llena el campo de usuario
        username_field = driver.find_element(By.ID, "j_username")
        username_field.send_keys(user_dgr)  # Reemplaza con el usuario que quieras ingresar
        
        # Encuentra y llena el campo de contraseña
        password_field = driver.find_element(By.ID, "j_password")
        password_field.send_keys(password_dgr)  # Reemplaza con la contraseña que quieras ingresar
        
        login_button = driver.find_element(By.XPATH, "//input[@value='ingresar' and @type='submit']")
        login_button.click()
        
        # Defino el wait. 10sec
        wait = WebDriverWait(driver, 10)
        
        # Espera hasta que la página se cargue y el elemento esté disponible
        wait.until(EC.presence_of_element_located((By.ID, "j_id15:j_id30")))
        
        return driver
        
    except Exception as e:
        print(f"An error occurred during login: {e}")
        if 'driver' in locals():
            driver.quit()
        raise
    