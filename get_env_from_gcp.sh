#!/bin/bash

# Function to print usage
usage() {
  echo "Usage: $0 [--production|--sandbox]"
  exit 1
}

# Check if the correct number of arguments is provided
if [ "$#" -ne 1 ]; then
  usage
fi

# Define the map for environment variables and their corresponding secret names
SECRET_MAP=(
  "FIREBASE_API_KEY=firebase_api_key"
  "MAGIC_API_SECRET_KEY=MAGIC_API_SECRET_KEY"
  "POSTMARK_API_TOKEN=POSTMARK_API_TOKEN"
  "JWT_SECRET=SHELF_ANALYTICS_JWT_SECRET"
  "FERNET_SECRET_KEY=API_KEYS_FERNET_SECRET"
  "API_KEYS_SECRET_SALT=API_KEYS_SECRET_SALT"
  "SANDBOX_API_KEY=SANDBOX_API_KEY"
)

# Fetch the secret values based on the provided flag
fetch_secrets() {
  local env="$1"
  if [ "$env" = "production" ]; then
    db_user=$(gcloud secrets versions access latest --secret=POSTGRES_PRODUCTION_USER)
    db_pass=$(gcloud secrets versions access latest --secret=POSTGRES_PRODUCTION_PASSWORD)
  elif [ "$env" = "sandbox" ]; then
    db_user=$(gcloud secrets versions access latest --secret=POSTGRES_SANDBOX_USER)
    db_pass=$(gcloud secrets versions access latest --secret=POSTGRES_SANDBOX_PASSWORD)
  else
    usage
  fi

  # Fetch the secrets from the SECRET_MAP
  for item in "${SECRET_MAP[@]}"; do
    env_var_name="${item%%=*}"
    secret_name="${item#*=}"
    value=$(gcloud secrets versions access latest --secret="$secret_name")
    eval "$env_var_name='$value'"
  done
}

# Update the .env file with the fetched secrets
update_env_file() {
  local env_file=".env"
  cp .env.example $env_file

  # Determine if the system is macOS
  if [[ "$OSTYPE" == "darwin"* ]]; then
    sed -i '' "s/^DB_USER=.*/DB_USER=$db_user/" $env_file
    sed -i '' "s/^DB_PASS=.*/DB_PASS=$db_pass/" $env_file

    for item in "${SECRET_MAP[@]}"; do
      env_var_name="${item%%=*}"
      value=$(eval echo \$$env_var_name)
      sed -i '' "s/^$env_var_name=.*/$env_var_name=$value/" $env_file
    done
  else
    sed -i "s/^DB_USER=.*/DB_USER=$db_user/" $env_file
    sed -i "s/^DB_PASS=.*/DB_PASS=$db_pass/" $env_file

    for item in "${SECRET_MAP[@]}"; do
      env_var_name="${item%%=*}"
      value=$(eval echo \$$env_var_name)
      sed -i "s/^$env_var_name=.*/$env_var_name=$value/" $env_file
    done
  fi
}

# Determine the environment based on the provided flag
case $1 in
  --production)
    environment="production"
    ;;
  --sandbox)
    environment="sandbox"
    ;;
  *)
    usage
    ;;
esac

# Fetch the secrets
fetch_secrets $environment

# Check if the secrets were fetched successfully
if [ -z "$db_user" ] || [ -z "$db_pass" ]; then
  echo "Failed to fetch the secret values."
  exit 1
fi

# Update the .env file
update_env_file $environment

echo ".env file created successfully with the $environment environment."
