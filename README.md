# Stock Screener - Cloud Function

This project implements a stock screener that runs on Google Cloud Functions. It calculates stock screening metrics based on stock data, and sends the results via email every workday at 16:00. The credentials for sending emails are securely managed using Google Cloud Secret Manager.

## Architecture

- **Google Cloud Functions**: Executes the stock screener and sends the results via email.
- **Google Cloud Secret Manager**: Stores and retrieves sensitive email credentials.
- **Google Cloud Scheduler**: Triggers the Cloud Function every workday at 16:00.

## Deployment

1. **Deploy the Cloud Function**:

   ```sh
   gcloud functions deploy screener_run \
   --runtime python39 \
   --trigger-http \
   --allow-unauthenticated \
   --entry-point screener_run
   --set-secrets 'CREDENTIALS={Your Secrets Manager object URL}' \
   ```

2. **Set up the Cloud Scheduler**:
   - Navigate to Cloud Scheduler in the Google Cloud Console.
   - Create a new job with the following settings:
     - Frequency: `0 16 * * 1-5` (every workday at 16:00)
     - Target: HTTP
     - URL: [Your Cloud Function URL]
     - HTTP Method: POST

## Usage

The Cloud Function automatically runs every workday at 16:00, triggered by Cloud Scheduler. It performs the following steps:

1. Fetches the credentials from Secret Manager.
2. Reads the stock data from the provided CSV file.
3. Calculates the stock screening metrics.
4. Sends the results via email.

## Environment Variables

- **CREDENTIALS**: The JSON structure containing the email credentials, stored in Secret Manager.

## Security

Sensitive information such as email credentials are securely stored in Google Cloud Secret Manager, ensuring they are not hard-coded in the source code. Access to the Secret Manager should be tightly controlled using IAM roles and permissions.
