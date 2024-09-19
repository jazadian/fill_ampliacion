import os
import boto3
from pymongo import MongoClient
from datetime import datetime
import logging
import time


from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from login import login


s3_client = boto3.client('s3')
sqs_client = boto3.client('sqs')


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
    id_ampliacion = event.get('id')
    try:
        client = MongoClient(os.environ.get('MONGO_ACCESS_KEY'))
        db = client['canastas'] 
        buckets_collection = db['status_ampliacion']
        document = {
                    "id_ampliacion": id_ampliacion,
                    "description": "waiting_lambda",
                    "createdAt": datetime.utcnow()# Use UTC for consistent time zone
                }

                # Insert the document into the collection
        buckets_collection.insert_one(document)
        print("Documento guardado en status_ampliacion")
    except Exception as e:
        logging.error(f"CUSTOM_ERROR: Failed to insert into status_ampliacion - {str(e)}")
        raise RuntimeError(f"CUSTOM_ERROR: Failed to insert into status_ampliacion - {str(e)}")

    download_dir = "/tmp"
    try:
        downloaded_pdf_path = wait_for_download_to_complete(download_dir, timeout=60)
    except Exception as e:
        logging.error(f"CUSTOM_ERROR: Failed Downloading PDF- {str(e)}")
        raise RuntimeError(f"CUSTOM_ERROR: Failed Downloading PDF - {str(e)}")
   
    if downloaded_pdf_path:
        # Rename the downloaded PDF to match the bucket_id
        new_pdf_path = os.path.join(download_dir, f"{id_ampliacion}.pdf")
        os.rename(downloaded_pdf_path, new_pdf_path)
        print(f"Talon descargado y renombrado a: {new_pdf_path}")
            
        # Proceed to upload the file to S3
        s3_bucket = os.environ.get('S3_BUCKET_NAME')
        if not s3_bucket:
            raise ValueError("S3_BUCKET_NAME environment variable is not set.")
        
        try:    
            s3_client.upload_file(new_pdf_path, s3_bucket, f"bills/{os.path.basename(new_pdf_path)}")
            print(f"Uploaded {os.path.basename(new_pdf_path)} to S3 bucket {s3_bucket} with key bills/{os.path.basename(new_pdf_path)}")
        except Exception as e:
            logging.error("Error en guardado en S3", e)
            raise RuntimeError(f"Error en guardado en S3 - {str(e)}")
        try:
            # Create the document
            document = {
                "id_bucket": id_ampliacion,
                "description": "pdf_downloaded",
                "createdAt": datetime.utcnow()  # Use UTC for consistent time zone
            }

            # Insert the document into the collection
            result = buckets_collection.insert_one(document)
            print(f"Inserted document with id: {result.inserted_id}")     
        except Exception as e:
            logging.error("Error en guardado en mongo status downloaded_pdf", e)
            raise RuntimeError(f"Error en guardado en mongo status downloaded_pdf - {str(e)}")
        
        if driver is not None:  # Ensure driver is not None before calling quit
            driver.quit()
            
        try:
            SQS_QUEUE_URL = os.environ.get('SQS_QUEUE_URL')

            sqs_client.send_message(
                QueueUrl=SQS_QUEUE_URL,
                MessageBody=str(id_ampliacion)
            )
        except Exception as e:
            logging.error("Error en SQS", e)
            raise RuntimeError(f"Error en SQS - {str(e)}")
        
        print(f"Sent bucket_id {bucket_id} to SQS queue {SQS_QUEUE_URL}")

            


def wait_for_download_to_complete(download_dir, timeout=60):
    start_time = time.time()
    downloaded_files_before = set(os.listdir(download_dir))

    while time.time() - start_time < timeout:
        downloaded_files_after = set(os.listdir(download_dir))
        new_files = downloaded_files_after - downloaded_files_before
        
        if new_files:
            for file in new_files:
                file_path = os.path.join(download_dir, file)
                partial_file_path = file_path + ".crdownload"
                
                # Check if the file exists and is no longer in a partial download state
                if os.path.exists(file_path) and not os.path.exists(partial_file_path):
                    return file_path
        time.sleep(0.5)  # Poll every half second

    print(f"Timeout: PDF was not downloaded within {timeout} seconds.")
    return None

   
    
        
        
        
        
