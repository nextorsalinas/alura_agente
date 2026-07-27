@echo off
echo 🚀 Iniciando despliegue de Alura Agente en Google Cloud Platform (GCP)...

set SERVICE_NAME=alura-agente
set REGION=us-central1

echo ⚙️ Habilitando APIs necesarias en GCP...
call gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com

echo 📦 Construyendo imagen y desplegando en Cloud Run...
call gcloud run deploy %SERVICE_NAME% --source . --platform managed --region %REGION% --allow-unauthenticated --memory 1Gi --cpu 1

echo --------------------------------------------------------
echo ✅ ¡Despliegue exitoso!
echo 🌐 URL pública de tu Alura Agente en GCP:
call gcloud run services describe %SERVICE_NAME% --platform managed --region %REGION% --format "value(status.url)"
echo --------------------------------------------------------
pause
