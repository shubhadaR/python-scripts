import os
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Ticket(db.Model):
    """
    Represents a ticket in the database.

    Attributes:
        id (int): The unique identifier for the ticket.
        glpi_ticket_id (int): The GLPI ticket ID.
        title (str): The title of the ticket.
        content (str): The content of the ticket.
        priority (str): The priority of the ticket.
        instance (str): The instance associated with the ticket.
        alertname (str): The name of the alert.
        service (str): The service associated with the ticket.
        resource (str): The resource associated with the ticket.
        alert_identifier (str): The unique identifier for the alert associated with the ticket.

    Methods:
        __init__: Initializes a new Ticket instance with the provided attributes.
    """
    __tablename__ = os.environ.get("TICKETS_TABLE_NAME")

    id = db.Column(db.Integer, primary_key=True)
    glpi_ticket_id = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String(1000), nullable=False)
    content = db.Column(db.Text, nullable=False)
    priority = db.Column(db.String(10))
    instance = db.Column(db.String(255))
    alertname = db.Column(db.String(1000))
    service = db.Column(db.String(255))
    resource = db.Column(db.String(255))
    alert_identifier = db.Column(db.String(700), unique=True) 
    alert_status = db.Column(db.String(255))
    resolved_timestamp = db.Column(db.Integer)
    processed = db.Column(db.Boolean, default=False)

    def __init__(self, title, content, priority, glpi_ticket_id, instance, alertname, service, resource, alert_identifier, alert_status, resolved_timestamp, processed):
        self.title = title
        self.content = content
        self.priority = priority
        self.glpi_ticket_id = glpi_ticket_id
        self.instance = instance
        self.alertname = alertname
        self.service = service
        self.resource = resource
        self.alert_identifier = alert_identifier 
        self.alert_status = alert_status
        self.resolved_timestamp = resolved_timestamp
        self.processed = processed
        
class AlertHistoryEntry(db.Model):
    __tablename__ = os.environ.get("ALERT_HISTORY_TABLE_NAME")

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(1000))  # Example ticket title
    priority = db.Column(db.String(10))
    alert_identifier = db.Column(db.String(700), unique=True)
    timestamps = db.Column(db.Integer)
    count = db.Column(db.Integer)
   
    def __init__(self, title, priority, alert_identifier, timestamps, count):  #glpi_ticket_id,
        """
        Initializes a new Ticket instance.

        Args:
            title (str): The title of the ticket.
            content (str): The content of the ticket.
            priority (str): The priority of the ticket.
            instance (str): The instance associated with the ticket.
            alertname (str): The name of the alert.
            service (str): The service associated with the ticket.
            resource (str): The resource associated with the ticket.
            alert_identifier (str): The unique identifier for the alert associated with the ticket.
        """    
        self.title = title
        self.priority = priority
        self.alert_identifier = alert_identifier  
        self.timestamps = timestamps 
        self.count = count
    
def check_database_connection():
    try:
        # Perform a simple query to check the connection
        db.session.query("1").from_statement("SELECT 1").all()
        return True
    except Exception as e:
        return False    
    