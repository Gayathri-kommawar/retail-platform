pipeline {
    agent any

    parameters {
        choice(
            name: 'DEPLOYMENT_ACTION',
            choices: ['DEPLOY', 'ROLLBACK'],
            description: 'Select deployment action'
        )

        choice(
            name: 'ENVIRONMENT',
            choices: ['UAT', 'PRODUCTION'],
            description: 'Select environment'
        )

        string(
            name: 'VERSION',
            defaultValue: '4.2.1',
            description: 'Version to deploy, for example 4.2.1'
        )

        choice(
            name: 'CONFIRM_PROD',
            choices: ['YES', 'NO'],
            description: 'Production deployment confirmation'
        )
    }

    environment {
        DOCKER_EXE = 'C:\\Users\\gayat\\AppData\\Local\\Programs\\DockerDesktop\\resources\\bin\\docker.exe'
        PREVIOUS_IMAGE = ''
        IMAGE_TAG = ''
    }

    stages {

        stage('Show Parameters') {
            steps {
                echo "DEPLOYMENT_ACTION = ${params.DEPLOYMENT_ACTION}"
                echo "ENVIRONMENT = ${params.ENVIRONMENT}"
                echo "VERSION = ${params.VERSION}"
                echo "CONFIRM_PROD = ${params.CONFIRM_PROD}"
            }
        }

        stage('Validate Production') {
            steps {
                script {
                    if (params.ENVIRONMENT == 'PRODUCTION' &&
                        params.CONFIRM_PROD != 'YES') {
                        error('PRODUCTION deployment blocked: CONFIRM_PROD must be YES.')
                    }

                    echo 'Production validation passed.'
                }
            }
        }

        stage('Validate Version') {
            steps {
                powershell """
                    & "\${env:DOCKER_EXE}" --version
                    git fetch --tags --force
                    git rev-parse "refs/tags/v${params.VERSION}"
                """
            }
        }

        stage('Checkout Selected Version') {
            steps {
                powershell """
                    git checkout "v${params.VERSION}"
                    git log -1 --oneline
                """
            }
        }

        stage('Build Docker Image') {
            steps {
                script {
                    def buildNumber = env.BUILD_NUMBER
                    env.IMAGE_TAG = "retail-app:${params.VERSION}-${buildNumber}"

                    echo "Building Docker image: ${env.IMAGE_TAG}"

                    powershell """
                        & "\${env:DOCKER_EXE}" build -t "${env.IMAGE_TAG}" .
                    """

                    echo "Docker image created: ${env.IMAGE_TAG}"
                }
            }
        }

        stage('Prepare Docker Network') {
            steps {
                powershell """
                    & "\${env:DOCKER_EXE}" network inspect retail-network

                    if (\$LASTEXITCODE -ne 0) {
                        Write-Host "Docker network does not exist. Creating it..."
                        & "\${env:DOCKER_EXE}" network create retail-network
                    }
                    else {
                        Write-Host "Docker network retail-network already exists."
                    }

                    exit 0
                """
            }
        }

        stage('Record Previous Production Image') {
            steps {
                script {
                    def result = powershell(
                        returnStdout: true,
                        script: """
                            & "\${env:DOCKER_EXE}" inspect retail-app-prod --format="{{.Config.Image}}"
                        """
                    ).trim()

                    if (result) {
                        env.PREVIOUS_IMAGE = result
                        echo "Previous production image: ${env.PREVIOUS_IMAGE}"
                    } else {
                        env.PREVIOUS_IMAGE = ''
                        echo "No previous production image found."
                    }
                }
            }
        }

        stage('Start Candidate') {
            steps {
                script {
                    def healthFail = 'false'

                    if (params.VERSION == '4.2.2') {
                        healthFail = 'true'
                        echo 'FAILURE INJECTION ENABLED for v4.2.2'
                    }

                    powershell """
                        & "\${env:DOCKER_EXE}" rm -f retail-app-candidate

                        & "\${env:DOCKER_EXE}" run -d `
                            --name retail-app-candidate `
                            --network retail-network `
                            -p 8082:8081 `
                            -e APP_VERSION=${params.VERSION} `
                            -e ENVIRONMENT=${params.ENVIRONMENT} `
                            -e HEALTH_FAIL=${healthFail} `
                            ${env.IMAGE_TAG}

                        exit 0
                    """
                }
            }
        }

        stage('Candidate Health Check') {
            steps {
                script {
                    sleep(time: 10, unit: 'SECONDS')

                    def candidateHealth = powershell(
                        returnStdout: true,
                        script: """
                            & "\${env:DOCKER_EXE}" inspect --format="{{.State.Health.Status}}" retail-app-candidate
                        """
                    ).trim()

                    echo "Candidate health status: ${candidateHealth}"

                    if (candidateHealth != 'healthy') {
                        error("Candidate health check FAILED: ${candidateHealth}")
                    }

                    echo 'Candidate health check PASSED.'
                }
            }
        }

        stage('Deploy New Version') {
            steps {
                powershell """
                    & "\${env:DOCKER_EXE}" rm -f retail-app-prod

                    & "\${env:DOCKER_EXE}" run -d `
                        --name retail-app-prod `
                        --network retail-network `
                        -p 8081:8081 `
                        -e APP_VERSION=${params.VERSION} `
                        -e ENVIRONMENT=${params.ENVIRONMENT} `
                        -e HEALTH_FAIL=false `
                        ${env.IMAGE_TAG}

                    exit 0
                """
            }
        }

        stage('Production Health Check') {
            steps {
                script {
                    sleep(time: 10, unit: 'SECONDS')

                    def productionHealth = powershell(
                        returnStdout: true,
                        script: """
                            & "\${env:DOCKER_EXE}" inspect --format="{{.State.Health.Status}}" retail-app-prod
                        """
                    ).trim()

                    echo "Production health status: ${productionHealth}"

                    if (productionHealth != 'healthy') {
                        error("Production health check FAILED: ${productionHealth}")
                    }

                    echo 'Production health check PASSED.'
                }
            }
        }

        stage('Remove Candidate') {
            steps {
                powershell """
                    & "\${env:DOCKER_EXE}" rm -f retail-app-candidate
                    exit 0
                """
            }
        }

        stage('Final Status') {
            steps {
                echo 'Deployment completed successfully.'
                echo "Version deployed: ${params.VERSION}"
                echo "Docker image: ${env.IMAGE_TAG}"
                echo "Environment: ${params.ENVIRONMENT}"
                echo 'Final status: SUCCESS'
            }
        }
    }

    post {

        failure {
            script {

                echo '======================================'
                echo 'DEPLOYMENT FAILED'
                echo 'STARTING AUTOMATIC ROLLBACK'
                echo '======================================'

                powershell """
                    & "\${env:DOCKER_EXE}" rm -f retail-app-candidate
                    exit 0
                """

                if (env.PREVIOUS_IMAGE?.trim()) {

                    echo "Restoring previous production image: ${env.PREVIOUS_IMAGE}"

                    powershell """
                        & "\${env:DOCKER_EXE}" rm -f retail-app-prod

                        & "\${env:DOCKER_EXE}" run -d `
                            --name retail-app-prod `
                            --network retail-network `
                            -p 8081:8081 `
                            -e APP_VERSION=4.2.1 `
                            -e ENVIRONMENT=PRODUCTION `
                            -e HEALTH_FAIL=false `
                            ${env.PREVIOUS_IMAGE}

                        exit 0
                    """

                    sleep(time: 10, unit: 'SECONDS')

                    def rollbackHealth = powershell(
                        returnStdout: true,
                        script: """
                            & "\${env:DOCKER_EXE}" inspect --format="{{.State.Health.Status}}" retail-app-prod
                        """
                    ).trim()

                    echo "Rollback health status: ${rollbackHealth}"

                    if (rollbackHealth == 'healthy') {
                        echo '======================================'
                        echo 'ROLLBACK VERIFIED'
                        echo 'Previous production image is HEALTHY'
                        echo '======================================'
                    } else {
                        echo '======================================'
                        echo 'ROLLBACK HEALTH CHECK FAILED'
                        echo '======================================'
                    }

                } else {

                    echo 'No previous production image was recorded.'
                    echo 'Rollback cannot be performed.'
                }

                echo 'Final status: FAILED'
            }
        }

        success {
            echo '======================================'
            echo 'FINAL STATUS: SUCCESS'
            echo '======================================'
        }
    }
}