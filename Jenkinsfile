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

        stage('Validate Production') {
            steps {
                script {
                    if (params.ENVIRONMENT == 'PRODUCTION' &&
                        params.CONFIRM_PROD != 'YES') {

                        error("Production deployment blocked: CONFIRM_PROD must be YES")
                    }

                    echo "Production validation passed."
                }
            }
        }

        stage('Validate Version') {
            steps {
                powershell """
                    git fetch --tags --force

                    git rev-parse "refs/tags/v${params.VERSION}^{commit}"

                    Write-Host "Version tag v${params.VERSION} exists."
                """
            }
        }

        stage('Checkout Selected Version') {
            steps {
                powershell """
                    git checkout "tags/v${params.VERSION}"

                    Write-Host "Selected Git commit:"
                    git rev-parse HEAD
                """
            }
        }

        stage('Build Docker Image') {
            steps {
                powershell """
                    & "$env:DOCKER_PATH\\docker.exe" build -t retail-app:${params.VERSION}-${env.BUILD_NUMBER} .
                """
            }
        }

        stage('Show Docker Image') {
            steps {
                powershell """
                    & "$env:DOCKER_PATH\\docker.exe" images retail-app
                """
            }
        }
    }
}