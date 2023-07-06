import os
from azure.communication.email import EmailClient
from azure.identity import DefaultAzureCredential
from azure.core.credentials import AzureKeyCredential

key = AzureKeyCredential("lgst3jyX9G93klet60Wjr+I+MX4G7YCKPoI2e/Vr2wX6KYn2Fnw38JQ7iZp8kzEEcKiM/kXZhGVY6BregBCCVQ==")
endpoint = "https://noisemailsending.communication.azure.com/"

email_client = EmailClient(endpoint, key)


message = {
    "content": {
        "subject": "THIEN",
        "plainText": "Hello",
        "html": "<html><h1>Hello</h1></html>"
    },
    "recipients": {
        "to": [
            {
                "address": "thien.tran@nois.vn",
                "displayName": "Thien Tran"
            }
        ]
    },
    "senderAddress": "DoNotReply@161ef723-848d-4612-8552-2dae7b65d6f2.azurecomm.net"
}

poller = email_client.begin_send(message)
print("Result: " + str(poller.result()))