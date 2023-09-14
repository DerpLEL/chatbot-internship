#!/usr/bin/env python3
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import os

""" Bot Configuration """

# Default
id = "b8838874-d6d2-4747-a8c7-862d2f530db0"
pw = "Gf~8Q~wMv-0j1TwBFlOy4mJauAE2eDKfwwXnTalx"
pw_alt = "pX18Q~uSkMsrII.eP-Cq8gKUcX56zoK6kOECib2h"

# azure-intern01
id01 = "d70aeb25-d473-4545-b414-70e9050580bf"
pw01 = "GdD8Q~63pxG~gNl4IRkPXRWOfyxAbrhl2~TRKanF"

"""Default auth config
Grant type: authorization_code
Login URL: https://login.microsoftonline.com
Tenant ID: 5e2a3cbd-1a52-45ad-b514-ab42956b372c
Resource URL: https://graph.microsoft.com/
Scopes: User.Read"""


class DefaultConfig:
    """ Bot Configuration """

    PORT = 3978
    APP_ID = os.environ.get("MicrosoftAppId", id)
    APP_PASSWORD = os.environ.get("MicrosoftAppPassword", pw)
    CONNECTION_NAME = os.environ.get("ConnectionName", "BotLogin")
