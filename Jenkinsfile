pipeline {
    agent any

    environment {
        PROJECT_NAME = "pipeline-test"
        SONARQUBE_URL = "http://sonarqube:9000"
        SONARQUBE_TOKEN = "sqa_d8a9666b36e5cc9a23732692362a620bbc36a7e8"
        FLASK_PORT = '5000'
        TARGET_URL = "http://127.0.0.1:${FLASK_PORT}"
    }

    stages {
        stage('Install Python') {
            steps {
                sh '''
                    apt update
                    apt install -y python3 python3-venv python3-pip
                '''
            }
        }
        
        stage('Setup Environment') {
            steps {
                sh '''
                    python3 -m venv venv
                    . venv/bin/activate
                    pip install --upgrade pip
                    pip install -r requirements.txt
                '''
            }
        }

        stage('Python Security Audit') {
            steps {
                sh '''
                    . venv/bin/activate
                    pip install pip-audit
                    mkdir -p dependency-check-report
                    pip-audit -r requirements.txt -f markdown -o dependency-check-report/pip-audit.md || true
                '''
            }
        }

        stage('Start Flask server') {
            steps {
                // launch the app in background, keep its PID
                sh '''
                    . venv/bin/activate
                    nohup python vulnerable_server.py > flask.log 2>&1 &
                    echo $! > flask.pid
                    # wait until the HTTP endpoint answers
                    for i in {1..15}; do
                        if curl -s ${TARGET_URL}/ > /dev/null; then
                            echo "Flask is up"
                            break
                        fi
                        sleep 1
                    done
                '''
            }
        }

        stage('OWASP ZAP (DAST Scan)') {
            agent {
                docker {
                    image 'zaproxy/zap-stable'
                    args '-v $WORKSPACE:/zap/wrk'
                }

            }
            steps {
                echo "Ejecutando escaneo dinámico con OWASP ZAP..."
                sh '''
                    zap-baseline.py \
                    -t ${TARGET_URL} \
                    -r zap_report.html
                '''
            }
        }

        stage('Stop Flask server') {
            steps {
                sh '''
                    if [ -f flask.pid ]; then
                        kill $(cat flask.pid) && echo "Flask stopped"
                    else
                        echo "PID file not found"
                    fi
                '''
            }
        }
        
        stage('SonarQube Analysis') {
            steps {
                script {
                    def scannerHome = tool 'SonarQube Scanner'
                    withSonarQubeEnv('SonarQube Install') {
                        sh """
                            ${scannerHome}/bin/sonar-scanner \
                                -Dsonar.projectKey=$PROJECT_NAME \
                                -Dsonar.sources=. \
                                -Dsonar.host.url=$SONARQUBE_URL \
                                -Dsonar.login=$SONARQUBE_TOKEN
                        """
                    }
                }
            }
        }

        stage('Dependency Check') {
            environment {
                NVD_API_KEY = credentials('nvdApiKey')
            }
            steps {
                dependencyCheck additionalArguments: "--scan . --format HTML --out dependency-check-report --enableExperimental --enableRetired --disableRetireJS --nvdApiKey ${NVD_API_KEY}", odcInstallation: 'Dependency Check'
            }
        }

        stage('Publish Reports') {
            steps {
                publishHTML([
                    allowMissing: false,
                    alwaysLinkToLastBuild: true,
                    keepAll: true,
                    reportDir: 'dependency-check-report',
                    reportFiles: 'dependency-check-report.html',
                    reportName: 'OWASP Dependency Check Report'
                ])
            }
        }


    }

}
