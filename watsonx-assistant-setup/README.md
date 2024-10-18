# Steps to Connect this Application to watsonx Assistant

You connect your assistant by using the api specification to add a custom extension.

### Download the api specifications

Download the [sequifi_openapi_v1.json](./sequifi_openapi_v1.json) and [texttosql_openapi_v1.json](./texttosql_openapi_v1.json) specification files. 

Use these specification files to create and add the extensions to your assistant.

### Build and add extension

1.  In your assistant, on the **Integrations** page, click **Build custom extension** and use the desired specification file to build a custom extension named `RAG LLM App`. For general instructions on building any custom extension, see [Building the custom extension](https://cloud.ibm.com/docs/watson-assistant?topic=watson-assistant-build-custom-extension#building-the-custom-extension).

1.  After you build the extension, and it appears on your **Integrations** page, click **Add** to add it to your assistant. For general instructions on adding any custom extension, see [Adding an extension to your assistant](https://cloud.ibm.com/docs/watson-assistant?topic=watson-assistant-add-custom-extension).

1.  For the `texttosql` extension, under **Authentication**, choose **API key auth**. For **API key**, copy and paste the value you set for **APP_API_KEY** in your environment variables.

1.  In **Servers**, under **Server Variables**, add the url (without the https) for your hosted application as `llm_route`. 

If you add apis and capabilities to this application, feel free to add them to the openapi specification. The application is intended to be an example of how to get started. If you add APIs after the Actions have been loaded, you will need to download your Actions, upload the new Open API spec and re-upload your Actions.

## Upload sample actions

This utility includes [a JSON file with sample actions](./Sequifi-IBM-POC-action.json) that are configured to use the above extensions.

Use **Actions Global Settings** (see wheel icon top right of **Actions** page) to upload the `Sequifi-IBM-POC-action.json` to your assistant. For more information, see [Uploading](https://cloud.ibm.com/docs/watson-assistant?topic=watson-assistant-admin-backup-restore#backup-restore-import). You may also need to refresh the action **Preview** chat, after uploading, to get all the session variables initialized before these actions will work correctly.

**NOTE**: If you import the actions _before_ configuring the extension, you will see errors on the actions because it could not find the extension. Configure the extension (as described [above](#prerequisites)), and re-import the action JSON file.

| Action                        | Description                                                                                                                                                                                   |
| ----------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| SQL Generation | An action flow that will classify a natural language question, if an SQL type query, will generate the SQL, execute and return results|
| No Action Matches | This is created by watsonx Assistant, but for this starter kit it is configured to trigger the "SQL Generation" as a sub-action using the defaults and the user input. |


### Session variables

These are the customizable session variables used in this example.

- `db_type`: Defaults to MYSQL. options are MYSQL, DB2, MONGODB, 

All other session variables will be overwritten by the Actions
