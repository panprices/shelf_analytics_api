# What is this
The middleware used in the digital shelf analytics solution. The product was originally developed for Venture Design,
but the scope was defined to include multiple clients in the future. 

# How to deploy 

Careful! This command is missing the connexion to cloud SQL. 

```bash
gcloud run deploy shelf-analytics-middleware --update-secrets=FIREBASE_API_KEY=firebase_api_key:latest,DB_NAME=POSTGRES_SANDBOX_SHELF_ANALYTICS_DB:latest,DB_USER=POSTGRES_SANDBOX_USER:latest,DB_PASS=POSTGRES_SANDBOX_PASSWORD:latest,DB_HOST=POSTGRES_SANDBOX_HOST:latest --add-cloudsql-instances=panprices:europe-west1:panprices-core-sandbox --source .
```