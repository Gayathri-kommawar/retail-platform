pipeline {
    agent any

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Show Parameters') {
            steps {
                echo "Deployment Action: ${params.DEPLOYMENT_ACTION}"
                echo "Environment: ${params.ENVIRONMENT}"
                echo "Version: ${params.VERSION}"
                echo "Production Confirmation: ${params.CONFIRM_PROD}"
            }
        }
    }
}