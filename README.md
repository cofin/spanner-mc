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
  vpcaccess.googleapis.com

# create service account to run container
gcloud iam service-accounts create spannermc-service-account
export CLOUDRUN_SERVICE_ACCOUNT=$(gcloud iam service-accounts list \
    --filter spannermc-service-account --format "value(email)")
export PROJECT_NUMBER=$(gcloud projects describe ${PROJECT_ID} --format 'value(projectNumber)')
export CLOUDBUILD_SERVICE_ACCOUNT=${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com

# create secrets
echo DB_URL=\"spanner+spanner:///projects/\${PROJECT_ID}/\${SPANNER_INSTANCE}/databases/\${SPANNER_DATABASE}\" > .env.cloudrun
echo SECRET_KEY=\"$(cat /dev/urandom | LC_ALL=C tr -dc 'a-zA-Z0-9' | fold -w 50 | head -n 1)\" >> .env.cloudrun
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
echo _REGION=\"${REGION_NAME}\" >> .gcloud.env
echo _SERVICE_NAME=\"spanner-mc\" >> .gcloud.env
echo _SERVICE_ACCOUNT=\"${CLOUDRUN_SERVICE_ACCOUNT}\" >> .gcloud.env
echo _ENV_SECRETS=\"runtime-secrets\" >> .gcloud.env
echo _MEMORY_SIZE=\"1Gi\" >> .gcloud.env
echo _MAX_INSTANCES=3 >> .gcloud.env
echo _CONTAINER_IMAGE=\"docker.io/codyfincher/spannermc:latest\" >> .gcloud.env
```
