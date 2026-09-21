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

        stage('Record Previous Production') {
            steps {
                powershell """
                    & 'C:\\Users\\gayat\\AppData\\Local\\Programs\\DockerDesktop\\resources\\bin\\docker.exe' inspect retail-app-prod --format="{{.Config.Image}}" 2>\\$null

                    if (\\$LASTEXITCODE -eq 0) {
                        \\$previousImage = & 'C:\\Users\\gayat\\AppData\\Local\\Programs\\DockerDesktop\\resources\\bin\\docker.exe' inspect retail-app-prod --format="{{.Config.Image}}"
                        Write-Host "Previous production image: \\$previousImage"
                        Set-Content -Path previous-production-image.txt -Value \\$previousImage
                    }
                    else {
                        Write-Host "No previous production container found."
                        Set-Content -Path previous-production-image.txt -Value ""
                    }
                """
            }
        }

        stage('Start Candidate') {
            steps {
                powershell """
                    Write-Host "Starting new version before removing old version..."

                    & 'C:\\Users\\gayat\\AppData\\Local\\Programs\\DockerDesktop\\resources\\bin\\docker.exe' rm -f retail-app-candidate 2>\\$null

                    \\$healthFail = "false"

                    if ("${params.VERSION}" -eq "4.2.2") {
                        \\$healthFail = "true"
                    }

                    & 'C:\\Users\\gayat\\AppData\\Local\\Programs\\DockerDesktop\\resources\\bin\\docker.exe' run -d `
                        --name retail-app-candidate `
                        --network retail-network `
                        -p 8082:8081 `
                        -e APP_VERSION=${params.VERSION} `
                        -e ENVIRONMENT=${params.ENVIRONMENT} `
                        -e HEALTH_FAIL=\\$healthFail `
                        retail-app:${params.VERSION}-${env.BUILD_NUMBER}

                    Write-Host "Candidate container started."
                    Write-Host "Candidate version: ${params.VERSION}"
                """
            }
        }

        stage('Candidate Health Check') {
            steps {
                script {
                    def healthy = false

                    for (int i = 1; i <= 12; i++) {
                        def status = powershell(
                            returnStdout: true,
                            script: """
                                & 'C:\\Users\\gayat\\AppData\\Local\\Programs\\DockerDesktop\\resources\\bin\\docker.exe' inspect --format="{{.State.Health.Status}}" retail-app-candidate
                            """
                        ).trim()

                        echo "Candidate health status: ${status}"

                        if (status == "healthy") {
                            healthy = true
                            break
                        }

                        if (status == "unhealthy") {
                            break
                        }

                        sleep(time: 5, unit: 'SECONDS')
                    }

                    if (!healthy) {
                        echo "NEW VERSION FAILED HEALTH CHECK."
                        error("Candidate deployment failed. Rollback required.")
                    }
                }
            }
        }

        stage('Switch Production') {
            steps {
                powershell """
                    Write-Host "Candidate is healthy."
                    Write-Host "Switching production to new version..."

                    & 'C:\\Users\\gayat\\AppData\\Local\\Programs\\DockerDesktop\\resources\\bin\\docker.exe' stop retail-app-prod 2>\\$null

                    & 'C:\\Users\\gayat\\AppData\\Local\\Programs\\DockerDesktop\\resources\\bin\\docker.exe' rm retail-app-prod 2>\\$null

                    & 'C:\\Users\\gayat\\AppData\\Local\\Programs\\DockerDesktop\\resources\\bin\\docker.exe' run -d `
                        --name retail-app-prod `
                        --network retail-network `
                        -p 8081:8081 `
                        -e APP_VERSION=${params.VERSION} `
                        -e ENVIRONMENT=${params.ENVIRONMENT} `
                        -e HEALTH_FAIL=false `
                        retail-app:${params.VERSION}-${env.BUILD_NUMBER}

                    Write-Host "New production container started."
                """
            }
        }

        stage('Production Health Check') {
            steps {
                script {
                    def healthy = false

                    for (int i = 1; i <= 12; i++) {
                        def status = powershell(
                            returnStdout: true,
                            script: """
                                & 'C:\\Users\\gayat\\AppData\\Local\\Programs\\DockerDesktop\\resources\\bin\\docker.exe' inspect --format="{{.State.Health.Status}}" retail-app-prod
                            """
                        ).trim()

                        echo "Production health status: ${status}"

                        if (status == "healthy") {
                            healthy = true
                            break
                        }

                        if (status == "unhealthy") {
                            break
                        }

                        sleep(time: 5, unit: 'SECONDS')
                    }

                    if (!healthy) {
                        error("Production health check failed.")
                    }
                }
            }
        }

        stage('Cleanup Candidate') {
            steps {
                powershell """
                    & 'C:\\Users\\gayat\\AppData\\Local\\Programs\\DockerDesktop\\resources\\bin\\docker.exe' rm -f retail-app-candidate 2>\\$null
                    Write-Host "Old candidate container removed."
                """
            }
        }

        stage('Deployment Status') {
            steps {
                powershell """
                    Write-Host "========== FINAL DEPLOYMENT STATE =========="

                    Write-Host "Previous production image:"
                    Get-Content previous-production-image.txt

                    Write-Host "New production image:"
                    & 'C:\\Users\\gayat\\AppData\\Local\\Programs\\DockerDesktop\\resources\\bin\\docker.exe' inspect --format="{{.Config.Image}}" retail-app-prod

                    Write-Host "Running containers:"
                    & 'C:\\Users\\gayat\\AppData\\Local\\Programs\\DockerDesktop\\resources\\bin\\docker.exe' ps

                    Write-Host "Production health:"
                    & 'C:\\Users\\gayat\\AppData\\Local\\Programs\\DockerDesktop\\resources\\bin\\docker.exe' inspect --format="{{.State.Health.Status}}" retail-app-prod
                """
            }
        }
    }

    post {

        failure {
            powershell """
                Write-Host "========== AUTOMATIC ROLLBACK =========="

                & 'C:\\Users\\gayat\\AppData\\Local\\Programs\\DockerDesktop\\resources\\bin\\docker.exe' rm -f retail-app-candidate 2>\\$null

                if (Test-Path previous-production-image.txt) {
                    \\$previousImage = Get-Content previous-production-image.txt

                    if (\\$previousImage -and \\$previousImage.Trim() -ne "") {
                        Write-Host "Restoring previous production image: \\$previousImage"

                        & 'C:\\Users\\gayat\\AppData\\Local\\Programs\\DockerDesktop\\resources\\bin\\docker.exe' rm -f retail-app-prod 2>\\$null

                        & 'C:\\Users\\gayat\\AppData\\Local\\Programs\\DockerDesktop\\resources\\bin\\docker.exe' run -d `
                            --name retail-app-prod `
                            --network retail-network `
                            -p 8081:8081 `
                            -e APP_VERSION=4.2.1 `
                            -e ENVIRONMENT=PRODUCTION `
                            -e HEALTH_FAIL=false `
                            \\$previousImage

                        Start-Sleep -Seconds 10

                        \\$health = & 'C:\\Users\\gayat\\AppData\\Local\\Programs\\DockerDesktop\\resources\\bin\\docker.exe' inspect --format="{{.State.Health.Status}}" retail-app-prod

                        Write-Host "Rollback health status: \\$health"

                        if (\\$health.Trim() -eq "healthy") {
                            Write-Host "ROLLBACK VERIFIED: previous production image is healthy."
                        }
                        else {
                            Write-Host "ROLLBACK HEALTH CHECK FAILED."
                        }
                    }
                    else {
                        Write-Host "No previous production image was recorded."
                    }
                }
            """
        }
    }
}