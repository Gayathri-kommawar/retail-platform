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
                    def imageTag = "retail-app:${params.VERSION}-${buildNumber}"

                    env.IMAGE_TAG = imageTag

                    echo "Building Docker image: ${imageTag}"

                    powershell """
                        & "\${env:DOCKER_EXE}" build -t "${imageTag}" .
                    """

                    echo "Docker image created: ${imageTag}"
                }
            }
        }

        stage('Prepare Docker Network') {
            steps {
                powershell """
                    & "\${env:DOCKER_EXE}" network create retail-network 2>NUL
                    exit 0
                """
            }
        }

        stage('Record Previous Production Image') {
            steps {
                powershell """
                    & "\${env:DOCKER_EXE}" inspect retail-app-prod --format="{{.Config.Image}}" > previous-production-image.txt 2>NUL
                """

                script {
                    if (fileExists('previous-production-image.txt')) {
                        env.PREVIOUS_IMAGE =
                            readFile('previous-production-image.txt').trim()
                    }

                    if (env.PREVIOUS_IMAGE) {
                        echo "Previous production image: ${env.PREVIOUS_IMAGE}"
                    } else {
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
                        & "\${env:DOCKER_EXE}" rm -f retail-app-candidate 2>NUL

                        & "\${env:DOCKER_EXE}" run -d `
                            --name retail-app-candidate `
                            --network retail-network `
                            -p 8082:8081 `
                            -e APP_VERSION=${params.VERSION} `
                            -e ENVIRONMENT=${params.ENVIRONMENT} `
                            -e HEALTH_FAIL=${healthFail} `
                            ${env.IMAGE_TAG}
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
                    & "\${env:DOCKER_EXE}" rm -f retail-app-prod 2>NUL

                    & "\${env:DOCKER_EXE}" run -d `
                        --name retail-app-prod `
                        --network retail-network `
                        -p 8081:8081 `
                        -e APP_VERSION=${params.VERSION} `
                        -e ENVIRONMENT=${params.ENVIRONMENT} `
                        -e HEALTH_FAIL=false `
                        ${env.IMAGE_TAG}
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
                    & "\${env:DOCKER_EXE}" rm -f retail-app-candidate 2>NUL
                """
            }
        }

        stage('Final Status') {
            steps {
                echo "Deployment completed successfully."
                echo "Version deployed: ${params.VERSION}"
                echo "Docker image: ${env.IMAGE_TAG}"
                echo "Environment: ${params.ENVIRONMENT}"
                echo "Final status: SUCCESS"
            }
        }
    }

    post {
        failure {
            script {
                echo 'DEPLOYMENT FAILED.'
                echo 'Starting automatic rollback.'

                powershell """
                    & "\${env:DOCKER_EXE}" rm -f retail-app-candidate 2>NUL
                """

                if (env.PREVIOUS_IMAGE?.trim()) {

                    echo "Restoring previous production image: ${env.PREVIOUS_IMAGE}"

                    powershell """
                        & "\${env:DOCKER_EXE}" rm -f retail-app-prod 2>NUL

                        & "\${env:DOCKER_EXE}" run -d `
                            --name retail-app-prod `
                            --network retail-network `
                            -p 8081:8081 `
                            -e APP_VERSION=4.2.1 `
                            -e ENVIRONMENT=PRODUCTION `
                            -e HEALTH_FAIL=false `
                            ${env.PREVIOUS_IMAGE}
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
                        echo 'ROLLBACK VERIFIED: previous production image is healthy.'
                    } else {
                        echo 'ROLLBACK HEALTH CHECK FAILED.'
                    }

                } else {
                    echo 'No previous production image was recorded. Rollback cannot be performed.'
                }

                echo 'Final status: FAILED'
            }
        }

        success {
            echo 'Final status: SUCCESS'
        }
    }
}