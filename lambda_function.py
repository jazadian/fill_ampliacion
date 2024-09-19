import os
import boto3
from pymongo import MongoClient
from datetime import datetime
import logging

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from login import login


s3_client = boto3.client('s3')


def lambda_handler(event, context):
    driver = None  # Initialize driver to None
    try:
        user_dgr = os.environ.get('DGR_USERNAME')
        password_dgr = os.environ.get('DGR_PASSWORD')
        driver = login(user_dgr,password_dgr)
    except Exception as e:
        logging.error(f"CUSTOM_ERROR: Failed to login to dgr")
        raise RuntimeError(f"CUSTOM_ERROR: Login failed - {str(e)}")
    try:
        #lleno numero de solicitud
        field = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "_NROSOLIC")))
        field.clear()
        field.send_keys(event.get('dgr_id'))
       
        #click boton submit
        field = driver.find_element(By.NAME, "BUTTON1")
        field.click()
        
        try:
            error_element = driver.find_element(By.CLASS_NAME, "ErrorViewer")
            if(error_element):
                logging.error("Se encontro error", error_element)
                raise RuntimeError(f"Fill form failed - {str(error_element)}")
        except:
            print("No hay error")
            
    except Exception as e:
        logging.error("Error en llenado de id solicitud", e)
        raise RuntimeError(f"Fill form failed - {str(e)}")
    
    field = driver.find_element(By.NAME, "BUTTON1")
    field.click()
    
    try:
        client = MongoClient(os.environ.get('MONGO_ACCESS_KEY'))
        db = client['canastas'] 
        buckets_collection = db['status_ampliacion']
        document = {
                    "id_ampliacion": event.get('id'),
                    "description": "waiting_lambda",
                    "createdAt": datetime.utcnow()# Use UTC for consistent time zone
                }

                # Insert the document into the collection
        buckets_collection.insert_one(document)
        print("Documento guardado en status_ampliacion")
    except Exception as e:
        logging.error(f"CUSTOM_ERROR: Failed to insert into status_ampliacion - {str(e)}")
        raise RuntimeError(f"CUSTOM_ERROR: Failed to insert into status_ampliacion - {str(e)}")



################################################################
##### VER ACA QUE PASA AL HACER CLIC EN AMPLIACION ################
################################################################



    try:
        filename = f'talon_de_pago_{event.get('id')}.pdf'
        driver.save_screenshot(filename)
        s3_client.upload_file(filename, 'dgr', filename)
        ##### VER ACA QUE PASA AL HACER CLIC EN AMPLIACION
    
    except Exception as e:
        logging.error(f"CUSTOM_ERROR: Failed to save pdf - {str(e)}")
        raise RuntimeError(f"CUSTOM_ERROR: Failed to save pdf - {str(e)}")

    finally:
        if driver is not None:  # Ensure driver is not None before calling quit
            driver.quit()

    return {
        'statusCode': 200,
        'body': json.dumps('Processed bucket successfully')
    }    
         
        
        
        
        
