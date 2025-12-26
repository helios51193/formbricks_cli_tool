# Formbricks Synthetic Survey Generator

A CLI tool for generating synthetic surveys and responses for Formbricks, an open-source survey platform. This tool helps you quickly populate your Formbricks instance with realistic test data using OpenAI.

## Features

- Start and stop local Formbricks instances via Docker
- Generate synthetic surveys and responses using OpenAI
- Automatically seed generated surveys into Formbricks via API

## Commands

### `python main.py formbricks up`
Starts a local instance of Formbricks using Docker.

### `python main.py formbricks down`
Stops the running local Formbricks instance.

### `python main.py formbricks generate`
Generates synthetic surveys and their answers using OpenAI. Requires an OpenAI API key.

### `python main.py formbricks seed`
Uploads the generated surveys and their respective answers to Formbricks using the Formbricks API v1.

## Requirements

### 1. CLI Environment Configuration

Create a file named `cli.env` at the root of the project with the following keys:

```env
OPEN_AI_KEY=your_openai_api_key_here
FORMBRICKS_HOST=http://localhost:3000
ENVIRONMENT_ID=your_formbricks_environment_id
API_KEY=your_formbricks_api_key
```

- **OPEN_AI_KEY**: Your OpenAI API key for generating synthetic data
- **FORMBRICKS_HOST**: The URL of your Formbricks instance (use `http://localhost:3000` for local development)
- **ENVIRONMENT_ID**: Your Formbricks environment ID (refer to the [Formbricks documentation](https://formbricks.com/docs) for instructions on obtaining this)
- **API_KEY**: Your Formbricks API key (refer to the [Formbricks documentation](https://formbricks.com/docs) for generating an API key)

### 2. Formbricks Environment Configuration

Create a file named `formbricks.env` at `templates/formbricks/` with the following environment variables:

```env
DATABASE_URL=your_database_url
NEXTAUTH_SECRET=your_nextauth_secret
ENCRYPTION_KEY=your_encryption_key
CRON_SECRET=your_cron_secret
NEXTAUTH_URL=your_nextauth_url
```

These environment variables are required for running the Formbricks instance.

## Defining Survey Specifications

Survey definitions are specified in JSON format. Refer to `prompts/survey_description_prompts.json` for the expected format and structure.

The repository includes sample questions and answers to demonstrate how the JSON files should be structured for survey generation.

## Getting Started

1. Set up your environment files as described in the Requirements section
2. Start your local Formbricks instance: `formbricks up`
3. Generate synthetic surveys: `formbricks generate`
4. Seed the surveys into Formbricks: `formbricks seed`
5. When finished, stop the instance: `formbricks down`

## Documentation

For more information about Formbricks configuration and API usage, refer to the [official Formbricks documentation](https://formbricks.com/docs).