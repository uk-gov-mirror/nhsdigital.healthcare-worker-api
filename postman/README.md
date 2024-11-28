# Postman Collection

The files in this directory contain the postman collection and environment files. To setup locally:

1. Open postman and select "Import" in the left panel
2. Click the "files" link to open the selector dialog
3. Select all the json files in this directory and click "Open"
4. Confirm the selected files with the "Import" button
5. Before sending any requests, you have to add the private key used for authentication:
   1. Select the "Generate JWT" request
   2. Go to the "Authorization" tab
   3. Click "Select File" button on the "Private Key" line
   4. Navigate to `integration_tests/utils/test-1.pem` and click "Open"

## Sending the requests

Before sending any requests, select the environment you're going to run against.

We need to authenticate as the test service before sending requests. This is done by generating a JWT, and then
sending it to CIS auth. This generates an access token which can be used in future requests. First send the
"Generate JWT" request, then the "Auth" one. The first request is a placeholder for generating the JWT, the actual
response isn't important since the JWT is generated as part of the request.

The access token returned from the "Auth" call will be valid for 10 minutes until it needs to be re-generated.
