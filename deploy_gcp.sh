#!/bin/bash
# Script de Despliegue en GCP Cloud Run para Alura Agente

set -e

echo "🚀 Iniciando despliegue de Alura Agente en Google Cloud Platform (GCP)..."

# Configurar variables
PROJECT_ID=$(gcloud config get-value project 2>/dev/null || echo "")
SERVICE_NAME="alura-agente"
REGION="us-central1"

if [ -z "$PROJECT_ID" ]; then
  echo "❌ Error: No tienes un proyecto activo configurado en gcloud."
  echo "Ejecuta: gcloud config set project TU_PROJECT_ID"
  exit 1
fi

echo "📌 Proyecto GCP Activo: $PROJECT_ID"
echo "📌 Servicio Cloud Run: $SERVICE_NAME"
echo "📌 Región: $REGION"

# Habilitar API de Cloud Run y Artifact Registry / Cloud Build
echo "⚙️ Habilitando APIs de Google Cloud..."
gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com

# Desplegar directamente desde el código fuente con Cloud Build
echo "📦 Construyendo contenedor y desplegando en GCP Cloud Run..."
gcloud run deploy $SERVICE_NAME \
  --source . \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --memory 1Gi \
  --cpu 1

echo "--------------------------------------------------------"
echo "✅ ¡Despliegue exitoso!"
echo "🌐 URL pública de tu Alura Agente:"
gcloud run services describe $SERVICE_NAME --platform managed --region $REGION --format 'value(status.url)'
echo "--------------------------------------------------------"
