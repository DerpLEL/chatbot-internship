#!/usr/bin/env python3
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import os

""" Bot Configuration """

id = "b8838874-d6d2-4747-a8c7-862d2f530db0"
pw = "Gf~8Q~wMv-0j1TwBFlOy4mJauAE2eDKfwwXnTalx"

class DefaultConfig:
    """ Bot Configuration """

    PORT = 3978
    APP_ID = os.environ.get("MicrosoftAppId", id)
    APP_PASSWORD = os.environ.get("MicrosoftAppPassword", pw)
    CONNECTION_NAME = os.environ.get("ConnectionName", "BotLogin")