from flask import Flask
import os

app = Flask(__name__)

VERSION = os.getenv("APP_VERSION", "4.2.0")
ENVIRONMENT = os.getenv("ENVIRONMENT", "UAT")

@app.route("/")
def home():
    return f"""
    <h1>Retail Platform</h1>
    <p>Version: {VERSION}</p>
    <p>Environment: {ENVIRONMENT}</p>
    <p>Payment Status: Hotfix Applied</p>
    """

@app.route("/health")
def health():
    return "healthy", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8081)
