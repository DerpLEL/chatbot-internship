import os
import uuid
import requests
import msal
import app_config
import time

from flask import Flask, render_template, session, request, redirect, url_for, jsonify
from flask_session import Session  # https://pythonhosted.org/Flask-Session
from functools import wraps
from langchain.llms import AzureOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains.qa_with_sources import load_qa_with_sources_chain
from langchain.chat_models import AzureChatOpenAI

from chatbot import *

from speechRecognizerPython import  get_audio
bot = chatAI()

app = Flask(__name__)

app.config.from_object(app_config)
Session(app)

# session['last_active'] = time.time()


# This section is needed for url_for("foo", _external=True) to automatically
# generate http scheme when this sample is running on localhost,
# and to generate https scheme when it is deployed behind reversed proxy.
# See also https://flask.palletsprojects.com/en/1.0.x/deploying/wsgi-standalone/#proxy-setups
# from werkzeug.middleware.proxy_fix import ProxyFix
# app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

@app.route("/")
def index():
    if not session.get("user"):
        return redirect(url_for("login"))
    return render_template('index.html', user=session["user"], version=msal.__version__)

# def check_last_active_time(func):
#     @wraps(func)
#     def wrapper(*args, **kwargs):
#         if 'last_active' in session:
#             last_active_time = session['last_active']
#             if time.time() - last_active_time > 15:   # 30 minutes
#                 # log the user out and redirect to the login page
#                 session.clear()
#                 return redirect(url_for('login'))
#         return func(*args, **kwargs)
#     return wrapper

# @app.route('/dashboard')
# @check_last_active_time
# def dashboard():
#     # your dashboard code here
#     session['last_active'] = time.time()
#     return redirect(  # Also logout from your tenant's web session
#         app_config.AUTHORITY + "/oauth2/v2.0/logout" +
#         "?post_logout_redirect_uri=" + url_for("index", _external=True))

@app.route("/login")
def login():
    # Technically we could use empty list [] as scopes to do just sign in,
    # here we choose to also collect end user consent upfront
    session["flow"] = _build_auth_code_flow(scopes=app_config.SCOPE)
    return render_template("login.html", auth_url=session["flow"]["auth_uri"], version=msal.__version__)

@app.post("/predict")
def predict():
    text = request.get_json().get("message") 

    if 'claims_challenge' in session['flow']:
        bot.private = False
    else:
        bot.private = True

    response, doc = bot.chat(text)
    message = {"answer": response['output_text']}
    print(doc)

    return jsonify(message)

#custom STT
@app.post("/recordFunction")
def record():

    message,doc = {"answer": get_audio()}
    print(doc)

    return jsonify(message)

@app.route(app_config.REDIRECT_PATH)  # Its absolute URL must match your app's redirect_uri set in AAD
def authorized():
    try:
        cache = _load_cache()
        result = _build_msal_app(cache=cache).acquire_token_by_auth_code_flow(
            session.get("flow", {}), request.args)
        if "error" in result:
            return render_template("auth_error.html", result=result)
        session["user"] = result.get("id_token_claims")
        _save_cache(cache)
    except ValueError:  # Usually caused by CSRF
        pass  # Simply ignore them

    return redirect(url_for("index"))

@app.route("/logout")
def logout():
    session.clear()  # Wipe out user and its token cache from session
    return redirect(  # Also logout from your tenant's web session
        app_config.AUTHORITY + "/oauth2/v2.0/logout" +
        "?post_logout_redirect_uri=" + url_for("index", _external=True))

@app.route("/graphcall")
def graphcall():
    token = _get_token_from_cache(app_config.SCOPE)
    if not token:
        return redirect(url_for("login"))
    graph_data = requests.get(  # Use token to call downstream service
        app_config.ENDPOINT,
        headers={'Authorization': 'Bearer ' + token['access_token']},
        ).json()
    return render_template('display.html', result=graph_data)


def _load_cache():
    cache = msal.SerializableTokenCache()
    if session.get("token_cache"):
        cache.deserialize(session["token_cache"])
    return cache

def _save_cache(cache):
    if cache.has_state_changed:
        session["token_cache"] = cache.serialize()

def _build_msal_app(cache=None, authority=None):
    return msal.ConfidentialClientApplication(
        app_config.CLIENT_ID, authority=authority or app_config.AUTHORITY,
        client_credential=app_config.CLIENT_SECRET, token_cache=cache)

def _build_auth_code_flow(authority=None, scopes=None):
    return _build_msal_app(authority=authority).initiate_auth_code_flow(
        scopes or [],
        redirect_uri=url_for("authorized", _external=True))

def _get_token_from_cache(scope=None):
    cache = _load_cache()  # This web app maintains one cache per session
    cca = _build_msal_app(cache=cache)
    accounts = cca.get_accounts()
    if accounts:  # So all account(s) belong to the current signed-in user
        result = cca.acquire_token_silent(scope, account=accounts[0])
        _save_cache(cache)
        return result
    



# app.jinja_env.globals.update(_build_auth_code_flow=_build_auth_code_flow)  # Used in template

if __name__ == "__main__":
    app.run()

