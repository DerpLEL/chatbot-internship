#!/usr/bin/env python3
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import os

""" Bot Configuration """


class DefaultConfig:
    """ Bot Configuration """

    PORT = 3978
    APP_ID = os.environ.get("MicrosoftAppId", "d70aeb25-d473-4545-b414-70e9050580bf")
    APP_PASSWORD = os.environ.get("MicrosoftAppPassword", "GdD8Q~63pxG~gNl4IRkPXRWOfyxAbrhl2~TRKanF")
    CONNECTION_NAME = os.environ.get("ConnectionName", "BotLogin")
