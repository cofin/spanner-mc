# Cloud Run deployment

```bash
export PROJECT_ID=[PROJECT_ID]
export REGION_NAME=[REGION_NAME]
export ZONE=[ZONE]
export SPANNER_INSTANCE=[SPANNER_INSTANCE]
export SPANNER_DATABASE=[SPANNER_DATABASE]


# set project
gcloud config set project $PROJECT_ID

# enable APIs
gcloud services enable \
  run.googleapis.com \
  compute.googleapis.com \
  cloudbuild.googleapis.com \
  secretmanager.googleapis.com \
  artifactregistry.googleapis.com \
  vpcaccess.googleapis.com \
  iam.googleapis.com

# create service account to run container
gcloud iam service-accounts create spannermc-service-account


export PROJECT_NUMBER=$(gcloud projects describe ${PROJECT_ID} --format 'value(projectNumber)')
export CLOUDBUILD_SERVICE_ACCOUNT=${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com
export CLOUDRUN_SERVICE_ACCOUNT=$(gcloud iam service-accounts list \
    --filter spannermc-service-account --format "value(email)")
# create secrets
echo DB_URL=\"spanner+spanner:///projects/${PROJECT_ID}/instances/${SPANNER_INSTANCE}/databases/${SPANNER_DATABASE}\" > .env.cloudrun
echo SECRET_KEY=\"$(cat /dev/urandom | LC_ALL=C tr -dc 'a-zA-Z0-9' | fold -w 50 | head -n 1)\" >> .env.cloudrun
echo LITESTAR_APP="\"spannermc.asgi:create_app\"" >> .env.cloudrun
echo BACKEND_CORS_ORIGINS=[\"*\"] >> .env.cloudrun
echo DEBUG=\"False\" >> .env.cloudrun

gcloud secrets create runtime-secrets --data-file .env.cloudrun
# allow cloudbuild to execute migrations and access objects
gcloud secrets add-iam-policy-binding runtime-secrets \
    --member serviceAccount:${CLOUDRUN_SERVICE_ACCOUNT} \
    --role roles/secretmanager.secretAccessor
gcloud secrets add-iam-policy-binding runtime-secrets \
    --member serviceAccount:${CLOUDBUILD_SERVICE_ACCOUNT} \
    --role roles/secretmanager.secretAccessor


# create .gcloud execution env file for deployment
echo _PROJECT_ID=\"${PROJECT_ID}\"  > .gcloud.env
echo _REGION_NAME=\"${REGION_NAME}\" >> .gcloud.env
echo _ZONE_NAME=\"${ZONE}\" >> .gcloud.env
echo _SERVICE_NAME=\"spanner-mc\" >> .gcloud.env
echo _SERVICE_ACCOUNT=\"${CLOUDRUN_SERVICE_ACCOUNT}\" >> .gcloud.env
echo _ENV_SECRETS=\"runtime-secrets\" >> .gcloud.env
echo _MEMORY_SIZE=\"1Gi\" >> .gcloud.env
echo _MAX_INSTANCES=3 >> .gcloud.env
echo _CONTAINER_IMAGE=\"docker.io/codyfincher/spannermc:latest\" >> .gcloud.env

# grant access to the spanner instance
gcloud spanner databases add-iam-policy-binding ${SPANNER_DATABASE} \
    --instance ${SPANNER_INSTANCE} \
    --member "serviceAccount:${CLOUDRUN_SERVICE_ACCOUNT}" \
    --role roles/spanner.databaseAdmin
gcloud spanner databases add-iam-policy-binding ${SPANNER_DATABASE} \
    --instance ${SPANNER_INSTANCE} \
    --member "serviceAccount:${CLOUDBUILD_SERVICE_ACCOUNT}" \
    --role roles/spanner.databaseAdmin

# allow the service accounts to execute cloudrun
gcloud beta run services add-iam-policy-binding spannermc \
  --member=serviceAccount:${CLOUDRUN_SERVICE_ACCOUNT} \
  --role=roles/run.admin \
  --project=$PROJECT_ID \
  --region=$REGION_NAME
gcloud beta run services add-iam-policy-binding spannermc \
  --member=serviceAccount:${CLOUDBUILD_SERVICE_ACCOUNT} \
  --role=roles/run.admin \
  --project=$PROJECT_ID \
  --region=$REGION_NAME
gcloud beta iam service-accounts add-iam-policy-binding ${CLOUDRUN_SERVICE_ACCOUNT} \
  --member=serviceAccount:${CLOUDBUILD_SERVICE_ACCOUNT} \
  --role roles/iam.serviceAccountUser
  --project=$PROJECT_ID \
  --region=$REGION_NAME

# deploy the service
gcloud beta run services add-iam-policy-binding --region=us-east4 --member serviceAccount:${CLOUDBUILD_SERVICE_ACCOUNT} --role=roles/run.invoker spannermc
gcloud run services add-iam-policy-binding spannermc \
    --member="allUsers" \
    --role="roles/run.invoker"
gcloud run deploy spannermc \
    --image=$REGION_NAME-docker.pkg.dev/$PROJECT_ID/spannermc-artifacts/spanner-mc@sha256:b77df72393c12b9f59c7e1de11be18635601d1cb3f5917ada09d952ac6c4c133 \
    --allow-unauthenticated \
    --service-account=${CLOUDRUN_SERVICE_ACCOUNT} \
    --max-instances=5 \
    --execution-environment=gen2 \
    --cpu-boost \
    --region=$REGION_NAME \
    --project=$PROJECT_ID
```
