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
            description: 'Version to deploy'
        )

        choice(
            name: 'CONFIRM_PROD',
            choices: ['YES', 'NO'],
            description: 'Production deployment confirmation'
        )
    }

    environment {
        DOCKER_EXE = 'C:\\Users\\gayat\\AppData\\Local\\Programs\\DockerDesktop\\resources\\bin\\docker.exe'
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
                    exit 0
                """
            }
        }

        stage('Build Docker Image') {
            steps {
                script {
                    def imageTag = "retail-app:${params.VERSION}-${env.BUILD_NUMBER}"

                    echo "Building Docker image: ${imageTag}"

                    powershell """
                        & "\${env:DOCKER_EXE}" build -t "${imageTag}" .
                    """

                    writeFile(
                        file: 'image-tag.txt',
                        text: imageTag
                    )

                    echo "Docker image created: ${imageTag}"
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
                    def previousImage = powershell(
                        returnStdout: true,
                        script: """
                            & "\${env:DOCKER_EXE}" ps -a --filter "name=retail-app-prod" --format "{{.Image}}"
                            exit 0
                        """
                    ).trim()

                    if (previousImage) {

                        writeFile(
                            file: 'previous-image.txt',
                            text: previousImage
                        )

                        echo "Previous production image: ${previousImage}"

                    } else {

                        writeFile(
                            file: 'previous-image.txt',
                            text: ''
                        )

                        echo "No previous production container found. This is the first deployment."
                    }
                }
            }
        }

        stage('Start Candidate') {
            steps {
                script {
                    def imageTag = readFile('image-tag.txt').trim()
                    def healthFail = 'false'

                    if (params.VERSION == '4.2.2') {
                        healthFail = 'true'
                        echo 'FAILURE INJECTION ENABLED for v4.2.2'
                    }

                    echo "Starting candidate image: ${imageTag}"

                    powershell """
                        & "\${env:DOCKER_EXE}" rm -f retail-app-candidate
                        exit 0
                    """

                    powershell """
                        & "\${env:DOCKER_EXE}" run -d `
                            --name retail-app-candidate `
                            --network retail-network `
                            -p 8082:8081 `
                            -e APP_VERSION=${params.VERSION} `
                            -e ENVIRONMENT=${params.ENVIRONMENT} `
                            -e HEALTH_FAIL=${healthFail} `
                            ${imageTag}
                    """
                }
            }
        }

        stage('Candidate Health Check') {
            steps {
                script {
                    def candidateHealth = 'starting'

                    for (int i = 1; i <= 6; i++) {
                        sleep(time: 5, unit: 'SECONDS')

                        candidateHealth = powershell(
                            returnStdout: true,
                            script: """
                                & "\${env:DOCKER_EXE}" inspect --format="{{.State.Health.Status}}" retail-app-candidate
                            """
                        ).trim()

                        echo "Candidate health check ${i}/6: ${candidateHealth}"

                        if (candidateHealth == 'healthy') {
                            echo 'Candidate health check PASSED.'
                            break
                        }

                        if (candidateHealth == 'unhealthy') {
                            error("Candidate health check FAILED: ${candidateHealth}")
                        }
                    }

                    if (candidateHealth != 'healthy') {
                        error("Candidate health check FAILED: ${candidateHealth}")
                    }
                }
            }
        }

        stage('Deploy New Version') {
            steps {
                script {
                    def imageTag = readFile('image-tag.txt').trim()

                    echo "Deploying production image: ${imageTag}"

                    powershell """
                        & "\${env:DOCKER_EXE}" rm -f retail-app-prod
                        exit 0
                    """

                    powershell """
                        & "\${env:DOCKER_EXE}" run -d `
                            --name retail-app-prod `
                            --network retail-network `
                            -p 8081:8081 `
                            -e APP_VERSION=${params.VERSION} `
                            -e ENVIRONMENT=${params.ENVIRONMENT} `
                            -e HEALTH_FAIL=false `
                            ${imageTag}
                    """
                }
            }
        }

        stage('Production Health Check') {
            steps {
                script {
                    def productionHealth = 'starting'

                    for (int i = 1; i <= 6; i++) {
                        sleep(time: 5, unit: 'SECONDS')

                        productionHealth = powershell(
                            returnStdout: true,
                            script: """
                                & "\${env:DOCKER_EXE}" inspect --format="{{.State.Health.Status}}" retail-app-prod
                            """
                        ).trim()

                        echo "Production health check ${i}/6: ${productionHealth}"

                        if (productionHealth == 'healthy') {
                            echo 'Production health check PASSED.'
                            break
                        }

                        if (productionHealth == 'unhealthy') {
                            error("Production health check FAILED: ${productionHealth}")
                        }
                    }

                    if (productionHealth != 'healthy') {
                        error("Production health check FAILED: ${productionHealth}")
                    }
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
                echo '======================================'
                echo 'DEPLOYMENT SUCCESSFUL'
                echo "Version: ${params.VERSION}"
                echo "Environment: ${params.ENVIRONMENT}"
                echo 'Final status: SUCCESS'
                echo '======================================'
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

                def previousImage = fileExists('previous-image.txt')
                    ? readFile('previous-image.txt').trim()
                    : ''

                if (previousImage) {

                    echo "Restoring previous production image: ${previousImage}"

                    powershell """
                        & "\${env:DOCKER_EXE}" rm -f retail-app-prod
                        exit 0
                    """

                    powershell """
                        & "\${env:DOCKER_EXE}" run -d `
                            --name retail-app-prod `
                            --network retail-network `
                            -p 8081:8081 `
                            -e APP_VERSION=4.2.1 `
                            -e ENVIRONMENT=PRODUCTION `
                            -e HEALTH_FAIL=false `
                            ${previousImage}
                    """

                    def rollbackHealth = 'starting'

                    for (int i = 1; i <= 6; i++) {
                        sleep(time: 5, unit: 'SECONDS')

                        rollbackHealth = powershell(
                            returnStdout: true,
                            script: """
                                & "\${env:DOCKER_EXE}" inspect --format="{{.State.Health.Status}}" retail-app-prod
                            """
                        ).trim()

                        echo "Rollback health check ${i}/6: ${rollbackHealth}"

                        if (rollbackHealth == 'healthy') {
                            break
                        }
                    }

                    if (rollbackHealth == 'healthy') {

                        echo '======================================'
                        echo 'ROLLBACK VERIFIED'
                        echo 'Previous production image is HEALTHY'
                        echo "Restored image: ${previousImage}"
                        echo '======================================'

                    } else {

                        echo 'ROLLBACK HEALTH CHECK FAILED.'
                    }

                } else {

                    echo 'No previous production image exists.'
                    echo 'This was the first deployment, so there is nothing to rollback to.'
                }

                echo 'Final status: FAILED'
            }
        }

        success {
            echo 'FINAL STATUS: SUCCESS'
        }
    }
}