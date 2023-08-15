#!/usr/bin/env python3
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import os

""" Bot Configuration """

# Default
id = "b8838874-d6d2-4747-a8c7-862d2f530db0"
pw = "Gf~8Q~wMv-0j1TwBFlOy4mJauAE2eDKfwwXnTalx"

# azure-intern01
id01 = "d70aeb25-d473-4545-b414-70e9050580bf"
pw01 = "GdD8Q~63pxG~gNl4IRkPXRWOfyxAbrhl2~TRKanF"

id02 = "5248756a-41a7-4e41-9c09-49d9923a779f"
pw02 ="Ae48Q~Gpn8dCNMy0D8bBkHWiOB3fUlDQ2NnESbwB"
class DefaultConfig:
    """ Bot Configuration """

    PORT = 3978
    APP_ID = os.environ.get("MicrosoftAppId", id)
    APP_PASSWORD = os.environ.get("MicrosoftAppPassword", pw)
    CONNECTION_NAME = os.environ.get("ConnectionName", "BotLogin")