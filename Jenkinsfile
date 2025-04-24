pipeline {
    agent any
    
    environment {
        IMAGE_NAME = "idrisniyi94/password-app"
        IMAGE_TAG = "${BUILD_NUMBER}"
        CONTAINER_NAME = "lab-server-password-app"
    }
    
    stages {
        stage('Git Checkout') {
            steps {
                checkout scmGit(branches: [[name: '*/master']], extensions: [], userRemoteConfigs: [[url: 'https://github.com/stwins60/password-reminder.git']])
            }
        }
        stage("Docker Build") {
            steps {
                sh "docker build -t ${IMAGE_NAME}:v-0.0.${IMAGE_TAG} ."
            }
        }
        stage("Trivy Scan") {
            steps {
                script {
                    sh "trivy image --exit-code 1 --severity HIGH,CRITICAL ${IMAGE_NAME}:v-0.0.${IMAGE_TAG}"
                }
            }
        }
        stage("Stop Old Container") {
            steps {
                sh """
                    if [ \$(docker ps -q -f name=${CONTAINER_NAME}) ]; then
                        echo "Stopping and removing existing container: ${CONTAINER_NAME}"
                        docker stop ${CONTAINER_NAME}
                        docker rm ${CONTAINER_NAME}
                    else
                        echo "No existing container named ${CONTAINER_NAME} found."
                    fi
                """
            }
        }
       stage("Run App") {
           steps {
               sh "docker run -d --name ${CONTAINER_NAME} -p 3414:5000 -e USER=lab-server ${IMAGE_NAME}:v-0.0.${IMAGE_TAG}"
           }
       }
    }
    post {
        always {
            echo "cleaning up unused image or exited container"
            sh "docker system prune -f"
        }
    }
}