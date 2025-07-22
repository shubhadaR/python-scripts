import json
import logging
import sys
import os
from flask_cors import CORS
import time
import requests
from flask import Flask, request, jsonify
from models import Ticket, db, AlertHistoryEntry 
from collections import deque
import datetime

glpi_url                  = os.environ.get("GLPI_URL")
glpi_app_token            = os.environ.get("GLPI_APP_TOKEN")
glpi_user_token           = os.environ.get("GLPI_USER_TOKEN")
db_username               = os.environ.get("DB_USERNAME")
db_password               = os.environ.get("DB_PASSWORD")
db_host                   = os.environ.get("DB_HOST")
db_port                   = os.environ.get("DB_PORT")
db_name                   = os.environ.get("DB_NAME")
ticket_threshold_count    = os.environ.get("TICKET_THRESHOLD_COUNT")
ticket_threshold_duration = os.environ.get("TICKET_THRESHOLD_DURATION")
close_ticket_threshold_duration = os.environ.get("CLOSE_TICKET_THRESHOLD_DURATION")
ticket_endpoint           = f"{glpi_url}/Ticket"
glpi_session_token        = ""
alert_history             = {}
session_token_expiry      = 0

ivr_endpoint_url          = os.environ.get("IVR_ENDPOINT_URL")
app = Flask(__name__)
CORS(app)
app.logger.addHandler(logging.StreamHandler(sys.stdout))
app.logger.setLevel(logging.INFO)
app.logger.info("ivr url: %s",ivr_endpoint_url)

# Configure the database URI
app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql://{db_username}:{db_password}@{db_host}:3306/{db_name}'
# Disable modification tracking (not recommended for production)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_POOL_SIZE'] = 20  # Increase the pool size to 20 or an appropriate value.
app.config['SQLALCHEMY_MAX_OVERFLOW'] = 100
# Initialize the db object with the app instance
resource_mapping = os.environ.get("RESOURCE_MAPPING")
app.logger.info(resource_mapping)
if resource_mapping is not None:
    try:
        # Parse the JSON data
        data_dict = json.loads(resource_mapping)
        resource_mapping = data_dict["resource_mapping"]
        result_dict = {item["resource_name"]: item["identifierkey"] for item in resource_mapping}
        app.logger.info("result_dict %s", result_dict)
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
else:
    print("RESOURCE_MAPPING environment variable is not set or is None.") 
db.init_app(app)
@app.route('/webhook', methods=['POST'])

def receive_alerts():
    current_time              = int(time.time())
    alert_queue               = deque()
    def get_alert_start_time(alert):
        starts_at = alert.get('startsAt')
        if starts_at:
            return datetime.datetime.fromisoformat(starts_at.replace("Z", "+00:00"))    
    try:
        # Alert Data received
        data = request.json  # Extract the payload as JSON
        app.logger.info(data)
        if 'alerts' in data:
            payload_status = data.get('status').upper()
            app.logger.info(f"status of a payload {payload_status}") 
            alerts = data['alerts']
            app.logger.info(f"Number of Alerts: {len(alerts)}")
            
            for index, alert in enumerate(alerts):
            # for alert in alerts:
                try:
                    app.logger.info(f"Processing alert {index + 1}")
                    # Append the alert to the deque
                    alert_queue.append(alert)

                except Exception as alert_processing_error:
                    app.logger.error("Error processing individual alert: %s", str(alert_processing_error))
            # Append alerts to the queue and sort them by start time
            sorted_queue = sorted(alert_queue, key=lambda alert: get_alert_start_time(alert))
            app.logger.info(f"sorted alerts : {sorted_queue}")            
            # After processing all alerts, process them in FIFO order
            for alert in sorted_queue:  
                #alert = alert_queue.popleft()
                app.logger.info(f"Processing alert from queue: {alert}")
                ticket_content      = None
                ticket_id           = None
                ticket_status_id    = None
                application         = None
                alert_name          = alert.get('labels', {}).get('alertname')
                alert_status        = alert.get('status', '').upper()
                alert_description   = alert.get('annotations', {}).get('description')
                instance            = alert.get('labels', {}).get('instance')
                severity            = alert.get('labels', {}).get('severity')
                cluster             = alert.get('labels', {}).get('cluster')
                Name                = alert.get('labels', {}).get('Name')
                service             = alert.get('labels', {}).get('service')
                resource            = alert.get('labels', {}).get('resource')
                app.logger.info("resource: %s",resource)
                env                 = alert.get('labels', {}).get('env')
                value               = alert.get('labels', {}).get('value')
                company             = alert.get('labels', {}).get('company')
                summary             = alert.get('annotations', {}).get('summary')
                tag_COP_Application = alert.get('labels', {}).get('tag_COP_Application')
                COP_Application     = alert.get('labels', {}).get('COP_Application')
                COP_Service         = alert.get('labels', {}).get('COP_Service')
                tag_COP_Service     = alert.get('labels', {}).get('tag_COP_Service')
                device              = alert.get('labels', {}).get('device')
                dimension_ReplicationInstanceIdentifier = alert.get('labels', {}).get('dimension_ReplicationInstanceIdentifier')
                title_identifier    = None
                alert_identifier    = None
                found_match         = False
                    
                if COP_Application is not None:
                    application = COP_Application
                else:
                    application = tag_COP_Application
                app.logger.info("application %s", application)
                 
                if device is not None and str(device) != "None":
                    alert_name = f"{alert_name}-{device}"
                else:
                    alert_name = alert_name
                # Iterate through the resource_mapping list to find a match
                for mapping in resource_mapping:
                    identifierkey =  mapping['identifierkey'] 
                    app.logger.info("identifierkey %s", identifierkey) 
                    identifier = alert.get('labels', {}).get(identifierkey)
                    app.logger.info("identifier %s", identifier)
                    if mapping["resource_name"] == resource:
                        if identifierkey and identifier:
                            alert_identifier = f"{alert_name}_{identifier}"
                            title_identifier = identifier
                            found_match = True
                            break
                app.logger.info("identifier in title %s", title_identifier)
                if not found_match:
                    alert_identifier = alert_name
                app.logger.info("alert identifier %s", alert_identifier) 
                                   
                ### alert title mapping
                title_components = []
                if severity and severity != "None":
                    title_components.append(severity)
                if company and company != "None":
                    title_components.append(company)
                if env and env != "None":
                    title_components.append(env)
                if resource and resource != "None":
                    title_components.append(resource)
                if dimension_ReplicationInstanceIdentifier and dimension_ReplicationInstanceIdentifier != "None":
                    title_components.append(dimension_ReplicationInstanceIdentifier)    
                if title_identifier and title_identifier != "None":
                    title_components.append(title_identifier)
                if Name and Name != "None":
                    title_components.append(Name)
                if cluster and cluster != "None":
                    title_components.append(cluster) 
                if service and service != "None":
                    title_components.append(service)
                if alert_name and alert_name != "None":
                    title_components.append(alert_name)
                if summary and summary != "None":
                    title_components.append(summary)
                if value and value != "None":
                     title_components.append(f"Value = {value}")
                
                        
                # Construct the title by joining non-None components
                ticket_title = " | ".join(title_components)
                ticket_content      = alert_description
                app.logger.info("title: %s",ticket_title)
                ### alert title mapping 
                ticket_priority = severity
                existing_ticket = Ticket.query.filter_by(alert_identifier=alert_identifier,priority=ticket_priority).first()
                alert_entry = AlertHistoryEntry.query.filter_by(alert_identifier=alert_identifier,priority=ticket_priority).first()
                if existing_ticket:
                    app.logger.info("existing ticket in databse %s", existing_ticket.glpi_ticket_id)
                    ticket_id = existing_ticket.glpi_ticket_id
                    ticket_status_id = get_glpi_ticket_status(existing_ticket.glpi_ticket_id)
                    app.logger.info(f"status id of ticket {ticket_id} is {ticket_status_id}")
                    app.logger.info(f"existing ticket priority {ticket_id} %s", existing_ticket.priority)
                    app.logger.info(f"new ticket priority {ticket_id} %s", ticket_priority)
                    ## check if alert is resolved
                    if payload_status == "RESOLVED":
                            existing_ticket.resolved_timestamp = current_time
                            existing_ticket.alert_status       = "RESOLVED"
                            app.logger.info(f"Setting ticket status to RESOLVED and adding timestamp")
                            db.session.commit()                   
                          
                    elif existing_ticket.alert_status == "RESOLVED" and payload_status == "RESOLVED":
                        existing_resolved_timestamp = existing_ticket.resolved_timestamp
                        if existing_resolved_timestamp and current_time - existing_resolved_timestamp >= int(close_ticket_threshold_duration):
                            # Introduce a 5-second delay before processing each alert
                            time.sleep(5)
                            alert_entry = AlertHistoryEntry.query.filter_by(alert_identifier=existing_ticket.alert_identifier, priority=existing_ticket.priority).first()
                            ticket_content = f"Ticket Automatically Closed..."
                            update_ticket_data_in_glpi(existing_ticket.glpi_ticket_id, ticket_content)
                            ticket_deleted = close_glpi_ticket(existing_ticket.glpi_ticket_id)
                            app.logger.info(f"ticket to be closed... Ticket ID:{existing_ticket.glpi_ticket_id}")
                            if ticket_deleted:
                                #processed_alerts[ticket.alert_identifier] = {"status": ticket.alert_status, "identifier": ticket.alert_identifier}
                                delete_ticket(existing_ticket)
                                if alert_entry is not None:
                                    db.session.delete(alert_entry)  # Remove the entry from the database
                                    db.session.commit()
                                    app.logger.info(f"ticket deleted from alert_history") 
                                    continue
                                else:
                                    app.logger.info(f"ticket does not found in alert_history") 
                                app.logger.info(f"Ticket Closed successfully! {existing_ticket.glpi_ticket_id}")
                                continue
                            else: 
                                app.logger.info(f"Ticket already closed and deleted from database! {existing_ticket.glpi_ticket_id}")
                                continue                        
                    # If a resolved timestamp exists in the database
                        # else:
                        #     existing_ticket.resolved_timestamp = current_time
                        #     existing_ticket.alert_status       = "RESOLVED"
                        #     app.logger.info(f"Setting ticket status to RESOLVED and adding timestamp") 
                        #     db.session.commit()                       
                        # continue                        
                    elif ticket_status_id == 6: 
                        ticket_in_databse = Ticket.query.filter_by(alert_identifier=alert_identifier, priority=ticket_priority).first()                        
                        delete_ticket_database = delete_ticket(ticket_in_databse)
                        if delete_ticket_database:
                            app.logger.info(f"Deleted ticket entry from Tickets database..{ticket_id}")
                            continue
                        else:
                            app.logger.info(f"Failed to Delete ticket entry from Tickets database..{ticket_id}")
                                                    
                        if alert_entry is not None:
                            db.session.delete(alert_entry)  # Remove the entry from the database
                            db.session.commit()
                            continue
                        else:
                            app.logger.info(f"ticket does not found in alert_history")
                            continue

                    #elif ticket_priority < existing_ticket.priority:
                    # elif ticket_priority == "P1" and existing_ticket.priority == "P2":
                    #     app.logger.info("ticket updating  %s", existing_ticket.glpi_ticket_id)
                    #     app.logger.info("severity %s", severity)
                    #     title_update = update_ticket_title_in_glpi(ticket_title, ticket_id)
                    #     if title_update:
                    #         ticket_content = f"Ticket priority changed from {existing_ticket.priority} to {ticket_priority} \n {alert_description}"
                    #         updated = update_ticket_data_in_glpi(existing_ticket.glpi_ticket_id, ticket_content)
                    #         if updated:
                    #             update_ticket(ticket_title, ticket_content, ticket_priority, alert_identifier)
                    #             if alert_identifier in alert_history:
                    #                 alert_data = alert_history[alert_identifier]
                    #                 alert_data["ticket_title"] = ticket_title
                    #                 app.logger.info(f"Ticket with updated successfully!- ticket ID {ticket_id}")
                    #                 continue
                    #         else:
                    #             app.logger.info(f"Failed to update ticket or store alert data. - ticket ID {ticket_id}")
                    #             continue
                    ###### Update ticket with a comments 
                    # elif ticket_priority == existing_ticket.priority and alert_status == "FIRING":
                    #     app.logger.info("ticket updating  %s", existing_ticket.glpi_ticket_id)
                    #     ticket_content = f"Ticket Updated \n {alert_description} "
                    #     existing_resolved_timestamp = current_time
                    #     existing_ticket.alert_status = "FIRING"
                    #     updated = update_ticket_data_in_glpi(existing_ticket.glpi_ticket_id, ticket_content)
                    #     if updated:
                    #         update_ticket(ticket_title, ticket_content, ticket_priority, alert_identifier, existing_ticket.alert_status)
                    #         app.logger.info("Ticket updated successfully!")
                    #         continue
                    #     else:
                    #         app.logger.info("Failed to update ticket or store alert data.")
                    #         continue
                    elif ticket_priority == existing_ticket.priority and alert_status == "FIRING":
                        app.logger.info("ticket already created in GLPI %s", existing_ticket.glpi_ticket_id)
                        existing_ticket.alert_status       = "FIRING"
                        existing_ticket.resolved_timestamp =  None
                        app.logger.info(f"Counter reset for alert to resolve") 
                        db.session.commit()                          
                        continue
                        
                else:                  
                    app.logger.info("Ticket does not exists %s in MYSQL DB! \t Checking in alert history. . .", alert_identifier)
                    # Check Database alerts with alert_identifier
                    current_time = int(time.time()) 
                    #alert_entry = AlertHistoryEntry.query.filter_by(alert_identifier=alert_identifier,priority=ticket_priority).first()
                    #app.logger.info(f"alert entry from alert history {alert_entry.alert_identifier}")
                    if alert_entry is not None:
                        # Get the alert data for this alert_identifier
                        # Check if the alert has occurred 'alert_threshold' times within the window
                        app.logger.info(alert_entry.alert_identifier)
                        ticket_threshold_duration1 = int(ticket_threshold_duration)
                        ticket_threshold_count1 = int(ticket_threshold_count)
                        app.logger.info("ticket_threshold_duration: %s", ticket_threshold_duration1)
                        app.logger.info("current_time: %s",current_time)
                        app.logger.info("ticket last updated timestapm: %s",alert_entry.timestamps)
                        valid_duartion = current_time - alert_entry.timestamps <= ticket_threshold_duration1
                        app.logger.info(valid_duartion)
                        #timestamps = [t for t in timestamps if current_time - t <= ticket_threshold_duration1]
                        if valid_duartion:
                            app.logger.info(f"ticket counts in alert_history {alert_entry.count}")
                            if alert_entry.count >= ticket_threshold_count1 and alert_status == "FIRING":
                                ticket_id = create_glpi_ticket(ticket_title, ticket_content)
                                if ticket_id:
                                    alert_status = "FIRING"
                                    create_glpi_ticket_and_store(ticket_id, ticket_title, ticket_content, ticket_priority, instance, alert_name, service, resource, alert_identifier, alert_status)
                                    db.session.delete(alert_entry)  # Remove the entry from the database
                                    db.session.commit()
                                    send_ivr_payload(ticket_id, ticket_title, application, resource, severity, ivr_endpoint_url)
                                    app.logger.info("Ticket created successfully! -- ticket_id: %s", ticket_id)
                                    continue
                                else:
                                    app.logger.info("Failed to create ticket or store alert data.")
                                    continue
                            else:
                                alert_entry.count += 1
                                db.session.commit()
                                continue
                        else:                                 ### To reset alert_history for alert after specified time window
                            alert_entry.timestamps = current_time
                            alert_entry.count = 1
                            db.session.commit()
                            continue
                    else:
                        # First occurrence of the alert, add it to the history
                        alert_data = AlertHistoryEntry(
                            alert_identifier=alert_identifier,
                            timestamps=current_time,
                            count=1,
                            title=ticket_title, # Example ticket title
                            priority=ticket_priority
                        )
                        db.session.add(alert_data)
                        db.session.commit()
                        continue
            #processed_alerts.clear()                        
            return 'alerts received and processed', 200
        else:
            return jsonify({"status": "error", "message": "No alerts found in the payload"}), 400
        
    except Exception as payload_processing_error:
        app.logger.error("Error processing payload: %s", str(payload_processing_error))
        return jsonify({"status": "error", "message": "Error processing the payload"}), 500
  

##### Create session token #####
#@retrying.retry(wait_fixed=2000, stop_max_attempt_number=3, retry_on_result=lambda x: x is None)
def generate_glpi_session_token():
    session_ticket_endpoint=f"{glpi_url}/initSession/"
    global glpi_session_token
    global session_token_expiry
    current_time = int(time.time())
    
    if glpi_session_token and session_token_expiry > current_time:
        return glpi_session_token  # Reuse the existing token
    headers = {
        "Authorization": f"user_token {glpi_user_token}",  # Use "Authorization" header for user token
        "Content-Type": "application/json",
        "App-Token": glpi_app_token
    }
    try:
        response = requests.get(session_ticket_endpoint, headers=headers)
        # Check if the request was successful (HTTP status code 200 - Created)
        if response.status_code == 200:
            print("Session token created successfully!")
            glpi_session_token = response.json().get("session_token")
            print(glpi_session_token)
            return glpi_session_token
        else:
            print(f"Failed to create session token. Status code: {response.status_code}")
            print(response.text)
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
    except Exception as ex:
        print(f"An unexpected error occurred: {ex}")
    return None
##### Create ticket ######
glpi_session_token = generate_glpi_session_token()
#@retrying.retry(wait_fixed=2000, stop_max_attempt_number=3, retry_on_result=lambda x: x is None)
def create_glpi_ticket(ticket_title, ticket_content):
    #glpi_session_token = generate_glpi_session_token()
    headers = {
        "Content-Type": "application/json",
        "Session-Token": glpi_session_token,
        "App-Token": glpi_app_token
    }
    # Data to be sent in the POST request to create the ticket
    data = {
        "input": {
            "name": ticket_title,
            "content": ticket_content,
            "type": 1 
        }
    }
    try:
        # Send POST request to create the ticketprocessed
        response = requests.post(ticket_endpoint, headers=headers, json=data)

        # Check if the request was successful (HTTP status code 201 - Created)
        if response.status_code == 201:
            app.logger.info("Ticket created successfully! %s")
            ticket_id = response.json().get("id")
            app.logger.info("Ticket ID %s: ", ticket_id)
            
            return ticket_id
        else:
            app.logger.error("Failed to create the ticket... Status code: %s", response.status_code)
            app.logger.error("Response: %s", response.text)

    except requests.exceptions.RequestException as request_error:
        app.logger.error("Request error occurred: %s", request_error)
    except Exception as e:
        app.logger.error("An unexpected error occurred: %s" ,e)

    # Return None to indicate that ticket creation failed
    return None


########Update ticket#########
#@retrying.retry(wait_fixed=2000, stop_max_attempt_number=3, retry_on_result=lambda x: x is None)
def update_ticket_data_in_glpi(ticket_id, ticket_content=None):
    # Headers containing the session token and content type
    #glpi_session_token = generate_glpi_session_token()
    ticket_update_endpoint = f"{ticket_endpoint}/{ticket_id}/ITILFollowup/"
    headers = {
        "Content-Type": "application/json",
        "Session-Token": glpi_session_token,
        "App-Token": glpi_app_token
    }
    data = {
        "input": {
            # "name": ticket_title,
            "itemtype": "Ticket",
            "items_id": ticket_id,
            "content": ticket_content
        }
    }    
    try:
        response = requests.post(ticket_update_endpoint, json=data, headers=headers)
        if response.status_code == 201:
            ticket_id = response.json().get("id")
            app.logger.info("Ticket updated successfully! %s",ticket_id)
            #app.logger.info("Ticket ID %s: ", ticket_id)
            return ticket_id
        else:
            app.logger.error("Failed to update the ticket... Status code: %s", response.status_code)
            app.logger.error("Response: %s", response.text)

    except requests.exceptions.RequestException as request_error:
        app.logger.error("Request error occurred: %s", request_error)
    except Exception as e:
        app.logger.error("An unexpected error occurred: %s" ,e)

    # Return None to indicate that ticket creation failed
    return None   

########Update ticket#########
#@retrying.retry(wait_fixed=2000, stop_max_attempt_number=3, retry_on_result=lambda x: x is None)
def update_ticket_title_in_glpi(ticket_title, ticket_id):
    #glpi_session_token = generate_glpi_session_token()
    # Headers containing the session token and content type
    ticket_update_endpoint = f"{ticket_endpoint}/{ticket_id}"
    headers = {
        "Content-Type": "application/json",
        "Session-Token": glpi_session_token,
        "App-Token": glpi_app_token
    }
    data = {
        "input": {
            "name": ticket_title,
            "type": 1,
            "id": ticket_id
        }
    }    
    try:
        response = requests.put(ticket_update_endpoint, json=data, headers=headers)
        if response.status_code == 200:
            app.logger.info("Ticket title updated successfully! %s")
            #ticket_id = response.json().get("ticket_id")
            #app.logger.info("Ticket ID %s: ", ticket_id)
            return ticket_id
        else:
            app.logger.error("Failed to update the ticket title... Status code: %s", response.status_code)
            app.logger.error("Response: %s", response.text)

    except requests.exceptions.RequestException as request_error:
        app.logger.error("Request error occurred: %s", request_error)
    except Exception as e:
        app.logger.error("An unexpected error occurred: %s" ,e)

    # Return None to indicate that ticket creation failed
    return None
#@retrying.retry(wait_fixed=2000, stop_max_attempt_number=3, retry_on_result=lambda x: x is None)
def close_glpi_ticket(ticket_id):
    # Headers containing the session token and content type
    #glpi_session_token = generate_glpi_session_token()
    ticket_close_endpoint = f"{ticket_endpoint}/{ticket_id}"
    headers = {
        "Content-Type": "application/json",
        "Session-Token":  glpi_session_token,
        "App-Token": glpi_app_token
    }
        # Send a PUT request to close the ticket
    data = {
        "input": {
            "status": 6  # Set the status to 6 to indicate "closed" status (check GLPI API for the correct status code)
        }
    }
    try:
        response = requests.put(ticket_close_endpoint, json=data, headers=headers)
        response.raise_for_status()
        app.logger.info("Ticket closed successfully from GLPI!")
        return True
    except requests.exceptions.RequestException as e:
        app.logger.info(f"An error occurred while closing the ticket: {e}")
        return False 
    
#@retrying.retry(wait_fixed=2000, stop_max_attempt_number=3, retry_on_result=lambda x: x is None)
def get_glpi_ticket_status(ticket_id):
    ticket_status_endpoint = f"{ticket_endpoint}/{ticket_id}"
    headers = {
        "Content-Type": "application/json",
        "Session-Token": glpi_session_token,
        "App-Token": glpi_app_token
    }
    try:
        response = requests.get(ticket_status_endpoint, headers=headers)
        if response.status_code == 200:
            ticket_status_id = response.json().get("status")
            return ticket_status_id
        else: 
            return False
    except requests.exceptions.RequestException as e:
        return f"An error occurred: {e}"
### helper finction
def map_severity_to_priority(severity):
    priority_mapping = {
        "P1": 4,
        "P2": 3,
        "P3": 1,
        "P4": 2
    }
    return priority_mapping.get(severity.lower(), 1) 
#@retrying.retry(wait_fixed=2000, stop_max_attempt_number=3, retry_on_result=lambda x: x is None)
def create_glpi_ticket_and_store(ticket_id, ticket_title, ticket_content, ticket_priority, instance, alert_name, service, resource, alert_identifier, alert_status="FIRING", processed=False):
    # Store the ticket information in the database
    new_ticket = Ticket(title=ticket_title, content=ticket_content, glpi_ticket_id=ticket_id, priority=ticket_priority, instance=instance, alertname=alert_name, service=service,resource=resource, alert_identifier=alert_identifier, resolved_timestamp=None, alert_status=alert_status, processed=processed)
    #app.logger.info (new_ticket.priority)
    try:
        db.session.add(new_ticket)
        db.session.commit()
    except Exception as ex:
        db.session.rollback()
        app.logger.error(f"Commit failed. {ex}")
        return None
    return new_ticket.id   
#@retrying.retry(wait_fixed=2000, stop_max_attempt_number=3, retry_on_result=lambda x: x is None)
def update_ticket(ticket_title, ticket_content, ticket_priority, alert_identifier, alert_status="FIRING", resolved_timestamp=None):
    try:
        existing_ticket = Ticket.query.filter_by(alert_identifier=alert_identifier).first()
        existing_ticket.title = ticket_title
        existing_ticket.content = ticket_content
        existing_ticket.priority = ticket_priority
        existing_ticket.alert_status = alert_status
        existing_ticket.resolved_timestamp = resolved_timestamp
        
        db.session.commit()
    except Exception as ex:
        db.session.rollback()
        # thing_1.id can be referenced after rollback
        app.logger.error(f"Commit failed. {ex}") 
#@retrying.retry(wait_fixed=2000, stop_max_attempt_number=3, retry_on_result=lambda x: x is None)
def delete_ticket(ticket):
    try:
        db.session.delete(ticket)
        db.session.commit()
    except Exception as ex:
        db.session.rollback()
        # thing_1.id can be referenced after rollback
        app.logger.error(f"delete failed. {ex}")
def send_ivr_payload(ticket_id, ticket_title, application, resource, severity, ivr_endpoint_url):
    try:
        headers = {"Content-Type": "application/json"}        
        ivr_payload = {
        "ivr_payload": [
            {
            "ticket_id": ticket_id,
            "ticket_title": ticket_title,
            "application": application,
            "resource": resource,
            "severity": severity
            }
        ]
        }
        json_payload= json.dumps(ivr_payload)
        response = requests.post(ivr_endpoint_url, data=json_payload, headers=headers)
        if response.status_code == 200:
            app.logger.info(f"Payload sent successfully!! {ivr_payload}")
            return True
        else:
            app.logger.info(f"failed to send payload to IVR!! status_code {response.status_code}")
    
    except requests.exceptions.RequestException as e:
        # Handle any network-related errors (e.g., connection issues)
        app.logger.info("Network error: %s", str(e))
        return False 

    except Exception as ex:
        # Handle any other unexpected exceptions
        app.logger.info("An unexpected error occurred: %s", str(ex))
        return False 