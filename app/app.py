from flask import Flask
import os

app = Flask(__name__)

VERSION = os.getenv("APP_VERSION", "4.2.0")
ENVIRONMENT = os.getenv("ENVIRONMENT", "UAT")
HEALTH_FAIL = os.getenv("HEALTH_FAIL", "false").lower() == "true"

@app.route("/")
def home():
    return f"""
    <h1>Retail Platform</h1>
    <p>Version: {VERSION}</p>
    <p>Environment: {ENVIRONMENT}</p>
    <p>Payment Status: Hotfix Applied</p>
    <p>Feature: Product Catalog Enabled</p>
    <p>Feature: Order Tracking Enabled</p>
    """

@app.route("/health")
def health():
    if HEALTH_FAIL:
        return "unhealthy", 500
    return "healthy", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8081)