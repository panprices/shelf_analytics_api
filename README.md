# What is this
The middleware used in the digital shelf analytics solution.


# How to run

## 1. Make sure you are logger into the GCP CLI
Run the following command:

```bash
gcloud config list project
```

You want the following result: `project = panprices`. If you are seeing something else you can just run this:

```bash
gcloud init
```

## 2. Create a .env file
We have a .example_env file which you need to save as .env and replace the values with secrets from GCP's Secret Manager: https://console.cloud.google.com/security/secret-manager?project=panprices

You can do this automatically by running the following script and specifying in a flag if you want the --sandbox or --production environment secrets.: 

```bash
chmod +x get_env_from_gcp.sh
./get_env_from_gcp.sh --sandbox
```

## 3. Run the GCP Cloud SQL Proxy

Download it here: https://cloud.google.com/sql/docs/postgres/sql-proxy

Run it with the following for sandbox: 

```bash
./cloud_sql_proxy -instances=panprices:europe-west1:panprices-core-sandbox=tcp:5432
```

And for production:

```bash
./cloud_sql_proxy -instances=panprices:europe-west1:panprices-core=tcp:5432
```

## 4. Install the dependencies in a pipenv
```bash
pipenv install
```

## 5. Start a pipenv shell
```bash
pipenv shell
```

## 6. Run the app in the new shell
```bash
python -m uvicorn app.main:app --reload --log-level debug
```

# Integration tests / benchmark 

Make sure that: 
1. The API is running on localhost:8000
2. You are connected to the database through cloud-sql-proxy.
3. You replaced the API JWT in [config](benchmark/config.py) with a valid one (can be grabbed from the local storage in
your browser by visiting the [production website](https://app.getloupe.co))