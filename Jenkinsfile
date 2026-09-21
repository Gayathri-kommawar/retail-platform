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
                    & 'C:\\Users\\gayat\\AppData\\Local\\Programs\\DockerDesktop\\resources\\bin\\docker.exe' build -t retail-app:${params.VERSION}-${env.BUILD_NUMBER} .
                """
            }
        }

        stage('Show Docker Image') {
            steps {
                powershell """
                    & 'C:\\Users\\gayat\\AppData\\Local\\Programs\\DockerDesktop\\resources\\bin\\docker.exe' images retail-app
                """
            }
        }

        stage('Prepare Docker Network') {
            steps {
                powershell """
                    & 'C:\\Users\\gayat\\AppData\\Local\\Programs\\DockerDesktop\\resources\\bin\\docker.exe' network inspect retail-network 2>\\$null
                    if (\\$LASTEXITCODE -ne 0) {
                        & 'C:\\Users\\gayat\\AppData\\Local\\Programs\\DockerDesktop\\resources\\bin\\docker.exe' network create retail-network
                    }
                """
            }
        }

        stage('Deploy Container') {
            steps {
                powershell """
                    Write-Host "Starting deployment..."

                    & 'C:\\Users\\gayat\\AppData\\Local\\Programs\\DockerDesktop\\resources\\bin\\docker.exe' rm -f retail-app-prod 2>\\$null

                    & 'C:\\Users\\gayat\\AppData\\Local\\Programs\\DockerDesktop\\resources\\bin\\docker.exe' run -d `
                        --name retail-app-prod `
                        --network retail-network `
                        -p 8081:8081 `
                        -e APP_VERSION=${params.VERSION} `
                        -e ENVIRONMENT=${params.ENVIRONMENT} `
                        retail-app:${params.VERSION}-${env.BUILD_NUMBER}

                    Write-Host "New container started."
                """
            }
        }

        stage('Health Check') {
            steps {
                powershell """
                    Write-Host "Waiting for application..."

                    Start-Sleep -Seconds 10

                    & 'C:\\Users\\gayat\\AppData\\Local\\Programs\\DockerDesktop\\resources\\bin\\docker.exe' inspect --format="{{.State.Health.Status}}" retail-app-prod

                    if (\\$LASTEXITCODE -ne 0) {
                        Write-Host "Health check failed."
                        exit 1
                    }

                    Write-Host "Health check completed."
                """
            }
        }

        stage('Deployment Status') {
            steps {
                powershell """
                    Write-Host "Running container:"
                    & 'C:\\Users\\gayat\\AppData\\Local\\Programs\\DockerDesktop\\resources\\bin\\docker.exe' ps

                    Write-Host "Container details:"
                    & 'C:\\Users\\gayat\\AppData\\Local\\Programs\\DockerDesktop\\resources\\bin\\docker.exe' inspect retail-app-prod
                """
            }
        }
    }
}