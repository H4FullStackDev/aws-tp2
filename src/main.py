import json
import boto3
import urllib.parse
import logging
import os
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['DYNAMODB_TABLE'])

# Extensions d'images autorisées
ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}

def lambda_handler(event, context):
    print("Event:", json.dumps(event))

    record = event['Records'][0]
    bucket = record['s3']['bucket']['name']
    key = urllib.parse.unquote_plus(record['s3']['object']['key'])

    file_name = key.split('/')[-1]
    extension = '.' + file_name.rsplit('.', 1)[-1].lower()

    logger.info(f"Fichier reçu : s3://{bucket}/{key}")

    # Contrôle sur l'extension
    if extension not in ALLOWED_EXTENSIONS:
        logger.warning(f"⛔ Format non autorisé : {file_name} ({extension})")
        return {
            'statusCode': 400,
            'body': json.dumps(f'Format non autorisé : {extension}')
        }

    try:
        table.put_item(
            Item={
                'PK': file_name,
                'bucket': bucket,
                'full_key': key,
            },
            ConditionExpression='attribute_not_exists(PK)'
        )
        logger.info(f"✅ Nouveau fichier enregistré : {file_name}")
        return {
            'statusCode': 200,
            'body': json.dumps(f'Fichier traité : {file_name}')
        }

    except ClientError as e:
        if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
            logger.warning(f"⛔ Doublon détecté, ignoré : {file_name}")
            return {
                'statusCode': 409,
                'body': json.dumps(f'Fichier déjà traité : {file_name}')
            }
        raise