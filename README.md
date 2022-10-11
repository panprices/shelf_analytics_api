# What is this
The middleware used in the digital shelf analytics solution. The product was originally developed for Venture Design,
but the scope was defined to include multiple clients in the future. 

# How to deploy 
```bash
gcloud run deploy shelf-analytics-middleware --update-secrets=FIREBASE_API_KEY=firebase_api_key:latest --source .
```